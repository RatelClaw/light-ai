"""
User management system with user_name mapping and lifecycle management.

Provides user creation, authentication, and management with support for
human-readable usernames mapped to user_ids for simplified access.
"""

import sqlite3
import hashlib
import secrets
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from contextlib import contextmanager
import threading
import uuid
import json

from ..core.models import AccessLevel
from ..config import Config, get_config
from ..logger import get_logger
from .isolation import DataIsolationLayer
from .access_control import AccessControlLayer
from .audit_logger import AuditLogger, AuditEventType, AuditSeverity

logger = get_logger(__name__)


@dataclass
class User:
    """User information with authentication and metadata."""
    user_id: str
    client_id: str
    user_name: str  # Human-readable username (unique within client)
    email: Optional[str]
    full_name: Optional[str]
    access_level: AccessLevel
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    password_hash: Optional[str] = None  # For future authentication
    metadata: Optional[Dict[str, Any]] = None


class UserManager:
    """
    Comprehensive user management system.
    
    Manages user lifecycle including creation, authentication, permissions,
    and data isolation with support for human-readable usernames.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize user manager."""
        self.config = config or get_config()
        self.data_isolation = DataIsolationLayer(config)
        self.access_control = AccessControlLayer(config)
        self.audit_logger = AuditLogger(config)
        self._user_cache: Dict[str, User] = {}
        self._username_cache: Dict[str, str] = {}  # username -> user_id mapping
        self._cache_lock = threading.Lock()
        
        # Initialize user database
        self._init_user_database()
    
    def _init_user_database(self) -> None:
        """Initialize user management database."""
        db_path = self.config.get_full_path("security/users.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(str(db_path)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Create users table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    client_id TEXT NOT NULL,
                    user_name TEXT NOT NULL,
                    email TEXT,
                    full_name TEXT,
                    access_level TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_login TEXT,
                    password_hash TEXT,
                    metadata TEXT
                )
            """)
            
            # Create unique index on client_id + user_name
            conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_client_username 
                ON users (client_id, user_name)
            """)
            
            # Create indexes for fast lookups
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_client_id ON users (client_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_active ON users (is_active)")
            
            conn.commit()
            logger.info("User management database initialized")
    
    @contextmanager
    def _get_db_connection(self):
        """Get database connection with proper resource management."""
        db_path = self.config.get_full_path("security/users.db")
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def create_user(self, client_id: str, user_name: str, 
                   email: Optional[str] = None, full_name: Optional[str] = None,
                   access_level: AccessLevel = AccessLevel.USER,
                   metadata: Optional[Dict[str, Any]] = None) -> User:
        """
        Create a new user with complete isolation setup.
        
        Args:
            client_id: Client identifier
            user_name: Human-readable username (unique within client)
            email: Optional email address
            full_name: Optional full name
            access_level: User access level
            metadata: Optional additional metadata
            
        Returns:
            Created User object
            
        Raises:
            ValueError: If username already exists within client
        """
        # Generate unique user_id
        user_id = str(uuid.uuid4())
        
        # Validate username uniqueness within client
        if self.get_user_by_username(client_id, user_name):
            raise ValueError(f"Username '{user_name}' already exists for client '{client_id}'")
        
        # Create user record
        user = User(
            user_id=user_id,
            client_id=client_id,
            user_name=user_name,
            email=email,
            full_name=full_name,
            access_level=access_level,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata=metadata
        )
        
        try:
            # Save user to database
            self._save_user(user)
            
            # Create data isolation namespace
            namespace = self.data_isolation.create_user_namespace(
                user_id, client_id, user_name
            )
            
            # Create access control permissions
            self.access_control.create_user_permissions(
                user_id, client_id, user_name, access_level
            )
            
            # Cache user
            with self._cache_lock:
                cache_key = f"{client_id}:{user_id}"
                username_key = f"{client_id}:{user_name}"
                self._user_cache[cache_key] = user
                self._username_cache[username_key] = user_id
            
            # Log audit event
            self.audit_logger.log_event(
                event_type=AuditEventType.USER_CREATED,
                action=f"Created user {user_name}",
                severity=AuditSeverity.INFO,
                user_id=user_id,
                client_id=client_id,
                details={
                    'user_name': user_name,
                    'email': email,
                    'access_level': access_level.value
                }
            )
            
            logger.info(f"Created user: {client_id}:{user_name} ({user_id})")
            return user
            
        except Exception as e:
            logger.error(f"Failed to create user {client_id}:{user_name}: {e}")
            # Cleanup on failure
            try:
                self.delete_user(user_id, client_id)
            except:
                pass
            raise
    
    def get_user(self, user_id: str, client_id: str) -> Optional[User]:
        """
        Get user by user_id.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            
        Returns:
            User object or None if not found
        """
        cache_key = f"{client_id}:{user_id}"
        
        # Check cache first
        with self._cache_lock:
            if cache_key in self._user_cache:
                return self._user_cache[cache_key]
        
        # Load from database
        user = self._load_user(user_id, client_id)
        if user:
            with self._cache_lock:
                self._user_cache[cache_key] = user
                username_key = f"{client_id}:{user.user_name}"
                self._username_cache[username_key] = user_id
        
        return user
    
    def get_user_by_username(self, client_id: str, user_name: str) -> Optional[User]:
        """
        Get user by username within a client.
        
        Args:
            client_id: Client identifier
            user_name: Username to look up
            
        Returns:
            User object or None if not found
        """
        username_key = f"{client_id}:{user_name}"
        
        # Check cache first
        with self._cache_lock:
            if username_key in self._username_cache:
                user_id = self._username_cache[username_key]
                return self.get_user(user_id, client_id)
        
        # Load from database
        with self._get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM users WHERE client_id = ? AND user_name = ? AND is_active = 1",
                (client_id, user_name)
            )
            row = cursor.fetchone()
            
            if row:
                user = self._user_from_row(row)
                
                # Cache user
                with self._cache_lock:
                    cache_key = f"{client_id}:{user.user_id}"
                    self._user_cache[cache_key] = user
                    self._username_cache[username_key] = user.user_id
                
                return user
        
        return None
    
    def get_user_id_by_username(self, client_id: str, user_name: str) -> Optional[str]:
        """
        Get user_id by username (for simplified access).
        
        Args:
            client_id: Client identifier
            user_name: Username to look up
            
        Returns:
            User ID or None if not found
        """
        user = self.get_user_by_username(client_id, user_name)
        return user.user_id if user else None
    
    def list_users(self, client_id: str, include_inactive: bool = False) -> List[User]:
        """
        List all users for a client.
        
        Args:
            client_id: Client identifier
            include_inactive: Whether to include inactive users
            
        Returns:
            List of User objects
        """
        users = []
        
        with self._get_db_connection() as conn:
            if include_inactive:
                cursor = conn.execute(
                    "SELECT * FROM users WHERE client_id = ? ORDER BY user_name",
                    (client_id,)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM users WHERE client_id = ? AND is_active = 1 ORDER BY user_name",
                    (client_id,)
                )
            
            for row in cursor.fetchall():
                user = self._user_from_row(row)
                users.append(user)
                
                # Cache user
                with self._cache_lock:
                    cache_key = f"{client_id}:{user.user_id}"
                    username_key = f"{client_id}:{user.user_name}"
                    self._user_cache[cache_key] = user
                    self._username_cache[username_key] = user.user_id
        
        return users
    
    def update_user(self, user_id: str, client_id: str, 
                   email: Optional[str] = None, full_name: Optional[str] = None,
                   access_level: Optional[AccessLevel] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update user information.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            email: Optional new email
            full_name: Optional new full name
            access_level: Optional new access level
            metadata: Optional new metadata
            
        Returns:
            True if update was successful
        """
        user = self.get_user(user_id, client_id)
        if not user:
            return False
        
        # Update fields
        if email is not None:
            user.email = email
        if full_name is not None:
            user.full_name = full_name
        if access_level is not None:
            user.access_level = access_level
            # Update access control permissions
            self.access_control.update_user_access_level(user_id, client_id, access_level)
        if metadata is not None:
            user.metadata = metadata
        
        user.updated_at = datetime.utcnow()
        
        # Save to database
        self._save_user(user)
        
        # Update cache
        with self._cache_lock:
            cache_key = f"{client_id}:{user_id}"
            self._user_cache[cache_key] = user
        
        # Log audit event
        self.audit_logger.log_event(
            event_type=AuditEventType.USER_CREATED,  # Using USER_CREATED for updates too
            action=f"Updated user {user.user_name}",
            severity=AuditSeverity.INFO,
            user_id=user_id,
            client_id=client_id,
            details={
                'updated_fields': {
                    'email': email,
                    'full_name': full_name,
                    'access_level': access_level.value if access_level else None
                }
            }
        )
        
        logger.info(f"Updated user: {client_id}:{user.user_name}")
        return True
    
    def deactivate_user(self, user_id: str, client_id: str) -> bool:
        """
        Deactivate a user (soft delete).
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            
        Returns:
            True if deactivation was successful
        """
        user = self.get_user(user_id, client_id)
        if not user:
            return False
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        # Save to database
        self._save_user(user)
        
        # Deactivate access control permissions
        self.access_control.deactivate_user(user_id, client_id)
        
        # Remove from cache
        with self._cache_lock:
            cache_key = f"{client_id}:{user_id}"
            username_key = f"{client_id}:{user.user_name}"
            self._user_cache.pop(cache_key, None)
            self._username_cache.pop(username_key, None)
        
        # Log audit event
        self.audit_logger.log_event(
            event_type=AuditEventType.USER_DELETED,
            action=f"Deactivated user {user.user_name}",
            severity=AuditSeverity.WARNING,
            user_id=user_id,
            client_id=client_id
        )
        
        logger.info(f"Deactivated user: {client_id}:{user.user_name}")
        return True
    
    def delete_user(self, user_id: str, client_id: str, hard_delete: bool = False) -> bool:
        """
        Delete a user and all associated data.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            hard_delete: If True, permanently delete all data
            
        Returns:
            True if deletion was successful
        """
        user = self.get_user(user_id, client_id)
        if not user:
            return False
        
        try:
            if hard_delete:
                # Delete data isolation namespace (removes all user data)
                self.data_isolation.delete_user_namespace(user_id, client_id)
                
                # Delete access control permissions
                self.access_control.delete_user_permissions(user_id, client_id)
                
                # Delete user record from database
                with self._get_db_connection() as conn:
                    conn.execute("DELETE FROM users WHERE user_id = ? AND client_id = ?", 
                               (user_id, client_id))
                    conn.commit()
            else:
                # Soft delete (deactivate)
                return self.deactivate_user(user_id, client_id)
            
            # Remove from cache
            with self._cache_lock:
                cache_key = f"{client_id}:{user_id}"
                username_key = f"{client_id}:{user.user_name}"
                self._user_cache.pop(cache_key, None)
                self._username_cache.pop(username_key, None)
            
            # Log audit event
            self.audit_logger.log_event(
                event_type=AuditEventType.USER_DELETED,
                action=f"{'Hard' if hard_delete else 'Soft'} deleted user {user.user_name}",
                severity=AuditSeverity.CRITICAL if hard_delete else AuditSeverity.WARNING,
                user_id=user_id,
                client_id=client_id,
                details={'hard_delete': hard_delete}
            )
            
            logger.info(f"{'Hard' if hard_delete else 'Soft'} deleted user: {client_id}:{user.user_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete user {client_id}:{user.user_name}: {e}")
            return False
    
    def authenticate_user(self, client_id: str, user_name: str, 
                         password: Optional[str] = None) -> Optional[User]:
        """
        Authenticate user (placeholder for future authentication).
        
        Args:
            client_id: Client identifier
            user_name: Username
            password: Optional password (for future use)
            
        Returns:
            User object if authentication successful, None otherwise
        """
        user = self.get_user_by_username(client_id, user_name)
        
        if user and user.is_active:
            # Update last login
            user.last_login = datetime.utcnow()
            self._save_user(user)
            
            # Log audit event
            self.audit_logger.log_event(
                event_type=AuditEventType.USER_LOGIN,
                action=f"User {user_name} logged in",
                severity=AuditSeverity.INFO,
                user_id=user.user_id,
                client_id=client_id
            )
            
            return user
        
        # Log failed authentication
        self.audit_logger.log_event(
            event_type=AuditEventType.ACCESS_DENIED,
            action=f"Failed login attempt for user {user_name}",
            severity=AuditSeverity.WARNING,
            client_id=client_id,
            details={'user_name': user_name}
        )
        
        return None
    
    def _save_user(self, user: User) -> None:
        """Save user to database."""
        with self._get_db_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO users 
                (user_id, client_id, user_name, email, full_name, access_level, 
                 is_active, created_at, updated_at, last_login, password_hash, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user.user_id,
                user.client_id,
                user.user_name,
                user.email,
                user.full_name,
                user.access_level.value,
                user.is_active,
                user.created_at.isoformat(),
                user.updated_at.isoformat(),
                user.last_login.isoformat() if user.last_login else None,
                user.password_hash,
                json.dumps(user.metadata) if user.metadata else None
            ))
            conn.commit()
    
    def _load_user(self, user_id: str, client_id: str) -> Optional[User]:
        """Load user from database."""
        with self._get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM users WHERE user_id = ? AND client_id = ?",
                (user_id, client_id)
            )
            row = cursor.fetchone()
            
            if row:
                return self._user_from_row(row)
        
        return None
    
    def _user_from_row(self, row: sqlite3.Row) -> User:
        """Create User object from database row."""
        return User(
            user_id=row['user_id'],
            client_id=row['client_id'],
            user_name=row['user_name'],
            email=row['email'],
            full_name=row['full_name'],
            access_level=AccessLevel(row['access_level']),
            is_active=bool(row['is_active']),
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None,
            password_hash=row['password_hash'],
            metadata=json.loads(row['metadata']) if row['metadata'] else None
        )
    
    def get_user_statistics(self, client_id: str) -> Dict[str, Any]:
        """
        Get user statistics for a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            User statistics
        """
        with self._get_db_connection() as conn:
            # Total users
            cursor = conn.execute(
                "SELECT COUNT(*) as total FROM users WHERE client_id = ?",
                (client_id,)
            )
            total_users = cursor.fetchone()['total']
            
            # Active users
            cursor = conn.execute(
                "SELECT COUNT(*) as active FROM users WHERE client_id = ? AND is_active = 1",
                (client_id,)
            )
            active_users = cursor.fetchone()['active']
            
            # Users by access level
            cursor = conn.execute(
                "SELECT access_level, COUNT(*) as count FROM users WHERE client_id = ? AND is_active = 1 GROUP BY access_level",
                (client_id,)
            )
            users_by_level = {row['access_level']: row['count'] for row in cursor.fetchall()}
            
            # Recent logins (last 30 days)
            thirty_days_ago = datetime.utcnow().replace(day=datetime.utcnow().day - 30)
            cursor = conn.execute(
                "SELECT COUNT(*) as recent FROM users WHERE client_id = ? AND last_login > ?",
                (client_id, thirty_days_ago.isoformat())
            )
            recent_logins = cursor.fetchone()['recent']
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': total_users - active_users,
            'users_by_access_level': users_by_level,
            'recent_logins_30_days': recent_logins
        }
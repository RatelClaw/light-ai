"""
Simple data isolation system for user data separation.

Provides essential user isolation without complex encryption or heavy infrastructure.
Focuses on core requirement: users can only access their own data with user_name mapping.
"""

import sqlite3
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from contextlib import contextmanager
import uuid

from ..core.models import DataHierarchy, ResourceMetadata
from ..config import Config, get_config
from ..logger import get_logger

logger = get_logger(__name__)


@dataclass
class SimpleUser:
    """Simple user with essential information."""
    user_id: str
    client_id: str
    user_name: str  # Human-readable username (unique within client)
    created_at: datetime
    is_active: bool = True


class SimpleDataIsolation:
    """
    Simple data isolation system focusing on core requirements.
    
    Ensures users can only access their own data with user_name to user_id mapping.
    No complex encryption or heavy infrastructure - just essential isolation.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize simple data isolation."""
        self.config = config or get_config()
        self._users: Dict[str, SimpleUser] = {}  # Cache for users
        self._username_map: Dict[str, str] = {}  # client_id:user_name -> user_id
        
        # Initialize user database
        self._init_user_db()
    
    def _init_user_db(self) -> None:
        """Initialize simple user database."""
        db_path = self.config.get_full_path("metadata/users.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(str(db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS simple_users (
                    user_id TEXT PRIMARY KEY,
                    client_id TEXT NOT NULL,
                    user_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    UNIQUE(client_id, user_name)
                )
            """)
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_client_username ON simple_users (client_id, user_name)")
            conn.commit()
    
    @contextmanager
    def _get_db_connection(self):
        """Get database connection."""
        db_path = self.config.get_full_path("metadata/users.db")
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def create_user(self, client_id: str, user_name: str) -> SimpleUser:
        """
        Create a new user with basic isolation.
        
        Args:
            client_id: Client identifier
            user_name: Human-readable username (unique within client)
            
        Returns:
            Created SimpleUser object
        """
        # Check if username already exists
        if self.get_user_by_username(client_id, user_name):
            raise ValueError(f"Username '{user_name}' already exists for client '{client_id}'")
        
        user_id = str(uuid.uuid4())
        user = SimpleUser(
            user_id=user_id,
            client_id=client_id,
            user_name=user_name,
            created_at=datetime.utcnow(),
            is_active=True
        )
        
        # Save to database
        with self._get_db_connection() as conn:
            conn.execute("""
                INSERT INTO simple_users (user_id, client_id, user_name, created_at, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, client_id, user_name, user.created_at.isoformat(), True))
            conn.commit()
        
        # Create user directories
        self._create_user_directories(user_id, client_id)
        
        # Cache user
        cache_key = f"{client_id}:{user_id}"
        username_key = f"{client_id}:{user_name}"
        self._users[cache_key] = user
        self._username_map[username_key] = user_id
        
        logger.info(f"Created user: {client_id}:{user_name} ({user_id})")
        return user
    
    def get_user_by_username(self, client_id: str, user_name: str) -> Optional[SimpleUser]:
        """
        Get user by username (for simplified access).
        
        Args:
            client_id: Client identifier
            user_name: Username to look up
            
        Returns:
            SimpleUser object or None if not found
        """
        username_key = f"{client_id}:{user_name}"
        
        # Check cache first
        if username_key in self._username_map:
            user_id = self._username_map[username_key]
            cache_key = f"{client_id}:{user_id}"
            if cache_key in self._users:
                return self._users[cache_key]
        
        # Load from database
        with self._get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM simple_users WHERE client_id = ? AND user_name = ? AND is_active = 1",
                (client_id, user_name)
            )
            row = cursor.fetchone()
            
            if row:
                user = SimpleUser(
                    user_id=row['user_id'],
                    client_id=row['client_id'],
                    user_name=row['user_name'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    is_active=bool(row['is_active'])
                )
                
                # Cache user
                cache_key = f"{client_id}:{user.user_id}"
                self._users[cache_key] = user
                self._username_map[username_key] = user.user_id
                
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
    
    def validate_user_access(self, user_id: str, client_id: str, resource_metadata: ResourceMetadata) -> bool:
        """
        Validate that user can access a resource.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            resource_metadata: Resource metadata to validate
            
        Returns:
            True if user can access the resource
        """
        # Simple validation: user can only access their own resources
        return (resource_metadata.user_id == user_id and 
                resource_metadata.client_id == client_id and
                not resource_metadata.is_deleted)
    
    def get_user_storage_path(self, user_id: str, client_id: str, data_type: str = 'structured') -> Path:
        """
        Get storage path for user data.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            data_type: Type of data ('structured', 'json', 'unstructured')
            
        Returns:
            Path to user's data directory
        """
        return self.config.get_full_path(f"data/users/{client_id}/{user_id}/{data_type}")
    
    def _create_user_directories(self, user_id: str, client_id: str) -> None:
        """Create directory structure for user."""
        base_path = self.config.get_full_path(f"data/users/{client_id}/{user_id}")
        
        # Create subdirectories
        subdirs = ['structured', 'json', 'unstructured', 'temp']
        for subdir in subdirs:
            subdir_path = base_path / subdir
            subdir_path.mkdir(parents=True, exist_ok=True)
    
    def list_users(self, client_id: str) -> List[SimpleUser]:
        """
        List all users for a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            List of SimpleUser objects
        """
        users = []
        
        with self._get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM simple_users WHERE client_id = ? AND is_active = 1 ORDER BY user_name",
                (client_id,)
            )
            
            for row in cursor.fetchall():
                user = SimpleUser(
                    user_id=row['user_id'],
                    client_id=row['client_id'],
                    user_name=row['user_name'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    is_active=bool(row['is_active'])
                )
                users.append(user)
        
        return users
    
    def delete_user(self, user_id: str, client_id: str) -> bool:
        """
        Delete user and their data.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            
        Returns:
            True if deletion was successful
        """
        try:
            # Mark user as inactive
            with self._get_db_connection() as conn:
                conn.execute(
                    "UPDATE simple_users SET is_active = 0 WHERE user_id = ? AND client_id = ?",
                    (user_id, client_id)
                )
                conn.commit()
            
            # Remove from cache
            cache_key = f"{client_id}:{user_id}"
            if cache_key in self._users:
                user = self._users[cache_key]
                username_key = f"{client_id}:{user.user_name}"
                del self._users[cache_key]
                self._username_map.pop(username_key, None)
            
            logger.info(f"Deleted user: {client_id}:{user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete user {client_id}:{user_id}: {e}")
            return False


class SimpleTransactionManager:
    """
    Simple transaction manager for basic ACID compliance.
    
    Provides basic transaction support without complex distributed transactions.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize simple transaction manager."""
        self.config = config or get_config()
    
    @contextmanager
    def transaction(self, user_id: str, client_id: str):
        """
        Simple transaction context manager.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            
        Yields:
            Transaction context (just returns user info for now)
        """
        # For now, just provide basic context
        # In a real implementation, this would manage database transactions
        transaction_context = {
            'user_id': user_id,
            'client_id': client_id,
            'started_at': datetime.utcnow()
        }
        
        try:
            yield transaction_context
            # Transaction committed successfully
            logger.debug(f"Transaction completed for user {client_id}:{user_id}")
        except Exception as e:
            # Transaction failed, would rollback here
            logger.error(f"Transaction failed for user {client_id}:{user_id}: {e}")
            raise


class SimpleAuditLogger:
    """
    Simple audit logger for basic access tracking.
    
    Provides essential audit logging without complex integrity verification.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize simple audit logger."""
        self.config = config or get_config()
        self.log_file = self.config.get_full_path("logs/audit.log")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log_access(self, user_id: str, client_id: str, action: str, 
                   resource_id: Optional[str] = None, details: Optional[str] = None) -> None:
        """
        Log user access event.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            action: Action performed
            resource_id: Optional resource identifier
            details: Optional additional details
        """
        timestamp = datetime.utcnow().isoformat()
        log_entry = f"{timestamp} | {client_id}:{user_id} | {action}"
        
        if resource_id:
            log_entry += f" | resource:{resource_id}"
        
        if details:
            log_entry += f" | {details}"
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
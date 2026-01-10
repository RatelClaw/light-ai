"""
Data isolation layer for strict user data separation.

Provides complete data isolation between users with ACID compliance,
isolated database schemas, and secure file system organization.
"""

import sqlite3
import duckdb
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from contextlib import contextmanager
import threading
import uuid

from ..core.models import DataHierarchy, ResourceMetadata
from ..config import Config, get_config
from ..logger import get_logger
from .encryption import UserEncryptionManager
from .transaction_manager import TransactionManager

logger = get_logger(__name__)


@dataclass
class UserNamespace:
    """Isolated namespace for user data."""
    user_id: str
    client_id: str
    user_name: Optional[str]
    encryption_key_id: str
    database_schema: str
    storage_path: str
    created_at: datetime
    last_accessed: datetime
    is_active: bool = True


class DatabaseIsolationManager:
    """
    Manages isolated database schemas for each user.
    
    Creates separate schemas in DuckDB and SQLite for complete data isolation.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize database isolation manager."""
        self.config = config or get_config()
        self._schema_locks: Dict[str, threading.Lock] = {}
        self._lock = threading.Lock()
    
    def _get_schema_lock(self, schema_name: str) -> threading.Lock:
        """Get or create a lock for a specific schema."""
        with self._lock:
            if schema_name not in self._schema_locks:
                self._schema_locks[schema_name] = threading.Lock()
            return self._schema_locks[schema_name]
    
    def create_user_schema(self, user_id: str, client_id: str) -> str:
        """
        Create isolated database schema for a user.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            
        Returns:
            Schema name created
        """
        # Create schema name that's safe for SQL
        schema_name = f"user_{client_id.replace('-', '_')}_{user_id.replace('-', '_')}"
        
        # Create schema in DuckDB
        self._create_duckdb_schema(schema_name)
        
        # Create schema in SQLite (using separate database file)
        self._create_sqlite_schema(schema_name, user_id, client_id)
        
        logger.info(f"Created isolated database schema: {schema_name}")
        return schema_name
    
    def _create_duckdb_schema(self, schema_name: str) -> None:
        """Create schema in DuckDB."""
        db_path = self.config.get_full_path(self.config.database.duckdb_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with duckdb.connect(str(db_path)) as conn:
            # Create schema
            conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
            
            # Create user-specific tables within the schema
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {schema_name}.structured_data (
                    table_name VARCHAR PRIMARY KEY,
                    resource_id VARCHAR NOT NULL,
                    file_path VARCHAR NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    row_count INTEGER,
                    column_count INTEGER
                )
            """)
            
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {schema_name}.json_data (
                    id VARCHAR PRIMARY KEY,
                    resource_id VARCHAR NOT NULL,
                    data JSON NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            logger.debug(f"Created DuckDB schema: {schema_name}")
    
    def _create_sqlite_schema(self, schema_name: str, user_id: str, client_id: str) -> None:
        """Create isolated SQLite database for user metadata."""
        # Create user-specific SQLite database
        user_db_path = self.config.get_full_path(f"metadata/users/{client_id}_{user_id}.db")
        user_db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(str(user_db_path)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Create user-specific metadata tables
            conn.execute("""
                CREATE TABLE IF NOT EXISTS resource_metadata (
                    resource_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    client_id TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    file_size_bytes INTEGER NOT NULL,
                    storage_path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    is_deleted BOOLEAN NOT NULL DEFAULT 0,
                    row_count INTEGER,
                    column_count INTEGER,
                    chunk_count INTEGER,
                    file_hash TEXT,
                    content_preview TEXT,
                    processing_status TEXT NOT NULL DEFAULT 'pending',
                    error_message TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_info (
                    schema_id TEXT PRIMARY KEY,
                    resource_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    schema_json TEXT NOT NULL,
                    statistics_json TEXT NOT NULL,
                    detected_at TEXT NOT NULL,
                    FOREIGN KEY (resource_id) REFERENCES resource_metadata (resource_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_trail (
                    audit_id TEXT PRIMARY KEY,
                    resource_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    client_id TEXT NOT NULL,
                    operation_details TEXT,
                    timestamp TEXT NOT NULL,
                    version_before INTEGER,
                    version_after INTEGER
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_resource_user_id ON resource_metadata (user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_resource_client_id ON resource_metadata (client_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_trail (timestamp)")
            
            conn.commit()
            logger.debug(f"Created SQLite schema for user: {client_id}:{user_id}")
    
    @contextmanager
    def get_user_duckdb_connection(self, schema_name: str):
        """Get DuckDB connection with user schema context."""
        db_path = self.config.get_full_path(self.config.database.duckdb_path)
        
        with self._get_schema_lock(schema_name):
            conn = duckdb.connect(str(db_path))
            try:
                # Set default schema for this connection
                conn.execute(f"SET schema = '{schema_name}'")
                yield conn
            finally:
                conn.close()
    
    @contextmanager
    def get_user_sqlite_connection(self, user_id: str, client_id: str):
        """Get SQLite connection for user-specific metadata."""
        user_db_path = self.config.get_full_path(f"metadata/users/{client_id}_{user_id}.db")
        
        conn = sqlite3.connect(str(user_db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def delete_user_schema(self, user_id: str, client_id: str) -> bool:
        """
        Delete user's isolated database schema.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            
        Returns:
            True if deletion was successful
        """
        try:
            schema_name = f"user_{client_id.replace('-', '_')}_{user_id.replace('-', '_')}"
            
            # Drop DuckDB schema
            db_path = self.config.get_full_path(self.config.database.duckdb_path)
            with duckdb.connect(str(db_path)) as conn:
                conn.execute(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE")
            
            # Delete SQLite database file
            user_db_path = self.config.get_full_path(f"metadata/users/{client_id}_{user_id}.db")
            if user_db_path.exists():
                user_db_path.unlink()
            
            # Remove schema lock
            with self._lock:
                if schema_name in self._schema_locks:
                    del self._schema_locks[schema_name]
            
            logger.info(f"Deleted database schema for user {client_id}:{user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete user schema for {client_id}:{user_id}: {e}")
            return False


class FileSystemIsolationManager:
    """
    Manages isolated file system organization for each user.
    
    Creates secure directory structures with proper permissions.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize file system isolation manager."""
        self.config = config or get_config()
    
    def create_user_directories(self, user_id: str, client_id: str) -> Path:
        """
        Create isolated directory structure for a user.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            
        Returns:
            Path to user's root directory
        """
        # Create user directory structure
        user_root = self.config.get_full_path(f"data/isolated/{client_id}/{user_id}")
        
        # Create subdirectories
        subdirs = [
            'structured',
            'json', 
            'unstructured',
            'temp',
            'cache',
            'exports'
        ]
        
        for subdir in subdirs:
            subdir_path = user_root / subdir
            subdir_path.mkdir(parents=True, exist_ok=True)
            
            # Set restrictive permissions (owner read/write/execute only)
            import os
            os.chmod(subdir_path, 0o700)
        
        logger.info(f"Created isolated directories for user {client_id}:{user_id}")
        return user_root
    
    def get_user_storage_path(self, user_id: str, client_id: str, 
                             data_type: str = 'structured') -> Path:
        """
        Get storage path for user data.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            data_type: Type of data ('structured', 'json', 'unstructured')
            
        Returns:
            Path to user's data directory
        """
        return self.config.get_full_path(f"data/isolated/{client_id}/{user_id}/{data_type}")
    
    def delete_user_directories(self, user_id: str, client_id: str) -> bool:
        """
        Delete user's isolated directory structure.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            
        Returns:
            True if deletion was successful
        """
        try:
            import shutil
            
            user_root = self.config.get_full_path(f"data/isolated/{client_id}/{user_id}")
            if user_root.exists():
                shutil.rmtree(user_root)
            
            logger.info(f"Deleted isolated directories for user {client_id}:{user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete user directories for {client_id}:{user_id}: {e}")
            return False


class DataIsolationLayer:
    """
    Main data isolation layer ensuring complete user data separation.
    
    Combines database isolation, file system isolation, and encryption
    to provide comprehensive data protection with ACID compliance.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize data isolation layer."""
        self.config = config or get_config()
        self.encryption_manager = UserEncryptionManager(config)
        self.db_isolation = DatabaseIsolationManager(config)
        self.fs_isolation = FileSystemIsolationManager(config)
        self.transaction_manager = TransactionManager(config)
        self.user_namespaces: Dict[str, UserNamespace] = {}
        self._namespace_lock = threading.Lock()
    
    def create_user_namespace(self, user_id: str, client_id: str, 
                             user_name: Optional[str] = None) -> UserNamespace:
        """
        Create complete isolated namespace for a user.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            user_name: Optional human-readable username
            
        Returns:
            UserNamespace object
        """
        with self._namespace_lock:
            namespace_key = f"{client_id}:{user_id}"
            
            if namespace_key in self.user_namespaces:
                return self.user_namespaces[namespace_key]
            
            # Create encryption namespace
            encryption_info = self.encryption_manager.create_user_namespace(
                user_id, client_id, user_name
            )
            
            # Create database schema
            schema_name = self.db_isolation.create_user_schema(user_id, client_id)
            
            # Create file system directories
            storage_path = self.fs_isolation.create_user_directories(user_id, client_id)
            
            # Create namespace object
            namespace = UserNamespace(
                user_id=user_id,
                client_id=client_id,
                user_name=user_name,
                encryption_key_id=encryption_info['key_id'],
                database_schema=schema_name,
                storage_path=str(storage_path),
                created_at=datetime.utcnow(),
                last_accessed=datetime.utcnow(),
                is_active=True
            )
            
            # Cache namespace
            self.user_namespaces[namespace_key] = namespace
            
            logger.info(f"Created complete user namespace: {client_id}:{user_id}")
            return namespace
    
    def get_user_namespace(self, user_id: str, client_id: str) -> Optional[UserNamespace]:
        """
        Get user namespace if it exists.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            
        Returns:
            UserNamespace object or None if not found
        """
        namespace_key = f"{client_id}:{user_id}"
        
        with self._namespace_lock:
            if namespace_key in self.user_namespaces:
                namespace = self.user_namespaces[namespace_key]
                namespace.last_accessed = datetime.utcnow()
                return namespace
        
        # Try to load from storage
        encryption_info = self.encryption_manager.get_user_namespace_info(user_id, client_id)
        if encryption_info:
            schema_name = f"user_{client_id.replace('-', '_')}_{user_id.replace('-', '_')}"
            storage_path = self.config.get_full_path(f"data/isolated/{client_id}/{user_id}")
            
            namespace = UserNamespace(
                user_id=user_id,
                client_id=client_id,
                user_name=encryption_info.get('user_name'),
                encryption_key_id=encryption_info['key_id'],
                database_schema=schema_name,
                storage_path=str(storage_path),
                created_at=datetime.fromisoformat(encryption_info['created_at']),
                last_accessed=datetime.utcnow(),
                is_active=True
            )
            
            with self._namespace_lock:
                self.user_namespaces[namespace_key] = namespace
            
            return namespace
        
        return None
    
    def validate_data_access(self, user_id: str, client_id: str, 
                           resource_ids: List[str]) -> bool:
        """
        Validate that user can access specified resources.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            resource_ids: List of resource IDs to validate
            
        Returns:
            True if user can access all resources
        """
        namespace = self.get_user_namespace(user_id, client_id)
        if not namespace or not namespace.is_active:
            return False
        
        # Check each resource belongs to this user
        try:
            with self.db_isolation.get_user_sqlite_connection(user_id, client_id) as conn:
                for resource_id in resource_ids:
                    cursor = conn.execute(
                        "SELECT user_id, client_id FROM resource_metadata WHERE resource_id = ? AND is_deleted = 0",
                        (resource_id,)
                    )
                    row = cursor.fetchone()
                    
                    if not row or row['user_id'] != user_id or row['client_id'] != client_id:
                        logger.warning(f"Access denied: User {client_id}:{user_id} cannot access resource {resource_id}")
                        return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating data access: {e}")
            return False
    
    @contextmanager
    def get_isolated_connection(self, user_id: str, client_id: str, db_type: str = 'duckdb'):
        """
        Get isolated database connection for a user.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            db_type: Database type ('duckdb' or 'sqlite')
            
        Yields:
            Database connection within user's isolated schema
        """
        namespace = self.get_user_namespace(user_id, client_id)
        if not namespace:
            raise ValueError(f"No namespace found for user {client_id}:{user_id}")
        
        if db_type == 'duckdb':
            with self.db_isolation.get_user_duckdb_connection(namespace.database_schema) as conn:
                yield conn
        elif db_type == 'sqlite':
            with self.db_isolation.get_user_sqlite_connection(user_id, client_id) as conn:
                yield conn
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def execute_isolated_query(self, user_id: str, client_id: str, 
                              query: str, parameters: Optional[List] = None,
                              db_type: str = 'duckdb') -> List[Dict[str, Any]]:
        """
        Execute query within user's isolated environment.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            query: SQL query to execute
            parameters: Optional query parameters
            db_type: Database type ('duckdb' or 'sqlite')
            
        Returns:
            Query results
        """
        with self.get_isolated_connection(user_id, client_id, db_type) as conn:
            if db_type == 'duckdb':
                if parameters:
                    result = conn.execute(query, parameters)
                else:
                    result = conn.execute(query)
                
                columns = [desc[0] for desc in result.description]
                rows = result.fetchall()
                return [dict(zip(columns, row)) for row in rows]
            
            elif db_type == 'sqlite':
                if parameters:
                    cursor = conn.execute(query, parameters)
                else:
                    cursor = conn.execute(query)
                
                return [dict(row) for row in cursor.fetchall()]
    
    def delete_user_namespace(self, user_id: str, client_id: str) -> bool:
        """
        Delete complete user namespace and all data.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            
        Returns:
            True if deletion was successful
        """
        try:
            # Remove from cache
            namespace_key = f"{client_id}:{user_id}"
            with self._namespace_lock:
                if namespace_key in self.user_namespaces:
                    del self.user_namespaces[namespace_key]
            
            # Delete encryption namespace
            self.encryption_manager.delete_user_namespace(user_id, client_id)
            
            # Delete database schema
            self.db_isolation.delete_user_schema(user_id, client_id)
            
            # Delete file system directories
            self.fs_isolation.delete_user_directories(user_id, client_id)
            
            logger.info(f"Deleted complete user namespace: {client_id}:{user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete user namespace for {client_id}:{user_id}: {e}")
            return False
    
    def list_user_namespaces(self, client_id: str) -> List[UserNamespace]:
        """
        List all user namespaces for a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            List of UserNamespace objects
        """
        namespaces = []
        encryption_namespaces = self.encryption_manager.list_user_namespaces(client_id)
        
        for enc_info in encryption_namespaces:
            user_id = enc_info['user_id']
            namespace = self.get_user_namespace(user_id, client_id)
            if namespace:
                namespaces.append(namespace)
        
        return namespaces
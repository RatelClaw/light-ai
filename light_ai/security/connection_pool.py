"""
Database connection pooling with user isolation.

Provides connection pooling for DuckDB and SQLite with proper user isolation,
connection lifecycle management, and resource optimization.
"""

import sqlite3
import duckdb
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from contextlib import contextmanager
from queue import Queue, Empty
from datetime import datetime

from ..config import Config, get_config
from ..logger import get_logger

logger = get_logger(__name__)


@dataclass
class PooledConnection:
    """Pooled database connection with metadata."""
    connection: Any  # sqlite3.Connection or duckdb.DuckDBPyConnection
    created_at: datetime
    last_used: datetime
    use_count: int
    is_active: bool
    user_schema: Optional[str] = None


class ConnectionPool:
    """
    Base connection pool with lifecycle management.
    """
    
    def __init__(self, max_connections: int = 10, max_idle_time: int = 300):
        """
        Initialize connection pool.
        
        Args:
            max_connections: Maximum number of connections in pool
            max_idle_time: Maximum idle time in seconds before connection is closed
        """
        self.max_connections = max_connections
        self.max_idle_time = max_idle_time
        self._pool: Queue = Queue(maxsize=max_connections)
        self._active_connections: Dict[int, PooledConnection] = {}
        self._lock = threading.Lock()
        self._cleanup_thread = None
        self._shutdown = False
        
        # Start cleanup thread
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self) -> None:
        """Start background thread for connection cleanup."""
        def cleanup_worker():
            while not self._shutdown:
                try:
                    self._cleanup_idle_connections()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    logger.error(f"Error in connection cleanup: {e}")
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()
    
    def _cleanup_idle_connections(self) -> None:
        """Clean up idle connections."""
        current_time = datetime.utcnow()
        
        with self._lock:
            # Check pooled connections
            idle_connections = []
            
            try:
                while True:
                    pooled_conn = self._pool.get_nowait()
                    
                    idle_time = (current_time - pooled_conn.last_used).total_seconds()
                    
                    if idle_time > self.max_idle_time:
                        idle_connections.append(pooled_conn)
                    else:
                        self._pool.put(pooled_conn)
            except Empty:
                pass
            
            # Close idle connections
            for pooled_conn in idle_connections:
                try:
                    pooled_conn.connection.close()
                    logger.debug("Closed idle connection")
                except Exception as e:
                    logger.warning(f"Error closing idle connection: {e}")
    
    def _create_connection(self) -> Any:
        """Create new database connection (to be implemented by subclasses)."""
        raise NotImplementedError
    
    def _validate_connection(self, connection: Any) -> bool:
        """Validate that connection is still active (to be implemented by subclasses)."""
        raise NotImplementedError
    
    def get_connection(self) -> PooledConnection:
        """
        Get connection from pool.
        
        Returns:
            PooledConnection object
        """
        with self._lock:
            # Try to get connection from pool
            try:
                pooled_conn = self._pool.get_nowait()
                
                # Validate connection
                if self._validate_connection(pooled_conn.connection):
                    pooled_conn.last_used = datetime.utcnow()
                    pooled_conn.use_count += 1
                    return pooled_conn
                else:
                    # Connection is invalid, close it
                    try:
                        pooled_conn.connection.close()
                    except:
                        pass
            except Empty:
                pass
            
            # Create new connection if pool is empty or connection was invalid
            connection = self._create_connection()
            pooled_conn = PooledConnection(
                connection=connection,
                created_at=datetime.utcnow(),
                last_used=datetime.utcnow(),
                use_count=1,
                is_active=True
            )
            
            return pooled_conn
    
    def return_connection(self, pooled_conn: PooledConnection) -> None:
        """
        Return connection to pool.
        
        Args:
            pooled_conn: Connection to return
        """
        if not pooled_conn.is_active:
            try:
                pooled_conn.connection.close()
            except:
                pass
            return
        
        pooled_conn.last_used = datetime.utcnow()
        
        try:
            self._pool.put_nowait(pooled_conn)
        except:
            # Pool is full, close connection
            try:
                pooled_conn.connection.close()
            except:
                pass
    
    def close_all(self) -> None:
        """Close all connections and shutdown pool."""
        self._shutdown = True
        
        with self._lock:
            # Close pooled connections
            while True:
                try:
                    pooled_conn = self._pool.get_nowait()
                    try:
                        pooled_conn.connection.close()
                    except:
                        pass
                except Empty:
                    break
            
            # Close active connections
            for pooled_conn in self._active_connections.values():
                try:
                    pooled_conn.connection.close()
                except:
                    pass
            
            self._active_connections.clear()
        
        logger.info("Connection pool closed")


class DuckDBConnectionPool(ConnectionPool):
    """
    DuckDB connection pool with user schema isolation.
    """
    
    def __init__(self, db_path: Path, max_connections: int = 10, max_idle_time: int = 300):
        """
        Initialize DuckDB connection pool.
        
        Args:
            db_path: Path to DuckDB database file
            max_connections: Maximum number of connections
            max_idle_time: Maximum idle time in seconds
        """
        self.db_path = db_path
        super().__init__(max_connections, max_idle_time)
    
    def _create_connection(self) -> duckdb.DuckDBPyConnection:
        """Create new DuckDB connection."""
        connection = duckdb.connect(str(self.db_path))
        
        # Install required extensions
        extensions = ['json', 'parquet']
        for extension in extensions:
            try:
                connection.execute(f"INSTALL {extension}")
                connection.execute(f"LOAD {extension}")
            except:
                pass  # Extension might already be installed
        
        return connection
    
    def _validate_connection(self, connection: duckdb.DuckDBPyConnection) -> bool:
        """Validate DuckDB connection."""
        try:
            connection.execute("SELECT 1")
            return True
        except:
            return False
    
    @contextmanager
    def get_user_connection(self, user_schema: str):
        """
        Get DuckDB connection with user schema set.
        
        Args:
            user_schema: User schema name
            
        Yields:
            DuckDB connection with schema context
        """
        pooled_conn = self.get_connection()
        
        try:
            # Set user schema
            pooled_conn.connection.execute(f"SET schema = '{user_schema}'")
            pooled_conn.user_schema = user_schema
            
            yield pooled_conn.connection
        finally:
            # Reset schema
            try:
                pooled_conn.connection.execute("SET schema = 'main'")
                pooled_conn.user_schema = None
            except:
                pass
            
            self.return_connection(pooled_conn)


class SQLiteConnectionPool(ConnectionPool):
    """
    SQLite connection pool for user-specific databases.
    """
    
    def __init__(self, db_path: Path, max_connections: int = 5, max_idle_time: int = 300):
        """
        Initialize SQLite connection pool.
        
        Args:
            db_path: Path to SQLite database file
            max_connections: Maximum number of connections
            max_idle_time: Maximum idle time in seconds
        """
        self.db_path = db_path
        super().__init__(max_connections, max_idle_time)
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create new SQLite connection."""
        connection = sqlite3.connect(str(self.db_path))
        connection.execute("PRAGMA foreign_keys = ON")
        connection.row_factory = sqlite3.Row
        return connection
    
    def _validate_connection(self, connection: sqlite3.Connection) -> bool:
        """Validate SQLite connection."""
        try:
            connection.execute("SELECT 1")
            return True
        except:
            return False
    
    @contextmanager
    def get_connection_context(self):
        """
        Get SQLite connection with context management.
        
        Yields:
            SQLite connection
        """
        pooled_conn = self.get_connection()
        
        try:
            yield pooled_conn.connection
        finally:
            self.return_connection(pooled_conn)


class IsolatedConnectionManager:
    """
    Connection manager with user isolation.
    
    Manages separate connection pools for each user to ensure complete isolation.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize isolated connection manager."""
        self.config = config or get_config()
        self._duckdb_pools: Dict[str, DuckDBConnectionPool] = {}
        self._sqlite_pools: Dict[str, SQLiteConnectionPool] = {}
        self._pool_lock = threading.Lock()
    
    def get_duckdb_pool(self, user_schema: str) -> DuckDBConnectionPool:
        """
        Get DuckDB connection pool for user schema.
        
        Args:
            user_schema: User schema name
            
        Returns:
            DuckDB connection pool
        """
        with self._pool_lock:
            if user_schema not in self._duckdb_pools:
                db_path = self.config.get_full_path(self.config.database.duckdb_path)
                self._duckdb_pools[user_schema] = DuckDBConnectionPool(db_path)
            
            return self._duckdb_pools[user_schema]
    
    def get_sqlite_pool(self, user_id: str, client_id: str) -> SQLiteConnectionPool:
        """
        Get SQLite connection pool for user.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            
        Returns:
            SQLite connection pool
        """
        pool_key = f"{client_id}_{user_id}"
        
        with self._pool_lock:
            if pool_key not in self._sqlite_pools:
                db_path = self.config.get_full_path(f"metadata/users/{client_id}_{user_id}.db")
                self._sqlite_pools[pool_key] = SQLiteConnectionPool(db_path)
            
            return self._sqlite_pools[pool_key]
    
    @contextmanager
    def get_user_duckdb_connection(self, user_schema: str):
        """
        Get isolated DuckDB connection for user.
        
        Args:
            user_schema: User schema name
            
        Yields:
            DuckDB connection with user schema context
        """
        pool = self.get_duckdb_pool(user_schema)
        with pool.get_user_connection(user_schema) as conn:
            yield conn
    
    @contextmanager
    def get_user_sqlite_connection(self, user_id: str, client_id: str):
        """
        Get isolated SQLite connection for user.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            
        Yields:
            SQLite connection for user's database
        """
        pool = self.get_sqlite_pool(user_id, client_id)
        with pool.get_connection_context() as conn:
            yield conn
    
    def close_user_pools(self, user_id: str, client_id: str) -> None:
        """
        Close connection pools for a specific user.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
        """
        with self._pool_lock:
            # Close SQLite pool
            sqlite_key = f"{client_id}_{user_id}"
            if sqlite_key in self._sqlite_pools:
                self._sqlite_pools[sqlite_key].close_all()
                del self._sqlite_pools[sqlite_key]
            
            # Close DuckDB pool for user schema
            user_schema = f"user_{client_id.replace('-', '_')}_{user_id.replace('-', '_')}"
            if user_schema in self._duckdb_pools:
                self._duckdb_pools[user_schema].close_all()
                del self._duckdb_pools[user_schema]
        
        logger.info(f"Closed connection pools for user {client_id}:{user_id}")
    
    def close_all_pools(self) -> None:
        """Close all connection pools."""
        with self._pool_lock:
            # Close all DuckDB pools
            for pool in self._duckdb_pools.values():
                pool.close_all()
            self._duckdb_pools.clear()
            
            # Close all SQLite pools
            for pool in self._sqlite_pools.values():
                pool.close_all()
            self._sqlite_pools.clear()
        
        logger.info("Closed all connection pools")
    
    def get_pool_statistics(self) -> Dict[str, Any]:
        """
        Get connection pool statistics.
        
        Returns:
            Pool statistics
        """
        with self._pool_lock:
            return {
                'duckdb_pools': len(self._duckdb_pools),
                'sqlite_pools': len(self._sqlite_pools),
                'total_pools': len(self._duckdb_pools) + len(self._sqlite_pools)
            }
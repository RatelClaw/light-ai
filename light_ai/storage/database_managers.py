"""
Database connection managers for Universal Data Handler.

Provides connection management for DuckDB, ChromaDB, and SQLite databases
with proper initialization, connection pooling, and error handling.
"""

import sqlite3
import duckdb
import chromadb
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from threading import Lock
import json

from ..config import Config, get_config
from ..logger import get_logger

logger = get_logger(__name__)


class DuckDBManager:
    """
    Manages DuckDB connections for structured and JSON data storage.
    
    Handles both in-memory and persistent DuckDB databases with support for
    virtual tables, JSONB storage, and query optimization.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize DuckDB manager.
        
        Args:
            config: Optional configuration instance
        """
        self.config = config or get_config()
        self.db_path = self.config.get_full_path(self.config.database.duckdb_path)
        self._connection = None
        self._lock = Lock()
        
    def initialize(self) -> None:
        """
        Initialize DuckDB database and create necessary extensions.
        
        Sets up the database file, installs required extensions, and creates
        initial schemas for structured and JSON data.
        """
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with self._lock:
            try:
                # Close existing connection if any
                if self._connection:
                    try:
                        self._connection.close()
                    except:
                        pass
                    self._connection = None
                
                # Create connection to persistent database
                self._connection = duckdb.connect(str(self.db_path))
                
                # Install and load required extensions
                self._setup_extensions()
                
                # Create schemas for different data types
                self._create_schemas()
                
                logger.info(f"DuckDB initialized at: {self.db_path}")
                
            except Exception as e:
                logger.error(f"Failed to initialize DuckDB: {e}")
                raise
    
    def _setup_extensions(self) -> None:
        """Install and load required DuckDB extensions."""
        extensions = [
            'json',      # JSON processing
            'parquet',   # Parquet file support
            'spatial',   # Spatial extension (includes Excel support via st_read)
        ]
        
        for extension in extensions:
            try:
                self._connection.execute(f"INSTALL {extension}")
                self._connection.execute(f"LOAD {extension}")
                logger.debug(f"Loaded DuckDB extension: {extension}")
            except Exception as e:
                # Some extensions might not be available, log but continue
                logger.warning(f"Could not load DuckDB extension {extension}: {e}")
    
    def _create_schemas(self) -> None:
        """Create schemas for organizing different data types."""
        schemas = [
            "CREATE SCHEMA IF NOT EXISTS structured_data",
            "CREATE SCHEMA IF NOT EXISTS json_data", 
            "CREATE SCHEMA IF NOT EXISTS temp_data",
        ]
        
        for schema_sql in schemas:
            self._connection.execute(schema_sql)
            logger.debug(f"Created schema: {schema_sql}")
    
    @contextmanager
    def get_connection(self):
        """
        Get a DuckDB connection with proper resource management.
        
        Yields:
            duckdb.DuckDBPyConnection: Database connection
        """
        if self._connection is None:
            self.initialize()
        
        with self._lock:
            try:
                yield self._connection
            except Exception as e:
                logger.error(f"DuckDB operation failed: {e}")
                raise
    
    def create_virtual_table(self, table_name: str, file_path: str, 
                           schema_name: str = "structured_data",
                           client_id: str = None, user_id: str = None, 
                           resource_id: str = None) -> None:
        """
        Create a virtual table that queries a file directly.
        
        Args:
            table_name: Name for the virtual table
            file_path: Path to the data file (CSV, Parquet, etc.)
            schema_name: Schema to create the table in
            client_id: Client ID for access control
            user_id: User ID for access control
            resource_id: Resource ID for tracking
        """
        with self.get_connection() as conn:
            # Determine file type and create appropriate virtual table
            file_path_obj = Path(file_path)
            file_extension = file_path_obj.suffix.lower()
            
            if file_extension == '.csv':
                sql = f"""
                CREATE OR REPLACE VIEW {schema_name}.{table_name} AS 
                SELECT * FROM read_csv_auto('{file_path}')
                """
            elif file_extension == '.parquet':
                sql = f"""
                CREATE OR REPLACE VIEW {schema_name}.{table_name} AS 
                SELECT * FROM read_parquet('{file_path}')
                """
            elif file_extension in ['.xlsx', '.xls']:
                # Use spatial extension for Excel files
                sql = f"""
                CREATE OR REPLACE VIEW {schema_name}.{table_name} AS 
                SELECT * FROM st_read('{file_path}')
                """
            else:
                raise ValueError(f"Unsupported file type for virtual table: {file_extension}")
            
            conn.execute(sql)
            logger.info(f"Created virtual table: {schema_name}.{table_name}")
            
            # Create enhanced view with metadata columns for access control
            if client_id and user_id and resource_id:
                enhanced_sql = f"""
                CREATE OR REPLACE VIEW {schema_name}.{table_name}_enhanced AS
                SELECT *, 
                       '{client_id}' as client_id,
                       '{user_id}' as user_id,
                       '{resource_id}' as resource_id
                FROM {schema_name}.{table_name}
                """
                conn.execute(enhanced_sql)
                logger.debug(f"Created enhanced view: {schema_name}.{table_name}_enhanced")
    
    def store_json_data(self, table_name: str, json_data: Dict[str, Any], 
                       resource_id: str, version: int = 1) -> None:
        """
        Store JSON data in JSONB format with indexing.
        
        Args:
            table_name: Name for the JSON table
            json_data: JSON data to store
            resource_id: Resource identifier
            version: Version number
        """
        with self.get_connection() as conn:
            # Create table if it doesn't exist
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS json_data.{table_name} (
                id VARCHAR PRIMARY KEY,
                resource_id VARCHAR NOT NULL,
                version INTEGER NOT NULL,
                data JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            conn.execute(create_table_sql)
            
            # Insert JSON data
            insert_sql = f"""
            INSERT OR REPLACE INTO json_data.{table_name} 
            (id, resource_id, version, data, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            
            record_id = f"{resource_id}_v{version}"
            conn.execute(insert_sql, [record_id, resource_id, version, json.dumps(json_data)])
            
            logger.info(f"Stored JSON data in table: json_data.{table_name}")
    
    def execute_query(self, sql: str, parameters: Optional[List] = None) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results.
        
        Args:
            sql: SQL query string
            parameters: Optional query parameters
            
        Returns:
            List[Dict[str, Any]]: Query results as list of dictionaries
        """
        with self.get_connection() as conn:
            if parameters:
                result = conn.execute(sql, parameters)
            else:
                result = conn.execute(sql)
            
            # Convert to list of dictionaries
            columns = [desc[0] for desc in result.description]
            rows = result.fetchall()
            
            return [dict(zip(columns, row)) for row in rows]
    
    def close(self) -> None:
        """Close the database connection."""
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None
                logger.info("DuckDB connection closed")
    
    def vacuum(self) -> None:
        """Optimize DuckDB database by running VACUUM."""
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                logger.info("DuckDB vacuum completed")
        except Exception as e:
            logger.error(f"Error running DuckDB vacuum: {e}")
            raise
    
    def get_database_size(self) -> int:
        """Get database file size in bytes."""
        try:
            if self.db_path.exists():
                return self.db_path.stat().st_size
            return 0
        except Exception as e:
            logger.error(f"Error getting DuckDB size: {e}")
            return 0


class ChromaDBManager:
    """
    Manages ChromaDB connections for unstructured data embeddings.
    
    Handles persistent ChromaDB storage with collection management,
    embedding storage, and semantic search capabilities.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize ChromaDB manager.
        
        Args:
            config: Optional configuration instance
        """
        self.config = config or get_config()
        self.db_path = self.config.get_full_path(self.config.database.chromadb_path)
        self._client = None
        self._lock = Lock()
    
    def initialize(self) -> None:
        """
        Initialize ChromaDB with persistent storage.
        
        Creates the ChromaDB client with persistent storage and sets up
        default collections for different data types.
        """
        # Ensure database directory exists
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        with self._lock:
            try:
                # Create persistent ChromaDB client
                self._client = chromadb.PersistentClient(path=str(self.db_path))
                
                logger.info(f"ChromaDB initialized at: {self.db_path}")
                
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB: {e}")
                raise
    
    @contextmanager
    def get_client(self):
        """
        Get a ChromaDB client with proper resource management.
        
        Yields:
            chromadb.Client: ChromaDB client instance
        """
        if self._client is None:
            self.initialize()
        
        with self._lock:
            try:
                yield self._client
            except Exception as e:
                logger.error(f"ChromaDB operation failed: {e}")
                raise
    
    def create_collection(self, collection_name: str, 
                         metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Create a new collection for storing embeddings.
        
        Args:
            collection_name: Name of the collection
            metadata: Optional metadata for the collection
        """
        with self.get_client() as client:
            try:
                collection = client.create_collection(
                    name=collection_name,
                    metadata=metadata or {}
                )
                logger.info(f"Created ChromaDB collection: {collection_name}")
                return collection
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.debug(f"Collection {collection_name} already exists")
                    return client.get_collection(collection_name)
                else:
                    raise
    
    def get_collection(self, collection_name: str):
        """
        Get an existing collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            chromadb.Collection: Collection instance
        """
        with self.get_client() as client:
            return client.get_collection(collection_name)
    
    def add_embeddings(self, collection_name: str, embeddings: List[List[float]], 
                      documents: List[str], metadatas: List[Dict[str, Any]], 
                      ids: List[str]) -> None:
        """
        Add embeddings to a collection.
        
        Args:
            collection_name: Name of the collection
            embeddings: List of embedding vectors
            documents: List of document texts
            metadatas: List of metadata dictionaries
            ids: List of unique identifiers
        """
        with self.get_client() as client:
            collection = client.get_collection(collection_name)
            collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(embeddings)} embeddings to collection: {collection_name}")
    
    def query_collection(self, collection_name: str, query_embeddings: List[List[float]], 
                        n_results: int = 5, where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Query a collection for similar embeddings.
        
        Args:
            collection_name: Name of the collection
            query_embeddings: Query embedding vectors
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            Dict[str, Any]: Query results
        """
        with self.get_client() as client:
            collection = client.get_collection(collection_name)
            results = collection.query(
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where
            )
            return results
    
    def delete_collection(self, collection_name: str) -> None:
        """
        Delete a collection.
        
        Args:
            collection_name: Name of the collection to delete
        """
        with self.get_client() as client:
            client.delete_collection(collection_name)
            logger.info(f"Deleted ChromaDB collection: {collection_name}")
    
    def list_collections(self) -> List[str]:
        """
        List all collections.
        
        Returns:
            List[str]: List of collection names
        """
        with self.get_client() as client:
            collections = client.list_collections()
            return [col.name for col in collections]
    
    def optimize(self) -> None:
        """Optimize ChromaDB (placeholder - ChromaDB handles optimization internally)."""
        logger.info("ChromaDB optimization requested (handled internally)")
    
    def get_database_size(self) -> int:
        """Get ChromaDB storage size in bytes."""
        try:
            if self.persist_directory.exists():
                total_size = 0
                for file_path in self.persist_directory.rglob('*'):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
                return total_size
            return 0
        except Exception as e:
            logger.error(f"Error getting ChromaDB size: {e}")
            return 0


class SQLiteManager:
    """
    Manages SQLite connections for metadata registry.
    
    Handles the metadata database with proper schema management,
    connection pooling, and transaction support.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize SQLite manager.
        
        Args:
            config: Optional configuration instance
        """
        self.config = config or get_config()
        self.db_path = self.config.get_full_path(self.config.database.sqlite_path)
        self._lock = Lock()
    
    def initialize(self) -> None:
        """
        Initialize SQLite database and create metadata schema.
        
        Creates the database file and all required tables for metadata storage.
        """
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with self._lock:
            try:
                # Create database and tables
                with sqlite3.connect(str(self.db_path)) as conn:
                    conn.execute("PRAGMA foreign_keys = ON")
                    self._create_tables(conn)
                    conn.commit()
                
                logger.info(f"SQLite metadata registry initialized at: {self.db_path}")
                
            except Exception as e:
                logger.error(f"Failed to initialize SQLite: {e}")
                raise
    
    def _create_tables(self, conn: sqlite3.Connection) -> None:
        """Create all required tables for metadata storage."""
        
        # Resource metadata table
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
        
        # Schema information table
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
        
        # Audit trail / lineage table
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
        
        # Upload progress tracking table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS upload_progress (
                resource_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                total_bytes INTEGER NOT NULL,
                uploaded_bytes INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'uploading',
                stage TEXT NOT NULL DEFAULT 'validation',
                message TEXT NOT NULL DEFAULT '',
                started_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Create indexes for fast filtering
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_resource_user_id ON resource_metadata (user_id)",
            "CREATE INDEX IF NOT EXISTS idx_resource_client_id ON resource_metadata (client_id)",
            "CREATE INDEX IF NOT EXISTS idx_resource_type ON resource_metadata (resource_type)",
            "CREATE INDEX IF NOT EXISTS idx_resource_created_at ON resource_metadata (created_at)",
            "CREATE INDEX IF NOT EXISTS idx_resource_is_deleted ON resource_metadata (is_deleted)",
            "CREATE INDEX IF NOT EXISTS idx_schema_resource_id ON schema_info (resource_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_resource_id ON audit_trail (resource_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_trail (timestamp)",
        ]
        
        for index_sql in indexes:
            conn.execute(index_sql)
            logger.debug(f"Created index: {index_sql}")
    
    @contextmanager
    def get_connection(self):
        """
        Get a SQLite connection with proper resource management.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        with self._lock:
            conn = None
            try:
                conn = sqlite3.connect(str(self.db_path))
                conn.execute("PRAGMA foreign_keys = ON")
                conn.row_factory = sqlite3.Row  # Enable dict-like access
                yield conn
            except Exception as e:
                if conn:
                    conn.rollback()
                logger.error(f"SQLite operation failed: {e}")
                raise
            finally:
                if conn:
                    conn.close()
    
    def execute_query(self, sql: str, parameters: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results.
        
        Args:
            sql: SQL query string
            parameters: Optional query parameters
            
        Returns:
            List[Dict[str, Any]]: Query results as list of dictionaries
        """
        with self.get_connection() as conn:
            if parameters:
                cursor = conn.execute(sql, parameters)
            else:
                cursor = conn.execute(sql)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_update(self, sql: str, parameters: Optional[tuple] = None) -> int:
        """
        Execute an INSERT, UPDATE, or DELETE query.
        
        Args:
            sql: SQL query string
            parameters: Optional query parameters
            
        Returns:
            int: Number of affected rows
        """
        with self.get_connection() as conn:
            if parameters:
                cursor = conn.execute(sql, parameters)
            else:
                cursor = conn.execute(sql)
            conn.commit()
            return cursor.rowcount
    
    def vacuum(self) -> None:
        """Optimize SQLite database by running VACUUM."""
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                logger.info("SQLite vacuum completed")
        except Exception as e:
            logger.error(f"Error running SQLite vacuum: {e}")
            raise
    
    def get_database_size(self) -> int:
        """Get database file size in bytes."""
        try:
            if self.db_path.exists():
                return self.db_path.stat().st_size
            return 0
        except Exception as e:
            logger.error(f"Error getting SQLite size: {e}")
            return 0


class DatabaseManagers:
    """
    Unified manager for all database connections.
    
    Provides a single interface to access DuckDB, ChromaDB, and SQLite
    managers with proper initialization and lifecycle management.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize all database managers.
        
        Args:
            config: Optional configuration instance
        """
        self.config = config or get_config()
        self.duckdb = DuckDBManager(config)
        self.chromadb = ChromaDBManager(config)
        self.sqlite = SQLiteManager(config)
        self._initialized = False
    
    def initialize_all(self) -> None:
        """
        Initialize all database managers.
        
        Creates all necessary databases, schemas, and tables.
        """
        if self._initialized:
            return
        
        try:
            logger.info("Initializing all database managers...")
            
            # Initialize in order of dependency
            self.sqlite.initialize()
            self.duckdb.initialize()
            self.chromadb.initialize()
            
            self._initialized = True
            logger.info("All database managers initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database managers: {e}")
            raise
    
    def close_all(self) -> None:
        """Close all database connections."""
        try:
            self.duckdb.close()
            # ChromaDB and SQLite connections are managed per-operation
            logger.info("All database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")
    
    def health_check(self) -> Dict[str, bool]:
        """
        Check the health of all database connections.
        
        Returns:
            Dict[str, bool]: Health status for each database
        """
        health = {}
        
        # Test SQLite
        try:
            with self.sqlite.get_connection() as conn:
                conn.execute("SELECT 1")
            health['sqlite'] = True
        except Exception as e:
            logger.error(f"SQLite health check failed: {e}")
            health['sqlite'] = False
        
        # Test DuckDB
        try:
            with self.duckdb.get_connection() as conn:
                conn.execute("SELECT 1")
            health['duckdb'] = True
        except Exception as e:
            logger.error(f"DuckDB health check failed: {e}")
            health['duckdb'] = False
        
        # Test ChromaDB
        try:
            with self.chromadb.get_client() as client:
                client.heartbeat()
            health['chromadb'] = True
        except Exception as e:
            logger.error(f"ChromaDB health check failed: {e}")
            health['chromadb'] = False
        
        return health
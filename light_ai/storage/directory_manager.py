"""
Directory structure management for Universal Data Handler.

Handles automatic creation and management of the standardized directory structure
required by the system for storing different types of data and metadata.
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional
from ..config import Config, get_config
from ..logger import get_logger

logger = get_logger(__name__)


class DirectoryManager:
    """
    Manages the standardized directory structure for the Universal Data Handler.
    
    Creates and maintains the following structure:
    - data/structured/     - Structured data files (CSV, Excel, etc.)
    - data/json/          - JSON data storage
    - data/unstructured/  - Unstructured data and embeddings
    - data/raw/           - Original uploaded files
    - metadata/           - SQLite metadata registry
    - cache/              - Query result cache
    - logs/               - System logs
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize directory manager with configuration.
        
        Args:
            config: Optional configuration instance. If None, uses global config.
        """
        self.config = config or get_config()
        self.base_path = Path(self.config.storage.base_directory)
        
    def create_all_directories(self) -> None:
        """
        Create all required directories for the system.
        
        Creates the complete directory structure needed for data storage,
        metadata, caching, and logging.
        
        Raises:
            OSError: If directory creation fails due to permissions or disk space
        """
        directories = self._get_required_directories()
        
        logger.info(f"Creating directory structure at: {self.base_path}")
        
        for directory in directories:
            full_path = self.base_path / directory
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created directory: {full_path}")
            except OSError as e:
                logger.error(f"Failed to create directory {full_path}: {e}")
                raise
        
        # Create subdirectories for hierarchical data organization
        self._create_hierarchical_subdirs()
        
        logger.info("Directory structure created successfully")
    
    def _get_required_directories(self) -> List[str]:
        """Get list of all required directories."""
        return [
            self.config.storage.structured_data_dir,
            self.config.storage.json_data_dir, 
            self.config.storage.unstructured_data_dir,
            self.config.storage.raw_data_dir,
            self.config.storage.metadata_dir,
            self.config.storage.cache_dir,
            self.config.storage.logs_dir,
            # Additional subdirectories
            "data/duckdb",  # DuckDB database files
            "data/unstructured/chroma_db",  # ChromaDB persistent storage
            "cache/query_cache",  # Query result cache
            "cache/embeddings",  # Embedding cache
            "temp",  # Temporary files during processing
        ]
    
    def _create_hierarchical_subdirs(self) -> None:
        """Create common subdirectories for hierarchical organization."""
        # These will be created on-demand as clients/users are added
        # but we can create the base structure
        hierarchical_dirs = [
            "data/structured",
            "data/raw", 
        ]
        
        for base_dir in hierarchical_dirs:
            full_path = self.base_path / base_dir
            full_path.mkdir(parents=True, exist_ok=True)
    
    def get_directory_path(self, directory_type: str) -> Path:
        """
        Get the full path for a specific directory type.
        
        Args:
            directory_type: Type of directory ('structured', 'json', 'unstructured', 
                          'raw', 'metadata', 'cache', 'logs', 'temp')
        
        Returns:
            Path: Full path to the directory
            
        Raises:
            ValueError: If directory type is not recognized
        """
        directory_map = {
            'structured': self.config.storage.structured_data_dir,
            'json': self.config.storage.json_data_dir,
            'unstructured': self.config.storage.unstructured_data_dir,
            'raw': self.config.storage.raw_data_dir,
            'metadata': self.config.storage.metadata_dir,
            'cache': self.config.storage.cache_dir,
            'logs': self.config.storage.logs_dir,
            'temp': 'temp',
            'duckdb': 'data/duckdb',
            'chromadb': 'data/unstructured/chroma_db',
        }
        
        if directory_type not in directory_map:
            raise ValueError(f"Unknown directory type: {directory_type}")
        
        return self.base_path / directory_map[directory_type]
    
    def create_client_directory(self, client_id: str) -> Path:
        """
        Create directory structure for a new client.
        
        Args:
            client_id: UUID of the client
            
        Returns:
            Path: Path to the client's root directory
        """
        client_dirs = [
            f"data/structured/{client_id}",
            f"data/raw/{client_id}",
        ]
        
        for directory in client_dirs:
            full_path = self.base_path / directory
            full_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created client directory: {full_path}")
        
        return self.base_path / "data" / client_id
    
    def create_user_directory(self, client_id: str, user_id: str) -> Path:
        """
        Create directory structure for a new user within a client.
        
        Args:
            client_id: UUID of the client
            user_id: UUID of the user
            
        Returns:
            Path: Path to the user's root directory
        """
        user_dirs = [
            f"data/structured/{client_id}/{user_id}",
            f"data/raw/{client_id}/{user_id}",
        ]
        
        for directory in user_dirs:
            full_path = self.base_path / directory
            full_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created user directory: {full_path}")
        
        return self.base_path / "data" / client_id / user_id
    
    def create_resource_directory(self, client_id: str, user_id: str, 
                                resource_id: str) -> Path:
        """
        Create directory structure for a new resource.
        
        Args:
            client_id: UUID of the client
            user_id: UUID of the user
            resource_id: UUID of the resource
            
        Returns:
            Path: Path to the resource's directory
        """
        resource_dirs = [
            f"data/structured/{client_id}/{user_id}/{resource_id}",
            f"data/raw/{client_id}/{user_id}/{resource_id}",
        ]
        
        for directory in resource_dirs:
            full_path = self.base_path / directory
            full_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created resource directory: {full_path}")
        
        return self.base_path / "data" / client_id / user_id / resource_id
    
    def cleanup_temp_directory(self) -> None:
        """
        Clean up temporary files and directories.
        
        Removes all files from the temp directory that are older than 1 hour.
        """
        temp_dir = self.get_directory_path('temp')
        if not temp_dir.exists():
            return
        
        import time
        current_time = time.time()
        one_hour_ago = current_time - 3600  # 1 hour in seconds
        
        for item in temp_dir.iterdir():
            try:
                if item.stat().st_mtime < one_hour_ago:
                    if item.is_file():
                        item.unlink()
                        logger.debug(f"Removed temp file: {item}")
                    elif item.is_dir():
                        shutil.rmtree(item)
                        logger.debug(f"Removed temp directory: {item}")
            except OSError as e:
                logger.warning(f"Failed to remove temp item {item}: {e}")
    
    def get_storage_usage(self) -> dict:
        """
        Get storage usage statistics for all directories.
        
        Returns:
            dict: Storage usage information with directory sizes in bytes
        """
        usage = {}
        
        for dir_type in ['structured', 'json', 'unstructured', 'raw', 
                        'metadata', 'cache', 'logs', 'temp']:
            try:
                dir_path = self.get_directory_path(dir_type)
                if dir_path.exists():
                    size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                    usage[dir_type] = size
                else:
                    usage[dir_type] = 0
            except OSError as e:
                logger.warning(f"Failed to calculate size for {dir_type}: {e}")
                usage[dir_type] = 0
        
        return usage
    
    def validate_directory_structure(self) -> bool:
        """
        Validate that all required directories exist and are accessible.
        
        Returns:
            bool: True if all directories are valid, False otherwise
        """
        required_dirs = self._get_required_directories()
        
        for directory in required_dirs:
            full_path = self.base_path / directory
            if not full_path.exists():
                logger.error(f"Required directory missing: {full_path}")
                return False
            if not full_path.is_dir():
                logger.error(f"Path is not a directory: {full_path}")
                return False
            if not os.access(full_path, os.R_OK | os.W_OK):
                logger.error(f"Directory not accessible: {full_path}")
                return False
        
        return True
    
    def get_directory_stats(self) -> dict:
        """
        Get comprehensive directory statistics.
        
        Returns:
            dict: Directory statistics including sizes and file counts
        """
        stats = {}
        required_dirs = self._get_required_directories()
        
        for directory in required_dirs:
            full_path = self.base_path / directory
            if full_path.exists():
                total_size = 0
                file_count = 0
                
                try:
                    for file_path in full_path.rglob('*'):
                        if file_path.is_file():
                            total_size += file_path.stat().st_size
                            file_count += 1
                    
                    stats[directory] = {
                        "size_bytes": total_size,
                        "file_count": file_count,
                        "path": str(full_path)
                    }
                except Exception as e:
                    logger.error(f"Error getting stats for {directory}: {e}")
                    stats[directory] = {
                        "size_bytes": 0,
                        "file_count": 0,
                        "path": str(full_path),
                        "error": str(e)
                    }
            else:
                stats[directory] = {
                    "size_bytes": 0,
                    "file_count": 0,
                    "path": str(full_path),
                    "exists": False
                }
        
        return stats


def create_directory_structure(config: Optional[Config] = None) -> DirectoryManager:
    """
    Convenience function to create the complete directory structure.
    
    Args:
        config: Optional configuration instance
        
    Returns:
        DirectoryManager: Configured directory manager instance
        
    Raises:
        OSError: If directory creation fails
    """
    manager = DirectoryManager(config)
    manager.create_all_directories()
    return manager
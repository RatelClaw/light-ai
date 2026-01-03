"""
Storage layer for Universal Data Handler.

Provides database connection managers, directory structure management,
and storage utilities for the multi-database architecture.
"""

from .directory_manager import DirectoryManager, create_directory_structure
from .database_managers import (
    DuckDBManager,
    ChromaDBManager, 
    SQLiteManager,
    DatabaseManagers
)
from .metadata_registry import MetadataRegistry
from .storage_utils import (
    StoragePathUtils,
    FileManager,
    generate_storage_path,
    ensure_directory_exists,
    get_file_hash,
    cleanup_temp_files
)
from .storage_router import StorageRouter
from .version_manager import VersionManager

__all__ = [
    "DirectoryManager",
    "create_directory_structure", 
    "DuckDBManager",
    "ChromaDBManager",
    "SQLiteManager", 
    "DatabaseManagers",
    "MetadataRegistry",
    "StoragePathUtils",
    "FileManager",
    "generate_storage_path",
    "ensure_directory_exists",
    "get_file_hash",
    "cleanup_temp_files",
    "StorageRouter",
    "VersionManager"
]
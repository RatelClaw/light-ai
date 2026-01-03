"""
Storage utilities and file management functions for Universal Data Handler.

Provides path utilities, file management operations, and helper functions
for working with the hierarchical storage system.
"""

import os
import shutil
import hashlib
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta

from ..core.models import DataHierarchy, ResourceMetadata
from ..config import Config, get_config
from ..logger import get_logger

logger = get_logger(__name__)


class StoragePathUtils:
    """
    Utilities for generating and managing storage paths.
    
    Handles path generation for the hierarchical storage system with
    client_id/user_id/resource_id organization.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize storage path utilities.
        
        Args:
            config: Optional configuration instance
        """
        self.config = config or get_config()
        self.base_path = Path(self.config.storage.base_directory)
    
    def generate_hierarchical_path(self, hierarchy: DataHierarchy, 
                                 storage_type: str = "structured") -> Path:
        """
        Generate hierarchical storage path for a resource.
        
        Args:
            hierarchy: Data hierarchy with client/user/resource IDs
            storage_type: Type of storage ('structured', 'raw', 'json', 'unstructured')
            
        Returns:
            Path: Full hierarchical path
            
        Raises:
            ValueError: If storage_type is not recognized
        """
        storage_dirs = {
            'structured': self.config.storage.structured_data_dir,
            'raw': self.config.storage.raw_data_dir,
            'json': self.config.storage.json_data_dir,
            'unstructured': self.config.storage.unstructured_data_dir,
        }
        
        if storage_type not in storage_dirs:
            raise ValueError(f"Unknown storage type: {storage_type}")
        
        base_dir = storage_dirs[storage_type]
        
        # For JSON and unstructured, we don't use hierarchical paths
        if storage_type in ['json', 'unstructured']:
            return self.base_path / base_dir
        
        # For structured and raw, use full hierarchy
        return (self.base_path / base_dir / 
                hierarchy.client_id / hierarchy.user_id / hierarchy.resource_id)
    
    def generate_file_path(self, hierarchy: DataHierarchy, filename: str,
                          storage_type: str = "structured", version: int = 1) -> Path:
        """
        Generate full file path including filename and version.
        
        Args:
            hierarchy: Data hierarchy
            filename: Original filename
            storage_type: Type of storage
            version: Version number
            
        Returns:
            Path: Full file path with version
        """
        dir_path = self.generate_hierarchical_path(hierarchy, storage_type)
        
        # Add version prefix to filename
        file_stem = Path(filename).stem
        file_suffix = Path(filename).suffix
        versioned_filename = f"v{version}_{file_stem}{file_suffix}"
        
        return dir_path / versioned_filename
    
    def get_current_file_path(self, hierarchy: DataHierarchy, filename: str,
                            storage_type: str = "structured") -> Path:
        """
        Get path to current version symlink.
        
        Args:
            hierarchy: Data hierarchy
            filename: Original filename
            storage_type: Type of storage
            
        Returns:
            Path: Path to current version symlink
        """
        dir_path = self.generate_hierarchical_path(hierarchy, storage_type)
        file_stem = Path(filename).stem
        file_suffix = Path(filename).suffix
        current_filename = f"current_{file_stem}{file_suffix}"
        
        return dir_path / current_filename
    
    def list_versions(self, hierarchy: DataHierarchy, filename: str,
                     storage_type: str = "structured") -> List[int]:
        """
        List all versions of a file.
        
        Args:
            hierarchy: Data hierarchy
            filename: Original filename
            storage_type: Type of storage
            
        Returns:
            List[int]: List of version numbers, sorted descending
        """
        dir_path = self.generate_hierarchical_path(hierarchy, storage_type)
        
        if not dir_path.exists():
            return []
        
        file_stem = Path(filename).stem
        file_suffix = Path(filename).suffix
        pattern = f"v*_{file_stem}{file_suffix}"
        
        versions = []
        for file_path in dir_path.glob(pattern):
            try:
                # Extract version number from filename
                version_part = file_path.name.split('_')[0]  # Get 'vN' part
                version_num = int(version_part[1:])  # Remove 'v' and convert to int
                versions.append(version_num)
            except (ValueError, IndexError):
                continue
        
        return sorted(versions, reverse=True)
    
    def get_temp_path(self, filename: str) -> Path:
        """
        Generate temporary file path for processing.
        
        Args:
            filename: Original filename
            
        Returns:
            Path: Temporary file path
        """
        temp_dir = self.base_path / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Add timestamp to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        temp_filename = f"{timestamp}_{filename}"
        
        return temp_dir / temp_filename


class FileManager:
    """
    File management operations for the storage system.
    
    Handles file operations, versioning, cleanup, and integrity checks.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize file manager.
        
        Args:
            config: Optional configuration instance
        """
        self.config = config or get_config()
        self.path_utils = StoragePathUtils(config)
    
    def store_file(self, source_path: Union[str, Path], hierarchy: DataHierarchy,
                  filename: str, storage_type: str = "structured", 
                  version: int = 1, create_current_link: bool = True) -> Path:
        """
        Store a file in the hierarchical storage system.
        
        Args:
            source_path: Path to source file
            hierarchy: Data hierarchy
            filename: Original filename
            storage_type: Type of storage
            version: Version number
            create_current_link: Whether to create/update current version link
            
        Returns:
            Path: Path where file was stored
            
        Raises:
            FileNotFoundError: If source file doesn't exist
            OSError: If file operations fail
        """
        source_path = Path(source_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        # Generate target path
        target_path = self.path_utils.generate_file_path(
            hierarchy, filename, storage_type, version
        )
        
        # Ensure target directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file to target location
        shutil.copy2(source_path, target_path)
        logger.info(f"Stored file: {target_path}")
        
        # Create or update current version link
        if create_current_link:
            self._update_current_link(hierarchy, filename, storage_type, version)
        
        return target_path
    
    def _update_current_link(self, hierarchy: DataHierarchy, filename: str,
                           storage_type: str, version: int) -> None:
        """Update the current version symlink."""
        current_path = self.path_utils.get_current_file_path(hierarchy, filename, storage_type)
        versioned_path = self.path_utils.generate_file_path(hierarchy, filename, storage_type, version)
        
        # Remove existing link if it exists
        if current_path.exists() or current_path.is_symlink():
            current_path.unlink()
        
        # Create new symlink (relative path for portability)
        relative_target = os.path.relpath(versioned_path, current_path.parent)
        current_path.symlink_to(relative_target)
        logger.debug(f"Updated current link: {current_path} -> {relative_target}")
    
    def retrieve_file(self, hierarchy: DataHierarchy, filename: str,
                     storage_type: str = "structured", version: Optional[int] = None) -> Optional[Path]:
        """
        Retrieve a file from storage.
        
        Args:
            hierarchy: Data hierarchy
            filename: Original filename
            storage_type: Type of storage
            version: Optional version number (if None, gets current)
            
        Returns:
            Optional[Path]: Path to file or None if not found
        """
        if version:
            file_path = self.path_utils.generate_file_path(hierarchy, filename, storage_type, version)
        else:
            file_path = self.path_utils.get_current_file_path(hierarchy, filename, storage_type)
        
        if file_path.exists():
            return file_path
        else:
            return None
    
    def delete_file(self, hierarchy: DataHierarchy, filename: str,
                   storage_type: str = "structured", version: Optional[int] = None,
                   hard_delete: bool = False) -> bool:
        """
        Delete a file from storage.
        
        Args:
            hierarchy: Data hierarchy
            filename: Original filename
            storage_type: Type of storage
            version: Optional version number (if None, deletes all versions)
            hard_delete: If True, permanently delete; if False, move to trash
            
        Returns:
            bool: True if file(s) were deleted, False if not found
        """
        if version:
            # Delete specific version
            file_path = self.path_utils.generate_file_path(hierarchy, filename, storage_type, version)
            if file_path.exists():
                if hard_delete:
                    file_path.unlink()
                else:
                    self._move_to_trash(file_path)
                logger.info(f"Deleted file version {version}: {file_path}")
                return True
        else:
            # Delete all versions
            dir_path = self.path_utils.generate_hierarchical_path(hierarchy, storage_type)
            if not dir_path.exists():
                return False
            
            file_stem = Path(filename).stem
            file_suffix = Path(filename).suffix
            pattern = f"*_{file_stem}{file_suffix}"
            
            deleted_any = False
            for file_path in dir_path.glob(pattern):
                if hard_delete:
                    file_path.unlink()
                else:
                    self._move_to_trash(file_path)
                deleted_any = True
            
            # Also delete current link
            current_path = self.path_utils.get_current_file_path(hierarchy, filename, storage_type)
            if current_path.exists() or current_path.is_symlink():
                current_path.unlink()
                deleted_any = True
            
            if deleted_any:
                logger.info(f"Deleted all versions of file: {filename}")
            
            return deleted_any
        
        return False
    
    def _move_to_trash(self, file_path: Path) -> None:
        """Move file to trash directory."""
        trash_dir = self.path_utils.base_path / "trash"
        trash_dir.mkdir(parents=True, exist_ok=True)
        
        # Add timestamp to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        trash_filename = f"{timestamp}_{file_path.name}"
        trash_path = trash_dir / trash_filename
        
        shutil.move(str(file_path), str(trash_path))
        logger.debug(f"Moved to trash: {file_path} -> {trash_path}")
    
    def copy_file(self, source_hierarchy: DataHierarchy, target_hierarchy: DataHierarchy,
                 filename: str, storage_type: str = "structured", 
                 source_version: Optional[int] = None) -> Optional[Path]:
        """
        Copy a file between hierarchies.
        
        Args:
            source_hierarchy: Source data hierarchy
            target_hierarchy: Target data hierarchy
            filename: Filename to copy
            storage_type: Type of storage
            source_version: Optional source version (if None, copies current)
            
        Returns:
            Optional[Path]: Path to copied file or None if source not found
        """
        # Get source file
        source_path = self.retrieve_file(source_hierarchy, filename, storage_type, source_version)
        if not source_path:
            return None
        
        # Determine target version
        existing_versions = self.path_utils.list_versions(target_hierarchy, filename, storage_type)
        target_version = max(existing_versions, default=0) + 1
        
        # Store copy
        return self.store_file(source_path, target_hierarchy, filename, storage_type, target_version)
    
    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """
        Get file information including size, hash, and timestamps.
        
        Args:
            file_path: Path to file
            
        Returns:
            Dict[str, Any]: File information
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        stat = file_path.stat()
        
        return {
            'size_bytes': stat.st_size,
            'created_at': datetime.fromtimestamp(stat.st_ctime),
            'modified_at': datetime.fromtimestamp(stat.st_mtime),
            'hash_md5': get_file_hash(file_path, 'md5'),
            'hash_sha256': get_file_hash(file_path, 'sha256'),
        }
    
    def cleanup_old_trash(self, days_to_keep: int = 30) -> int:
        """
        Clean up old files from trash directory.
        
        Args:
            days_to_keep: Number of days to keep files in trash
            
        Returns:
            int: Number of files deleted
        """
        trash_dir = self.path_utils.base_path / "trash"
        if not trash_dir.exists():
            return 0
        
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)
        deleted_count = 0
        
        for file_path in trash_dir.iterdir():
            if file_path.is_file():
                try:
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1
                        logger.debug(f"Deleted old trash file: {file_path}")
                except OSError as e:
                    logger.warning(f"Failed to delete trash file {file_path}: {e}")
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old trash files")
        
        return deleted_count


# Utility Functions

def generate_storage_path(hierarchy: DataHierarchy, storage_type: str = "structured",
                         config: Optional[Config] = None) -> Path:
    """
    Generate storage path for a data hierarchy.
    
    Args:
        hierarchy: Data hierarchy
        storage_type: Type of storage
        config: Optional configuration
        
    Returns:
        Path: Storage path
    """
    path_utils = StoragePathUtils(config)
    return path_utils.generate_hierarchical_path(hierarchy, storage_type)


def ensure_directory_exists(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        Path: Path object for the directory
        
    Raises:
        OSError: If directory creation fails
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_hash(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """
    Calculate hash of a file.
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm ('md5', 'sha1', 'sha256', 'sha512')
        
    Returns:
        str: Hexadecimal hash string
        
    Raises:
        ValueError: If algorithm is not supported
        FileNotFoundError: If file doesn't exist
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if algorithm not in ['md5', 'sha1', 'sha256', 'sha512']:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    hash_obj = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


def cleanup_temp_files(temp_dir: Optional[Union[str, Path]] = None, 
                      max_age_hours: int = 1) -> int:
    """
    Clean up temporary files older than specified age.
    
    Args:
        temp_dir: Temporary directory path (if None, uses default)
        max_age_hours: Maximum age in hours for temp files
        
    Returns:
        int: Number of files cleaned up
    """
    if temp_dir is None:
        config = get_config()
        temp_dir = Path(config.storage.base_directory) / "temp"
    else:
        temp_dir = Path(temp_dir)
    
    if not temp_dir.exists():
        return 0
    
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    deleted_count = 0
    
    for item in temp_dir.iterdir():
        try:
            item_time = datetime.fromtimestamp(item.stat().st_mtime)
            if item_time < cutoff_time:
                if item.is_file():
                    item.unlink()
                    deleted_count += 1
                elif item.is_dir():
                    shutil.rmtree(item)
                    deleted_count += 1
                logger.debug(f"Cleaned up temp item: {item}")
        except OSError as e:
            logger.warning(f"Failed to clean up temp item {item}: {e}")
    
    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} temporary files/directories")
    
    return deleted_count


def get_directory_size(directory: Union[str, Path]) -> int:
    """
    Calculate total size of a directory in bytes.
    
    Args:
        directory: Directory path
        
    Returns:
        int: Total size in bytes
    """
    directory = Path(directory)
    if not directory.exists():
        return 0
    
    total_size = 0
    for item in directory.rglob('*'):
        if item.is_file():
            try:
                total_size += item.stat().st_size
            except OSError:
                # Skip files that can't be accessed
                continue
    
    return total_size


def validate_file_integrity(file_path: Union[str, Path], 
                          expected_hash: str, algorithm: str = 'sha256') -> bool:
    """
    Validate file integrity using hash comparison.
    
    Args:
        file_path: Path to file
        expected_hash: Expected hash value
        algorithm: Hash algorithm used
        
    Returns:
        bool: True if file integrity is valid, False otherwise
    """
    try:
        actual_hash = get_file_hash(file_path, algorithm)
        return actual_hash.lower() == expected_hash.lower()
    except (FileNotFoundError, ValueError):
        return False
"""
File upload and validation system for Sub-Layer 1.

Handles file type detection, validation, size checking, and duplicate detection.
"""

import hashlib
import mimetypes
import os
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union, Any
import magic

from ..core.models import (
    DataHierarchy, ResourceMetadata, ResourceType, DataType, UploadProgress
)
from ..config import get_config
from ..logger import get_logger

logger = get_logger(__name__)


class FileTypeDetectionError(Exception):
    """Raised when file type cannot be detected or is unsupported."""
    pass


class FileSizeError(Exception):
    """Raised when file size exceeds limits."""
    pass


class FileValidator:
    """
    Validates file types, sizes, and formats.
    """
    
    # Mapping of file extensions to DataType enums
    EXTENSION_TO_DATATYPE = {
        # Structured data
        '.csv': DataType.CSV,
        '.tsv': DataType.TSV,
        '.xlsx': DataType.EXCEL,
        '.xls': DataType.EXCEL,
        '.parquet': DataType.PARQUET,
        
        # JSON data
        '.json': DataType.JSON,
        '.jsonl': DataType.JSONL,
        
        # Unstructured data
        '.pdf': DataType.PDF,
        '.txt': DataType.TXT,
        '.md': DataType.MARKDOWN,
        '.markdown': DataType.MARKDOWN,
        '.docx': DataType.DOCX,
        '.html': DataType.HTML,
        '.htm': DataType.HTML,
    }
    
    # Mapping of DataType to ResourceType
    DATATYPE_TO_RESOURCETYPE = {
        # Structured
        DataType.CSV: ResourceType.STRUCTURED,
        DataType.TSV: ResourceType.STRUCTURED,
        DataType.EXCEL: ResourceType.STRUCTURED,
        DataType.PARQUET: ResourceType.STRUCTURED,
        
        # JSON
        DataType.JSON: ResourceType.JSON,
        DataType.JSONL: ResourceType.JSON,
        
        # Unstructured
        DataType.PDF: ResourceType.UNSTRUCTURED,
        DataType.TXT: ResourceType.UNSTRUCTURED,
        DataType.MARKDOWN: ResourceType.UNSTRUCTURED,
        DataType.DOCX: ResourceType.UNSTRUCTURED,
        DataType.HTML: ResourceType.UNSTRUCTURED,
    }
    
    # MIME type validation for additional security
    VALID_MIME_TYPES = {
        DataType.CSV: ['text/csv', 'text/plain', 'application/csv'],
        DataType.TSV: ['text/tab-separated-values', 'text/plain'],
        DataType.EXCEL: [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel'
        ],
        DataType.PARQUET: ['application/octet-stream'],
        DataType.JSON: ['application/json', 'text/json', 'text/plain'],
        DataType.JSONL: ['application/jsonl', 'text/plain'],
        DataType.PDF: ['application/pdf'],
        DataType.TXT: ['text/plain'],
        DataType.MARKDOWN: ['text/markdown', 'text/plain'],
        DataType.DOCX: [
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ],
        DataType.HTML: ['text/html'],
    }
    
    def __init__(self, config=None):
        """Initialize file validator with configuration."""
        self.config = config or get_config()
        self.max_file_size_bytes = self.config.storage.max_file_size_mb * 1024 * 1024
    
    def detect_file_type(self, file_path: Union[str, Path]) -> Tuple[DataType, ResourceType]:
        """
        Detect file type from extension and MIME type.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (DataType, ResourceType)
            
        Raises:
            FileTypeDetectionError: If file type cannot be detected or is unsupported
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileTypeDetectionError(f"File does not exist: {file_path}")
        
        # Get file extension
        extension = file_path.suffix.lower()
        
        if extension not in self.EXTENSION_TO_DATATYPE:
            raise FileTypeDetectionError(
                f"Unsupported file extension: {extension}. "
                f"Supported extensions: {list(self.EXTENSION_TO_DATATYPE.keys())}"
            )
        
        data_type = self.EXTENSION_TO_DATATYPE[extension]
        resource_type = self.DATATYPE_TO_RESOURCETYPE[data_type]
        
        # Validate MIME type for additional security
        try:
            mime_type = magic.from_file(str(file_path), mime=True)
            valid_mimes = self.VALID_MIME_TYPES.get(data_type, [])
            
            if valid_mimes and mime_type not in valid_mimes:
                logger.warning(
                    f"MIME type mismatch for {file_path}: got {mime_type}, "
                    f"expected one of {valid_mimes}"
                )
                # Don't raise error, just log warning as some systems may report different MIME types
        
        except Exception as e:
            logger.warning(f"Could not detect MIME type for {file_path}: {e}")
        
        return data_type, resource_type
    
    def validate_file_size(self, file_path: Union[str, Path]) -> int:
        """
        Validate file size against configured limits.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File size in bytes
            
        Raises:
            FileSizeError: If file size exceeds limits
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileSizeError(f"File does not exist: {file_path}")
        
        file_size = file_path.stat().st_size
        
        if file_size > self.max_file_size_bytes:
            raise FileSizeError(
                f"File size {file_size / (1024*1024):.1f}MB exceeds limit of "
                f"{self.config.storage.max_file_size_mb}MB"
            )
        
        if file_size == 0:
            raise FileSizeError("File is empty")
        
        return file_size
    
    def validate_file(self, file_path: Union[str, Path]) -> Tuple[DataType, ResourceType, int]:
        """
        Perform complete file validation.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (DataType, ResourceType, file_size_bytes)
            
        Raises:
            FileTypeDetectionError: If file type is unsupported
            FileSizeError: If file size is invalid
        """
        file_path = Path(file_path)
        
        # Validate file exists and is readable
        if not file_path.exists():
            raise FileTypeDetectionError(f"File does not exist: {file_path}")
        
        if not file_path.is_file():
            raise FileTypeDetectionError(f"Path is not a file: {file_path}")
        
        if not os.access(file_path, os.R_OK):
            raise FileTypeDetectionError(f"File is not readable: {file_path}")
        
        # Detect file type
        data_type, resource_type = self.detect_file_type(file_path)
        
        # Validate file size
        file_size = self.validate_file_size(file_path)
        
        logger.info(
            f"File validation successful: {file_path.name} "
            f"({data_type.value}, {file_size / (1024*1024):.1f}MB)"
        )
        
        return data_type, resource_type, file_size


class DuplicateDetector:
    """
    Detects duplicate files using hash-based comparison.
    """
    
    def __init__(self, config=None):
        """Initialize duplicate detector."""
        self.config = config or get_config()
    
    def calculate_file_hash(self, file_path: Union[str, Path], 
                           algorithm: str = "sha256") -> str:
        """
        Calculate hash of a file.
        
        Args:
            file_path: Path to the file
            algorithm: Hash algorithm to use (sha256, md5, etc.)
            
        Returns:
            Hex digest of the file hash
        """
        file_path = Path(file_path)
        
        hash_obj = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            # Read file in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(8192), b""):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    def find_duplicates_by_hash(self, file_path: Union[str, Path], 
                               existing_hashes: Dict[str, List[str]]) -> List[str]:
        """
        Find duplicate files by comparing hash.
        
        Args:
            file_path: Path to the file to check
            existing_hashes: Dictionary mapping hashes to lists of resource_ids
            
        Returns:
            List of resource_ids that are duplicates of this file
        """
        file_hash = self.calculate_file_hash(file_path)
        return existing_hashes.get(file_hash, [])
    
    def find_duplicates_by_content(self, file_path: Union[str, Path],
                                  existing_files: List[Path]) -> List[Path]:
        """
        Find duplicates by comparing file content directly.
        
        Args:
            file_path: Path to the file to check
            existing_files: List of existing file paths to compare against
            
        Returns:
            List of file paths that are duplicates
        """
        file_path = Path(file_path)
        duplicates = []
        
        file_hash = self.calculate_file_hash(file_path)
        
        for existing_file in existing_files:
            try:
                existing_hash = self.calculate_file_hash(existing_file)
                if file_hash == existing_hash:
                    duplicates.append(existing_file)
            except Exception as e:
                logger.warning(f"Could not hash existing file {existing_file}: {e}")
        
        return duplicates


class FileUploadAPI:
    """
    Main API for file upload operations with progress tracking and bulk support.
    """
    
    def __init__(self, config=None):
        """Initialize file upload API."""
        self.config = config or get_config()
        self.validator = FileValidator(config)
        self.duplicate_detector = DuplicateDetector(config)
        
        # Ensure directories exist
        self.config.create_directories()
    
    def upload_file(self, client_id: str, user_id: str, file_path: Union[str, Path],
                   resource_name: Optional[str] = None, 
                   check_duplicates: bool = True) -> ResourceMetadata:
        """
        Upload a single file with validation and duplicate checking.
        
        Args:
            client_id: Client identifier (UUID v4)
            user_id: User identifier (UUID v4)
            file_path: Path to the file to upload
            resource_name: Optional custom name for the resource
            check_duplicates: Whether to check for duplicates
            
        Returns:
            ResourceMetadata for the uploaded file
            
        Raises:
            ValueError: If IDs are invalid
            FileTypeDetectionError: If file type is unsupported
            FileSizeError: If file size is invalid
        """
        file_path = Path(file_path)
        
        # Generate data hierarchy
        hierarchy = DataHierarchy.generate_new(client_id, user_id)
        
        logger.info(f"Starting upload for {file_path.name} (resource_id: {hierarchy.resource_id})")
        
        # Validate file
        data_type, resource_type, file_size = self.validator.validate_file(file_path)
        
        # Calculate file hash for duplicate detection
        file_hash = self.duplicate_detector.calculate_file_hash(file_path)
        
        # Check for duplicates if requested
        duplicates = []
        if check_duplicates:
            # This would normally query the metadata registry
            # For now, we'll just log that duplicate checking would happen here
            logger.info(f"Duplicate check for hash {file_hash[:8]}... (would query metadata registry)")
        
        # Determine storage path
        storage_subdir = self._get_storage_subdir(resource_type)
        storage_dir = (
            self.config.get_full_path(storage_subdir) / 
            client_id / user_id / hierarchy.resource_id
        )
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy file to storage location
        storage_path = storage_dir / f"v1_{file_path.name}"
        shutil.copy2(file_path, storage_path)
        
        # Create resource metadata
        metadata = ResourceMetadata(
            resource_id=hierarchy.resource_id,
            user_id=user_id,
            client_id=client_id,
            resource_type=resource_type,
            data_type=data_type,
            original_filename=file_path.name,
            file_size_bytes=file_size,
            storage_path=str(storage_path.relative_to(self.config.get_full_path(""))),
            file_hash=file_hash,
            processing_status="uploaded"
        )
        
        logger.info(f"File upload completed: {file_path.name} -> {hierarchy.resource_id}")
        
        return metadata
    
    def upload_bulk(self, client_id: str, user_id: str, file_paths: List[Union[str, Path]],
                   parallel: bool = True, max_workers: Optional[int] = None) -> List[ResourceMetadata]:
        """
        Upload multiple files with optional parallel processing.
        
        Args:
            client_id: Client identifier (UUID v4)
            user_id: User identifier (UUID v4)
            file_paths: List of file paths to upload
            parallel: Whether to use parallel processing
            max_workers: Maximum number of worker threads (uses config default if None)
            
        Returns:
            List of ResourceMetadata for successfully uploaded files
        """
        if not file_paths:
            return []
        
        max_workers = max_workers or self.config.processing.max_parallel_workers
        
        logger.info(f"Starting bulk upload of {len(file_paths)} files")
        
        if not parallel or len(file_paths) == 1:
            # Sequential processing
            results = []
            for file_path in file_paths:
                try:
                    metadata = self.upload_file(client_id, user_id, file_path)
                    results.append(metadata)
                except Exception as e:
                    logger.error(f"Failed to upload {file_path}: {e}")
            return results
        
        # Parallel processing
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all upload tasks
            future_to_path = {
                executor.submit(self.upload_file, client_id, user_id, file_path): file_path
                for file_path in file_paths
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_path):
                file_path = future_to_path[future]
                try:
                    metadata = future.result()
                    results.append(metadata)
                    logger.info(f"Parallel upload completed: {file_path}")
                except Exception as e:
                    logger.error(f"Parallel upload failed for {file_path}: {e}")
        
        logger.info(f"Bulk upload completed: {len(results)}/{len(file_paths)} files successful")
        
        return results
    
    def _get_storage_subdir(self, resource_type: ResourceType) -> str:
        """Get storage subdirectory for resource type."""
        if resource_type == ResourceType.STRUCTURED:
            return self.config.storage.structured_data_dir
        elif resource_type == ResourceType.JSON:
            return self.config.storage.json_data_dir
        elif resource_type == ResourceType.UNSTRUCTURED:
            return self.config.storage.unstructured_data_dir
        else:
            raise ValueError(f"Unknown resource type: {resource_type}")
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions."""
        return list(FileValidator.EXTENSION_TO_DATATYPE.keys())
    
    def get_supported_types(self) -> Dict[str, List[str]]:
        """Get supported file types grouped by resource type."""
        result = {
            "structured": [],
            "json": [],
            "unstructured": []
        }
        
        for ext, data_type in FileValidator.EXTENSION_TO_DATATYPE.items():
            resource_type = FileValidator.DATATYPE_TO_RESOURCETYPE[data_type]
            result[resource_type.value].append(ext)
        
        return result
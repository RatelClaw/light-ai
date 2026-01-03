"""
Version management and audit system for Universal Data Handler.

Provides comprehensive versioning capabilities with non-destructive updates,
complete audit trails, version retrieval, rollback functionality, and
soft/hard delete operations with retention policies.
"""

import uuid
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ..core.models import ResourceMetadata, DataHierarchy, ResourceType
from .metadata_registry import MetadataRegistry
from .storage_utils import FileManager, StoragePathUtils
from ..config import Config, get_config
from ..logger import get_logger

logger = get_logger(__name__)


class OperationType(Enum):
    """Types of operations that can be audited."""
    UPLOAD = "upload"
    UPDATE = "update"
    DELETE = "delete"
    RESTORE = "restore"
    ROLLBACK = "rollback"
    EXPORT = "export"
    CLEAN = "clean"
    TRANSFORM = "transform"


class DeleteType(Enum):
    """Types of delete operations."""
    SOFT = "soft"
    HARD = "hard"


@dataclass
class VersionInfo:
    """Information about a specific version of a resource."""
    resource_id: str
    version: int
    created_at: datetime
    created_by: str
    operation: OperationType
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    file_hash: Optional[str] = None
    metadata_snapshot: Optional[Dict[str, Any]] = None
    operation_details: Optional[str] = None


@dataclass
class AuditRecord:
    """Complete audit record for an operation."""
    audit_id: str
    resource_id: str
    operation: OperationType
    user_id: str
    client_id: str
    timestamp: datetime
    version_before: Optional[int] = None
    version_after: Optional[int] = None
    operation_details: Optional[str] = None
    metadata_before: Optional[Dict[str, Any]] = None
    metadata_after: Optional[Dict[str, Any]] = None


@dataclass
class RetentionPolicy:
    """Retention policy for soft-deleted resources."""
    soft_delete_days: int = 30
    audit_retention_days: int = 90
    version_retention_count: Optional[int] = None  # None = keep all versions
    cleanup_interval_hours: int = 24


class VersionManager:
    """
    Comprehensive version management and audit system.
    
    Handles all versioning operations including creation, retrieval, rollback,
    and deletion with complete audit trails and retention policies.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize version manager.
        
        Args:
            config: Optional configuration instance
        """
        self.config = config or get_config()
        self.metadata_registry = MetadataRegistry(config)
        self.file_manager = FileManager(config)
        self.path_utils = StoragePathUtils(config)
        self.retention_policy = RetentionPolicy()
        
        # Initialize components
        self.metadata_registry.initialize()
    
    # Version Management Operations
    
    def create_version(self, resource_metadata: ResourceMetadata, 
                      source_file_path: Optional[Union[str, Path]] = None,
                      user_id: str = None, operation: OperationType = OperationType.UPLOAD,
                      operation_details: Optional[str] = None) -> int:
        """
        Create a new version of a resource with complete audit trail.
        
        Args:
            resource_metadata: Resource metadata for the new version
            source_file_path: Optional path to source file to store
            user_id: User creating the version (defaults to resource user_id)
            operation: Type of operation creating this version
            operation_details: Optional details about the operation
            
        Returns:
            int: New version number
            
        Raises:
            ValueError: If resource doesn't exist for updates
            OSError: If file operations fail
        """
        user_id = user_id or resource_metadata.user_id
        
        # Get current metadata if this is an update
        current_metadata = self.metadata_registry.get_resource_metadata(resource_metadata.resource_id)
        version_before = current_metadata.version if current_metadata else None
        
        # Determine new version number
        if current_metadata:
            new_version = current_metadata.version + 1
            resource_metadata.version = new_version
        else:
            new_version = 1
            resource_metadata.version = new_version
        
        # Create hierarchy for file operations
        hierarchy = DataHierarchy(
            client_id=resource_metadata.client_id,
            user_id=resource_metadata.user_id,
            resource_id=resource_metadata.resource_id
        )
        
        try:
            # Store file if provided
            stored_file_path = None
            if source_file_path:
                storage_type = self._get_storage_type(resource_metadata.resource_type)
                stored_file_path = self.file_manager.store_file(
                    source_file_path, hierarchy, resource_metadata.original_filename,
                    storage_type, new_version, create_current_link=True
                )
                resource_metadata.storage_path = str(stored_file_path)
            
            # Update metadata
            resource_metadata.updated_at = datetime.utcnow()
            
            if current_metadata:
                self.metadata_registry.update_resource_metadata(resource_metadata)
            else:
                self.metadata_registry.create_resource_metadata(resource_metadata)
            
            # Log audit trail
            self._log_audit_record(
                resource_id=resource_metadata.resource_id,
                operation=operation,
                user_id=user_id,
                client_id=resource_metadata.client_id,
                version_before=version_before,
                version_after=new_version,
                operation_details=operation_details,
                metadata_before=current_metadata.to_dict() if current_metadata else None,
                metadata_after=resource_metadata.to_dict()
            )
            
            logger.info(f"Created version {new_version} for resource {resource_metadata.resource_id}")
            return new_version
            
        except Exception as e:
            logger.error(f"Failed to create version for resource {resource_metadata.resource_id}: {e}")
            raise
    
    def get_version_info(self, resource_id: str, version: Optional[int] = None) -> Optional[VersionInfo]:
        """
        Get information about a specific version.
        
        Args:
            resource_id: Resource identifier
            version: Version number (if None, gets current version)
            
        Returns:
            Optional[VersionInfo]: Version information or None if not found
        """
        # Get metadata for the version
        metadata = self.metadata_registry.get_resource_metadata(resource_id)
        if not metadata:
            return None
        
        # If specific version requested, check if it exists
        if version and version != metadata.version:
            # Check if version exists in file system
            hierarchy = DataHierarchy(
                client_id=metadata.client_id,
                user_id=metadata.user_id,
                resource_id=resource_id
            )
            
            storage_type = self._get_storage_type(metadata.resource_type)
            versions = self.path_utils.list_versions(hierarchy, metadata.original_filename, storage_type)
            
            if version not in versions:
                return None
            
            # Get file path for specific version
            file_path = self.path_utils.generate_file_path(
                hierarchy, metadata.original_filename, storage_type, version
            )
        else:
            version = metadata.version
            file_path = Path(metadata.storage_path) if metadata.storage_path else None
        
        # Get audit record for this version
        audit_records = self.get_audit_trail(resource_id, limit=100)
        creation_record = None
        for record in reversed(audit_records):  # Oldest first
            if record.get('version_after') == version:
                creation_record = record
                break
        
        # Extract operation details from JSON if needed
        operation_details = None
        if creation_record and creation_record.get('operation_details'):
            details_str = creation_record['operation_details']
            try:
                import json
                details_dict = json.loads(details_str)
                operation_details = details_dict.get('description', details_str)
            except (json.JSONDecodeError, TypeError):
                operation_details = details_str
        
        return VersionInfo(
            resource_id=resource_id,
            version=version,
            created_at=metadata.updated_at if version == metadata.version else 
                      datetime.fromisoformat(creation_record['timestamp']) if creation_record else metadata.created_at,
            created_by=creation_record['user_id'] if creation_record else metadata.user_id,
            operation=OperationType(creation_record['operation']) if creation_record else OperationType.UPLOAD,
            file_path=str(file_path) if file_path and file_path.exists() else None,
            file_size_bytes=file_path.stat().st_size if file_path and file_path.exists() else None,
            file_hash=metadata.file_hash,
            metadata_snapshot=metadata.to_dict(),
            operation_details=operation_details
        )
    
    def list_versions(self, resource_id: str) -> List[VersionInfo]:
        """
        List all versions of a resource.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            List[VersionInfo]: List of version information, sorted by version descending
        """
        metadata = self.metadata_registry.get_resource_metadata(resource_id)
        if not metadata:
            return []
        
        # For resources with files, check file system versions
        if metadata.storage_path and metadata.resource_type in [ResourceType.STRUCTURED]:
            hierarchy = DataHierarchy(
                client_id=metadata.client_id,
                user_id=metadata.user_id,
                resource_id=resource_id
            )
            
            storage_type = self._get_storage_type(metadata.resource_type)
            version_numbers = self.path_utils.list_versions(hierarchy, metadata.original_filename, storage_type)
        else:
            # For JSON and unstructured data, get versions from audit trail
            audit_records = self.get_audit_trail(resource_id, limit=1000)
            version_numbers = set()
            for record in audit_records:
                if record.get('version_after'):
                    version_numbers.add(record['version_after'])
            version_numbers = sorted(list(version_numbers), reverse=True)
        
        versions = []
        for version_num in version_numbers:
            version_info = self.get_version_info(resource_id, version_num)
            if version_info:
                versions.append(version_info)
        
        return sorted(versions, key=lambda v: v.version, reverse=True)
    
    def rollback_to_version(self, resource_id: str, target_version: int, 
                           user_id: str, operation_details: Optional[str] = None) -> int:
        """
        Rollback a resource to a specific version.
        
        Args:
            resource_id: Resource identifier
            target_version: Version to rollback to
            user_id: User performing the rollback
            operation_details: Optional details about the rollback
            
        Returns:
            int: New version number after rollback
            
        Raises:
            ValueError: If target version doesn't exist
            OSError: If file operations fail
        """
        # Get current metadata
        current_metadata = self.metadata_registry.get_resource_metadata(resource_id)
        if not current_metadata:
            raise ValueError(f"Resource not found: {resource_id}")
        
        # Verify target version exists
        target_version_info = self.get_version_info(resource_id, target_version)
        if not target_version_info:
            raise ValueError(f"Version {target_version} not found for resource {resource_id}")
        
        # Create hierarchy
        hierarchy = DataHierarchy(
            client_id=current_metadata.client_id,
            user_id=current_metadata.user_id,
            resource_id=resource_id
        )
        
        # Copy target version file to new version
        storage_type = self._get_storage_type(current_metadata.resource_type)
        target_file_path = self.path_utils.generate_file_path(
            hierarchy, current_metadata.original_filename, storage_type, target_version
        )
        
        if not target_file_path.exists():
            raise ValueError(f"Target version file not found: {target_file_path}")
        
        # Create new version with rollback data
        new_version = current_metadata.version + 1
        new_file_path = self.file_manager.store_file(
            target_file_path, hierarchy, current_metadata.original_filename,
            storage_type, new_version, create_current_link=True
        )
        
        # Update metadata
        current_metadata.version = new_version
        current_metadata.storage_path = str(new_file_path)
        current_metadata.updated_at = datetime.utcnow()
        self.metadata_registry.update_resource_metadata(current_metadata)
        
        # Log audit trail
        rollback_details = f"Rolled back to version {target_version}"
        if operation_details:
            rollback_details += f": {operation_details}"
        
        self._log_audit_record(
            resource_id=resource_id,
            operation=OperationType.ROLLBACK,
            user_id=user_id,
            client_id=current_metadata.client_id,
            version_before=current_metadata.version - 1,
            version_after=new_version,
            operation_details=rollback_details,
            metadata_before=None,  # Could store previous state if needed
            metadata_after=current_metadata.to_dict()
        )
        
        logger.info(f"Rolled back resource {resource_id} to version {target_version}, created version {new_version}")
        return new_version
    
    # Delete Operations
    
    def soft_delete_resource(self, resource_id: str, user_id: str, 
                           operation_details: Optional[str] = None) -> bool:
        """
        Soft delete a resource (mark as deleted, retain data).
        
        Args:
            resource_id: Resource identifier
            user_id: User performing the deletion
            operation_details: Optional details about the deletion
            
        Returns:
            bool: True if resource was soft deleted, False if not found
        """
        metadata = self.metadata_registry.get_resource_metadata(resource_id)
        if not metadata:
            return False
        
        if metadata.is_deleted:
            logger.warning(f"Resource {resource_id} is already soft deleted")
            return True
        
        # Mark as deleted
        version_before = metadata.version
        metadata.is_deleted = True
        metadata.updated_at = datetime.utcnow()
        self.metadata_registry.update_resource_metadata(metadata)
        
        # Log audit trail
        self._log_audit_record(
            resource_id=resource_id,
            operation=OperationType.DELETE,
            user_id=user_id,
            client_id=metadata.client_id,
            version_before=version_before,
            version_after=metadata.version,
            operation_details=f"Soft delete: {operation_details or 'User requested deletion'}",
            metadata_before=None,
            metadata_after=metadata.to_dict()
        )
        
        logger.info(f"Soft deleted resource {resource_id}")
        return True
    
    def hard_delete_resource(self, resource_id: str, user_id: str, 
                           operation_details: Optional[str] = None) -> bool:
        """
        Hard delete a resource (permanently remove all data).
        
        Args:
            resource_id: Resource identifier
            user_id: User performing the deletion
            operation_details: Optional details about the deletion
            
        Returns:
            bool: True if resource was hard deleted, False if not found
        """
        metadata = self.metadata_registry.get_resource_metadata(resource_id)
        if not metadata:
            return False
        
        # Create hierarchy for file operations
        hierarchy = DataHierarchy(
            client_id=metadata.client_id,
            user_id=metadata.user_id,
            resource_id=resource_id
        )
        
        # Log audit trail before deletion
        self._log_audit_record(
            resource_id=resource_id,
            operation=OperationType.DELETE,
            user_id=user_id,
            client_id=metadata.client_id,
            version_before=metadata.version,
            version_after=None,
            operation_details=f"Hard delete: {operation_details or 'Permanent deletion requested'}",
            metadata_before=metadata.to_dict(),
            metadata_after=None
        )
        
        # Delete all file versions
        storage_type = self._get_storage_type(metadata.resource_type)
        self.file_manager.delete_file(
            hierarchy, metadata.original_filename, storage_type, 
            version=None, hard_delete=True
        )
        
        # Delete related records first to avoid foreign key constraints
        # Delete schema info records
        try:
            with self.metadata_registry.sqlite_manager.get_connection() as conn:
                conn.execute("DELETE FROM schema_info WHERE resource_id = ?", (resource_id,))
                conn.commit()
        except Exception as e:
            logger.warning(f"Failed to delete schema info for {resource_id}: {e}")
        
        # Delete upload progress records
        try:
            self.metadata_registry.delete_upload_progress(resource_id)
        except Exception as e:
            logger.warning(f"Failed to delete upload progress for {resource_id}: {e}")
        
        # Finally delete metadata (audit trail records will remain for historical purposes)
        self.metadata_registry.delete_resource_metadata(resource_id, hard_delete=True)
        
        logger.info(f"Hard deleted resource {resource_id}")
        return True
    
    def restore_resource(self, resource_id: str, user_id: str, 
                        operation_details: Optional[str] = None) -> bool:
        """
        Restore a soft-deleted resource.
        
        Args:
            resource_id: Resource identifier
            user_id: User performing the restoration
            operation_details: Optional details about the restoration
            
        Returns:
            bool: True if resource was restored, False if not found or not deleted
        """
        metadata = self.metadata_registry.get_resource_metadata(resource_id)
        if not metadata:
            return False
        
        if not metadata.is_deleted:
            logger.warning(f"Resource {resource_id} is not deleted")
            return True
        
        # Restore resource
        version_before = metadata.version
        metadata.is_deleted = False
        metadata.updated_at = datetime.utcnow()
        self.metadata_registry.update_resource_metadata(metadata)
        
        # Log audit trail
        self._log_audit_record(
            resource_id=resource_id,
            operation=OperationType.RESTORE,
            user_id=user_id,
            client_id=metadata.client_id,
            version_before=version_before,
            version_after=metadata.version,
            operation_details=f"Restore: {operation_details or 'User requested restoration'}",
            metadata_before=None,
            metadata_after=metadata.to_dict()
        )
        
        logger.info(f"Restored resource {resource_id}")
        return True
    
    # Audit Trail Operations
    
    def get_audit_trail(self, resource_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get complete audit trail for a resource.
        
        Args:
            resource_id: Resource identifier
            limit: Maximum number of records to return
            
        Returns:
            List[Dict[str, Any]]: Audit trail records
        """
        return self.metadata_registry.get_audit_trail(resource_id, limit)
    
    def get_audit_summary(self, resource_id: str) -> Dict[str, Any]:
        """
        Get audit summary statistics for a resource.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            Dict[str, Any]: Audit summary with operation counts and timeline
        """
        audit_records = self.get_audit_trail(resource_id, limit=1000)
        
        if not audit_records:
            return {
                'total_operations': 0,
                'operations_by_type': {},
                'operations_by_user': {},
                'first_operation': None,
                'last_operation': None,
                'total_versions': 0
            }
        
        # Count operations by type
        operations_by_type = {}
        operations_by_user = {}
        versions = set()
        
        for record in audit_records:
            op_type = record['operation']
            user_id = record['user_id']
            
            operations_by_type[op_type] = operations_by_type.get(op_type, 0) + 1
            operations_by_user[user_id] = operations_by_user.get(user_id, 0) + 1
            
            if record.get('version_after'):
                versions.add(record['version_after'])
        
        return {
            'total_operations': len(audit_records),
            'operations_by_type': operations_by_type,
            'operations_by_user': operations_by_user,
            'first_operation': audit_records[-1]['timestamp'] if audit_records else None,
            'last_operation': audit_records[0]['timestamp'] if audit_records else None,
            'total_versions': len(versions)
        }
    
    # Cleanup and Maintenance Operations
    
    def cleanup_old_soft_deleted(self, days_to_keep: Optional[int] = None) -> int:
        """
        Clean up old soft-deleted resources by hard deleting them.
        
        Args:
            days_to_keep: Number of days to keep soft-deleted resources
                         (defaults to retention policy)
            
        Returns:
            int: Number of resources hard deleted
        """
        days_to_keep = days_to_keep or self.retention_policy.soft_delete_days
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Find old soft-deleted resources
        # This would require a query method in metadata registry
        # For now, we'll implement a basic version
        
        deleted_count = 0
        # Implementation would query for soft-deleted resources older than cutoff_date
        # and call hard_delete_resource for each
        
        logger.info(f"Cleaned up {deleted_count} old soft-deleted resources")
        return deleted_count
    
    def cleanup_old_audit_records(self, days_to_keep: Optional[int] = None) -> int:
        """
        Clean up old audit trail records.
        
        Args:
            days_to_keep: Number of days to keep audit records
                         (defaults to retention policy)
            
        Returns:
            int: Number of audit records deleted
        """
        days_to_keep = days_to_keep or self.retention_policy.audit_retention_days
        return self.metadata_registry.cleanup_old_audit_records(days_to_keep)
    
    def cleanup_old_versions(self, resource_id: str, versions_to_keep: int) -> int:
        """
        Clean up old versions of a resource, keeping only the most recent ones.
        
        Args:
            resource_id: Resource identifier
            versions_to_keep: Number of versions to keep
            
        Returns:
            int: Number of versions deleted
        """
        versions = self.list_versions(resource_id)
        if len(versions) <= versions_to_keep:
            return 0
        
        # Sort by version number and keep the most recent
        versions_sorted = sorted(versions, key=lambda v: v.version, reverse=True)
        versions_to_delete = versions_sorted[versions_to_keep:]
        
        metadata = self.metadata_registry.get_resource_metadata(resource_id)
        if not metadata:
            return 0
        
        hierarchy = DataHierarchy(
            client_id=metadata.client_id,
            user_id=metadata.user_id,
            resource_id=resource_id
        )
        
        storage_type = self._get_storage_type(metadata.resource_type)
        deleted_count = 0
        
        for version_info in versions_to_delete:
            # Don't delete the current version
            if version_info.version == metadata.version:
                continue
            
            success = self.file_manager.delete_file(
                hierarchy, metadata.original_filename, storage_type,
                version=version_info.version, hard_delete=True
            )
            if success:
                deleted_count += 1
        
        logger.info(f"Cleaned up {deleted_count} old versions for resource {resource_id}")
        return deleted_count
    
    # Private Helper Methods
    
    def _get_storage_type(self, resource_type) -> str:
        """Get storage type string from ResourceType enum."""
        from ..core.models import ResourceType
        
        if resource_type == ResourceType.STRUCTURED:
            return "structured"
        elif resource_type == ResourceType.JSON:
            return "json"
        elif resource_type == ResourceType.UNSTRUCTURED:
            return "unstructured"
        else:
            return "raw"
    
    def _log_audit_record(self, resource_id: str, operation: OperationType,
                         user_id: str, client_id: str, version_before: Optional[int] = None,
                         version_after: Optional[int] = None, operation_details: Optional[str] = None,
                         metadata_before: Optional[Dict[str, Any]] = None,
                         metadata_after: Optional[Dict[str, Any]] = None) -> None:
        """Log an audit record with complete information."""
        
        # Store metadata snapshots as JSON strings if provided
        details_dict = {}
        if operation_details:
            details_dict['description'] = operation_details
        if metadata_before:
            details_dict['metadata_before'] = metadata_before
        if metadata_after:
            details_dict['metadata_after'] = metadata_after
        
        details_json = json.dumps(details_dict) if details_dict else operation_details
        
        self.metadata_registry.log_operation(
            resource_id=resource_id,
            operation=operation.value,
            user_id=user_id,
            client_id=client_id,
            operation_details=details_json,
            version_before=version_before,
            version_after=version_after
        )


# Utility Functions

def create_version_manager(config: Optional[Config] = None) -> VersionManager:
    """
    Create and initialize a version manager instance.
    
    Args:
        config: Optional configuration instance
        
    Returns:
        VersionManager: Initialized version manager
    """
    return VersionManager(config)


def get_resource_version_history(resource_id: str, config: Optional[Config] = None) -> List[VersionInfo]:
    """
    Get complete version history for a resource.
    
    Args:
        resource_id: Resource identifier
        config: Optional configuration instance
        
    Returns:
        List[VersionInfo]: Complete version history
    """
    version_manager = VersionManager(config)
    return version_manager.list_versions(resource_id)


def rollback_resource(resource_id: str, target_version: int, user_id: str,
                     operation_details: Optional[str] = None, 
                     config: Optional[Config] = None) -> int:
    """
    Rollback a resource to a specific version.
    
    Args:
        resource_id: Resource identifier
        target_version: Version to rollback to
        user_id: User performing the rollback
        operation_details: Optional details about the rollback
        config: Optional configuration instance
        
    Returns:
        int: New version number after rollback
    """
    version_manager = VersionManager(config)
    return version_manager.rollback_to_version(resource_id, target_version, user_id, operation_details)


def cleanup_old_resources(days_to_keep: int = 30, config: Optional[Config] = None) -> Dict[str, int]:
    """
    Clean up old soft-deleted resources and audit records.
    
    Args:
        days_to_keep: Number of days to keep soft-deleted resources
        config: Optional configuration instance
        
    Returns:
        Dict[str, int]: Cleanup statistics
    """
    version_manager = VersionManager(config)
    
    resources_deleted = version_manager.cleanup_old_soft_deleted(days_to_keep)
    audit_records_deleted = version_manager.cleanup_old_audit_records()
    
    return {
        'soft_deleted_resources_cleaned': resources_deleted,
        'audit_records_cleaned': audit_records_deleted
    }
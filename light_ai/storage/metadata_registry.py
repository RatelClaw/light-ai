"""
SQLite metadata registry implementation for Universal Data Handler.

Provides high-level operations for managing resource metadata, schema information,
audit trails, and upload progress tracking in the SQLite database.
"""

import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from ..core.models import ResourceMetadata, SchemaInfo, UploadProgress, DataHierarchy
from .database_managers import SQLiteManager
from ..config import Config, get_config
from ..logger import get_logger

logger = get_logger(__name__)


class MetadataRegistry:
    """
    High-level interface for metadata registry operations.
    
    Provides CRUD operations for resource metadata, schema information,
    audit trails, and upload progress tracking.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize metadata registry.
        
        Args:
            config: Optional configuration instance
        """
        self.config = config or get_config()
        self.sqlite_manager = SQLiteManager(config)
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize the metadata registry database."""
        if not self._initialized:
            self.sqlite_manager.initialize()
            self._initialized = True
    
    # Resource Metadata Operations
    
    def create_resource_metadata(self, metadata: ResourceMetadata) -> None:
        """
        Create a new resource metadata record.
        
        Args:
            metadata: ResourceMetadata instance to store
            
        Raises:
            ValueError: If resource_id already exists
        """
        self.initialize()
        
        # Check if resource already exists
        existing = self.get_resource_metadata(metadata.resource_id)
        if existing:
            raise ValueError(f"Resource {metadata.resource_id} already exists")
        
        sql = """
            INSERT INTO resource_metadata (
                resource_id, user_id, client_id, resource_type, data_type,
                original_filename, file_size_bytes, storage_path, created_at,
                updated_at, version, is_deleted, row_count, column_count,
                chunk_count, file_hash, content_preview, processing_status,
                error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        parameters = (
            metadata.resource_id,
            metadata.user_id,
            metadata.client_id,
            metadata.resource_type.value,
            metadata.data_type.value,
            metadata.original_filename,
            metadata.file_size_bytes,
            metadata.storage_path,
            metadata.created_at.isoformat(),
            metadata.updated_at.isoformat(),
            metadata.version,
            metadata.is_deleted,
            metadata.row_count,
            metadata.column_count,
            metadata.chunk_count,
            metadata.file_hash,
            metadata.content_preview,
            metadata.processing_status,
            metadata.error_message
        )
        
        rows_affected = self.sqlite_manager.execute_update(sql, parameters)
        if rows_affected == 1:
            logger.info(f"Created resource metadata: {metadata.resource_id}")
        else:
            raise RuntimeError(f"Failed to create resource metadata: {metadata.resource_id}")
    
    def get_resource_metadata(self, resource_id: str) -> Optional[ResourceMetadata]:
        """
        Get resource metadata by ID.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            Optional[ResourceMetadata]: Resource metadata or None if not found
        """
        self.initialize()
        
        sql = "SELECT * FROM resource_metadata WHERE resource_id = ?"
        results = self.sqlite_manager.execute_query(sql, (resource_id,))
        
        if not results:
            return None
        
        return self._dict_to_resource_metadata(results[0])
    
    def update_resource_metadata(self, metadata: ResourceMetadata) -> None:
        """
        Update existing resource metadata.
        
        Args:
            metadata: Updated ResourceMetadata instance
            
        Raises:
            ValueError: If resource doesn't exist
        """
        self.initialize()
        
        # Update timestamp
        metadata.updated_at = datetime.utcnow()
        
        sql = """
            UPDATE resource_metadata SET
                user_id = ?, client_id = ?, resource_type = ?, data_type = ?,
                original_filename = ?, file_size_bytes = ?, storage_path = ?,
                updated_at = ?, version = ?, is_deleted = ?, row_count = ?,
                column_count = ?, chunk_count = ?, file_hash = ?, content_preview = ?,
                processing_status = ?, error_message = ?
            WHERE resource_id = ?
        """
        
        parameters = (
            metadata.user_id,
            metadata.client_id,
            metadata.resource_type.value,
            metadata.data_type.value,
            metadata.original_filename,
            metadata.file_size_bytes,
            metadata.storage_path,
            metadata.updated_at.isoformat(),
            metadata.version,
            metadata.is_deleted,
            metadata.row_count,
            metadata.column_count,
            metadata.chunk_count,
            metadata.file_hash,
            metadata.content_preview,
            metadata.processing_status,
            metadata.error_message,
            metadata.resource_id
        )
        
        rows_affected = self.sqlite_manager.execute_update(sql, parameters)
        if rows_affected == 0:
            raise ValueError(f"Resource not found: {metadata.resource_id}")
        
        logger.info(f"Updated resource metadata: {metadata.resource_id}")
    
    def delete_resource_metadata(self, resource_id: str, hard_delete: bool = False) -> None:
        """
        Delete resource metadata (soft or hard delete).
        
        Args:
            resource_id: Resource identifier
            hard_delete: If True, permanently delete; if False, mark as deleted
        """
        self.initialize()
        
        if hard_delete:
            sql = "DELETE FROM resource_metadata WHERE resource_id = ?"
            rows_affected = self.sqlite_manager.execute_update(sql, (resource_id,))
            logger.info(f"Hard deleted resource metadata: {resource_id}")
        else:
            sql = """
                UPDATE resource_metadata 
                SET is_deleted = 1, updated_at = ? 
                WHERE resource_id = ?
            """
            timestamp = datetime.utcnow().isoformat()
            rows_affected = self.sqlite_manager.execute_update(sql, (timestamp, resource_id))
            logger.info(f"Soft deleted resource metadata: {resource_id}")
        
        if rows_affected == 0:
            raise ValueError(f"Resource not found: {resource_id}")
    
    def list_resources(self, client_id: str, user_id: Optional[str] = None, 
                      include_deleted: bool = False) -> List[ResourceMetadata]:
        """
        List resources for a client/user.
        
        Args:
            client_id: Client identifier
            user_id: Optional user identifier (if None, returns all client resources)
            include_deleted: Whether to include soft-deleted resources
            
        Returns:
            List[ResourceMetadata]: List of resource metadata
        """
        self.initialize()
        
        conditions = ["client_id = ?"]
        parameters = [client_id]
        
        if user_id:
            conditions.append("user_id = ?")
            parameters.append(user_id)
        
        if not include_deleted:
            conditions.append("is_deleted = 0")
        
        sql = f"SELECT * FROM resource_metadata WHERE {' AND '.join(conditions)} ORDER BY created_at DESC"
        results = self.sqlite_manager.execute_query(sql, tuple(parameters))
        
        return [self._dict_to_resource_metadata(row) for row in results]
    
    def _dict_to_resource_metadata(self, row: Dict[str, Any]) -> ResourceMetadata:
        """Convert database row to ResourceMetadata instance."""
        from ..core.models import ResourceType, DataType
        
        return ResourceMetadata(
            resource_id=row['resource_id'],
            user_id=row['user_id'],
            client_id=row['client_id'],
            resource_type=ResourceType(row['resource_type']),
            data_type=DataType(row['data_type']),
            original_filename=row['original_filename'],
            file_size_bytes=row['file_size_bytes'],
            storage_path=row['storage_path'],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            version=row['version'],
            is_deleted=bool(row['is_deleted']),
            row_count=row['row_count'],
            column_count=row['column_count'],
            chunk_count=row['chunk_count'],
            file_hash=row['file_hash'],
            content_preview=row['content_preview'],
            processing_status=row['processing_status'],
            error_message=row['error_message']
        )
    
    # Schema Information Operations
    
    def create_schema_info(self, schema_info: SchemaInfo) -> None:
        """
        Create schema information record.
        
        Args:
            schema_info: SchemaInfo instance to store
        """
        self.initialize()
        
        sql = """
            INSERT INTO schema_info (
                schema_id, resource_id, version, schema_json, 
                statistics_json, detected_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """
        
        parameters = (
            schema_info.schema_id,
            schema_info.resource_id,
            schema_info.version,
            schema_info.schema_json,
            schema_info.statistics_json,
            schema_info.detected_at.isoformat()
        )
        
        self.sqlite_manager.execute_update(sql, parameters)
        logger.info(f"Created schema info: {schema_info.schema_id}")
    
    def get_schema_info(self, resource_id: str, version: Optional[int] = None) -> Optional[SchemaInfo]:
        """
        Get schema information for a resource.
        
        Args:
            resource_id: Resource identifier
            version: Optional version (if None, gets latest)
            
        Returns:
            Optional[SchemaInfo]: Schema information or None if not found
        """
        self.initialize()
        
        if version:
            sql = "SELECT * FROM schema_info WHERE resource_id = ? AND version = ?"
            parameters = (resource_id, version)
        else:
            sql = "SELECT * FROM schema_info WHERE resource_id = ? ORDER BY version DESC LIMIT 1"
            parameters = (resource_id,)
        
        results = self.sqlite_manager.execute_query(sql, parameters)
        
        if not results:
            return None
        
        row = results[0]
        return SchemaInfo(
            schema_id=row['schema_id'],
            resource_id=row['resource_id'],
            version=row['version'],
            schema_json=row['schema_json'],
            statistics_json=row['statistics_json'],
            detected_at=datetime.fromisoformat(row['detected_at'])
        )
    
    # Audit Trail Operations
    
    def log_operation(self, resource_id: str, operation: str, user_id: str, 
                     client_id: str, operation_details: Optional[str] = None,
                     version_before: Optional[int] = None, 
                     version_after: Optional[int] = None) -> None:
        """
        Log an operation to the audit trail.
        
        Args:
            resource_id: Resource identifier
            operation: Operation type (upload, update, delete, etc.)
            user_id: User who performed the operation
            client_id: Client identifier
            operation_details: Optional details about the operation
            version_before: Version before the operation
            version_after: Version after the operation
        """
        self.initialize()
        
        audit_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        sql = """
            INSERT INTO audit_trail (
                audit_id, resource_id, operation, user_id, client_id,
                operation_details, timestamp, version_before, version_after
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        parameters = (
            audit_id, resource_id, operation, user_id, client_id,
            operation_details, timestamp, version_before, version_after
        )
        
        self.sqlite_manager.execute_update(sql, parameters)
        logger.debug(f"Logged operation: {operation} for resource {resource_id}")
    
    def get_audit_trail(self, resource_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get audit trail for a resource.
        
        Args:
            resource_id: Resource identifier
            limit: Maximum number of records to return
            
        Returns:
            List[Dict[str, Any]]: Audit trail records
        """
        self.initialize()
        
        sql = """
            SELECT * FROM audit_trail 
            WHERE resource_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """
        
        return self.sqlite_manager.execute_query(sql, (resource_id, limit))
    
    # Upload Progress Operations
    
    def create_upload_progress(self, progress: UploadProgress) -> None:
        """
        Create upload progress record.
        
        Args:
            progress: UploadProgress instance to store
        """
        self.initialize()
        
        sql = """
            INSERT OR REPLACE INTO upload_progress (
                resource_id, filename, total_bytes, uploaded_bytes,
                status, stage, message, started_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        parameters = (
            progress.resource_id,
            progress.filename,
            progress.total_bytes,
            progress.uploaded_bytes,
            progress.status,
            progress.stage,
            progress.message,
            progress.started_at.isoformat(),
            progress.updated_at.isoformat()
        )
        
        self.sqlite_manager.execute_update(sql, parameters)
        logger.debug(f"Created/updated upload progress: {progress.resource_id}")
    
    def get_upload_progress(self, resource_id: str) -> Optional[UploadProgress]:
        """
        Get upload progress for a resource.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            Optional[UploadProgress]: Upload progress or None if not found
        """
        self.initialize()
        
        sql = "SELECT * FROM upload_progress WHERE resource_id = ?"
        results = self.sqlite_manager.execute_query(sql, (resource_id,))
        
        if not results:
            return None
        
        row = results[0]
        return UploadProgress(
            resource_id=row['resource_id'],
            filename=row['filename'],
            total_bytes=row['total_bytes'],
            uploaded_bytes=row['uploaded_bytes'],
            status=row['status'],
            stage=row['stage'],
            message=row['message'],
            started_at=datetime.fromisoformat(row['started_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )
    
    def update_upload_progress(self, progress: UploadProgress) -> None:
        """
        Update upload progress.
        
        Args:
            progress: Updated UploadProgress instance
        """
        self.initialize()
        
        sql = """
            UPDATE upload_progress SET
                uploaded_bytes = ?, status = ?, stage = ?, 
                message = ?, updated_at = ?
            WHERE resource_id = ?
        """
        
        parameters = (
            progress.uploaded_bytes,
            progress.status,
            progress.stage,
            progress.message,
            progress.updated_at.isoformat(),
            progress.resource_id
        )
        
        rows_affected = self.sqlite_manager.execute_update(sql, parameters)
        if rows_affected == 0:
            # Create if doesn't exist
            self.create_upload_progress(progress)
        else:
            logger.debug(f"Updated upload progress: {progress.resource_id}")
    
    def delete_upload_progress(self, resource_id: str) -> None:
        """
        Delete upload progress record.
        
        Args:
            resource_id: Resource identifier
        """
        self.initialize()
        
        sql = "DELETE FROM upload_progress WHERE resource_id = ?"
        self.sqlite_manager.execute_update(sql, (resource_id,))
        logger.debug(f"Deleted upload progress: {resource_id}")
    
    # Statistics and Utility Operations
    
    def get_storage_statistics(self, client_id: str) -> Dict[str, Any]:
        """
        Get storage statistics for a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Dict[str, Any]: Storage statistics
        """
        self.initialize()
        
        stats = {}
        
        # Total resources
        sql = "SELECT COUNT(*) as total FROM resource_metadata WHERE client_id = ? AND is_deleted = 0"
        result = self.sqlite_manager.execute_query(sql, (client_id,))
        stats['total_resources'] = result[0]['total']
        
        # Resources by type
        sql = """
            SELECT resource_type, COUNT(*) as count 
            FROM resource_metadata 
            WHERE client_id = ? AND is_deleted = 0 
            GROUP BY resource_type
        """
        results = self.sqlite_manager.execute_query(sql, (client_id,))
        stats['resources_by_type'] = {row['resource_type']: row['count'] for row in results}
        
        # Total storage size
        sql = "SELECT SUM(file_size_bytes) as total_size FROM resource_metadata WHERE client_id = ? AND is_deleted = 0"
        result = self.sqlite_manager.execute_query(sql, (client_id,))
        stats['total_size_bytes'] = result[0]['total_size'] or 0
        
        # Recent uploads (last 7 days)
        sql = """
            SELECT COUNT(*) as recent_uploads 
            FROM resource_metadata 
            WHERE client_id = ? AND is_deleted = 0 
            AND datetime(created_at) > datetime('now', '-7 days')
        """
        result = self.sqlite_manager.execute_query(sql, (client_id,))
        stats['recent_uploads'] = result[0]['recent_uploads']
        
        return stats
    
    def cleanup_old_audit_records(self, days_to_keep: int = 90) -> int:
        """
        Clean up old audit trail records.
        
        Args:
            days_to_keep: Number of days of audit records to keep
            
        Returns:
            int: Number of records deleted
        """
        self.initialize()
        
        sql = "DELETE FROM audit_trail WHERE datetime(timestamp) < datetime('now', '-{} days')".format(days_to_keep)
        rows_affected = self.sqlite_manager.execute_update(sql)
        
        if rows_affected > 0:
            logger.info(f"Cleaned up {rows_affected} old audit records")
        
        return rows_affected
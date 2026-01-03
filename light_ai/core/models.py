"""
Core data models for Universal Data Handler.

Defines the data hierarchy, resource metadata, and schema information models.
"""

import uuid
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class ResourceType(Enum):
    """Supported resource types."""
    STRUCTURED = "structured"
    JSON = "json"
    UNSTRUCTURED = "unstructured"


class DataType(Enum):
    """Supported data file types."""
    # Structured data types
    CSV = "csv"
    EXCEL = "excel"
    TSV = "tsv"
    PARQUET = "parquet"
    
    # JSON data types
    JSON = "json"
    JSONL = "jsonl"
    
    # Unstructured data types
    PDF = "pdf"
    TXT = "txt"
    MARKDOWN = "markdown"
    DOCX = "docx"
    HTML = "html"


@dataclass
class DataHierarchy:
    """
    Core data hierarchy with client, user, and resource identifiers.
    - client_id: Organization identifier (can be human-readable like 'acme-corp')
    - user_id: User identifier (can be human-readable like 'john.doe')  
    - resource_id: Resource identifier (must be UUID v4)
    """
    client_id: str
    user_id: str
    resource_id: str
    
    def __post_init__(self):
        """Validate identifiers according to requirements."""
        # Only resource_id must be UUID v4, client_id and user_id can be human-readable
        self._validate_uuid(self.resource_id, "resource_id")
        self._validate_identifier(self.client_id, "client_id")
        self._validate_identifier(self.user_id, "user_id")
    
    @staticmethod
    def _validate_uuid(uuid_str: str, field_name: str) -> None:
        """Validate that a string is a valid UUID v4."""
        try:
            uuid_obj = uuid.UUID(uuid_str, version=4)
            if str(uuid_obj) != uuid_str:
                raise ValueError(f"{field_name} must be a valid UUID v4 string")
        except (ValueError, TypeError) as e:
            raise ValueError(f"{field_name} must be a valid UUID v4: {e}")
    
    @staticmethod
    def _validate_identifier(identifier: str, field_name: str) -> None:
        """Validate that identifier is non-empty and reasonable length."""
        if not identifier or not isinstance(identifier, str):
            raise ValueError(f"{field_name} must be a non-empty string")
        if len(identifier) > 255:
            raise ValueError(f"{field_name} must be 255 characters or less")
        # Allow alphanumeric, hyphens, underscores, dots
        if not re.match(r'^[a-zA-Z0-9._-]+$', identifier):
            raise ValueError(f"{field_name} can only contain letters, numbers, dots, hyphens, and underscores")
    
    @classmethod
    def generate_new(cls, client_id: str, user_id: str) -> "DataHierarchy":
        """Generate a new hierarchy with auto-generated resource_id."""
        resource_id = str(uuid.uuid4())
        return cls(client_id=client_id, user_id=user_id, resource_id=resource_id)


@dataclass
class ResourceMetadata:
    """
    Comprehensive metadata for a data resource.
    """
    resource_id: str
    user_id: str
    client_id: str
    resource_type: ResourceType
    data_type: DataType
    original_filename: str
    file_size_bytes: int
    storage_path: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    is_deleted: bool = False
    
    # Optional fields for structured data
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    
    # Optional field for unstructured data
    chunk_count: Optional[int] = None
    
    # Additional metadata
    file_hash: Optional[str] = None
    content_preview: Optional[str] = None
    processing_status: str = "pending"
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Validate the metadata after initialization."""
        DataHierarchy._validate_uuid(self.resource_id, "resource_id")
        DataHierarchy._validate_identifier(self.user_id, "user_id")
        DataHierarchy._validate_identifier(self.client_id, "client_id")
        
        if self.file_size_bytes < 0:
            raise ValueError("file_size_bytes must be non-negative")
        
        if self.version < 1:
            raise ValueError("version must be at least 1")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "resource_id": self.resource_id,
            "user_id": self.user_id,
            "client_id": self.client_id,
            "resource_type": self.resource_type.value,
            "data_type": self.data_type.value,
            "original_filename": self.original_filename,
            "file_size_bytes": self.file_size_bytes,
            "storage_path": self.storage_path,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "is_deleted": self.is_deleted,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "chunk_count": self.chunk_count,
            "file_hash": self.file_hash,
            "content_preview": self.content_preview,
            "processing_status": self.processing_status,
            "error_message": self.error_message,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceMetadata":
        """Create from dictionary."""
        # Convert string dates back to datetime
        created_at = datetime.fromisoformat(data["created_at"])
        updated_at = datetime.fromisoformat(data["updated_at"])
        
        return cls(
            resource_id=data["resource_id"],
            user_id=data["user_id"],
            client_id=data["client_id"],
            resource_type=ResourceType(data["resource_type"]),
            data_type=DataType(data["data_type"]),
            original_filename=data["original_filename"],
            file_size_bytes=data["file_size_bytes"],
            storage_path=data["storage_path"],
            created_at=created_at,
            updated_at=updated_at,
            version=data["version"],
            is_deleted=data["is_deleted"],
            row_count=data.get("row_count"),
            column_count=data.get("column_count"),
            chunk_count=data.get("chunk_count"),
            file_hash=data.get("file_hash"),
            content_preview=data.get("content_preview"),
            processing_status=data.get("processing_status", "pending"),
            error_message=data.get("error_message"),
        )


@dataclass
class SchemaInfo:
    """
    Schema information for structured data resources.
    """
    schema_id: str
    resource_id: str
    version: int
    schema_json: str  # JSON representation of column definitions
    statistics_json: str  # Data profiling statistics
    detected_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validate schema info after initialization."""
        DataHierarchy._validate_uuid(self.schema_id, "schema_id")
        DataHierarchy._validate_uuid(self.resource_id, "resource_id")
        
        if self.version < 1:
            raise ValueError("version must be at least 1")
    
    @classmethod
    def generate_new(cls, resource_id: str, version: int, 
                    schema_json: str, statistics_json: str) -> "SchemaInfo":
        """Generate new schema info with auto-generated schema_id."""
        schema_id = str(uuid.uuid4())
        return cls(
            schema_id=schema_id,
            resource_id=resource_id,
            version=version,
            schema_json=schema_json,
            statistics_json=statistics_json
        )


@dataclass
class UploadProgress:
    """
    Progress tracking for file uploads.
    """
    resource_id: str
    filename: str
    total_bytes: int
    uploaded_bytes: int = 0
    status: str = "uploading"  # uploading, processing, completed, failed
    stage: str = "validation"  # validation, upload, cleaning, storage
    message: str = ""
    started_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def progress_percentage(self) -> float:
        """Calculate upload progress percentage."""
        if self.total_bytes == 0:
            return 0.0
        return min(100.0, (self.uploaded_bytes / self.total_bytes) * 100.0)
    
    @property
    def is_complete(self) -> bool:
        """Check if upload is complete."""
        return self.status in ("completed", "failed")
    
    def update_progress(self, uploaded_bytes: int, stage: str = None, 
                       message: str = None) -> None:
        """Update progress information."""
        self.uploaded_bytes = min(uploaded_bytes, self.total_bytes)
        if stage:
            self.stage = stage
        if message:
            self.message = message
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self, message: str = "Upload completed successfully") -> None:
        """Mark upload as completed."""
        self.status = "completed"
        self.uploaded_bytes = self.total_bytes
        self.message = message
        self.updated_at = datetime.utcnow()
    
    def mark_failed(self, error_message: str) -> None:
        """Mark upload as failed."""
        self.status = "failed"
        self.message = error_message
        self.updated_at = datetime.utcnow()


# Hierarchy enforcement and access control functions

class AccessLevel(Enum):
    """Access levels for data hierarchy."""
    USER = "user"           # Access only own resources
    MANAGER = "manager"     # Access team resources
    ADMIN = "admin"         # Access company-wide resources


def validate_hierarchy_access(requesting_user_id: str, requesting_client_id: str,
                            target_hierarchy: DataHierarchy, 
                            access_level: AccessLevel = AccessLevel.USER) -> bool:
    """
    Validate if a user has access to a resource based on hierarchy and access level.
    
    Args:
        requesting_user_id: UUID of the user making the request
        requesting_client_id: UUID of the client organization
        target_hierarchy: The data hierarchy being accessed
        access_level: The access level of the requesting user
    
    Returns:
        bool: True if access is allowed, False otherwise
    """
    # Validate UUIDs
    try:
        DataHierarchy._validate_uuid(requesting_user_id, "requesting_user_id")
        DataHierarchy._validate_uuid(requesting_client_id, "requesting_client_id")
    except ValueError:
        return False
    
    # Must be same client
    if requesting_client_id != target_hierarchy.client_id:
        return False
    
    # Check access based on level
    if access_level == AccessLevel.USER:
        # User can only access their own resources
        return requesting_user_id == target_hierarchy.user_id
    elif access_level == AccessLevel.MANAGER:
        # Manager can access team resources (same client, any user)
        return True  # Already validated same client above
    elif access_level == AccessLevel.ADMIN:
        # Admin can access company-wide resources (same client, any user)
        return True  # Already validated same client above
    
    return False


def filter_accessible_resources(requesting_user_id: str, requesting_client_id: str,
                               resources: List[ResourceMetadata],
                               access_level: AccessLevel = AccessLevel.USER) -> List[ResourceMetadata]:
    """
    Filter a list of resources to only include those accessible to the requesting user.
    
    Args:
        requesting_user_id: UUID of the user making the request
        requesting_client_id: UUID of the client organization
        resources: List of resource metadata to filter
        access_level: The access level of the requesting user
    
    Returns:
        List[ResourceMetadata]: Filtered list of accessible resources
    """
    accessible_resources = []
    
    for resource in resources:
        hierarchy = DataHierarchy(
            client_id=resource.client_id,
            user_id=resource.user_id,
            resource_id=resource.resource_id
        )
        
        if validate_hierarchy_access(requesting_user_id, requesting_client_id, 
                                   hierarchy, access_level):
            accessible_resources.append(resource)
    
    return accessible_resources


def enforce_hierarchy_constraints(client_id: str, user_id: str, resource_id: str) -> DataHierarchy:
    """
    Enforce hierarchy constraints and create a validated DataHierarchy.
    
    Args:
        client_id: Client UUID
        user_id: User UUID  
        resource_id: Resource UUID
    
    Returns:
        DataHierarchy: Validated hierarchy object
    
    Raises:
        ValueError: If any UUID is invalid or constraints are violated
    """
    # This will validate all UUIDs through DataHierarchy.__post_init__
    hierarchy = DataHierarchy(
        client_id=client_id,
        user_id=user_id,
        resource_id=resource_id
    )
    
    return hierarchy


def generate_storage_path(hierarchy: DataHierarchy, base_path: str = "data") -> str:
    """
    Generate standardized storage path based on hierarchy.
    
    Args:
        hierarchy: Data hierarchy object
        base_path: Base directory path
    
    Returns:
        str: Standardized storage path following client_id/user_id/resource_id structure
    """
    return f"{base_path}/{hierarchy.client_id}/{hierarchy.user_id}/{hierarchy.resource_id}"


def validate_resource_ownership(resource_metadata: ResourceMetadata, 
                              expected_client_id: str, expected_user_id: str) -> bool:
    """
    Validate that a resource belongs to the expected client and user.
    
    Args:
        resource_metadata: Resource metadata to validate
        expected_client_id: Expected client UUID
        expected_user_id: Expected user UUID
    
    Returns:
        bool: True if ownership matches, False otherwise
    """
    try:
        DataHierarchy._validate_uuid(expected_client_id, "expected_client_id")
        DataHierarchy._validate_uuid(expected_user_id, "expected_user_id")
    except ValueError:
        return False
    
    return (resource_metadata.client_id == expected_client_id and 
            resource_metadata.user_id == expected_user_id)
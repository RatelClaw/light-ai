"""
Unit tests for core data models and hierarchy system.

Tests DataHierarchy, ResourceMetadata, SchemaInfo classes and hierarchy enforcement functions.
"""

import uuid
import pytest
from datetime import datetime
from unittest.mock import patch

from light_ai.core.models import (
    DataHierarchy, ResourceMetadata, SchemaInfo, UploadProgress,
    ResourceType, DataType, AccessLevel,
    validate_hierarchy_access, filter_accessible_resources,
    enforce_hierarchy_constraints, generate_storage_path,
    validate_resource_ownership
)


class TestDataHierarchy:
    """Test DataHierarchy class and UUID validation."""
    
    def test_valid_hierarchy_creation(self):
        """Test creating hierarchy with valid UUID v4 strings."""
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        resource_id = str(uuid.uuid4())
        
        hierarchy = DataHierarchy(
            client_id=client_id,
            user_id=user_id,
            resource_id=resource_id
        )
        
        assert hierarchy.client_id == client_id
        assert hierarchy.user_id == user_id
        assert hierarchy.resource_id == resource_id
    
    def test_invalid_client_id_raises_error(self):
        """Test that invalid client_id raises ValueError."""
        user_id = str(uuid.uuid4())
        resource_id = str(uuid.uuid4())
        
        with pytest.raises(ValueError, match="client_id must be a valid UUID v4"):
            DataHierarchy(
                client_id="invalid-uuid",
                user_id=user_id,
                resource_id=resource_id
            )
    
    def test_invalid_user_id_raises_error(self):
        """Test that invalid user_id raises ValueError."""
        client_id = str(uuid.uuid4())
        resource_id = str(uuid.uuid4())
        
        with pytest.raises(ValueError, match="user_id must be a valid UUID v4"):
            DataHierarchy(
                client_id=client_id,
                user_id="not-a-uuid",
                resource_id=resource_id
            )
    
    def test_invalid_resource_id_raises_error(self):
        """Test that invalid resource_id raises ValueError."""
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        with pytest.raises(ValueError, match="resource_id must be a valid UUID v4"):
            DataHierarchy(
                client_id=client_id,
                user_id=user_id,
                resource_id="123-456-789"
            )
    
    def test_generate_new_hierarchy(self):
        """Test generating new hierarchy with auto-generated resource_id."""
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        hierarchy = DataHierarchy.generate_new(client_id, user_id)
        
        assert hierarchy.client_id == client_id
        assert hierarchy.user_id == user_id
        # Verify resource_id is a valid UUID v4
        uuid.UUID(hierarchy.resource_id, version=4)
    
    def test_uuid_validation_with_wrong_version(self):
        """Test that UUID v1 is rejected for v4 validation."""
        client_id = str(uuid.uuid1())  # v1 UUID
        user_id = str(uuid.uuid4())
        resource_id = str(uuid.uuid4())
        
        with pytest.raises(ValueError, match="client_id must be a valid UUID v4"):
            DataHierarchy(
                client_id=client_id,
                user_id=user_id,
                resource_id=resource_id
            )


class TestResourceMetadata:
    """Test ResourceMetadata class and validation."""
    
    def test_valid_metadata_creation(self):
        """Test creating metadata with valid values."""
        resource_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        client_id = str(uuid.uuid4())
        
        metadata = ResourceMetadata(
            resource_id=resource_id,
            user_id=user_id,
            client_id=client_id,
            resource_type=ResourceType.STRUCTURED,
            data_type=DataType.CSV,
            original_filename="test.csv",
            file_size_bytes=1024,
            storage_path="/data/test.csv"
        )
        
        assert metadata.resource_id == resource_id
        assert metadata.user_id == user_id
        assert metadata.client_id == client_id
        assert metadata.resource_type == ResourceType.STRUCTURED
        assert metadata.data_type == DataType.CSV
        assert metadata.version == 1
        assert metadata.is_deleted is False
        assert isinstance(metadata.created_at, datetime)
        assert isinstance(metadata.updated_at, datetime)
    
    def test_negative_file_size_raises_error(self):
        """Test that negative file size raises ValueError."""
        resource_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        client_id = str(uuid.uuid4())
        
        with pytest.raises(ValueError, match="file_size_bytes must be non-negative"):
            ResourceMetadata(
                resource_id=resource_id,
                user_id=user_id,
                client_id=client_id,
                resource_type=ResourceType.STRUCTURED,
                data_type=DataType.CSV,
                original_filename="test.csv",
                file_size_bytes=-100,
                storage_path="/data/test.csv"
            )
    
    def test_invalid_version_raises_error(self):
        """Test that version less than 1 raises ValueError."""
        resource_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        client_id = str(uuid.uuid4())
        
        with pytest.raises(ValueError, match="version must be at least 1"):
            ResourceMetadata(
                resource_id=resource_id,
                user_id=user_id,
                client_id=client_id,
                resource_type=ResourceType.STRUCTURED,
                data_type=DataType.CSV,
                original_filename="test.csv",
                file_size_bytes=1024,
                storage_path="/data/test.csv",
                version=0
            )
    
    def test_to_dict_conversion(self):
        """Test converting metadata to dictionary."""
        resource_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        client_id = str(uuid.uuid4())
        
        metadata = ResourceMetadata(
            resource_id=resource_id,
            user_id=user_id,
            client_id=client_id,
            resource_type=ResourceType.JSON,
            data_type=DataType.JSON,
            original_filename="test.json",
            file_size_bytes=2048,
            storage_path="/data/test.json",
            row_count=100,
            column_count=5
        )
        
        data_dict = metadata.to_dict()
        
        assert data_dict["resource_id"] == resource_id
        assert data_dict["resource_type"] == "json"
        assert data_dict["data_type"] == "json"
        assert data_dict["row_count"] == 100
        assert data_dict["column_count"] == 5
        assert isinstance(data_dict["created_at"], str)
    
    def test_from_dict_conversion(self):
        """Test creating metadata from dictionary."""
        resource_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        client_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        data_dict = {
            "resource_id": resource_id,
            "user_id": user_id,
            "client_id": client_id,
            "resource_type": "unstructured",
            "data_type": "pdf",
            "original_filename": "test.pdf",
            "file_size_bytes": 5000,
            "storage_path": "/data/test.pdf",
            "created_at": created_at.isoformat(),
            "updated_at": created_at.isoformat(),
            "version": 2,
            "is_deleted": False,
            "chunk_count": 10,
            "processing_status": "completed"
        }
        
        metadata = ResourceMetadata.from_dict(data_dict)
        
        assert metadata.resource_id == resource_id
        assert metadata.resource_type == ResourceType.UNSTRUCTURED
        assert metadata.data_type == DataType.PDF
        assert metadata.version == 2
        assert metadata.chunk_count == 10
        assert metadata.processing_status == "completed"


class TestSchemaInfo:
    """Test SchemaInfo class and validation."""
    
    def test_valid_schema_creation(self):
        """Test creating schema info with valid values."""
        schema_id = str(uuid.uuid4())
        resource_id = str(uuid.uuid4())
        
        schema_info = SchemaInfo(
            schema_id=schema_id,
            resource_id=resource_id,
            version=1,
            schema_json='{"columns": ["id", "name"]}',
            statistics_json='{"row_count": 100}'
        )
        
        assert schema_info.schema_id == schema_id
        assert schema_info.resource_id == resource_id
        assert schema_info.version == 1
        assert isinstance(schema_info.detected_at, datetime)
    
    def test_generate_new_schema(self):
        """Test generating new schema info with auto-generated schema_id."""
        resource_id = str(uuid.uuid4())
        
        schema_info = SchemaInfo.generate_new(
            resource_id=resource_id,
            version=2,
            schema_json='{"columns": ["id", "name", "email"]}',
            statistics_json='{"row_count": 200}'
        )
        
        assert schema_info.resource_id == resource_id
        assert schema_info.version == 2
        # Verify schema_id is a valid UUID v4
        uuid.UUID(schema_info.schema_id, version=4)
    
    def test_invalid_version_raises_error(self):
        """Test that version less than 1 raises ValueError."""
        schema_id = str(uuid.uuid4())
        resource_id = str(uuid.uuid4())
        
        with pytest.raises(ValueError, match="version must be at least 1"):
            SchemaInfo(
                schema_id=schema_id,
                resource_id=resource_id,
                version=0,
                schema_json='{"columns": []}',
                statistics_json='{}'
            )


class TestHierarchyEnforcement:
    """Test hierarchy enforcement and access control functions."""
    
    def test_validate_hierarchy_access_user_level(self):
        """Test user-level access validation."""
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        resource_id = str(uuid.uuid4())
        
        hierarchy = DataHierarchy(client_id, user_id, resource_id)
        
        # User can access their own resource
        assert validate_hierarchy_access(user_id, client_id, hierarchy, AccessLevel.USER)
        
        # User cannot access other user's resource
        other_user_id = str(uuid.uuid4())
        assert not validate_hierarchy_access(other_user_id, client_id, hierarchy, AccessLevel.USER)
        
        # User cannot access resource from different client
        other_client_id = str(uuid.uuid4())
        assert not validate_hierarchy_access(user_id, other_client_id, hierarchy, AccessLevel.USER)
    
    def test_validate_hierarchy_access_manager_level(self):
        """Test manager-level access validation."""
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        resource_id = str(uuid.uuid4())
        manager_id = str(uuid.uuid4())
        
        hierarchy = DataHierarchy(client_id, user_id, resource_id)
        
        # Manager can access any resource in their client
        assert validate_hierarchy_access(manager_id, client_id, hierarchy, AccessLevel.MANAGER)
        
        # Manager cannot access resource from different client
        other_client_id = str(uuid.uuid4())
        assert not validate_hierarchy_access(manager_id, other_client_id, hierarchy, AccessLevel.MANAGER)
    
    def test_validate_hierarchy_access_admin_level(self):
        """Test admin-level access validation."""
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        resource_id = str(uuid.uuid4())
        admin_id = str(uuid.uuid4())
        
        hierarchy = DataHierarchy(client_id, user_id, resource_id)
        
        # Admin can access any resource in their client
        assert validate_hierarchy_access(admin_id, client_id, hierarchy, AccessLevel.ADMIN)
        
        # Admin cannot access resource from different client
        other_client_id = str(uuid.uuid4())
        assert not validate_hierarchy_access(admin_id, other_client_id, hierarchy, AccessLevel.ADMIN)
    
    def test_validate_hierarchy_access_invalid_uuids(self):
        """Test access validation with invalid UUIDs."""
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        resource_id = str(uuid.uuid4())
        
        hierarchy = DataHierarchy(client_id, user_id, resource_id)
        
        # Invalid requesting user ID
        assert not validate_hierarchy_access("invalid-uuid", client_id, hierarchy, AccessLevel.USER)
        
        # Invalid requesting client ID
        assert not validate_hierarchy_access(user_id, "invalid-uuid", hierarchy, AccessLevel.USER)
    
    def test_filter_accessible_resources(self):
        """Test filtering resources based on access level."""
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        other_user_id = str(uuid.uuid4())
        
        # Create test resources
        user_resource = ResourceMetadata(
            resource_id=str(uuid.uuid4()),
            user_id=user_id,
            client_id=client_id,
            resource_type=ResourceType.STRUCTURED,
            data_type=DataType.CSV,
            original_filename="user.csv",
            file_size_bytes=1024,
            storage_path="/data/user.csv"
        )
        
        other_resource = ResourceMetadata(
            resource_id=str(uuid.uuid4()),
            user_id=other_user_id,
            client_id=client_id,
            resource_type=ResourceType.JSON,
            data_type=DataType.JSON,
            original_filename="other.json",
            file_size_bytes=2048,
            storage_path="/data/other.json"
        )
        
        resources = [user_resource, other_resource]
        
        # User level - should only see own resource
        user_accessible = filter_accessible_resources(
            user_id, client_id, resources, AccessLevel.USER
        )
        assert len(user_accessible) == 1
        assert user_accessible[0].resource_id == user_resource.resource_id
        
        # Manager level - should see all resources in client
        manager_accessible = filter_accessible_resources(
            str(uuid.uuid4()), client_id, resources, AccessLevel.MANAGER
        )
        assert len(manager_accessible) == 2
    
    def test_enforce_hierarchy_constraints(self):
        """Test hierarchy constraint enforcement."""
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        resource_id = str(uuid.uuid4())
        
        # Valid hierarchy should work
        hierarchy = enforce_hierarchy_constraints(client_id, user_id, resource_id)
        assert hierarchy.client_id == client_id
        assert hierarchy.user_id == user_id
        assert hierarchy.resource_id == resource_id
        
        # Invalid UUID should raise error
        with pytest.raises(ValueError):
            enforce_hierarchy_constraints("invalid", user_id, resource_id)
    
    def test_generate_storage_path(self):
        """Test storage path generation."""
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        resource_id = str(uuid.uuid4())
        
        hierarchy = DataHierarchy(client_id, user_id, resource_id)
        
        # Default base path
        path = generate_storage_path(hierarchy)
        expected = f"data/{client_id}/{user_id}/{resource_id}"
        assert path == expected
        
        # Custom base path
        custom_path = generate_storage_path(hierarchy, "custom")
        expected_custom = f"custom/{client_id}/{user_id}/{resource_id}"
        assert custom_path == expected_custom
    
    def test_validate_resource_ownership(self):
        """Test resource ownership validation."""
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        metadata = ResourceMetadata(
            resource_id=str(uuid.uuid4()),
            user_id=user_id,
            client_id=client_id,
            resource_type=ResourceType.STRUCTURED,
            data_type=DataType.CSV,
            original_filename="test.csv",
            file_size_bytes=1024,
            storage_path="/data/test.csv"
        )
        
        # Correct ownership
        assert validate_resource_ownership(metadata, client_id, user_id)
        
        # Wrong client
        other_client_id = str(uuid.uuid4())
        assert not validate_resource_ownership(metadata, other_client_id, user_id)
        
        # Wrong user
        other_user_id = str(uuid.uuid4())
        assert not validate_resource_ownership(metadata, client_id, other_user_id)
        
        # Invalid UUIDs
        assert not validate_resource_ownership(metadata, "invalid", user_id)
        assert not validate_resource_ownership(metadata, client_id, "invalid")


class TestUploadProgress:
    """Test UploadProgress class functionality."""
    
    def test_upload_progress_creation(self):
        """Test creating upload progress tracker."""
        resource_id = str(uuid.uuid4())
        
        progress = UploadProgress(
            resource_id=resource_id,
            filename="test.csv",
            total_bytes=1000
        )
        
        assert progress.resource_id == resource_id
        assert progress.filename == "test.csv"
        assert progress.total_bytes == 1000
        assert progress.uploaded_bytes == 0
        assert progress.status == "uploading"
        assert progress.stage == "validation"
    
    def test_progress_percentage_calculation(self):
        """Test progress percentage calculation."""
        progress = UploadProgress(
            resource_id=str(uuid.uuid4()),
            filename="test.csv",
            total_bytes=1000
        )
        
        # Initial progress
        assert progress.progress_percentage == 0.0
        
        # Partial progress
        progress.uploaded_bytes = 250
        assert progress.progress_percentage == 25.0
        
        # Complete progress
        progress.uploaded_bytes = 1000
        assert progress.progress_percentage == 100.0
        
        # Over 100% should cap at 100%
        progress.uploaded_bytes = 1200
        assert progress.progress_percentage == 100.0
    
    def test_update_progress(self):
        """Test updating progress information."""
        progress = UploadProgress(
            resource_id=str(uuid.uuid4()),
            filename="test.csv",
            total_bytes=1000
        )
        
        initial_time = progress.updated_at
        
        progress.update_progress(500, "processing", "Processing file")
        
        assert progress.uploaded_bytes == 500
        assert progress.stage == "processing"
        assert progress.message == "Processing file"
        assert progress.updated_at > initial_time
    
    def test_mark_completed(self):
        """Test marking upload as completed."""
        progress = UploadProgress(
            resource_id=str(uuid.uuid4()),
            filename="test.csv",
            total_bytes=1000
        )
        
        progress.mark_completed("Upload successful")
        
        assert progress.status == "completed"
        assert progress.uploaded_bytes == 1000
        assert progress.message == "Upload successful"
        assert progress.is_complete
    
    def test_mark_failed(self):
        """Test marking upload as failed."""
        progress = UploadProgress(
            resource_id=str(uuid.uuid4()),
            filename="test.csv",
            total_bytes=1000
        )
        
        progress.mark_failed("Upload failed due to network error")
        
        assert progress.status == "failed"
        assert progress.message == "Upload failed due to network error"
        assert progress.is_complete
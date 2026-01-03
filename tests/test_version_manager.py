"""
Tests for version management and audit system.

Tests the comprehensive versioning capabilities including non-destructive updates,
audit trails, version retrieval, rollback functionality, and soft/hard delete operations.
"""

import pytest
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from light_ai.core.models import ResourceMetadata, DataHierarchy, ResourceType, DataType
from light_ai.storage.version_manager import (
    VersionManager, OperationType, DeleteType, VersionInfo, AuditRecord
)
from light_ai.config import Config


@pytest.fixture
def temp_config():
    """Create a temporary configuration for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = Config()
        config.storage.base_directory = temp_dir
        config.database.sqlite_path = f"{temp_dir}/metadata/test_registry.db"
        config.database.duckdb_path = f"{temp_dir}/data/test_duckdb.db"
        config.database.chromadb_path = f"{temp_dir}/data/test_chromadb"
        yield config


@pytest.fixture
def version_manager(temp_config):
    """Create a version manager for testing."""
    return VersionManager(temp_config)


@pytest.fixture
def sample_hierarchy():
    """Create a sample data hierarchy for testing."""
    return DataHierarchy(
        client_id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        resource_id=str(uuid.uuid4())
    )


@pytest.fixture
def sample_metadata(sample_hierarchy):
    """Create sample resource metadata for testing."""
    return ResourceMetadata(
        resource_id=sample_hierarchy.resource_id,
        user_id=sample_hierarchy.user_id,
        client_id=sample_hierarchy.client_id,
        resource_type=ResourceType.STRUCTURED,
        data_type=DataType.CSV,
        original_filename="test_data.csv",
        file_size_bytes=1024,
        storage_path="/test/path/test_data.csv",
        version=1,
        processing_status="completed"
    )


@pytest.fixture
def sample_file():
    """Create a sample file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("id,name,value\n1,test,100\n2,example,200\n")
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


class TestVersionManager:
    """Test version management functionality."""
    
    def test_create_first_version(self, version_manager, sample_metadata, sample_file):
        """Test creating the first version of a resource."""
        # Create first version
        version_num = version_manager.create_version(
            sample_metadata, sample_file, sample_metadata.user_id,
            OperationType.UPLOAD, "Initial upload"
        )
        
        assert version_num == 1
        assert sample_metadata.version == 1
        
        # Verify version info
        version_info = version_manager.get_version_info(sample_metadata.resource_id, 1)
        assert version_info is not None
        assert version_info.version == 1
        assert version_info.operation == OperationType.UPLOAD
        assert version_info.created_by == sample_metadata.user_id
    
    def test_create_multiple_versions(self, version_manager, sample_metadata, sample_file):
        """Test creating multiple versions of a resource."""
        # Create first version
        version1 = version_manager.create_version(
            sample_metadata, sample_file, sample_metadata.user_id,
            OperationType.UPLOAD, "Initial upload"
        )
        assert version1 == 1
        
        # Create second version
        sample_metadata.file_size_bytes = 2048  # Simulate file change
        version2 = version_manager.create_version(
            sample_metadata, sample_file, sample_metadata.user_id,
            OperationType.UPDATE, "Updated data"
        )
        assert version2 == 2
        
        # Create third version
        sample_metadata.file_size_bytes = 3072
        version3 = version_manager.create_version(
            sample_metadata, sample_file, sample_metadata.user_id,
            OperationType.UPDATE, "Another update"
        )
        assert version3 == 3
        
        # Verify all versions exist
        versions = version_manager.list_versions(sample_metadata.resource_id)
        assert len(versions) == 3
        assert [v.version for v in versions] == [3, 2, 1]  # Sorted descending
    
    def test_version_info_retrieval(self, version_manager, sample_metadata, sample_file):
        """Test retrieving version information."""
        # Create a version
        version_manager.create_version(
            sample_metadata, sample_file, sample_metadata.user_id,
            OperationType.UPLOAD, "Test upload"
        )
        
        # Get version info
        version_info = version_manager.get_version_info(sample_metadata.resource_id, 1)
        
        assert version_info is not None
        assert version_info.resource_id == sample_metadata.resource_id
        assert version_info.version == 1
        assert version_info.operation == OperationType.UPLOAD
        assert version_info.created_by == sample_metadata.user_id
        assert version_info.operation_details == "Test upload"
        assert version_info.file_path is not None
    
    def test_rollback_to_version(self, version_manager, sample_metadata, sample_file):
        """Test rolling back to a previous version."""
        # Create multiple versions
        version_manager.create_version(
            sample_metadata, sample_file, sample_metadata.user_id,
            OperationType.UPLOAD, "Version 1"
        )
        
        sample_metadata.file_size_bytes = 2048
        version_manager.create_version(
            sample_metadata, sample_file, sample_metadata.user_id,
            OperationType.UPDATE, "Version 2"
        )
        
        sample_metadata.file_size_bytes = 3072
        version_manager.create_version(
            sample_metadata, sample_file, sample_metadata.user_id,
            OperationType.UPDATE, "Version 3"
        )
        
        # Rollback to version 1
        new_version = version_manager.rollback_to_version(
            sample_metadata.resource_id, 1, sample_metadata.user_id,
            "Rolling back to original version"
        )
        
        assert new_version == 4  # New version created for rollback
        
        # Verify rollback was logged
        audit_trail = version_manager.get_audit_trail(sample_metadata.resource_id)
        rollback_record = next(r for r in audit_trail if r['operation'] == 'rollback')
        assert rollback_record is not None
        assert "Rolled back to version 1" in rollback_record['operation_details']
    
    def test_soft_delete_resource(self, version_manager, sample_metadata, sample_file):
        """Test soft deleting a resource."""
        # Create a version
        version_manager.create_version(
            sample_metadata, sample_file, sample_metadata.user_id,
            OperationType.UPLOAD, "Initial upload"
        )
        
        # Soft delete
        success = version_manager.soft_delete_resource(
            sample_metadata.resource_id, sample_metadata.user_id,
            "No longer needed"
        )
        
        assert success is True
        
        # Verify resource is marked as deleted
        metadata = version_manager.metadata_registry.get_resource_metadata(sample_metadata.resource_id)
        assert metadata.is_deleted is True
        
        # Verify audit trail
        audit_trail = version_manager.get_audit_trail(sample_metadata.resource_id)
        delete_record = next(r for r in audit_trail if r['operation'] == 'delete')
        assert delete_record is not None
        assert "Soft delete" in delete_record['operation_details']
    
    def test_restore_resource(self, version_manager, sample_metadata, sample_file):
        """Test restoring a soft-deleted resource."""
        # Create and soft delete a resource
        version_manager.create_version(
            sample_metadata, sample_file, sample_metadata.user_id,
            OperationType.UPLOAD, "Initial upload"
        )
        
        version_manager.soft_delete_resource(
            sample_metadata.resource_id, sample_metadata.user_id
        )
        
        # Restore the resource
        success = version_manager.restore_resource(
            sample_metadata.resource_id, sample_metadata.user_id,
            "Needed again"
        )
        
        assert success is True
        
        # Verify resource is no longer marked as deleted
        metadata = version_manager.metadata_registry.get_resource_metadata(sample_metadata.resource_id)
        assert metadata.is_deleted is False
        
        # Verify audit trail
        audit_trail = version_manager.get_audit_trail(sample_metadata.resource_id)
        restore_record = next(r for r in audit_trail if r['operation'] == 'restore')
        assert restore_record is not None
    
    def test_hard_delete_resource(self, version_manager, sample_metadata, sample_file):
        """Test hard deleting a resource."""
        # Create a version
        version_manager.create_version(
            sample_metadata, sample_file, sample_metadata.user_id,
            OperationType.UPLOAD, "Initial upload"
        )
        
        # Hard delete
        success = version_manager.hard_delete_resource(
            sample_metadata.resource_id, sample_metadata.user_id,
            "Permanent removal"
        )
        
        assert success is True
        
        # Verify resource no longer exists
        metadata = version_manager.metadata_registry.get_resource_metadata(sample_metadata.resource_id)
        assert metadata is None
    
    def test_audit_trail_logging(self, version_manager, sample_metadata, sample_file):
        """Test comprehensive audit trail logging."""
        # Perform various operations
        version_manager.create_version(
            sample_metadata, sample_file, sample_metadata.user_id,
            OperationType.UPLOAD, "Initial upload"
        )
        
        sample_metadata.file_size_bytes = 2048
        version_manager.create_version(
            sample_metadata, sample_file, sample_metadata.user_id,
            OperationType.UPDATE, "Updated data"
        )
        
        version_manager.soft_delete_resource(
            sample_metadata.resource_id, sample_metadata.user_id
        )
        
        version_manager.restore_resource(
            sample_metadata.resource_id, sample_metadata.user_id
        )
        
        # Get audit trail
        audit_trail = version_manager.get_audit_trail(sample_metadata.resource_id)
        
        # Verify all operations are logged
        operations = [record['operation'] for record in audit_trail]
        assert 'upload' in operations
        assert 'update' in operations
        assert 'delete' in operations
        assert 'restore' in operations
        
        # Verify audit summary
        summary = version_manager.get_audit_summary(sample_metadata.resource_id)
        assert summary['total_operations'] >= 4
        assert summary['operations_by_type']['upload'] >= 1
        assert summary['operations_by_type']['update'] >= 1
        assert summary['operations_by_type']['delete'] >= 1
        assert summary['operations_by_type']['restore'] >= 1
    
    def test_version_without_file(self, version_manager, sample_metadata):
        """Test creating a version without a file (e.g., for JSON data)."""
        # Create version without file
        version_num = version_manager.create_version(
            sample_metadata, None, sample_metadata.user_id,
            OperationType.UPLOAD, "JSON data upload"
        )
        
        assert version_num == 1
        
        # Verify version info
        version_info = version_manager.get_version_info(sample_metadata.resource_id, 1)
        assert version_info is not None
        assert version_info.file_path is None  # No file stored
    
    def test_nonexistent_resource_operations(self, version_manager):
        """Test operations on nonexistent resources."""
        fake_resource_id = str(uuid.uuid4())
        fake_user_id = str(uuid.uuid4())
        
        # Test rollback on nonexistent resource
        with pytest.raises(ValueError):
            version_manager.rollback_to_version(fake_resource_id, 1, fake_user_id)
        
        # Test soft delete on nonexistent resource
        success = version_manager.soft_delete_resource(fake_resource_id, fake_user_id)
        assert success is False
        
        # Test hard delete on nonexistent resource
        success = version_manager.hard_delete_resource(fake_resource_id, fake_user_id)
        assert success is False
        
        # Test restore on nonexistent resource
        success = version_manager.restore_resource(fake_resource_id, fake_user_id)
        assert success is False
    
    def test_version_info_for_nonexistent_version(self, version_manager, sample_metadata, sample_file):
        """Test getting version info for nonexistent version."""
        # Create one version
        version_manager.create_version(
            sample_metadata, sample_file, sample_metadata.user_id,
            OperationType.UPLOAD, "Initial upload"
        )
        
        # Try to get info for nonexistent version
        version_info = version_manager.get_version_info(sample_metadata.resource_id, 999)
        assert version_info is None
    
    def test_list_versions_empty(self, version_manager):
        """Test listing versions for nonexistent resource."""
        fake_resource_id = str(uuid.uuid4())
        versions = version_manager.list_versions(fake_resource_id)
        assert versions == []


class TestVersionManagerIntegration:
    """Test version manager integration with other components."""
    
    def test_metadata_consistency(self, version_manager, sample_metadata, sample_file):
        """Test that metadata remains consistent across versions."""
        # Create multiple versions
        version_manager.create_version(
            sample_metadata, sample_file, sample_metadata.user_id,
            OperationType.UPLOAD, "Version 1"
        )
        
        sample_metadata.file_size_bytes = 2048
        version_manager.create_version(
            sample_metadata, sample_file, sample_metadata.user_id,
            OperationType.UPDATE, "Version 2"
        )
        
        # Verify current metadata reflects latest version
        current_metadata = version_manager.metadata_registry.get_resource_metadata(sample_metadata.resource_id)
        assert current_metadata.version == 2
        assert current_metadata.file_size_bytes == 2048
        
        # Verify version history is complete
        versions = version_manager.list_versions(sample_metadata.resource_id)
        assert len(versions) == 2
    
    def test_file_storage_consistency(self, version_manager, sample_metadata, sample_file):
        """Test that file storage remains consistent across versions."""
        # Create multiple versions with different files
        version_manager.create_version(
            sample_metadata, sample_file, sample_metadata.user_id,
            OperationType.UPLOAD, "Version 1"
        )
        
        # Create a different file for version 2
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,name,value,extra\n1,test,100,A\n2,example,200,B\n")
            temp_path2 = Path(f.name)
        
        try:
            sample_metadata.file_size_bytes = 2048
            version_manager.create_version(
                sample_metadata, temp_path2, sample_metadata.user_id,
                OperationType.UPDATE, "Version 2"
            )
            
            # Verify both versions have their files
            version1_info = version_manager.get_version_info(sample_metadata.resource_id, 1)
            version2_info = version_manager.get_version_info(sample_metadata.resource_id, 2)
            
            assert version1_info.file_path is not None
            assert version2_info.file_path is not None
            assert version1_info.file_path != version2_info.file_path
            
            # Verify files exist
            assert Path(version1_info.file_path).exists()
            assert Path(version2_info.file_path).exists()
            
        finally:
            if temp_path2.exists():
                temp_path2.unlink()


if __name__ == "__main__":
    pytest.main([__file__])
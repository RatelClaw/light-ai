"""
Integration tests for versioning system with storage router.

Tests the integration between version manager and storage router to ensure
versioning works correctly across the entire storage system.
"""

import pytest
import tempfile
import uuid
from pathlib import Path

from light_ai.core.models import ResourceMetadata, DataHierarchy, ResourceType, DataType
from light_ai.storage.storage_router import StorageRouter
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
def storage_router(temp_config):
    """Create a storage router for testing."""
    return StorageRouter(temp_config)


@pytest.fixture
def sample_hierarchy():
    """Create a sample data hierarchy for testing."""
    return DataHierarchy(
        client_id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        resource_id=str(uuid.uuid4())
    )


@pytest.fixture
def sample_csv_file():
    """Create a sample CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("id,name,value\n1,test,100\n2,example,200\n")
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


class TestVersioningIntegration:
    """Test versioning integration with storage router."""
    
    def test_structured_data_versioning(self, storage_router, sample_hierarchy, sample_csv_file):
        """Test versioning with structured data storage."""
        # Create initial metadata
        metadata = ResourceMetadata(
            resource_id=sample_hierarchy.resource_id,
            user_id=sample_hierarchy.user_id,
            client_id=sample_hierarchy.client_id,
            resource_type=ResourceType.STRUCTURED,
            data_type=DataType.CSV,
            original_filename="test_data.csv",
            file_size_bytes=sample_csv_file.stat().st_size,
            storage_path="",
            version=1,
            processing_status="completed"
        )
        
        # Store initial version
        table_name = storage_router.store_structured_data(
            sample_csv_file, sample_hierarchy, metadata
        )
        
        assert table_name is not None
        
        # Verify version history
        version_history = storage_router.get_version_history(sample_hierarchy.resource_id)
        assert len(version_history) == 1
        assert version_history[0]['version'] == 1
        assert version_history[0]['operation'] == 'upload'
        
        # Update to new version
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,name,value,extra\n1,test,100,A\n2,example,200,B\n3,new,300,C\n")
            updated_file = Path(f.name)
        
        try:
            new_version = storage_router.update_resource(
                sample_hierarchy.resource_id, updated_file, 
                sample_hierarchy.user_id, "Added new column and row"
            )
            
            assert new_version == 2
            
            # Verify version history now has 2 versions
            version_history = storage_router.get_version_history(sample_hierarchy.resource_id)
            assert len(version_history) == 2
            assert version_history[0]['version'] == 2  # Most recent first
            assert version_history[1]['version'] == 1
            
        finally:
            if updated_file.exists():
                updated_file.unlink()
    
    def test_rollback_functionality(self, storage_router, sample_hierarchy, sample_csv_file):
        """Test rollback functionality through storage router."""
        # Create initial metadata
        metadata = ResourceMetadata(
            resource_id=sample_hierarchy.resource_id,
            user_id=sample_hierarchy.user_id,
            client_id=sample_hierarchy.client_id,
            resource_type=ResourceType.STRUCTURED,
            data_type=DataType.CSV,
            original_filename="test_data.csv",
            file_size_bytes=sample_csv_file.stat().st_size,
            storage_path="",
            version=1,
            processing_status="completed"
        )
        
        # Store initial version
        storage_router.store_structured_data(sample_csv_file, sample_hierarchy, metadata)
        
        # Create version 2
        storage_router.update_resource(
            sample_hierarchy.resource_id, sample_csv_file,
            sample_hierarchy.user_id, "Version 2"
        )
        
        # Create version 3
        storage_router.update_resource(
            sample_hierarchy.resource_id, sample_csv_file,
            sample_hierarchy.user_id, "Version 3"
        )
        
        # Rollback to version 1
        rollback_version = storage_router.rollback_resource(
            sample_hierarchy.resource_id, 1, sample_hierarchy.user_id,
            "Rolling back to original version"
        )
        
        assert rollback_version == 4  # New version created for rollback
        
        # Verify audit trail includes rollback
        audit_trail = storage_router.get_audit_trail(sample_hierarchy.resource_id)
        rollback_records = [r for r in audit_trail if r['operation'] == 'rollback']
        assert len(rollback_records) == 1
        assert "Rolled back to version 1" in rollback_records[0]['operation_details']
    
    def test_soft_delete_and_restore(self, storage_router, sample_hierarchy, sample_csv_file):
        """Test soft delete and restore functionality."""
        # Create initial metadata
        metadata = ResourceMetadata(
            resource_id=sample_hierarchy.resource_id,
            user_id=sample_hierarchy.user_id,
            client_id=sample_hierarchy.client_id,
            resource_type=ResourceType.STRUCTURED,
            data_type=DataType.CSV,
            original_filename="test_data.csv",
            file_size_bytes=sample_csv_file.stat().st_size,
            storage_path="",
            version=1,
            processing_status="completed"
        )
        
        # Store initial version
        storage_router.store_structured_data(sample_csv_file, sample_hierarchy, metadata)
        
        # Verify resource exists
        resource_info = storage_router.get_resource_info(sample_hierarchy.resource_id)
        assert resource_info is not None
        assert resource_info.is_deleted is False
        
        # Soft delete the resource
        success = storage_router.delete_resource(
            sample_hierarchy.resource_id, sample_hierarchy.user_id, hard_delete=False
        )
        assert success is True
        
        # Verify resource is marked as deleted
        resource_info = storage_router.get_resource_info(sample_hierarchy.resource_id)
        assert resource_info is not None
        assert resource_info.is_deleted is True
        
        # Restore the resource
        success = storage_router.restore_resource(
            sample_hierarchy.resource_id, sample_hierarchy.user_id,
            "Needed the data again"
        )
        assert success is True
        
        # Verify resource is no longer marked as deleted
        resource_info = storage_router.get_resource_info(sample_hierarchy.resource_id)
        assert resource_info is not None
        assert resource_info.is_deleted is False
        
        # Verify audit trail
        audit_trail = storage_router.get_audit_trail(sample_hierarchy.resource_id)
        operations = [r['operation'] for r in audit_trail]
        assert 'delete' in operations
        assert 'restore' in operations
    
    def test_hard_delete(self, storage_router, sample_hierarchy, sample_csv_file):
        """Test hard delete functionality."""
        # Create initial metadata
        metadata = ResourceMetadata(
            resource_id=sample_hierarchy.resource_id,
            user_id=sample_hierarchy.user_id,
            client_id=sample_hierarchy.client_id,
            resource_type=ResourceType.STRUCTURED,
            data_type=DataType.CSV,
            original_filename="test_data.csv",
            file_size_bytes=sample_csv_file.stat().st_size,
            storage_path="",
            version=1,
            processing_status="completed"
        )
        
        # Store initial version
        storage_router.store_structured_data(sample_csv_file, sample_hierarchy, metadata)
        
        # Verify resource exists
        resource_info = storage_router.get_resource_info(sample_hierarchy.resource_id)
        assert resource_info is not None
        
        # Hard delete the resource
        success = storage_router.delete_resource(
            sample_hierarchy.resource_id, sample_hierarchy.user_id, hard_delete=True
        )
        assert success is True
        
        # Verify resource no longer exists
        resource_info = storage_router.get_resource_info(sample_hierarchy.resource_id)
        assert resource_info is None
        
        # Verify version history is empty
        version_history = storage_router.get_version_history(sample_hierarchy.resource_id)
        assert len(version_history) == 0
    
    def test_json_data_versioning(self, storage_router, sample_hierarchy):
        """Test versioning with JSON data storage."""
        # Create initial metadata
        metadata = ResourceMetadata(
            resource_id=sample_hierarchy.resource_id,
            user_id=sample_hierarchy.user_id,
            client_id=sample_hierarchy.client_id,
            resource_type=ResourceType.JSON,
            data_type=DataType.JSON,
            original_filename="test_data.json",
            file_size_bytes=100,
            storage_path="",
            version=1,
            processing_status="completed"
        )
        
        # Store initial JSON version
        json_data = {"users": [{"id": 1, "name": "test"}]}
        table_name = storage_router.store_json_data(json_data, sample_hierarchy, metadata)
        
        assert table_name is not None
        
        # Verify version history
        version_history = storage_router.get_version_history(sample_hierarchy.resource_id)
        assert len(version_history) == 1
        assert version_history[0]['version'] == 1
        assert version_history[0]['operation'] == 'upload'
    
    def test_audit_trail_completeness(self, storage_router, sample_hierarchy, sample_csv_file):
        """Test that audit trail captures all operations."""
        # Create initial metadata
        metadata = ResourceMetadata(
            resource_id=sample_hierarchy.resource_id,
            user_id=sample_hierarchy.user_id,
            client_id=sample_hierarchy.client_id,
            resource_type=ResourceType.STRUCTURED,
            data_type=DataType.CSV,
            original_filename="test_data.csv",
            file_size_bytes=sample_csv_file.stat().st_size,
            storage_path="",
            version=1,
            processing_status="completed"
        )
        
        # Perform various operations
        storage_router.store_structured_data(sample_csv_file, sample_hierarchy, metadata)
        storage_router.update_resource(sample_hierarchy.resource_id, sample_csv_file, sample_hierarchy.user_id)
        storage_router.delete_resource(sample_hierarchy.resource_id, sample_hierarchy.user_id, hard_delete=False)
        storage_router.restore_resource(sample_hierarchy.resource_id, sample_hierarchy.user_id)
        
        # Get complete audit trail
        audit_trail = storage_router.get_audit_trail(sample_hierarchy.resource_id, limit=50)
        
        # Verify all operations are logged
        operations = [record['operation'] for record in audit_trail]
        assert 'upload' in operations
        assert 'update' in operations
        assert 'delete' in operations
        assert 'restore' in operations
        
        # Verify each record has required fields
        for record in audit_trail:
            assert 'audit_id' in record
            assert 'resource_id' in record
            assert 'operation' in record
            assert 'user_id' in record
            assert 'client_id' in record
            assert 'timestamp' in record
            assert record['resource_id'] == sample_hierarchy.resource_id
            assert record['user_id'] == sample_hierarchy.user_id
            assert record['client_id'] == sample_hierarchy.client_id


if __name__ == "__main__":
    pytest.main([__file__])
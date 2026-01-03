#!/usr/bin/env python3
"""
Test script to verify the storage layer foundation implementation.
"""

import os
import tempfile
import shutil
from pathlib import Path
import uuid

# Add the project root to Python path
import sys
sys.path.insert(0, '.')

from light_ai.storage import (
    DirectoryManager, 
    DatabaseManagers,
    MetadataRegistry,
    StoragePathUtils,
    FileManager
)
from light_ai.core.models import DataHierarchy, ResourceMetadata, ResourceType, DataType
from light_ai.config import Config


def test_storage_foundation():
    """Test the storage layer foundation components."""
    print("Testing Storage Layer Foundation...")
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temporary directory: {temp_dir}")
        
        # Create test configuration
        config = Config()
        config.storage.base_directory = temp_dir
        config.database.duckdb_path = "data/duckdb/test.db"
        config.database.sqlite_path = "metadata/test_registry.db"
        config.database.chromadb_path = "data/unstructured/test_chroma_db"
        
        # Test 1: Directory Manager
        print("\n1. Testing DirectoryManager...")
        dir_manager = DirectoryManager(config)
        dir_manager.create_all_directories()
        
        # Verify directories were created
        required_dirs = [
            "data/structured", "data/json", "data/unstructured", 
            "data/raw", "metadata", "cache", "logs"
        ]
        
        for directory in required_dirs:
            full_path = Path(temp_dir) / directory
            assert full_path.exists(), f"Directory not created: {full_path}"
            print(f"  ✓ Created directory: {directory}")
        
        # Test hierarchical directory creation
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        resource_id = str(uuid.uuid4())
        
        dir_manager.create_resource_directory(client_id, user_id, resource_id)
        
        resource_dir = Path(temp_dir) / "data" / "structured" / client_id / user_id / resource_id
        assert resource_dir.exists(), f"Resource directory not created: {resource_dir}"
        print(f"  ✓ Created hierarchical directory structure")
        
        # Test 2: Database Managers
        print("\n2. Testing DatabaseManagers...")
        db_managers = DatabaseManagers(config)
        db_managers.initialize_all()
        
        # Verify database files were created
        sqlite_path = Path(temp_dir) / config.database.sqlite_path
        duckdb_path = Path(temp_dir) / config.database.duckdb_path
        chromadb_path = Path(temp_dir) / config.database.chromadb_path
        
        assert sqlite_path.exists(), f"SQLite database not created: {sqlite_path}"
        assert duckdb_path.exists(), f"DuckDB database not created: {duckdb_path}"
        assert chromadb_path.exists(), f"ChromaDB directory not created: {chromadb_path}"
        
        print(f"  ✓ SQLite database created: {sqlite_path}")
        print(f"  ✓ DuckDB database created: {duckdb_path}")
        print(f"  ✓ ChromaDB directory created: {chromadb_path}")
        
        # Test health check
        health = db_managers.health_check()
        assert all(health.values()), f"Database health check failed: {health}"
        print(f"  ✓ All databases healthy: {health}")
        
        # Test 3: Metadata Registry
        print("\n3. Testing MetadataRegistry...")
        registry = MetadataRegistry(config)
        registry.initialize()
        
        # Create test metadata
        hierarchy = DataHierarchy(client_id, user_id, resource_id)
        metadata = ResourceMetadata(
            resource_id=resource_id,
            user_id=user_id,
            client_id=client_id,
            resource_type=ResourceType.STRUCTURED,
            data_type=DataType.CSV,
            original_filename="test.csv",
            file_size_bytes=1024,
            storage_path=f"data/structured/{client_id}/{user_id}/{resource_id}/test.csv"
        )
        
        # Test CRUD operations
        registry.create_resource_metadata(metadata)
        print(f"  ✓ Created resource metadata: {resource_id}")
        
        retrieved = registry.get_resource_metadata(resource_id)
        assert retrieved is not None, "Failed to retrieve metadata"
        assert retrieved.resource_id == resource_id, "Retrieved metadata mismatch"
        print(f"  ✓ Retrieved resource metadata successfully")
        
        # Test listing resources
        resources = registry.list_resources(client_id, user_id)
        assert len(resources) == 1, f"Expected 1 resource, got {len(resources)}"
        print(f"  ✓ Listed resources: {len(resources)} found")
        
        # Test audit logging
        registry.log_operation(
            resource_id=resource_id,
            operation="upload",
            user_id=user_id,
            client_id=client_id,
            operation_details="Test upload operation"
        )
        
        audit_trail = registry.get_audit_trail(resource_id)
        assert len(audit_trail) == 1, f"Expected 1 audit record, got {len(audit_trail)}"
        print(f"  ✓ Logged operation to audit trail")
        
        # Test 4: Storage Path Utils
        print("\n4. Testing StoragePathUtils...")
        path_utils = StoragePathUtils(config)
        
        # Test hierarchical path generation
        structured_path = path_utils.generate_hierarchical_path(hierarchy, "structured")
        expected_path = Path(temp_dir) / "data" / "structured" / client_id / user_id / resource_id
        assert structured_path == expected_path, f"Path mismatch: {structured_path} != {expected_path}"
        print(f"  ✓ Generated hierarchical path: {structured_path}")
        
        # Test file path generation
        file_path = path_utils.generate_file_path(hierarchy, "test.csv", "structured", 1)
        expected_file_path = expected_path / "v1_test.csv"
        assert file_path == expected_file_path, f"File path mismatch: {file_path} != {expected_file_path}"
        print(f"  ✓ Generated versioned file path: {file_path}")
        
        # Test 5: File Manager
        print("\n5. Testing FileManager...")
        file_manager = FileManager(config)
        
        # Create a test file
        test_file_content = "test,data,content\n1,2,3\n4,5,6\n"
        test_file_path = Path(temp_dir) / "test_input.csv"
        test_file_path.write_text(test_file_content)
        
        # Store the file
        stored_path = file_manager.store_file(
            test_file_path, hierarchy, "test.csv", "structured", 1
        )
        
        assert stored_path.exists(), f"Stored file not found: {stored_path}"
        assert stored_path.read_text() == test_file_content, "File content mismatch"
        print(f"  ✓ Stored file successfully: {stored_path}")
        
        # Retrieve the file
        retrieved_path = file_manager.retrieve_file(hierarchy, "test.csv", "structured")
        assert retrieved_path is not None, "Failed to retrieve file"
        assert retrieved_path.read_text() == test_file_content, "Retrieved file content mismatch"
        print(f"  ✓ Retrieved file successfully: {retrieved_path}")
        
        # Test file info
        file_info = file_manager.get_file_info(stored_path)
        assert file_info['size_bytes'] == len(test_file_content.encode()), "File size mismatch"
        assert 'hash_md5' in file_info, "MD5 hash not calculated"
        assert 'hash_sha256' in file_info, "SHA256 hash not calculated"
        print(f"  ✓ Retrieved file info: {file_info['size_bytes']} bytes")
        
        # Clean up database connections
        db_managers.close_all()
        
        print("\n✅ All storage layer foundation tests passed!")
        return True


if __name__ == "__main__":
    try:
        test_storage_foundation()
        print("\n🎉 Storage layer foundation implementation is working correctly!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
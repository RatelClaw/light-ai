"""
Property-based tests for file upload system.

Tests universal file upload and processing properties using hypothesis.
"""

import os
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any
import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite

from light_ai.sub_layer_1.file_upload import FileUploadAPI, FileValidator, DuplicateDetector
from light_ai.core.models import DataType, ResourceType, DataHierarchy
from light_ai.config import get_config


# Test data generation strategies
@composite
def valid_uuid_v4(draw):
    """Generate valid UUID v4 strings."""
    return str(uuid.uuid4())


@composite
def supported_file_content(draw):
    """Generate content for supported file types."""
    file_type = draw(st.sampled_from([
        'csv', 'json', 'txt', 'html', 'md'
    ]))
    
    if file_type == 'csv':
        # Simple CSV content
        return "id,name,value\n1,test,100\n2,sample,200\n", '.csv'
    elif file_type == 'json':
        # Simple JSON content
        return '{"id": 1, "name": "test", "data": [1, 2, 3]}', '.json'
    elif file_type == 'txt':
        # Plain text content
        content = draw(st.text(min_size=1, max_size=1000))
        return content, '.txt'
    elif file_type == 'html':
        # Simple HTML content
        return '<html><body><h1>Test</h1><p>Content</p></body></html>', '.html'
    elif file_type == 'md':
        # Markdown content
        return '# Test\n\nThis is a test markdown file.\n\n- Item 1\n- Item 2', '.md'


@composite
def file_size_bytes(draw):
    """Generate file sizes within reasonable limits for testing."""
    # Generate sizes from 1 byte to 10MB for testing
    return draw(st.integers(min_value=1, max_value=10 * 1024 * 1024))


class TestUniversalFileUploadProperties:
    """Property-based tests for universal file upload functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.config = get_config()
        self.upload_api = FileUploadAPI(self.config)
        self.validator = FileValidator(self.config)
        self.duplicate_detector = DuplicateDetector(self.config)
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test environment."""
        # Clean up temporary files
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_test_file(self, content: str, extension: str) -> Path:
        """Create a temporary test file with given content and extension."""
        filename = f"test_{uuid.uuid4().hex[:8]}{extension}"
        file_path = Path(self.temp_dir) / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return file_path
    
    @given(
        client_id=valid_uuid_v4(),
        user_id=valid_uuid_v4(),
        file_data=supported_file_content()
    )
    @settings(max_examples=50, deadline=10000)  # Reduced for faster testing
    def test_property_1_universal_file_upload_and_processing(self, client_id, user_id, file_data):
        """
        Feature: universal-data-handler, Property 1: Universal File Upload and Processing
        For any supported file type, when uploaded with valid IDs, should process successfully
        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
        """
        content, extension = file_data
        
        # Create test file
        file_path = self.create_test_file(content, extension)
        
        try:
            # Test file validation
            data_type, resource_type, file_size = self.validator.validate_file(file_path)
            
            # Verify file type detection worked
            assert isinstance(data_type, DataType)
            assert isinstance(resource_type, ResourceType)
            assert file_size > 0
            
            # Test file upload
            metadata = self.upload_api.upload_file(
                client_id=client_id,
                user_id=user_id,
                file_path=file_path,
                check_duplicates=False  # Skip duplicate check for property testing
            )
            
            # Verify metadata properties
            assert metadata.client_id == client_id
            assert metadata.user_id == user_id
            assert metadata.resource_type == resource_type
            assert metadata.data_type == data_type
            assert metadata.file_size_bytes == file_size
            assert metadata.original_filename == file_path.name
            assert metadata.processing_status == "uploaded"
            
            # Verify UUID v4 format for resource_id
            uuid.UUID(metadata.resource_id, version=4)
            
            # Verify storage path is set
            assert metadata.storage_path
            
            # Verify file hash is calculated
            assert metadata.file_hash
            assert len(metadata.file_hash) == 64  # SHA256 hex digest length
            
        except Exception as e:
            # If we get here, the upload failed for a supported file type
            pytest.fail(f"Universal file upload failed for {extension} file: {e}")
    
    @given(
        client_id=valid_uuid_v4(),
        user_id=valid_uuid_v4(),
        file_data=supported_file_content()
    )
    @settings(max_examples=30, deadline=10000)
    def test_property_file_type_detection_consistency(self, client_id, user_id, file_data):
        """
        Property: File type detection should be consistent and accurate
        For any supported file, the detected type should match the file extension
        """
        content, extension = file_data
        file_path = self.create_test_file(content, extension)
        
        # Test file type detection
        data_type, resource_type = self.validator.detect_file_type(file_path)
        
        # Verify the detected type matches expected mapping
        expected_data_type = FileValidator.EXTENSION_TO_DATATYPE.get(extension)
        expected_resource_type = FileValidator.DATATYPE_TO_RESOURCETYPE.get(expected_data_type)
        
        assert data_type == expected_data_type
        assert resource_type == expected_resource_type
    
    @given(
        client_id=valid_uuid_v4(),
        user_id=valid_uuid_v4(),
        file_data=supported_file_content()
    )
    @settings(max_examples=30, deadline=10000)
    def test_property_duplicate_detection_consistency(self, client_id, user_id, file_data):
        """
        Property: Duplicate detection should be consistent
        For any file, calculating hash multiple times should give same result
        """
        content, extension = file_data
        file_path = self.create_test_file(content, extension)
        
        # Calculate hash multiple times
        hash1 = self.duplicate_detector.calculate_file_hash(file_path)
        hash2 = self.duplicate_detector.calculate_file_hash(file_path)
        hash3 = self.duplicate_detector.calculate_file_hash(file_path)
        
        # All hashes should be identical
        assert hash1 == hash2 == hash3
        assert len(hash1) == 64  # SHA256 hex digest length
        assert all(c in '0123456789abcdef' for c in hash1)  # Valid hex
    
    @given(
        client_id=valid_uuid_v4(),
        user_id=valid_uuid_v4(),
        file_data=supported_file_content()
    )
    @settings(max_examples=30, deadline=10000)
    def test_property_file_size_validation_accuracy(self, client_id, user_id, file_data):
        """
        Property: File size validation should be accurate
        For any file, reported size should match actual file size
        """
        content, extension = file_data
        file_path = self.create_test_file(content, extension)
        
        # Get actual file size
        actual_size = file_path.stat().st_size
        
        # Validate file size through validator
        validated_size = self.validator.validate_file_size(file_path)
        
        # Sizes should match
        assert validated_size == actual_size
        assert validated_size > 0
    
    @given(
        client_id=valid_uuid_v4(),
        user_id=valid_uuid_v4(),
        file_paths=st.lists(supported_file_content(), min_size=1, max_size=5)
    )
    @settings(max_examples=20, deadline=15000)
    def test_property_bulk_upload_consistency(self, client_id, user_id, file_paths):
        """
        Property: Bulk upload should process all files consistently
        For any list of supported files, bulk upload should process each successfully
        """
        # Create test files
        test_files = []
        for content, extension in file_paths:
            file_path = self.create_test_file(content, extension)
            test_files.append(file_path)
        
        # Test bulk upload
        results = self.upload_api.upload_bulk(
            client_id=client_id,
            user_id=user_id,
            file_paths=test_files,
            parallel=False  # Use sequential for more predictable testing
        )
        
        # Should have results for all files
        assert len(results) == len(test_files)
        
        # Each result should be valid
        for i, metadata in enumerate(results):
            assert metadata.client_id == client_id
            assert metadata.user_id == user_id
            assert metadata.original_filename == test_files[i].name
            assert metadata.processing_status == "uploaded"
            
            # Verify UUID v4 format
            uuid.UUID(metadata.resource_id, version=4)
    
    @given(
        client_id=valid_uuid_v4(),
        user_id=valid_uuid_v4()
    )
    @settings(max_examples=20, deadline=5000)
    def test_property_hierarchy_validation_enforcement(self, client_id, user_id):
        """
        Property: Data hierarchy validation should be enforced
        For any valid client_id and user_id, generated hierarchy should be valid
        """
        # Generate new hierarchy
        hierarchy = DataHierarchy.generate_new(client_id, user_id)
        
        # Verify all IDs are valid UUID v4
        uuid.UUID(hierarchy.client_id, version=4)
        uuid.UUID(hierarchy.user_id, version=4)
        uuid.UUID(hierarchy.resource_id, version=4)
        
        # Verify IDs match input
        assert hierarchy.client_id == client_id
        assert hierarchy.user_id == user_id
        
        # Resource ID should be unique (different from client and user IDs)
        assert hierarchy.resource_id != client_id
        assert hierarchy.resource_id != user_id
    
    def test_property_unsupported_file_rejection(self):
        """
        Property: Unsupported file types should be consistently rejected
        For any unsupported file extension, validation should fail
        """
        # Create file with unsupported extension
        unsupported_extensions = ['.exe', '.bin', '.unknown', '.xyz']
        
        for extension in unsupported_extensions:
            file_path = self.create_test_file("test content", extension)
            
            # Should raise FileTypeDetectionError
            with pytest.raises(Exception):  # Could be FileTypeDetectionError or similar
                self.validator.validate_file(file_path)
    
    def test_property_empty_file_rejection(self):
        """
        Property: Empty files should be consistently rejected
        For any file with zero bytes, validation should fail
        """
        # Create empty file
        empty_file = Path(self.temp_dir) / "empty.txt"
        empty_file.touch()  # Creates empty file
        
        # Should raise FileSizeError
        with pytest.raises(Exception):  # Could be FileSizeError or similar
            self.validator.validate_file(empty_file)
    
    @given(
        client_id=st.text(min_size=1, max_size=50).filter(lambda x: not x.isspace()),
        user_id=valid_uuid_v4()
    )
    @settings(max_examples=20, deadline=5000)
    def test_property_invalid_client_id_rejection(self, client_id, user_id):
        """
        Property: Invalid client IDs should be consistently rejected
        For any non-UUID client_id, hierarchy creation should fail
        """
        assume(client_id != user_id)  # Avoid accidental valid UUID
        
        try:
            # Try to parse as UUID to see if it's accidentally valid
            uuid.UUID(client_id, version=4)
            # If we get here, it's actually a valid UUID, so skip this test case
            assume(False)
        except (ValueError, TypeError):
            # Good, it's not a valid UUID, proceed with test
            pass
        
        # Should raise ValueError for invalid UUID
        with pytest.raises(ValueError):
            DataHierarchy(client_id=client_id, user_id=user_id, resource_id=str(uuid.uuid4()))
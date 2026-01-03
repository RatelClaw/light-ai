"""
Integration tests for data cleaning with file upload system.
"""

import pytest
import pandas as pd
import tempfile
import json
from pathlib import Path

from light_ai.sub_layer_1.file_upload import FileUploadAPI
from light_ai.sub_layer_1.data_cleaning import DataCleaningEngine
from light_ai.core.models import DataType, ResourceType


class TestDataCleaningIntegration:
    """Test integration between file upload and data cleaning."""
    
    def test_csv_upload_and_cleaning_workflow(self):
        """Test complete workflow: upload CSV -> clean data."""
        # Create test CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('  Name  ,Age-Value,Score\n')
            f.write('  John  ,25,85.5\n')
            f.write('  Jane  ,,90\n')
            f.write(',30,95.2\n')
            csv_path = Path(f.name)
        
        try:
            # Step 1: Upload and validate file
            upload_api = FileUploadAPI()
            data_type, resource_type, file_size = upload_api.validator.validate_file(csv_path)
            
            assert data_type == DataType.CSV
            assert resource_type == ResourceType.STRUCTURED
            
            # Step 2: Load and clean the data
            df = pd.read_csv(csv_path)
            cleaning_engine = DataCleaningEngine()
            cleaned_df, stats = cleaning_engine.clean_data(df, data_type)
            
            # Verify cleaning operations
            assert 'normalize_column_names' in stats['operations_performed']
            assert 'strip_whitespace' in stats['operations_performed']
            
            # Check cleaned column names
            expected_columns = ['name', 'age_value', 'score']
            assert list(cleaned_df.columns) == expected_columns
            
            # Check data was cleaned
            assert cleaned_df['name'].iloc[0] == 'John'
            assert cleaned_df['name'].iloc[1] == 'Jane'
            
        finally:
            csv_path.unlink()  # Clean up
    
    def test_json_upload_and_cleaning_workflow(self):
        """Test complete workflow: upload JSON -> clean data."""
        # Create test JSON file
        test_data = {
            'User Info': {
                'First Name': 'John',
                'Last Name': 'Doe',
                'empty_field': None
            },
            'Settings': {
                'Theme': 'dark',
                'Notifications': True
            },
            'empty_object': {}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            json_path = Path(f.name)
        
        try:
            # Step 1: Upload and validate file
            upload_api = FileUploadAPI()
            data_type, resource_type, file_size = upload_api.validator.validate_file(json_path)
            
            assert data_type == DataType.JSON
            assert resource_type == ResourceType.JSON
            
            # Step 2: Load and clean the data
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            cleaning_engine = DataCleaningEngine()
            cleaned_data, stats = cleaning_engine.clean_data(data, data_type)
            
            # Verify cleaning operations
            assert 'remove_null_objects' in stats['operations_performed']
            assert 'normalize_keys' in stats['operations_performed']
            
            # Check that null objects were removed
            assert 'empty_field' not in str(cleaned_data)
            assert 'empty_object' not in cleaned_data
            
            # Check key normalization
            assert 'user_info' in cleaned_data
            
        finally:
            json_path.unlink()  # Clean up
    
    def test_text_upload_and_cleaning_workflow(self):
        """Test complete workflow: upload text -> clean and chunk."""
        # Create test text file
        test_text = """
        Page 1
        
        This is a sample document with multiple paragraphs.
        
        
        This is the second paragraph with some    extra    spaces.
        
        Page 2
        
        This is the third paragraph.
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_text)
            txt_path = Path(f.name)
        
        try:
            # Step 1: Upload and validate file
            upload_api = FileUploadAPI()
            data_type, resource_type, file_size = upload_api.validator.validate_file(txt_path)
            
            assert data_type == DataType.TXT
            assert resource_type == ResourceType.UNSTRUCTURED
            
            # Step 2: Clean the text data
            cleaning_engine = DataCleaningEngine()
            cleaned_text, chunks, stats = cleaning_engine.clean_data(test_text, data_type)
            
            # Verify chunks were created
            assert len(chunks) > 0
            assert stats['chunks_created'] == len(chunks)
            
            # Check that text was cleaned (page numbers should be removed)
            assert 'Page 1' not in cleaned_text
            assert 'Page 2' not in cleaned_text
            
        finally:
            txt_path.unlink()  # Clean up
    
    def test_supported_file_types_have_cleaning_support(self):
        """Test that all supported file types have corresponding cleaning support."""
        upload_api = FileUploadAPI()
        cleaning_engine = DataCleaningEngine()
        
        # Get all supported data types from file upload
        supported_types = upload_api.get_supported_types()
        
        # Test that each type can be processed by cleaning engine
        test_data = {
            'structured': pd.DataFrame({'col1': [1, 2], 'col2': ['a', 'b']}),
            'json': {'key': 'value'},
            'unstructured': 'Sample text content'
        }
        
        for resource_type, extensions in supported_types.items():
            if resource_type in test_data:
                # Map resource type to data type for testing
                if resource_type == 'structured':
                    data_type = DataType.CSV
                elif resource_type == 'json':
                    data_type = DataType.JSON
                else:  # unstructured
                    data_type = DataType.TXT
                
                # This should not raise an exception
                result = cleaning_engine.clean_data(test_data[resource_type], data_type)
                assert result is not None


if __name__ == "__main__":
    pytest.main([__file__])
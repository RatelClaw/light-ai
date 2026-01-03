"""
Tests for the data cleaning engine.
"""

import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import tempfile

from light_ai.sub_layer_1.data_cleaning import (
    DataCleaningEngine, StructuredDataCleaner, JSONDataCleaner, 
    UnstructuredDataCleaner, CleaningConfig, MissingValueStrategy
)
from light_ai.core.models import DataType


class TestStructuredDataCleaner:
    """Test structured data cleaning functionality."""
    
    def test_clean_dataframe_basic(self):
        """Test basic DataFrame cleaning operations."""
        # Create test DataFrame with various issues
        df = pd.DataFrame({
            '  Name  ': ['  John  ', '  Jane  ', '', None],
            'Age-Value': [25, None, 30, 35],
            'Empty Column': [None, None, None, None],
            'Score': ['85.5', '90', 'invalid', '95.2'],
            '': ['data1', 'data2', 'data3', 'data4']  # Empty column name
        })
        
        cleaner = StructuredDataCleaner()
        cleaned_df, stats = cleaner.clean_dataframe(df)
        
        # Check that operations were performed
        assert 'strip_whitespace' in stats['operations_performed']
        assert 'normalize_column_names' in stats['operations_performed']
        assert any('remove_empty_columns' in op for op in stats['operations_performed'])
        
        # Check column names are normalized
        expected_columns = ['name', 'age_value', 'score', 'column_0']
        assert list(cleaned_df.columns) == expected_columns
        
        # Check that empty column was removed
        assert 'empty_column' not in cleaned_df.columns
        
        # Check that whitespace was stripped
        assert cleaned_df['name'].iloc[0] == 'John'
        assert cleaned_df['name'].iloc[1] == 'Jane'
    
    def test_missing_value_strategies(self):
        """Test different missing value handling strategies."""
        df = pd.DataFrame({
            'A': [1, 2, None, 4],
            'B': [None, None, None, None],  # All missing
            'C': ['a', 'b', None, 'd']
        })
        
        # Test DROP_COLS strategy
        config = CleaningConfig(missing_value_strategy=MissingValueStrategy.DROP_COLS)
        cleaner = StructuredDataCleaner(config)
        cleaned_df, stats = cleaner.clean_dataframe(df)
        
        # Column B should be dropped (all missing)
        assert 'b' not in cleaned_df.columns
        assert 'a' in cleaned_df.columns
        assert 'c' in cleaned_df.columns
    
    def test_data_type_detection(self):
        """Test automatic data type detection and conversion."""
        df = pd.DataFrame({
            'integers': ['1', '2', '3', '4'],
            'floats': ['1.5', '2.7', '3.14', '4.0'],
            'booleans': ['true', 'false', 'true', 'false'],
            'dates': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04'],
            'strings': ['hello', 'world', 'test', 'data']
        })
        
        cleaner = StructuredDataCleaner()
        cleaned_df, stats = cleaner.clean_dataframe(df)
        
        # Check that data types were detected and converted
        assert 'detect_and_convert_types' in stats['operations_performed']
        assert cleaned_df['integers'].dtype == 'Int64'
        assert cleaned_df['floats'].dtype == 'float64'
        assert cleaned_df['booleans'].dtype == 'bool'
        assert pd.api.types.is_datetime64_any_dtype(cleaned_df['dates'])


class TestJSONDataCleaner:
    """Test JSON data cleaning functionality."""
    
    def test_clean_json_basic(self):
        """Test basic JSON cleaning operations."""
        data = {
            'User Name': 'John Doe',
            'user-age': 25,
            'empty_field': None,
            'nested': {
                'Field One': 'value1',
                'field_two': None
            },
            'empty_list': [],
            'empty_dict': {}
        }
        
        config = CleaningConfig(
            normalize_json_keys=True,
            remove_null_objects=True
        )
        cleaner = JSONDataCleaner(config)
        cleaned_data, stats = cleaner.clean_json(data)
        
        # Check operations were performed
        assert 'normalize_keys' in stats['operations_performed']
        assert 'remove_null_objects' in stats['operations_performed']
        
        # Check key normalization
        assert 'user_name' in cleaned_data
        assert 'user_age' in cleaned_data
        
        # Check null object removal
        assert 'empty_field' not in cleaned_data
        assert 'empty_list' not in cleaned_data
        assert 'empty_dict' not in cleaned_data
        
        # Check nested structure
        assert 'field_one' in cleaned_data['nested']
        assert 'field_two' not in cleaned_data['nested']
    
    def test_flatten_json(self):
        """Test JSON flattening functionality."""
        data = {
            'user': {
                'personal': {
                    'name': 'John',
                    'age': 25
                },
                'contact': {
                    'email': 'john@example.com'
                }
            },
            'settings': {
                'theme': 'dark'
            }
        }
        
        config = CleaningConfig(flatten_json=True, max_flatten_depth=2, normalize_json_keys=False)
        cleaner = JSONDataCleaner(config)
        cleaned_data, stats = cleaner.clean_json(data)
        
        # Check flattening was performed
        assert stats['flattened'] is True
        assert 'flatten_json' in stats['operations_performed']
        
        # Check flattened keys
        assert 'user_personal_name' in cleaned_data
        assert 'user_personal_age' in cleaned_data
        assert 'user_contact_email' in cleaned_data
        assert 'settings_theme' in cleaned_data


class TestUnstructuredDataCleaner:
    """Test unstructured data cleaning functionality."""
    
    def test_clean_text_basic(self):
        """Test basic text cleaning operations."""
        text = """
        
        Page 1
        
        This is a sample document with multiple paragraphs.
        
        
        
        This is the second paragraph with some    extra    spaces.
        
        
        Page 2
        
        This is the third paragraph.
        
        
        """
        
        cleaner = UnstructuredDataCleaner()
        cleaned_text, chunks, stats = cleaner.clean_text(text, DataType.TXT)
        
        # Check operations were performed
        assert 'remove_headers_footers' in stats['operations_performed']
        assert 'normalize_whitespace' in stats['operations_performed']
        
        # Check that text was cleaned
        assert 'Page 1' not in cleaned_text
        assert 'Page 2' not in cleaned_text
        assert 'extra    spaces' not in cleaned_text
        
        # Check chunks were created
        assert len(chunks) > 0
        assert stats['chunks_created'] == len(chunks)
    
    def test_create_semantic_chunks(self):
        """Test semantic chunking functionality."""
        # Create a long text that should be split into chunks
        text = " ".join([f"This is sentence {i} in the document." for i in range(100)])
        
        config = CleaningConfig(chunk_size_tokens=50, chunk_overlap_tokens=10)
        cleaner = UnstructuredDataCleaner(config)
        
        cleaned_text, chunks, stats = cleaner.clean_text(text, DataType.TXT)
        
        # Should create multiple chunks
        assert len(chunks) > 1
        assert stats['chunks_created'] > 1
        
        # Check that chunks have reasonable sizes
        for chunk in chunks:
            words = chunk.split()
            assert len(words) <= 60  # Should be around chunk_size_tokens + some buffer


class TestDataCleaningEngine:
    """Test the main data cleaning engine."""
    
    def test_clean_structured_data(self):
        """Test cleaning structured data through main engine."""
        df = pd.DataFrame({
            'Name': ['John', 'Jane', 'Bob'],
            'Age': [25, 30, 35],
            'Score': [85.5, 90.0, 95.2]
        })
        
        engine = DataCleaningEngine()
        cleaned_data, stats = engine.clean_data(df, DataType.CSV)
        
        assert isinstance(cleaned_data, pd.DataFrame)
        assert len(stats['operations_performed']) > 0
    
    def test_clean_json_data(self):
        """Test cleaning JSON data through main engine."""
        data = {'User Name': 'John', 'Age': 25}
        
        engine = DataCleaningEngine()
        cleaned_data, stats = engine.clean_data(data, DataType.JSON)
        
        assert isinstance(cleaned_data, dict)
        assert len(stats['operations_performed']) > 0
    
    def test_clean_text_data(self):
        """Test cleaning text data through main engine."""
        text = "This is a sample text document with some content."
        
        engine = DataCleaningEngine()
        cleaned_text, chunks, stats = engine.clean_data(text, DataType.TXT)
        
        assert isinstance(cleaned_text, str)
        assert isinstance(chunks, list)
        # Text cleaning may not always perform operations if text is already clean
        assert len(chunks) > 0
    
    def test_unsupported_data_type(self):
        """Test handling of unsupported data types."""
        engine = DataCleaningEngine()
        
        # Create a mock DataType that doesn't exist in our cleaning logic
        class UnsupportedType:
            value = "unsupported"
        
        with pytest.raises(ValueError, match="Unsupported data type"):
            engine.clean_data("test", UnsupportedType())


class TestCleaningConfig:
    """Test cleaning configuration functionality."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = CleaningConfig()
        
        assert config.remove_empty_rows is True
        assert config.remove_empty_columns is True
        assert config.strip_whitespace is True
        assert config.normalize_column_names is True
        assert config.missing_value_strategy == MissingValueStrategy.NULL
        assert config.chunk_size_tokens == 512
        assert config.chunk_overlap_tokens == 50
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = CleaningConfig(
            remove_empty_rows=False,
            missing_value_strategy=MissingValueStrategy.FILL_MEAN,
            chunk_size_tokens=256
        )
        
        assert config.remove_empty_rows is False
        assert config.missing_value_strategy == MissingValueStrategy.FILL_MEAN
        assert config.chunk_size_tokens == 256
    
    def test_engine_config_update(self):
        """Test updating engine configuration."""
        engine = DataCleaningEngine()
        
        # Update configuration
        engine.update_cleaning_config(
            remove_empty_rows=False,
            chunk_size_tokens=256
        )
        
        assert engine.config.remove_empty_rows is False
        assert engine.config.chunk_size_tokens == 256


if __name__ == "__main__":
    pytest.main([__file__])
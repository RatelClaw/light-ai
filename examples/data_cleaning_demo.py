#!/usr/bin/env python3
"""
Demonstration of the Data Cleaning Engine capabilities.

This script shows how to use the data cleaning engine for different data types.
"""

import pandas as pd
import json
from pathlib import Path

from light_ai.sub_layer_1.data_cleaning import (
    DataCleaningEngine, CleaningConfig, MissingValueStrategy
)
from light_ai.core.models import DataType


def demo_structured_data_cleaning():
    """Demonstrate structured data cleaning capabilities."""
    print("=" * 60)
    print("STRUCTURED DATA CLEANING DEMO")
    print("=" * 60)
    
    # Create sample messy DataFrame
    df = pd.DataFrame({
        '  Full Name  ': ['  John Doe  ', '  Jane Smith  ', '', None, '  Bob Johnson  '],
        'Age-Value': [25, None, 30, 35, 'invalid'],
        'Empty Column': [None, None, None, None, None],
        'Score': ['85.5', '90', 'invalid', '95.2', '88'],
        'Is_Active': ['true', 'false', 'yes', 'no', '1'],
        'Join Date': ['2023-01-15', '2023-02-20', '2023-03-10', 'invalid', '2023-05-01']
    })
    
    print("Original DataFrame:")
    print(df)
    print(f"Shape: {df.shape}")
    print(f"Data types:\n{df.dtypes}")
    
    # Clean the data
    engine = DataCleaningEngine()
    cleaned_df, stats = engine.clean_data(df, DataType.CSV)
    
    print("\nCleaned DataFrame:")
    print(cleaned_df)
    print(f"Shape: {cleaned_df.shape}")
    print(f"Data types:\n{cleaned_df.dtypes}")
    
    print(f"\nCleaning Statistics:")
    print(f"Operations performed: {stats['operations_performed']}")
    print(f"Columns renamed: {stats['columns_renamed']}")
    print(f"Data types detected: {stats['data_types_detected']}")
    print(f"Rows removed: {stats['rows_removed']}")
    print(f"Columns removed: {stats['columns_removed']}")


def demo_json_data_cleaning():
    """Demonstrate JSON data cleaning capabilities."""
    print("\n" + "=" * 60)
    print("JSON DATA CLEANING DEMO")
    print("=" * 60)
    
    # Create sample messy JSON
    json_data = {
        'User Profile': {
            'Personal Info': {
                'First Name': 'John',
                'Last Name': 'Doe',
                'Middle Name': None,
                'empty_field': None
            },
            'Contact Details': {
                'Email Address': 'john.doe@example.com',
                'Phone Number': '+1-555-0123',
                'empty_contact': {}
            }
        },
        'Application Settings': {
            'UI Preferences': {
                'Theme Mode': 'dark',
                'Language': 'en-US',
                'Notifications Enabled': True
            },
            'Privacy Settings': {
                'Profile Visibility': 'public',
                'Data Sharing': False
            }
        },
        'empty_section': {},
        'null_data': None
    }
    
    print("Original JSON structure:")
    print(json.dumps(json_data, indent=2))
    
    # Configure cleaning with flattening
    config = CleaningConfig(
        flatten_json=True,
        max_flatten_depth=3,
        normalize_json_keys=True,
        remove_null_objects=True
    )
    
    engine = DataCleaningEngine(config)
    cleaned_data, stats = engine.clean_data(json_data, DataType.JSON)
    
    print("\nCleaned and flattened JSON:")
    print(json.dumps(cleaned_data, indent=2))
    
    print(f"\nCleaning Statistics:")
    print(f"Operations performed: {stats['operations_performed']}")
    print(f"Keys normalized: {stats['keys_normalized']}")
    print(f"Objects removed: {stats['objects_removed']}")
    print(f"Flattened: {stats['flattened']}")


def demo_text_data_cleaning():
    """Demonstrate unstructured text data cleaning capabilities."""
    print("\n" + "=" * 60)
    print("UNSTRUCTURED TEXT DATA CLEANING DEMO")
    print("=" * 60)
    
    # Create sample messy text
    messy_text = """
    
    Page 1
    
    Introduction to Data Processing
    
    This document provides an overview of data processing techniques used in modern applications.    
    Data processing involves several key steps including data collection, cleaning, transformation, and analysis.
    
    
    
    Data Collection Methods
    
    There are various methods for collecting data from different sources. These include:
    - Database queries
    - API calls    
    - File uploads
    - Web scraping
    
    Page 2
    
    Data Cleaning Techniques
    
    Data cleaning is a crucial step that involves removing inconsistencies and errors from raw data.
    Common cleaning operations include handling missing values, removing duplicates, and standardizing formats.
    
    
    The importance of data quality cannot be overstated in any data-driven application.
    
    
    Page 3
    
    Conclusion
    
    Effective data processing requires careful attention to each step of the pipeline.
    
    """
    
    print("Original text:")
    print(repr(messy_text))
    print(f"Length: {len(messy_text)} characters")
    
    # Configure cleaning with custom chunking
    config = CleaningConfig(
        remove_headers_footers=True,
        remove_page_numbers=True,
        preserve_layout=True,
        chunk_size_tokens=50,
        chunk_overlap_tokens=10,
        min_chunk_size=100
    )
    
    engine = DataCleaningEngine(config)
    cleaned_text, chunks, stats = engine.clean_data(messy_text, DataType.TXT)
    
    print("\nCleaned text:")
    print(repr(cleaned_text))
    print(f"Length: {len(cleaned_text)} characters")
    
    print(f"\nText chunks ({len(chunks)} total):")
    for i, chunk in enumerate(chunks, 1):
        print(f"Chunk {i} ({len(chunk)} chars): {chunk[:100]}...")
    
    print(f"\nCleaning Statistics:")
    print(f"Operations performed: {stats['operations_performed']}")
    print(f"Original length: {stats['original_length']}")
    print(f"Final length: {stats['final_length']}")
    print(f"Chunks created: {stats['chunks_created']}")


def demo_custom_configuration():
    """Demonstrate custom cleaning configuration."""
    print("\n" + "=" * 60)
    print("CUSTOM CONFIGURATION DEMO")
    print("=" * 60)
    
    # Create DataFrame with missing values
    df = pd.DataFrame({
        'name': ['Alice', 'Bob', None, 'David', None],
        'age': [25, None, 30, None, 35],
        'score': [85.5, 90.0, None, 95.2, None],
        'active': [True, False, None, True, False]
    })
    
    print("Original DataFrame with missing values:")
    print(df)
    print(f"Missing values per column:\n{df.isnull().sum()}")
    
    # Test different missing value strategies
    strategies = [
        MissingValueStrategy.NULL,
        MissingValueStrategy.FILL_MEAN,
        MissingValueStrategy.DROP_ROWS
    ]
    
    for strategy in strategies:
        print(f"\n--- Using strategy: {strategy.value} ---")
        config = CleaningConfig(missing_value_strategy=strategy)
        engine = DataCleaningEngine(config)
        cleaned_df, stats = engine.clean_data(df.copy(), DataType.CSV)
        
        print(f"Result shape: {cleaned_df.shape}")
        print(f"Missing values: {cleaned_df.isnull().sum().sum()}")
        if strategy == MissingValueStrategy.FILL_MEAN:
            print("Numeric columns filled with mean values")
        elif strategy == MissingValueStrategy.DROP_ROWS:
            print(f"Rows with missing values removed")


def main():
    """Run all demonstrations."""
    print("Data Cleaning Engine Demonstration")
    print("This demo shows the capabilities of the Universal Data Handler's cleaning engine.")
    
    try:
        demo_structured_data_cleaning()
        demo_json_data_cleaning()
        demo_text_data_cleaning()
        demo_custom_configuration()
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nThe Data Cleaning Engine supports:")
        print("✓ Structured data (CSV, Excel, TSV, Parquet)")
        print("✓ JSON data with flattening and key normalization")
        print("✓ Unstructured text with chunking and cleaning")
        print("✓ Configurable cleaning strategies")
        print("✓ Automatic data type detection")
        print("✓ Missing value handling")
        print("✓ Comprehensive cleaning statistics")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
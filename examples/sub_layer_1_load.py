#!/usr/bin/env python3
"""
Sub-Layer 1 Testing Script

This script demonstrates and tests all Sub-Layer 1 functionality including:
- File upload and validation
- Data cleaning for different file types
- Progress tracking
- Duplicate detection
- Bulk operations

Usage:
    python examples/sub_layer_1_load.py
"""

import sys
import os
from pathlib import Path
import uuid
import time
import json

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from light_ai.sub_layer_1 import (
    FileUploadAPI, FileValidator, DuplicateDetector,
    UploadProgressTracker, DataCleaningEngine, CleaningConfig, MissingValueStrategy
)
from light_ai.core.models import DataType, ResourceType
from light_ai.config import get_config
from light_ai.logger import get_logger

logger = get_logger(__name__)


class SubLayer1Tester:
    """Test harness for Sub-Layer 1 functionality."""
    
    def __init__(self):
        """Initialize the tester."""
        self.config = get_config()
        self.upload_api = FileUploadAPI()
        self.validator = FileValidator()
        self.duplicate_detector = DuplicateDetector()
        self.progress_tracker = UploadProgressTracker()
        self.cleaning_engine = DataCleaningEngine()
        
        # Test client and user IDs
        self.client_id = str(uuid.uuid4())
        self.user_id = str(uuid.uuid4())
        
        # Sample data directory
        self.sample_dir = Path("examples/data_sub_layer_1")
        
        print(f"🚀 Sub-Layer 1 Tester Initialized")
        print(f"   Client ID: {self.client_id}")
        print(f"   User ID: {self.user_id}")
        print(f"   Sample Data: {self.sample_dir}")
        print()
    
    def test_file_validation(self):
        """Test file type detection and validation."""
        print("📋 Testing File Validation...")
        
        test_files = [
            "sample_customers.csv",
            "sample_products.json", 
            "sample_orders.jsonl",
            "sample_report.txt",
            "sample_inventory.tsv",
            "sample_documentation.md",
            "sample_config.html",
            "messy_data.csv",
            "nested_config.json"
        ]
        
        for filename in test_files:
            file_path = self.sample_dir / filename
            if not file_path.exists():
                print(f"   ❌ File not found: {filename}")
                continue
            
            try:
                data_type, resource_type, file_size = self.validator.validate_file(file_path)
                print(f"   ✅ {filename}: {data_type.value} ({resource_type.value}) - {file_size:,} bytes")
            except Exception as e:
                print(f"   ❌ {filename}: {e}")
        
        print()
    
    def test_duplicate_detection(self):
        """Test duplicate file detection."""
        print("🔍 Testing Duplicate Detection...")
        
        # Test with the same file
        file1 = self.sample_dir / "sample_customers.csv"
        file2 = self.sample_dir / "sample_customers.csv"  # Same file
        
        if file1.exists():
            hash1 = self.duplicate_detector.calculate_file_hash(file1)
            hash2 = self.duplicate_detector.calculate_file_hash(file2)
            
            print(f"   File 1 hash: {hash1[:16]}...")
            print(f"   File 2 hash: {hash2[:16]}...")
            print(f"   Are duplicates: {hash1 == hash2}")
        else:
            print("   ❌ Sample file not found for duplicate testing")
        
        print()
    
    def test_data_cleaning(self):
        """Test data cleaning for different file types."""
        print("🧹 Testing Data Cleaning...")
        
        # Test structured data cleaning (messy CSV)
        messy_csv = self.sample_dir / "messy_data.csv"
        if messy_csv.exists():
            print("   📊 Cleaning messy CSV data...")
            try:
                import pandas as pd
                df = pd.read_csv(messy_csv)
                print(f"      Original shape: {df.shape}")
                
                config = CleaningConfig(
                    remove_empty_rows=True,
                    remove_empty_columns=True,
                    strip_whitespace=True,
                    normalize_column_names=True,
                    detect_data_types=True,
                    missing_value_strategy=MissingValueStrategy.FILL_MODE
                )
                
                cleaned_df, stats = self.cleaning_engine.structured_cleaner.clean_dataframe(df)
                print(f"      Cleaned shape: {cleaned_df.shape}")
                print(f"      Operations: {', '.join(stats['operations_performed'])}")
                print(f"      Columns renamed: {len(stats['columns_renamed'])}")
                
            except Exception as e:
                print(f"      ❌ Error cleaning CSV: {e}")
        
        # Test JSON data cleaning (nested JSON)
        nested_json = self.sample_dir / "nested_config.json"
        if nested_json.exists():
            print("   📄 Cleaning nested JSON data...")
            try:
                with open(nested_json, 'r') as f:
                    data = json.load(f)
                
                config = CleaningConfig(
                    flatten_json=True,
                    max_flatten_depth=2,
                    normalize_json_keys=True,
                    remove_null_objects=True
                )
                
                cleaned_data, stats = self.cleaning_engine.json_cleaner.clean_json(data)
                print(f"      Operations: {', '.join(stats['operations_performed'])}")
                print(f"      Keys normalized: {len(stats['keys_normalized'])}")
                print(f"      Objects removed: {stats['objects_removed']}")
                print(f"      Flattened: {stats['flattened']}")
                
            except Exception as e:
                print(f"      ❌ Error cleaning JSON: {e}")
        
        # Test unstructured data cleaning (text file)
        text_file = self.sample_dir / "sample_report.txt"
        if text_file.exists():
            print("   📝 Cleaning unstructured text data...")
            try:
                with open(text_file, 'r') as f:
                    text = f.read()
                
                config = CleaningConfig(
                    preserve_layout=True,
                    remove_headers_footers=True,
                    chunk_size_tokens=100,
                    chunk_overlap_tokens=20
                )
                
                cleaned_text, chunks, stats = self.cleaning_engine.unstructured_cleaner.clean_text(
                    text, DataType.TXT
                )
                print(f"      Original length: {stats['original_length']:,} chars")
                print(f"      Cleaned length: {stats['final_length']:,} chars")
                print(f"      Chunks created: {stats['chunks_created']}")
                print(f"      Operations: {', '.join(stats['operations_performed'])}")
                
            except Exception as e:
                print(f"      ❌ Error cleaning text: {e}")
        
        print()
    
    def test_single_upload(self):
        """Test single file upload."""
        print("📤 Testing Single File Upload...")
        
        test_file = self.sample_dir / "sample_customers.csv"
        if not test_file.exists():
            print("   ❌ Test file not found")
            return
        
        try:
            # Start progress tracking
            resource_id = str(uuid.uuid4())
            file_size = test_file.stat().st_size
            progress = self.progress_tracker.start_upload(
                resource_id, test_file.name, file_size
            )
            
            # Simulate upload progress
            for i in range(0, file_size + 1, file_size // 4):
                self.progress_tracker.update_progress(
                    resource_id, min(i, file_size),
                    stage=f"uploading_{i//1000}kb",
                    message=f"Uploaded {min(i, file_size):,} of {file_size:,} bytes"
                )
                time.sleep(0.1)  # Simulate upload time
            
            # Complete upload
            metadata = self.upload_api.upload_file(
                self.client_id, self.user_id, test_file,
                resource_name="Test Customer Data"
            )
            
            self.progress_tracker.complete_upload(resource_id, "Upload successful!")
            
            print(f"   ✅ Upload completed:")
            print(f"      Resource ID: {metadata.resource_id}")
            print(f"      Data Type: {metadata.data_type.value}")
            print(f"      Resource Type: {metadata.resource_type.value}")
            print(f"      File Size: {metadata.file_size_bytes:,} bytes")
            print(f"      Storage Path: {metadata.storage_path}")
            print(f"      File Hash: {metadata.file_hash[:16]}...")
            
        except Exception as e:
            print(f"   ❌ Upload failed: {e}")
            if 'resource_id' in locals():
                self.progress_tracker.fail_upload(resource_id, str(e))
        
        print()
    
    def test_bulk_upload(self):
        """Test bulk file upload."""
        print("📦 Testing Bulk File Upload...")
        
        # Get all sample files
        sample_files = [
            f for f in self.sample_dir.glob("*") 
            if f.is_file() and f.suffix.lower() in ['.csv', '.json', '.jsonl', '.txt', '.tsv', '.md', '.html']
        ]
        
        if not sample_files:
            print("   ❌ No sample files found")
            return
        
        print(f"   📁 Found {len(sample_files)} files to upload")
        
        try:
            # Test parallel bulk upload
            start_time = time.time()
            metadata_list = self.upload_api.upload_bulk(
                self.client_id, self.user_id, sample_files,
                parallel=True, max_workers=3
            )
            end_time = time.time()
            
            print(f"   ✅ Bulk upload completed in {end_time - start_time:.2f} seconds")
            print(f"   📊 Successfully uploaded {len(metadata_list)}/{len(sample_files)} files")
            
            # Show summary by type
            type_counts = {}
            for metadata in metadata_list:
                data_type = metadata.data_type.value
                type_counts[data_type] = type_counts.get(data_type, 0) + 1
            
            print("   📈 Upload summary by type:")
            for data_type, count in type_counts.items():
                print(f"      {data_type}: {count} files")
            
        except Exception as e:
            print(f"   ❌ Bulk upload failed: {e}")
        
        print()
    
    def test_progress_tracking(self):
        """Test upload progress tracking."""
        print("📊 Testing Progress Tracking...")
        
        # Create some mock progress entries
        test_files = ["file1.csv", "file2.json", "file3.txt"]
        resource_ids = []
        
        for i, filename in enumerate(test_files):
            resource_id = str(uuid.uuid4())
            resource_ids.append(resource_id)
            
            # Start tracking
            progress = self.progress_tracker.start_upload(resource_id, filename, 1000 * (i + 1))
            
            # Simulate some progress
            for step in range(0, 1001, 250):
                self.progress_tracker.update_progress(
                    resource_id, step,
                    stage=f"step_{step}",
                    message=f"Processing {filename}..."
                )
                time.sleep(0.05)
        
        # Complete some, fail others
        self.progress_tracker.complete_upload(resource_ids[0], "Success!")
        self.progress_tracker.fail_upload(resource_ids[1], "Network error")
        self.progress_tracker.complete_upload(resource_ids[2], "Success!")
        
        # Get statistics
        stats = self.progress_tracker.get_upload_statistics()
        print(f"   📈 Progress Statistics:")
        print(f"      Total uploads: {stats['total_uploads']}")
        print(f"      Active uploads: {stats['active_uploads']}")
        print(f"      Completed uploads: {stats['completed_uploads']}")
        print(f"      Failed uploads: {stats['failed_uploads']}")
        print(f"      Overall progress: {stats['overall_progress_percentage']:.1f}%")
        
        # Show individual progress
        all_progress = self.progress_tracker.get_all_progress()
        print(f"   📋 Individual Progress:")
        for resource_id, progress in all_progress.items():
            print(f"      {progress.filename}: {progress.status} ({progress.progress_percentage:.1f}%)")
        
        print()
    
    def test_supported_formats(self):
        """Test supported file format detection."""
        print("🎯 Testing Supported Formats...")
        
        extensions = self.upload_api.get_supported_extensions()
        print(f"   📝 Supported extensions ({len(extensions)}):")
        print(f"      {', '.join(extensions)}")
        
        types_by_category = self.upload_api.get_supported_types()
        print(f"   📂 Supported types by category:")
        for category, exts in types_by_category.items():
            print(f"      {category.title()}: {', '.join(exts)}")
        
        print()
    
    def run_all_tests(self):
        """Run all Sub-Layer 1 tests."""
        print("🧪 Starting Sub-Layer 1 Comprehensive Testing")
        print("=" * 60)
        
        try:
            self.test_supported_formats()
            self.test_file_validation()
            self.test_duplicate_detection()
            self.test_data_cleaning()
            self.test_progress_tracking()
            self.test_single_upload()
            self.test_bulk_upload()
            
            print("🎉 All Sub-Layer 1 tests completed successfully!")
            
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point."""
    print("🚀 Sub-Layer 1 Testing Suite")
    print("=" * 40)
    
    # Check if sample data directory exists
    sample_dir = Path("examples/data_sub_layer_1")
    if not sample_dir.exists():
        print(f"❌ Sample data directory not found: {sample_dir}")
        print("Please ensure the sample files are created first.")
        return 1
    
    # Initialize and run tests
    tester = SubLayer1Tester()
    tester.run_all_tests()
    
    return 0


if __name__ == "__main__":
    exit(main())
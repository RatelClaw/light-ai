#!/usr/bin/env python3
"""
Basic functionality test for Universal Data Handler setup.

This script tests that the basic setup works correctly.
"""

import os
import tempfile
from pathlib import Path

# Set a test API key to avoid validation errors
os.environ['OPENROUTER_API_KEY'] = 'test-key-for-setup-verification'

from light_ai import Config, setup_logger

def test_basic_setup():
    """Test basic setup functionality."""
    print("Testing Universal Data Handler setup...")
    
    # Test configuration loading
    print("✓ Testing configuration loading...")
    config = Config.load()
    print(f"  - API key configured: {'Yes' if config.openrouter.api_key else 'No'}")
    print(f"  - Default model: {config.openrouter.default_model}")
    print(f"  - Max file size: {config.storage.max_file_size_mb}MB")
    print(f"  - Log level: {config.logging.level}")
    
    # Test directory creation
    print("✓ Testing directory creation...")
    with tempfile.TemporaryDirectory() as temp_dir:
        config.storage.base_directory = temp_dir
        config.create_directories()
        
        expected_dirs = [
            "data/structured", "data/json", "data/unstructured",
            "data/raw", "metadata", "cache", "logs"
        ]
        
        for dir_name in expected_dirs:
            dir_path = Path(temp_dir) / dir_name
            if dir_path.exists():
                print(f"  - Created: {dir_name}")
            else:
                print(f"  - ERROR: Failed to create {dir_name}")
                return False
    
    # Test logger setup
    print("✓ Testing logger setup...")
    logger = setup_logger("test_logger", config)
    print(f"  - Logger name: {logger.name}")
    print(f"  - Logger level: {logger.level}")
    print(f"  - Handler count: {len(logger.handlers)}")
    
    # Test logging
    logger.info("Test log message from setup verification")
    print("  - Test log message sent")
    
    print("\n🎉 All basic setup tests passed!")
    return True

if __name__ == "__main__":
    try:
        success = test_basic_setup()
        if success:
            print("\n✅ Universal Data Handler setup is working correctly!")
        else:
            print("\n❌ Setup verification failed!")
            exit(1)
    except Exception as e:
        print(f"\n❌ Setup verification failed with error: {e}")
        exit(1)
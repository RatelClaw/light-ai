"""
Unit tests for project setup components.

Tests package imports, dependency availability, configuration loading, and logging system.
"""

import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open
import pytest

import light_ai
from light_ai.config import Config, OpenRouterConfig, get_config, set_config
from light_ai.logger import setup_logger, get_logger


class TestPackageImports:
    """Test package imports and dependency availability."""
    
    def test_main_package_import(self):
        """Test that main package imports successfully."""
        assert hasattr(light_ai, '__version__')
        assert hasattr(light_ai, 'Config')
        assert hasattr(light_ai, 'setup_logger')
    
    def test_version_format(self):
        """Test that version follows semantic versioning."""
        version = light_ai.__version__
        assert isinstance(version, str)
        assert len(version.split('.')) >= 2  # At least major.minor
    
    def test_core_dependencies_available(self):
        """Test that core dependencies can be imported."""
        # Test database dependencies
        try:
            import duckdb
            import chromadb
            import sqlite3
        except ImportError as e:
            pytest.fail(f"Core database dependency missing: {e}")
        
        # Test data processing dependencies
        try:
            import pandas
            import yaml
        except ImportError as e:
            pytest.fail(f"Core processing dependency missing: {e}")
        
        # Test OpenRouter dependencies
        try:
            import openai
            import httpx
        except ImportError as e:
            pytest.fail(f"OpenRouter dependency missing: {e}")


class TestConfigurationLoading:
    """Test configuration loading and validation."""
    
    def setup_method(self):
        """Set up test environment."""
        # Clear any existing global config
        set_config(None)
        
        # Clear environment variables that might interfere
        self.original_env = {}
        env_vars = [
            'OPENROUTER_API_KEY', 'OPENROUTER_BASE_URL', 'OPENROUTER_DEFAULT_MODEL',
            'LIGHT_AI_BASE_DIR', 'LIGHT_AI_MAX_FILE_SIZE_MB', 'LIGHT_AI_LOG_LEVEL'
        ]
        for var in env_vars:
            if var in os.environ:
                self.original_env[var] = os.environ[var]
                del os.environ[var]
    
    def teardown_method(self):
        """Clean up test environment."""
        # Restore original environment variables
        for var, value in self.original_env.items():
            os.environ[var] = value
        
        # Clear global config
        set_config(None)
    
    def test_default_config_creation(self):
        """Test creating config with default values."""
        # Set required API key
        os.environ['OPENROUTER_API_KEY'] = 'test-key'
        
        config = Config.load()
        
        assert config.openrouter.api_key == 'test-key'
        assert config.openrouter.base_url == 'https://openrouter.ai/api/v1'
        assert config.storage.max_file_size_mb == 500
        assert config.processing.chunk_size_tokens == 512
        assert config.logging.level == 'INFO'
    
    def test_config_from_environment_variables(self):
        """Test loading configuration from environment variables."""
        # Set environment variables
        os.environ['OPENROUTER_API_KEY'] = 'env-test-key'
        os.environ['OPENROUTER_BASE_URL'] = 'https://custom.api.url'
        os.environ['LIGHT_AI_MAX_FILE_SIZE_MB'] = '1000'
        os.environ['LIGHT_AI_LOG_LEVEL'] = 'DEBUG'
        
        config = Config.load()
        
        assert config.openrouter.api_key == 'env-test-key'
        assert config.openrouter.base_url == 'https://custom.api.url'
        assert config.storage.max_file_size_mb == 1000
        assert config.logging.level == 'DEBUG'
    
    def test_config_from_yaml_file(self):
        """Test loading configuration from YAML file."""
        yaml_content = {
            'openrouter': {
                'api_key': 'yaml-test-key',
                'default_model': 'custom-model'
            },
            'storage': {
                'max_file_size_mb': 750
            },
            'logging': {
                'level': 'WARNING'
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(yaml_content, f)
            yaml_path = f.name
        
        try:
            config = Config.load(yaml_path)
            
            assert config.openrouter.api_key == 'yaml-test-key'
            assert config.openrouter.default_model == 'custom-model'
            assert config.storage.max_file_size_mb == 750
            assert config.logging.level == 'WARNING'
        finally:
            os.unlink(yaml_path)
    
    def test_environment_overrides_yaml(self):
        """Test that environment variables override YAML configuration."""
        yaml_content = {
            'openrouter': {
                'api_key': 'yaml-key'
            },
            'storage': {
                'max_file_size_mb': 750
            }
        }
        
        # Set environment variable that should override YAML
        os.environ['OPENROUTER_API_KEY'] = 'env-override-key'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(yaml_content, f)
            yaml_path = f.name
        
        try:
            config = Config.load(yaml_path)
            
            # Environment should override YAML
            assert config.openrouter.api_key == 'env-override-key'
            # YAML value should still be used where no env override
            assert config.storage.max_file_size_mb == 750
        finally:
            os.unlink(yaml_path)
    
    def test_missing_api_key_raises_error(self):
        """Test that missing OpenRouter API key raises ValueError."""
        with pytest.raises(ValueError, match="OpenRouter API key is required"):
            Config.load()
    
    def test_invalid_log_level_raises_error(self):
        """Test that invalid log level raises ValueError."""
        os.environ['OPENROUTER_API_KEY'] = 'test-key'
        os.environ['LIGHT_AI_LOG_LEVEL'] = 'INVALID'
        
        with pytest.raises(ValueError, match="Invalid log level"):
            Config.load()
    
    def test_invalid_file_size_raises_error(self):
        """Test that invalid file size raises ValueError."""
        yaml_content = {
            'openrouter': {'api_key': 'test-key'},
            'storage': {'max_file_size_mb': -1}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(yaml_content, f)
            yaml_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Max file size must be positive"):
                Config.load(yaml_path)
        finally:
            os.unlink(yaml_path)
    
    def test_nonexistent_config_file_raises_error(self):
        """Test that nonexistent config file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            Config.load("/nonexistent/config.yaml")
    
    def test_get_full_path(self):
        """Test getting full path relative to base directory."""
        os.environ['OPENROUTER_API_KEY'] = 'test-key'
        config = Config.load()
        config.storage.base_directory = "/base"
        
        full_path = config.get_full_path("data/test")
        assert str(full_path) == "/base/data/test"
    
    def test_create_directories(self):
        """Test directory creation."""
        os.environ['OPENROUTER_API_KEY'] = 'test-key'
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config.load()
            config.storage.base_directory = temp_dir
            
            config.create_directories()
            
            # Check that all directories were created
            expected_dirs = [
                "data/structured", "data/json", "data/unstructured",
                "data/raw", "metadata", "cache", "logs"
            ]
            
            for dir_name in expected_dirs:
                dir_path = Path(temp_dir) / dir_name
                assert dir_path.exists()
                assert dir_path.is_dir()


class TestLoggingSystem:
    """Test logging system functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        # Clear any existing global config
        set_config(None)
        # Clear environment variables
        if 'OPENROUTER_API_KEY' in os.environ:
            del os.environ['OPENROUTER_API_KEY']
    
    def teardown_method(self):
        """Clean up test environment."""
        set_config(None)
    
    def test_logger_setup_with_default_config(self):
        """Test logger setup with default configuration."""
        os.environ['OPENROUTER_API_KEY'] = 'test-key'
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config.load()
            config.storage.base_directory = temp_dir
            config.create_directories()
            
            logger = setup_logger("test_logger", config)
            
            assert logger.name == "test_logger"
            assert logger.level == getattr(__import__('logging'), config.logging.level)
            assert len(logger.handlers) >= 1  # Should have at least console handler
    
    def test_logger_file_output(self):
        """Test that logger creates log files."""
        os.environ['OPENROUTER_API_KEY'] = 'test-key'
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config.load()
            config.storage.base_directory = temp_dir
            config.logging.file_enabled = True
            config.create_directories()
            
            logger = setup_logger("test_logger", config)
            logger.info("Test log message")
            
            # Check that log file was created
            log_file = Path(temp_dir) / config.storage.logs_dir / "light_ai.log"
            assert log_file.exists()
            
            # Check that log message was written
            with open(log_file, 'r') as f:
                content = f.read()
                assert "Test log message" in content
    
    def test_logger_console_only(self):
        """Test logger with console output only."""
        os.environ['OPENROUTER_API_KEY'] = 'test-key'
        
        config = Config.load()
        config.logging.file_enabled = False
        config.logging.console_enabled = True
        
        logger = setup_logger("test_logger", config)
        
        # Should have only console handler
        assert len(logger.handlers) == 1
        assert logger.handlers[0].__class__.__name__ == 'StreamHandler'
    
    def test_logger_different_levels(self):
        """Test logger with different log levels."""
        os.environ['OPENROUTER_API_KEY'] = 'test-key'
        
        for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            config = Config.load()
            config.logging.level = level
            config.logging.file_enabled = False
            
            logger = setup_logger(f"test_logger_{level}", config)
            assert logger.level == getattr(__import__('logging'), level)
    
    def test_get_logger_creates_if_not_exists(self):
        """Test that get_logger creates logger if it doesn't exist."""
        os.environ['OPENROUTER_API_KEY'] = 'test-key'
        
        logger = get_logger("new_test_logger")
        assert logger.name == "new_test_logger"
        assert len(logger.handlers) >= 1
    
    def test_logger_prevents_duplicate_handlers(self):
        """Test that setting up logger multiple times doesn't create duplicate handlers."""
        os.environ['OPENROUTER_API_KEY'] = 'test-key'
        
        config = Config.load()
        config.logging.file_enabled = False
        config.logging.console_enabled = True
        
        logger1 = setup_logger("test_logger", config)
        initial_handler_count = len(logger1.handlers)
        
        logger2 = setup_logger("test_logger", config)  # Same name
        
        assert len(logger2.handlers) == initial_handler_count
        assert logger1 is logger2  # Should be the same logger instance
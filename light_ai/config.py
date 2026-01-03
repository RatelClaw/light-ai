"""
Configuration management system for Universal Data Handler.

Handles OpenRouter API key configuration and optional YAML config files.
Supports environment variables and configuration files.
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    duckdb_path: str = "data/duckdb/main.db"
    sqlite_path: str = "metadata/registry.db"
    chromadb_path: str = "data/unstructured/chroma_db"


@dataclass
class StorageConfig:
    """Storage configuration settings."""
    base_directory: str = "."
    structured_data_dir: str = "data/structured"
    json_data_dir: str = "data/json"
    unstructured_data_dir: str = "data/unstructured"
    raw_data_dir: str = "data/raw"
    metadata_dir: str = "metadata"
    cache_dir: str = "cache"
    logs_dir: str = "logs"
    max_file_size_mb: int = 500


@dataclass
class ProcessingConfig:
    """Data processing configuration settings."""
    chunk_size_tokens: int = 512
    chunk_overlap_tokens: int = 50
    cache_ttl_minutes: int = 5
    max_parallel_workers: int = 4
    streaming_threshold_rows: int = 10000


@dataclass
class OpenRouterConfig:
    """OpenRouter API configuration."""
    api_key: str = ""
    base_url: str = "https://openrouter.ai/api/v1"
    default_model: str = "anthropic/claude-3.5-sonnet"
    embedding_model: str = "text-embedding-3-small"
    timeout_seconds: int = 30


@dataclass
class LoggingConfig:
    """Logging configuration settings."""
    level: str = "INFO"
    file_enabled: bool = True
    console_enabled: bool = True
    max_file_size_mb: int = 10
    backup_count: int = 5


@dataclass
class Config:
    """Main configuration class for Universal Data Handler."""
    
    openrouter: OpenRouterConfig = field(default_factory=OpenRouterConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        """
        Load configuration from environment variables and optional YAML file.
        
        Args:
            config_path: Optional path to YAML configuration file
            
        Returns:
            Config instance with loaded settings
            
        Raises:
            ValueError: If OpenRouter API key is not provided
            FileNotFoundError: If specified config file doesn't exist
        """
        # Load environment variables from .env file if it exists
        load_dotenv()
        
        # Start with default configuration
        config = cls()
        
        # Load from YAML file if provided
        if config_path:
            config_file = Path(config_path)
            if not config_file.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
            with open(config_file, 'r') as f:
                yaml_config = yaml.safe_load(f)
                config._update_from_dict(yaml_config)
        
        # Override with environment variables
        config._load_from_env()
        
        # Validate required settings
        config._validate()
        
        return config
    
    def _update_from_dict(self, config_dict: Dict[str, Any]) -> None:
        """Update configuration from dictionary (YAML config)."""
        if "openrouter" in config_dict:
            or_config = config_dict["openrouter"]
            if "api_key" in or_config:
                self.openrouter.api_key = or_config["api_key"]
            if "base_url" in or_config:
                self.openrouter.base_url = or_config["base_url"]
            if "default_model" in or_config:
                self.openrouter.default_model = or_config["default_model"]
            if "embedding_model" in or_config:
                self.openrouter.embedding_model = or_config["embedding_model"]
            if "timeout_seconds" in or_config:
                self.openrouter.timeout_seconds = or_config["timeout_seconds"]
        
        if "storage" in config_dict:
            storage_config = config_dict["storage"]
            if "base_directory" in storage_config:
                self.storage.base_directory = storage_config["base_directory"]
            if "max_file_size_mb" in storage_config:
                self.storage.max_file_size_mb = storage_config["max_file_size_mb"]
        
        if "processing" in config_dict:
            proc_config = config_dict["processing"]
            if "chunk_size_tokens" in proc_config:
                self.processing.chunk_size_tokens = proc_config["chunk_size_tokens"]
            if "chunk_overlap_tokens" in proc_config:
                self.processing.chunk_overlap_tokens = proc_config["chunk_overlap_tokens"]
            if "cache_ttl_minutes" in proc_config:
                self.processing.cache_ttl_minutes = proc_config["cache_ttl_minutes"]
            if "max_parallel_workers" in proc_config:
                self.processing.max_parallel_workers = proc_config["max_parallel_workers"]
        
        if "logging" in config_dict:
            log_config = config_dict["logging"]
            if "level" in log_config:
                self.logging.level = log_config["level"]
            if "file_enabled" in log_config:
                self.logging.file_enabled = log_config["file_enabled"]
            if "console_enabled" in log_config:
                self.logging.console_enabled = log_config["console_enabled"]
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # OpenRouter configuration
        if api_key := os.getenv("OPENROUTER_API_KEY"):
            self.openrouter.api_key = api_key
        if base_url := os.getenv("OPENROUTER_BASE_URL"):
            self.openrouter.base_url = base_url
        if model := os.getenv("OPENROUTER_DEFAULT_MODEL"):
            self.openrouter.default_model = model
        if embedding_model := os.getenv("OPENROUTER_EMBEDDING_MODEL"):
            self.openrouter.embedding_model = embedding_model
        
        # Storage configuration
        if base_dir := os.getenv("LIGHT_AI_BASE_DIR"):
            self.storage.base_directory = base_dir
        if max_size := os.getenv("LIGHT_AI_MAX_FILE_SIZE_MB"):
            try:
                self.storage.max_file_size_mb = int(max_size)
            except ValueError:
                pass  # Keep default value
        
        # Logging configuration
        if log_level := os.getenv("LIGHT_AI_LOG_LEVEL"):
            self.logging.level = log_level.upper()
    
    def _validate(self) -> None:
        """Validate configuration settings."""
        if not self.openrouter.api_key:
            raise ValueError(
                "OpenRouter API key is required. Set OPENROUTER_API_KEY environment "
                "variable or provide it in configuration file."
            )
        
        # Validate log level
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.logging.level not in valid_levels:
            raise ValueError(f"Invalid log level: {self.logging.level}. Must be one of {valid_levels}")
        
        # Validate file size limit
        if self.storage.max_file_size_mb <= 0:
            raise ValueError("Max file size must be positive")
        
        # Validate processing settings
        if self.processing.chunk_size_tokens <= 0:
            raise ValueError("Chunk size must be positive")
        if self.processing.chunk_overlap_tokens < 0:
            raise ValueError("Chunk overlap cannot be negative")
        if self.processing.chunk_overlap_tokens >= self.processing.chunk_size_tokens:
            raise ValueError("Chunk overlap must be less than chunk size")
    
    def get_full_path(self, relative_path: str) -> Path:
        """Get full path relative to base directory."""
        return Path(self.storage.base_directory) / relative_path
    
    def create_directories(self) -> None:
        """Create all necessary directories."""
        directories = [
            self.storage.structured_data_dir,
            self.storage.json_data_dir,
            self.storage.unstructured_data_dir,
            self.storage.raw_data_dir,
            self.storage.metadata_dir,
            self.storage.cache_dir,
            self.storage.logs_dir,
        ]
        
        for directory in directories:
            full_path = self.get_full_path(directory)
            full_path.mkdir(parents=True, exist_ok=True)


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.load()
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config
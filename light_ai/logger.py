"""
Logging system for Universal Data Handler.

Provides configurable logging with file and console output, rotation, and proper formatting.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from .config import Config, get_config


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
            )
        return super().format(record)


def setup_logger(
    name: str = "light_ai",
    config: Optional[Config] = None
) -> logging.Logger:
    """
    Set up logger with file and console handlers.
    
    Args:
        name: Logger name
        config: Configuration object (uses global config if None)
        
    Returns:
        Configured logger instance
    """
    if config is None:
        config = get_config()
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.logging.level))
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatters
    file_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = ColoredFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler with rotation
    if config.logging.file_enabled:
        # Ensure logs directory exists
        logs_dir = config.get_full_path(config.storage.logs_dir)
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = logs_dir / "light_ai.log"
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=config.logging.max_file_size_mb * 1024 * 1024,  # Convert MB to bytes
            backupCount=config.logging.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, config.logging.level))
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Console handler
    if config.logging.console_enabled:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, config.logging.level))
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: str = "light_ai") -> logging.Logger:
    """
    Get a logger instance. Creates it if it doesn't exist.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    # If logger has no handlers, set it up
    if not logger.handlers:
        return setup_logger(name)
    
    return logger


# Create module-level logger
logger = get_logger(__name__)
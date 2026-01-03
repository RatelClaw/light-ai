"""
Universal Data Handler - Light AI Data Management Layer

A comprehensive on-premises data management system that provides automated ingestion,
cleaning, storage, and intelligent retrieval of multi-format data.
"""

__version__ = "0.1.0"
__author__ = "Light AI Team"

# Import main components for easy access
from .config import Config
from .logger import setup_logger
from .api import UniversalDataHandler, APIResponse, create_api

__all__ = ["Config", "setup_logger", "UniversalDataHandler", "APIResponse", "create_api", "__version__"]
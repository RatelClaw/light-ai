"""
Basic tests for Comprehensive API Layer v2.

Simple tests to validate core functionality without complex setup.
"""

import pytest
import uuid
from unittest.mock import Mock, AsyncMock, patch

from fastapi.testclient import TestClient
from light_ai.config import Config


def test_api_creation():
    """Test that the API can be created successfully."""
    from light_ai.api_v2 import create_comprehensive_api
    
    config = Config.load()
    app = create_comprehensive_api(config)
    
    assert app.title == "Intelligent AI Data Analyst API v2"
    assert app.version == "2.0.0"


def test_simple_rate_limiter():
    """Test the simple rate limiter functionality."""
    from light_ai.api_v2 import SimpleRateLimiter
    
    limiter = SimpleRateLimiter()
    
    # Test that requests are allowed initially
    assert limiter.is_allowed("test_key", "analysis") is True
    assert limiter.is_allowed("test_key", "analysis") is True
    
    # Test different endpoints have different limits
    assert limiter.is_allowed("test_key2", "health") is True


def test_security_validator():
    """Test security validation functionality."""
    from light_ai.api_v2 import SecurityValidator
    
    validator = SecurityValidator()
    
    # Test valid JSON payload
    valid_payload = {"key": "value", "nested": {"data": [1, 2, 3]}}
    assert validator.validate_json_payload(valid_payload) is True
    
    # Test header sanitization
    headers = {
        "Content-Type": "application/json",
        "X-Custom-Header": "safe_value"
    }
    
    sanitized = validator.sanitize_headers(headers)
    assert "content-type" in sanitized
    assert "x-custom-header" in sanitized


def test_connection_manager():
    """Test WebSocket connection manager."""
    from light_ai.api_v2 import ConnectionManager
    
    manager = ConnectionManager()
    
    # Test initial state
    connections = manager.get_active_connections()
    assert isinstance(connections, dict)
    assert len(connections) == 0


def test_api_response_model():
    """Test API response model."""
    from light_ai.api_v2 import APIResponse
    
    # Test successful response
    response = APIResponse(
        success=True,
        data={"result": "test"},
        metadata={"operation": "test"}
    )
    
    assert response.success is True
    assert response.data == {"result": "test"}
    assert response.metadata == {"operation": "test"}
    assert response.timestamp is not None
    
    # Test error response
    error_response = APIResponse(
        success=False,
        error="Test error",
        metadata={"operation": "test"}
    )
    
    assert error_response.success is False
    assert error_response.error == "Test error"
    assert error_response.data is None


def test_request_validation():
    """Test request validation models."""
    from light_ai.api_v2 import AnalysisAPIRequest
    
    # Test valid request
    valid_data = {
        "client_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "query": "What are the sales trends?",
        "access_level": "user"
    }
    
    request = AnalysisAPIRequest(**valid_data)
    assert request.client_id == valid_data["client_id"]
    assert request.user_id == valid_data["user_id"]
    assert request.query == valid_data["query"]
    assert request.access_level == "user"


def test_client_ip_extraction():
    """Test client IP extraction functionality."""
    from light_ai.api_v2 import get_client_ip
    from unittest.mock import Mock
    
    # Mock request with X-Forwarded-For header
    request = Mock()
    request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}
    request.client = Mock()
    request.client.host = "127.0.0.1"
    
    ip = get_client_ip(request)
    assert ip == "192.168.1.1"
    
    # Mock request without X-Forwarded-For header
    request.headers = {}
    ip = get_client_ip(request)
    assert ip == "127.0.0.1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
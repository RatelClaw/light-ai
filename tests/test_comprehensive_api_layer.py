"""
Tests for Comprehensive API Layer v2.

Tests RESTful API endpoints, WebSocket functionality, streaming capabilities,
request validation, and rate limiting.
"""

import pytest
import asyncio
import json
import uuid
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from fastapi.testclient import TestClient
from fastapi import FastAPI
import websockets

from light_ai.api_v2 import create_comprehensive_api, APIResponse, AnalysisAPIRequest
from light_ai.config import Config
from light_ai.core.models import AccessLevel


class TestComprehensiveAPILayer:
    """Test suite for comprehensive API layer."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config.load()
    
    @pytest.fixture
    def app(self, config):
        """Create test FastAPI application."""
        return create_comprehensive_api(config)
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def sample_request_data(self):
        """Create sample request data."""
        return {
            "client_id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "query": "What are the sales trends?",
            "access_level": "user",
            "include_visualizations": True
        }
    
    def test_api_creation(self, app):
        """Test API application creation."""
        assert isinstance(app, FastAPI)
        assert app.title == "Intelligent AI Data Analyst API v2"
        assert app.version == "2.0.0"
    
    def test_health_check_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v2/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "components" in data["data"]
        assert "timestamp" in data
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint."""
        response = client.get("/api/v2/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "websocket_metrics" in data["data"]
        assert "api_metrics" in data["data"]
    
    @patch('light_ai.api_v2.app.state.master_agent')
    @patch('light_ai.api_v2.app.state.access_control')
    def test_analysis_endpoint_success(self, mock_access_control, mock_agent, client, sample_request_data):
        """Test successful analysis request."""
        # Mock access control validation
        mock_access_control.validate_user_access.return_value = True
        
        # Mock agent response
        mock_result = Mock()
        mock_result.query_id = "test_query_123"
        mock_result.user_id = sample_request_data["user_id"]
        mock_result.client_id = sample_request_data["client_id"]
        mock_result.results = [{"test": "data"}]
        mock_result.insights = ["Test insight"]
        mock_result.methodology = "Test methodology"
        mock_result.sources_used = ["test_source"]
        mock_result.confidence_score = 0.9
        mock_result.execution_time_ms = 100.0
        mock_result.follow_up_suggestions = ["Test suggestion"]
        mock_result.visualizations = None
        mock_result.field_mappings = None
        mock_result.cross_resource_synthesis = None
        
        mock_agent.analyze_data = AsyncMock(return_value=mock_result)
        
        response = client.post("/api/v2/analysis", json=sample_request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["query_id"] == "test_query_123"
        assert "execution_time_ms" in data["metadata"]
    
    def test_analysis_endpoint_validation_error(self, client):
        """Test analysis endpoint with validation error."""
        invalid_data = {
            "client_id": "invalid-uuid",
            "user_id": str(uuid.uuid4()),
            "query": ""
        }
        
        response = client.post("/api/v2/analysis", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    @patch('light_ai.api_v2.app.state.access_control')
    def test_analysis_endpoint_access_denied(self, mock_access_control, client, sample_request_data):
        """Test analysis endpoint with access denied."""
        # Mock access control to deny access
        mock_access_control.validate_user_access.return_value = False
        
        response = client.post("/api/v2/analysis", json=sample_request_data)
        assert response.status_code == 403
    
    @patch('light_ai.api_v2.app.state.master_agent')
    @patch('light_ai.api_v2.app.state.access_control')
    def test_continue_conversation_endpoint(self, mock_access_control, mock_agent, client, sample_request_data):
        """Test continue conversation endpoint."""
        # Mock access control validation
        mock_access_control.validate_user_access.return_value = True
        
        # Add conversation_id to request
        sample_request_data["conversation_id"] = str(uuid.uuid4())
        
        # Mock agent response
        mock_result = Mock()
        mock_result.query_id = "test_query_123"
        mock_result.execution_time_ms = 100.0
        mock_agent.continue_conversation = AsyncMock(return_value=mock_result)
        
        response = client.post("/api/v2/analysis/continue", json=sample_request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "conversation_id" in data["metadata"]
    
    def test_continue_conversation_missing_id(self, client, sample_request_data):
        """Test continue conversation without conversation_id."""
        response = client.post("/api/v2/analysis/continue", json=sample_request_data)
        assert response.status_code == 400
    
    @patch('light_ai.api_v2.app.state.master_agent')
    @patch('light_ai.api_v2.app.state.access_control')
    def test_streaming_analysis_endpoint(self, mock_access_control, mock_agent, client):
        """Test streaming analysis endpoint."""
        # Mock access control validation
        mock_access_control.validate_user_access.return_value = True
        
        # Mock agent response
        mock_result = Mock()
        mock_result.query_id = "test_query_123"
        mock_result.results = [{"data": i} for i in range(5)]
        mock_result.execution_time_ms = 100.0
        mock_result.sources_used = ["test_source"]
        mock_result.insights = ["Test insight"]
        mock_result.follow_up_suggestions = ["Test suggestion"]
        mock_agent.analyze_data = AsyncMock(return_value=mock_result)
        
        streaming_data = {
            "client_id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "query": "Test streaming query",
            "chunk_size": 2,
            "include_metadata": True
        }
        
        response = client.post("/api/v2/analysis/streaming", json=streaming_data)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
    
    def test_cleanup_connections_endpoint(self, client):
        """Test cleanup connections endpoint."""
        response = client.post("/api/v2/admin/connections/cleanup")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "initial_connections" in data["data"]
        assert "final_connections" in data["data"]


class TestRequestValidation:
    """Test request validation and sanitization."""
    
    def test_base_api_request_validation(self):
        """Test base API request validation."""
        # Valid request
        valid_data = {
            "client_id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4())
        }
        request = AnalysisAPIRequest(query="test query", **valid_data)
        assert request.client_id == valid_data["client_id"]
        assert request.user_id == valid_data["user_id"]
    
    def test_invalid_uuid_format(self):
        """Test invalid UUID format validation."""
        with pytest.raises(ValueError):
            AnalysisAPIRequest(
                client_id="invalid-uuid",
                user_id=str(uuid.uuid4()),
                query="test query"
            )
    
    def test_query_sanitization(self):
        """Test query sanitization."""
        # Test with dangerous characters
        dangerous_query = "SELECT * FROM users WHERE id = '<script>alert(1)</script>'"
        request = AnalysisAPIRequest(
            client_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            query=dangerous_query
        )
        
        # Should remove dangerous characters
        assert "<script>" not in request.query
        assert "alert(1)" not in request.query
    
    def test_empty_query_validation(self):
        """Test empty query validation."""
        with pytest.raises(ValueError):
            AnalysisAPIRequest(
                client_id=str(uuid.uuid4()),
                user_id=str(uuid.uuid4()),
                query=""
            )
    
    def test_access_level_validation(self):
        """Test access level validation."""
        with pytest.raises(ValueError):
            AnalysisAPIRequest(
                client_id=str(uuid.uuid4()),
                user_id=str(uuid.uuid4()),
                query="test query",
                access_level="invalid_level"
            )


class TestSecurityValidator:
    """Test security validation functionality."""
    
    def test_validate_json_payload(self):
        """Test JSON payload validation."""
        from light_ai.api_v2 import SecurityValidator
        
        validator = SecurityValidator()
        
        # Valid payload
        valid_payload = {"key": "value", "nested": {"data": [1, 2, 3]}}
        assert validator.validate_json_payload(valid_payload) is True
        
        # Invalid payload (too deep nesting)
        deep_payload = {"level1": {"level2": {"level3": {"level4": {"level5": {
            "level6": {"level7": {"level8": {"level9": {"level10": {
                "level11": "too deep"
            }}}}}}}}}}}
        assert validator.validate_json_payload(deep_payload) is False
    
    def test_sanitize_headers(self):
        """Test header sanitization."""
        from light_ai.api_v2 import SecurityValidator
        
        validator = SecurityValidator()
        
        headers = {
            "Content-Type": "application/json",
            "X-Custom-Header": "safe_value",
            "Dangerous<Script>": "alert('xss')",
            "": "empty_key"
        }
        
        sanitized = validator.sanitize_headers(headers)
        
        assert "content-type" in sanitized
        assert "x-custom-header" in sanitized
        assert "dangerous" in sanitized  # Script tags removed
        assert "" not in sanitized  # Empty keys removed


class TestConnectionManager:
    """Test WebSocket connection management."""
    
    @pytest.fixture
    def connection_manager(self):
        """Create connection manager instance."""
        from light_ai.api_v2 import ConnectionManager
        return ConnectionManager()
    
    @pytest.mark.asyncio
    async def test_connection_lifecycle(self, connection_manager):
        """Test connection lifecycle management."""
        # Mock WebSocket
        mock_websocket = Mock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_json = AsyncMock()
        
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Test connection
        connection_id = await connection_manager.connect(mock_websocket, client_id, user_id)
        assert connection_id in connection_manager.active_connections
        assert connection_id in connection_manager.connection_metadata
        
        # Test sending message
        test_message = {"type": "test", "data": {"message": "hello"}}
        await connection_manager.send_personal_message(test_message, connection_id)
        mock_websocket.send_json.assert_called_once_with(test_message)
        
        # Test disconnection
        connection_manager.disconnect(connection_id)
        assert connection_id not in connection_manager.active_connections
        assert connection_id not in connection_manager.connection_metadata
    
    def test_get_active_connections(self, connection_manager):
        """Test getting active connections."""
        connections = connection_manager.get_active_connections()
        assert isinstance(connections, dict)
    
    @pytest.mark.asyncio
    async def test_broadcast_to_user(self, connection_manager):
        """Test broadcasting to user connections."""
        # Mock multiple WebSockets for same user
        mock_ws1 = Mock()
        mock_ws1.accept = AsyncMock()
        mock_ws1.send_json = AsyncMock()
        
        mock_ws2 = Mock()
        mock_ws2.accept = AsyncMock()
        mock_ws2.send_json = AsyncMock()
        
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Connect multiple WebSockets for same user
        conn_id1 = await connection_manager.connect(mock_ws1, client_id, user_id)
        conn_id2 = await connection_manager.connect(mock_ws2, client_id, user_id)
        
        # Broadcast message
        test_message = {"type": "broadcast", "data": {"message": "hello all"}}
        await connection_manager.broadcast_to_user(test_message, client_id, user_id)
        
        # Both WebSockets should receive the message
        mock_ws1.send_json.assert_called_once_with(test_message)
        mock_ws2.send_json.assert_called_once_with(test_message)


class TestAPIResponse:
    """Test API response formatting."""
    
    def test_api_response_success(self):
        """Test successful API response."""
        response = APIResponse(
            success=True,
            data={"result": "test"},
            metadata={"operation": "test"}
        )
        
        assert response.success is True
        assert response.data == {"result": "test"}
        assert response.metadata == {"operation": "test"}
        assert response.timestamp is not None
    
    def test_api_response_error(self):
        """Test error API response."""
        response = APIResponse(
            success=False,
            error="Test error message",
            metadata={"operation": "test"}
        )
        
        assert response.success is False
        assert response.error == "Test error message"
        assert response.data is None
        assert response.metadata == {"operation": "test"}


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limit_configuration(self):
        """Test rate limit configuration."""
        from light_ai.api_v2 import RATE_LIMITS
        
        assert "analysis" in RATE_LIMITS
        assert "streaming" in RATE_LIMITS
        assert "websocket" in RATE_LIMITS
        assert "health" in RATE_LIMITS
        assert "default" in RATE_LIMITS
    
    @patch('light_ai.api_v2.app.state.access_control')
    def test_rate_limit_enforcement(self, mock_access_control, client, sample_request_data):
        """Test rate limit enforcement (simplified test)."""
        # Mock access control validation
        mock_access_control.validate_user_access.return_value = True
        
        # This is a simplified test - in practice, rate limiting would need
        # multiple rapid requests to trigger
        response = client.post("/api/v2/analysis", json=sample_request_data)
        
        # Should not be rate limited on first request
        assert response.status_code != 429


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
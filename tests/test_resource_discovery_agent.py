"""
Minimal tests for Resource Discovery Agent.

Tests basic functionality without extensive test coverage.
"""

import pytest
import uuid
from unittest.mock import Mock, patch
from datetime import datetime

from light_ai.agents.resource_discovery_agent import ResourceDiscoveryAgent
from light_ai.core.models import ResourceMetadata, ResourceType, DataType
from light_ai.config import get_config


class TestResourceDiscoveryAgent:
    """Minimal test cases for Resource Discovery Agent."""
    
    @pytest.fixture
    def config(self):
        """Get test configuration."""
        return get_config()
    
    @pytest.fixture
    def sample_resource(self):
        """Sample resource for testing."""
        return ResourceMetadata(
            resource_id=str(uuid.uuid4()),
            user_id="test-user",
            client_id="test-client",
            resource_type=ResourceType.STRUCTURED,
            data_type=DataType.CSV,
            original_filename="test_data.csv",
            file_size_bytes=1024,
            storage_path="/test/path",
            row_count=100,
            column_count=5
        )
    
    def test_agent_initialization(self, config):
        """Test agent can be initialized."""
        with patch('light_ai.agents.resource_discovery_agent.OpenAI'):
            agent = ResourceDiscoveryAgent(config)
            assert agent is not None
            assert agent.agent_config.name == "resource_discovery_agent"
    
    def test_semantic_type_inference(self, config):
        """Test semantic type inference."""
        with patch('light_ai.agents.resource_discovery_agent.OpenAI'):
            agent = ResourceDiscoveryAgent(config)
            
            # Test email detection
            email_type = agent._infer_semantic_type("email_address", ["test@example.com"])
            assert email_type == "email"
            
            # Test name detection
            name_type = agent._infer_semantic_type("customer_name", ["John Doe"])
            assert name_type == "name"
            
            # Test general fallback
            general_type = agent._infer_semantic_type("unknown_field", ["some_value"])
            assert general_type == "general"
    
    def test_field_pattern_detection(self, config):
        """Test field pattern detection."""
        with patch('light_ai.agents.resource_discovery_agent.OpenAI'):
            agent = ResourceDiscoveryAgent(config)
            
            # Test email pattern
            email_patterns = agent._detect_field_patterns(["test@example.com", "user@domain.org"])
            assert "email_format" in email_patterns
            
            # Test UUID pattern
            uuid_patterns = agent._detect_field_patterns([str(uuid.uuid4()), str(uuid.uuid4())])
            assert "uuid_format" in uuid_patterns
    
    def test_field_quality_calculation(self, config):
        """Test field quality score calculation."""
        with patch('light_ai.agents.resource_discovery_agent.OpenAI'):
            agent = ResourceDiscoveryAgent(config)
            
            # High quality field
            high_quality = agent._calculate_field_quality({
                "null_percentage": 0.1,
                "type_consistency": 0.95,
                "unique_values": 50,
                "total_values": 100
            })
            assert high_quality > 0.7
            
            # Low quality field
            low_quality = agent._calculate_field_quality({
                "null_percentage": 0.8,
                "type_consistency": 0.5,
                "unique_values": 5,
                "total_values": 100
            })
            assert low_quality < 0.5
    
    @patch('light_ai.agents.resource_discovery_agent.OpenAI')
    def test_catalog_data_sources_no_resources(self, mock_openai, config):
        """Test cataloging when no resources exist."""
        agent = ResourceDiscoveryAgent(config)
        
        with patch.object(agent.metadata_registry, 'list_resources', return_value=[]):
            result = agent.catalog_data_sources("test-client", "test-user")
            
            # Should handle empty resource list gracefully
            assert "catalog" in result
            assert result["catalog"] == []
            assert result["summary"]["total_resources"] == 0


if __name__ == "__main__":
    pytest.main([__file__])
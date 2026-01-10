"""
Tests for Cross-Resource Synthesis Agent.

Tests the AI agent's ability to synthesize data from multiple sources,
resolve schema conflicts, and create unified views with lineage tracking.
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from light_ai.agents.cross_resource_synthesis_agent import (
    CrossResourceSynthesisAgent, JoinStrategy, SynthesisStrategy,
    JoinCondition, SchemaConflict, DataTypeHarmonization, UnifiedView
)
from light_ai.core.models import ResourceMetadata, ResourceType, DataType
from light_ai.config import Config


@pytest.fixture
def mock_config():
    """Create mock configuration."""
    config = Mock(spec=Config)
    config.openrouter = Mock()
    config.openrouter.default_model = "anthropic/claude-3.5-sonnet"
    config.openrouter.api_key = "test-key"
    config.openrouter.base_url = "https://openrouter.ai/api/v1"
    config.logging = Mock()
    config.logging.level = "INFO"
    return config


@pytest.fixture
def sample_resources():
    """Create sample resource metadata for testing."""
    import uuid
    return [
        ResourceMetadata(
            resource_id=str(uuid.uuid4()),
            user_id="test-user",
            client_id="test-client",
            resource_type=ResourceType.STRUCTURED,
            data_type=DataType.CSV,
            original_filename="customers.csv",
            file_size_bytes=1024,
            storage_path="/data/customers.csv",
            row_count=100,
            column_count=5,
            processing_status="completed"
        ),
        ResourceMetadata(
            resource_id=str(uuid.uuid4()),
            user_id="test-user",
            client_id="test-client",
            resource_type=ResourceType.STRUCTURED,
            data_type=DataType.CSV,
            original_filename="orders.csv",
            file_size_bytes=2048,
            storage_path="/data/orders.csv",
            row_count=200,
            column_count=6,
            processing_status="completed"
        )
    ]


@pytest.fixture
def synthesis_agent(mock_config):
    """Create synthesis agent with mocked dependencies."""
    with patch('light_ai.agents.cross_resource_synthesis_agent.MetadataRegistry'), \
         patch('light_ai.agents.cross_resource_synthesis_agent.StorageRouter'), \
         patch('light_ai.agents.cross_resource_synthesis_agent.DatabaseManagers'), \
         patch('light_ai.agents.cross_resource_synthesis_agent.get_activity_logger'):
        
        agent = CrossResourceSynthesisAgent(mock_config)
        
        # Mock the execute method to avoid actual AI calls
        agent.execute = Mock(return_value="Mocked AI response for synthesis analysis")
        
        return agent


class TestCrossResourceSynthesisAgent:
    """Test cases for Cross-Resource Synthesis Agent."""
    
    def test_agent_initialization(self, mock_config):
        """Test agent initializes correctly."""
        with patch('light_ai.agents.cross_resource_synthesis_agent.MetadataRegistry'), \
             patch('light_ai.agents.cross_resource_synthesis_agent.StorageRouter'), \
             patch('light_ai.agents.cross_resource_synthesis_agent.DatabaseManagers'), \
             patch('light_ai.agents.cross_resource_synthesis_agent.get_activity_logger'):
            
            agent = CrossResourceSynthesisAgent(mock_config)
            
            assert agent.agent_config.name == "cross_resource_synthesis_agent"
            assert agent.agent_config.model_name == "anthropic/claude-3.5-sonnet"
            assert agent.agent_config.temperature == 0.2
            assert not agent._initialized
    
    def test_agent_initialization_with_system_prompt(self, synthesis_agent):
        """Test agent has comprehensive system prompt."""
        system_prompt = synthesis_agent.agent_config.system_prompt
        
        # Check for key capabilities in system prompt
        assert "Cross-Resource Synthesis Agent" in system_prompt
        assert "multi-source data combination" in system_prompt
        assert "schema conflicts" in system_prompt
        assert "join strategies" in system_prompt
        assert "lineage tracking" in system_prompt
    
    def test_validate_and_get_resources_success(self, synthesis_agent, sample_resources):
        """Test successful resource validation and retrieval."""
        # Mock metadata registry
        synthesis_agent.metadata_registry.get_resource_metadata = Mock(side_effect=sample_resources)
        
        resource_ids = [sample_resources[0].resource_id, sample_resources[1].resource_id]
        
        # Use asyncio.run for async test
        import asyncio
        result = asyncio.run(synthesis_agent._validate_and_get_resources(
            "test-client", "test-user", resource_ids
        ))
        
        assert len(result) == 2
        assert result[0].resource_id == sample_resources[0].resource_id
        assert result[1].resource_id == sample_resources[1].resource_id
    
    def test_validate_and_get_resources_access_denied(self, synthesis_agent):
        """Test resource validation with access denied."""
        import uuid
        # Mock resource with different user
        wrong_user_resource = ResourceMetadata(
            resource_id=str(uuid.uuid4()),
            user_id="other-user",  # Different user
            client_id="test-client",
            resource_type=ResourceType.STRUCTURED,
            data_type=DataType.CSV,
            original_filename="test.csv",
            file_size_bytes=1024,
            storage_path="/data/test.csv",
            processing_status="completed"
        )
        
        synthesis_agent.metadata_registry.get_resource_metadata = Mock(return_value=wrong_user_resource)
        
        import asyncio
        with pytest.raises(ValueError, match="Access denied"):
            asyncio.run(synthesis_agent._validate_and_get_resources(
                "test-client", "test-user", [wrong_user_resource.resource_id]
            ))
    
    def test_analyze_structured_schema(self, synthesis_agent, sample_resources):
        """Test structured schema analysis."""
        # Mock schema info
        mock_schema_info = Mock()
        mock_schema_info.schema_json = json.dumps({
            "columns": {
                "customer_id": {
                    "type": "integer",
                    "nullable": False,
                    "unique_values": 100,
                    "sample_values": [1, 2, 3]
                },
                "customer_name": {
                    "type": "string",
                    "nullable": False,
                    "unique_values": 95,
                    "sample_values": ["John Doe", "Jane Smith", "Bob Wilson"]
                }
            }
        })
        
        synthesis_agent.metadata_registry.get_schema_info = Mock(return_value=mock_schema_info)
        
        import asyncio
        result = asyncio.run(synthesis_agent._analyze_structured_schema(sample_resources[0]))
        
        assert "fields" in result
        assert "customer_id" in result["fields"]
        assert "customer_name" in result["fields"]
        assert result["fields"]["customer_id"]["type"] == "integer"
        assert result["fields"]["customer_name"]["semantic_type"] == "name"
        assert result["metadata"]["resource_type"] == "structured"
    
    def test_infer_semantic_type_name_fields(self, synthesis_agent):
        """Test semantic type inference for name fields."""
        assert synthesis_agent._infer_semantic_type("customer_name", ["John Doe"]) == "name"
        assert synthesis_agent._infer_semantic_type("full_name", ["Jane Smith"]) == "name"
        assert synthesis_agent._infer_semantic_type("title", ["Manager"]) == "name"
    
    def test_infer_semantic_type_email_fields(self, synthesis_agent):
        """Test semantic type inference for email fields."""
        assert synthesis_agent._infer_semantic_type("email", ["test@example.com"]) == "email"
        assert synthesis_agent._infer_semantic_type("email_address", []) == "email"
        assert synthesis_agent._infer_semantic_type("contact_email", ["user@domain.com"]) == "email"
    
    def test_infer_semantic_type_identifier_fields(self, synthesis_agent):
        """Test semantic type inference for identifier fields."""
        assert synthesis_agent._infer_semantic_type("customer_id", [1, 2, 3]) == "identifier"
        assert synthesis_agent._infer_semantic_type("uuid", ["123e4567-e89b-12d3-a456-426614174000"]) == "identifier"
        assert synthesis_agent._infer_semantic_type("primary_key", []) == "identifier"
    
    def test_analyze_field_conflict_data_type(self, synthesis_agent):
        """Test field conflict analysis for data type conflicts."""
        field_instances = [
            {
                "resource_id": "resource-1",
                "field_info": {
                    "type": "integer",
                    "semantic_type": "identifier",
                    "sample_values": [1, 2, 3]
                }
            },
            {
                "resource_id": "resource-2", 
                "field_info": {
                    "type": "string",
                    "semantic_type": "identifier",
                    "sample_values": ["ID001", "ID002", "ID003"]
                }
            }
        ]
        
        conflict = synthesis_agent._analyze_field_conflict("customer_id", field_instances)
        
        assert conflict is not None
        assert conflict.conflict_type == "data_type"
        assert len(conflict.resource_ids) == 2
        assert "integer" in conflict.data_types
        assert "string" in conflict.data_types
    
    def test_analyze_field_conflict_no_conflict(self, synthesis_agent):
        """Test field conflict analysis when no conflict exists."""
        field_instances = [
            {
                "resource_id": "resource-1",
                "field_info": {
                    "type": "string",
                    "semantic_type": "name",
                    "sample_values": ["John", "Jane"]
                }
            },
            {
                "resource_id": "resource-2",
                "field_info": {
                    "type": "string", 
                    "semantic_type": "name",
                    "sample_values": ["Bob", "Alice"]
                }
            }
        ]
        
        conflict = synthesis_agent._analyze_field_conflict("customer_name", field_instances)
        
        assert conflict is None
    
    def test_determine_resolution_strategy_data_type(self, synthesis_agent):
        """Test resolution strategy determination for data type conflicts."""
        conflict = SchemaConflict(
            conflict_id="test-conflict",
            conflict_type="data_type",
            resource_ids=["resource-1", "resource-2"],
            field_names=["customer_id"],
            data_types=["integer", "string"],
            sample_values=[[1, 2], ["ID001", "ID002"]]
        )
        
        strategy = synthesis_agent._determine_resolution_strategy(conflict)
        assert strategy == "cast_to_string"
    
    def test_determine_resolution_strategy_numeric_types(self, synthesis_agent):
        """Test resolution strategy for numeric type conflicts."""
        conflict = SchemaConflict(
            conflict_id="test-conflict",
            conflict_type="data_type",
            resource_ids=["resource-1", "resource-2"],
            field_names=["amount"],
            data_types=["integer", "float"],
            sample_values=[[100, 200], [100.5, 200.7]]
        )
        
        strategy = synthesis_agent._determine_resolution_strategy(conflict)
        assert strategy == "cast_to_numeric"
    
    def test_generate_resolution_logic(self, synthesis_agent):
        """Test resolution logic generation."""
        conflict = SchemaConflict(
            conflict_id="test-conflict",
            conflict_type="data_type",
            resource_ids=["resource-1"],
            field_names=["test_field"],
            data_types=["integer"],
            sample_values=[[1, 2, 3]],
            resolution_strategy="cast_to_string"
        )
        
        logic = synthesis_agent._generate_resolution_logic(conflict)
        assert "CAST(test_field AS VARCHAR(255))" == logic
    
    def test_determine_target_type_string_priority(self, synthesis_agent):
        """Test target type determination prioritizes string types."""
        source_types = ["integer", "string", "float"]
        target_type = synthesis_agent._determine_target_type(source_types)
        assert target_type == "varchar"
    
    def test_determine_target_type_numeric_fallback(self, synthesis_agent):
        """Test target type determination for numeric types."""
        source_types = ["integer", "float", "decimal"]
        target_type = synthesis_agent._determine_target_type(source_types)
        assert target_type == "decimal"
    
    def test_assess_precision_loss_mixed_types(self, synthesis_agent):
        """Test precision loss assessment for mixed types."""
        source_types = ["integer", "string"]
        has_loss = synthesis_agent._assess_precision_loss(source_types)
        assert has_loss is True
    
    def test_assess_precision_loss_same_types(self, synthesis_agent):
        """Test precision loss assessment for same types."""
        source_types = ["integer", "integer"]
        has_loss = synthesis_agent._assess_precision_loss(source_types)
        assert has_loss is False
    
    def test_calculate_join_compatibility_exact_match(self, synthesis_agent):
        """Test join compatibility calculation for exact field name match."""
        field1_info = {"type": "integer", "semantic_type": "identifier"}
        field2_info = {"type": "integer", "semantic_type": "identifier"}
        
        score = synthesis_agent._calculate_join_compatibility(
            "customer_id", field1_info, "customer_id", field2_info
        )
        
        assert score >= 0.9  # High score for exact match
    
    def test_calculate_join_compatibility_semantic_match(self, synthesis_agent):
        """Test join compatibility for semantic type match."""
        field1_info = {"type": "string", "semantic_type": "identifier"}
        field2_info = {"type": "string", "semantic_type": "identifier"}
        
        score = synthesis_agent._calculate_join_compatibility(
            "cust_id", field1_info, "customer_key", field2_info
        )
        
        assert score > 0.3  # Should have some compatibility
    
    def test_calculate_schema_similarity_identical(self, synthesis_agent):
        """Test schema similarity calculation for identical schemas."""
        schema_analysis = {
            "resource-1": {"fields": {"id": {}, "name": {}, "email": {}}},
            "resource-2": {"fields": {"id": {}, "name": {}, "email": {}}}
        }
        
        similarity = synthesis_agent._calculate_schema_similarity(schema_analysis)
        assert similarity == 1.0
    
    def test_calculate_schema_similarity_no_overlap(self, synthesis_agent):
        """Test schema similarity calculation for no field overlap."""
        schema_analysis = {
            "resource-1": {"fields": {"id": {}, "name": {}}},
            "resource-2": {"fields": {"price": {}, "quantity": {}}}
        }
        
        similarity = synthesis_agent._calculate_schema_similarity(schema_analysis)
        assert similarity == 0.0
    
    def test_estimate_unified_row_count_union(self, synthesis_agent, sample_resources):
        """Test row count estimation for union-based synthesis."""
        count = synthesis_agent._estimate_unified_row_count(
            sample_resources, SynthesisStrategy.UNION_BASED, []
        )
        
        expected = sum(r.row_count for r in sample_resources)
        assert count == expected
    
    def test_estimate_unified_row_count_join(self, synthesis_agent, sample_resources):
        """Test row count estimation for join-based synthesis."""
        join_conditions = [Mock()]  # Mock join condition
        
        count = synthesis_agent._estimate_unified_row_count(
            sample_resources, SynthesisStrategy.JOIN_BASED, join_conditions
        )
        
        # Should be less than max due to join selectivity
        max_rows = max(r.row_count for r in sample_resources)
        assert count <= max_rows
        assert count > 0
    
    def test_calculate_quality_score_no_conflicts(self, synthesis_agent):
        """Test quality score calculation with no conflicts."""
        schema_analysis = {
            "resource-1": {"fields": {"id": {}, "name": {}}},
            "resource-2": {"fields": {"id": {}, "email": {}}}
        }
        
        score = synthesis_agent._calculate_quality_score(
            schema_analysis, [], []  # No conflicts or harmonizations
        )
        
        assert score > 0.8  # Should be high with no conflicts
    
    def test_calculate_quality_score_with_conflicts(self, synthesis_agent):
        """Test quality score calculation with conflicts."""
        schema_analysis = {"resource-1": {"fields": {"id": {}}}}
        conflicts = [Mock() for _ in range(3)]  # 3 conflicts
        harmonizations = [Mock(precision_loss=True)]  # 1 harmonization with loss
        
        score = synthesis_agent._calculate_quality_score(
            schema_analysis, conflicts, harmonizations
        )
        
        assert score < 0.8  # Should be lower due to conflicts
    
    def test_assess_performance_impact_high(self, synthesis_agent, sample_resources):
        """Test performance impact assessment for high impact scenario."""
        # Create scenario with many resources and large data
        many_resources = sample_resources * 3  # 6 resources total
        
        impact = synthesis_agent._assess_performance_impact(
            many_resources, SynthesisStrategy.JOIN_BASED, 1000000
        )
        
        assert impact == "high"
    
    def test_assess_performance_impact_low(self, synthesis_agent, sample_resources):
        """Test performance impact assessment for low impact scenario."""
        impact = synthesis_agent._assess_performance_impact(
            sample_resources[:1], SynthesisStrategy.UNION_BASED, 100
        )
        
        assert impact == "low"
    
    def test_health_check_healthy(self, synthesis_agent):
        """Test health check returns healthy status."""
        import asyncio
        result = asyncio.run(synthesis_agent.health_check())
        
        assert result["status"] == "healthy"
        assert "agent_info" in result
        assert "cache_stats" in result
        assert "test_response_length" in result
    
    def test_health_check_unhealthy(self, synthesis_agent):
        """Test health check handles errors gracefully."""
        # Make execute method raise an exception
        synthesis_agent.execute = Mock(side_effect=Exception("Test error"))
        
        import asyncio
        result = asyncio.run(synthesis_agent.health_check())
        
        assert result["status"] == "unhealthy"
        assert "error" in result
        assert "Test error" in result["error"]


class TestSynthesisDataModels:
    """Test synthesis-related data models."""
    
    def test_join_condition_creation(self):
        """Test JoinCondition dataclass creation."""
        join_condition = JoinCondition(
            left_resource_id="resource-1",
            right_resource_id="resource-2",
            left_field="customer_id",
            right_field="cust_id",
            join_type=JoinStrategy.INNER_JOIN,
            confidence_score=0.85,
            data_type_compatibility=True
        )
        
        assert join_condition.left_resource_id == "resource-1"
        assert join_condition.join_type == JoinStrategy.INNER_JOIN
        assert join_condition.confidence_score == 0.85
    
    def test_schema_conflict_creation(self):
        """Test SchemaConflict dataclass creation."""
        conflict = SchemaConflict(
            conflict_id="conflict-1",
            conflict_type="data_type",
            resource_ids=["resource-1", "resource-2"],
            field_names=["customer_id"],
            data_types=["integer", "string"],
            sample_values=[[1, 2], ["ID001", "ID002"]]
        )
        
        assert conflict.conflict_id == "conflict-1"
        assert conflict.conflict_type == "data_type"
        assert len(conflict.resource_ids) == 2
    
    def test_data_type_harmonization_creation(self):
        """Test DataTypeHarmonization dataclass creation."""
        harmonization = DataTypeHarmonization(
            harmonization_id="harm-1",
            source_types=["integer", "string"],
            target_type="varchar",
            conversion_logic="CAST(field AS VARCHAR(255))",
            validation_rules=["CHECK (field IS NOT NULL)"]
        )
        
        assert harmonization.harmonization_id == "harm-1"
        assert harmonization.target_type == "varchar"
        assert len(harmonization.source_types) == 2
    
    def test_unified_view_creation(self):
        """Test UnifiedView dataclass creation."""
        unified_view = UnifiedView(
            view_id="view-1",
            view_name="Customer Orders View",
            source_resources=["resource-1", "resource-2"],
            unified_schema={"customer_id": "varchar", "order_total": "decimal"},
            synthesis_strategy=SynthesisStrategy.JOIN_BASED,
            join_conditions=[],
            field_mappings={},
            data_transformations=[],
            lineage_tracking={},
            estimated_row_count=150,
            quality_score=0.85,
            performance_impact="medium"
        )
        
        assert unified_view.view_id == "view-1"
        assert unified_view.synthesis_strategy == SynthesisStrategy.JOIN_BASED
        assert unified_view.quality_score == 0.85


if __name__ == "__main__":
    pytest.main([__file__])
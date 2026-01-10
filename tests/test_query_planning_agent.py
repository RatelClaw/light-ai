"""
Tests for Query Planning Agent.

Tests the AI agent for optimal query execution planning, cost-based optimization,
streaming and pagination strategies, parallel execution planning, and resource
allocation and management.
"""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from light_ai.agents.query_planning_agent import (
    QueryPlanningAgent, QueryPlan, ExecutionStep, ResourceRequirements,
    QueryComplexity, ExecutionStrategy, OptimizationTechnique,
    StreamingConfig, PaginationConfig, ParallelConfig, ExecutionMetrics
)
from light_ai.core.models import ResourceMetadata, ResourceType, DataType, AccessLevel
from light_ai.config import Config


@pytest.fixture
def mock_config():
    """Create mock configuration."""
    config = Mock(spec=Config)
    config.openrouter = Mock()
    config.openrouter.api_key = "test-key"
    config.openrouter.base_url = "https://openrouter.ai/api/v1"
    config.openrouter.default_model = "anthropic/claude-3.5-sonnet"
    config.logging = Mock()
    config.logging.level = "INFO"
    config.database = Mock()
    config.database.duckdb_path = ":memory:"
    config.storage = Mock()
    config.storage.base_path = "/tmp/test"
    return config


@pytest.fixture
def sample_resources():
    """Create sample resource metadata for testing."""
    return [
        ResourceMetadata(
            resource_id="resource-1",
            client_id="test-client",
            user_id="test-user",
            original_filename="sales_data.csv",
            resource_type=ResourceType.STRUCTURED,
            data_type=DataType.CSV,
            file_size_bytes=1024 * 1024,  # 1MB
            storage_path="/tmp/test/sales_data.csv",
            row_count=10000,
            column_count=5,
            chunk_count=0,
            created_at=datetime.utcnow(),
            processing_status="completed",
            version=1
        ),
        ResourceMetadata(
            resource_id="resource-2",
            client_id="test-client",
            user_id="test-user",
            original_filename="customer_data.json",
            resource_type=ResourceType.JSON,
            data_type=DataType.JSON,
            file_size_bytes=2 * 1024 * 1024,  # 2MB
            storage_path="/tmp/test/customer_data.json",
            row_count=5000,
            column_count=0,
            chunk_count=100,
            created_at=datetime.utcnow() - timedelta(days=1),
            processing_status="completed",
            version=1
        )
    ]


@pytest.fixture
def query_planning_agent(mock_config):
    """Create Query Planning Agent instance."""
    with patch('light_ai.agents.query_planning_agent.MetadataRegistry'), \
         patch('light_ai.agents.query_planning_agent.StorageRouter'), \
         patch('light_ai.agents.query_planning_agent.DatabaseManagers'), \
         patch('light_ai.agents.query_planning_agent.get_activity_logger'):
        
        agent = QueryPlanningAgent(mock_config)
        
        # Mock the OpenAI client
        agent.client = Mock()
        agent.client.chat = Mock()
        agent.client.chat.completions = Mock()
        agent.client.chat.completions.create = Mock()
        
        return agent


class TestQueryPlanningAgent:
    """Test cases for Query Planning Agent."""
    
    def test_agent_initialization(self, query_planning_agent):
        """Test agent initialization."""
        agent = query_planning_agent
        
        assert agent.agent_config.name == "query_planning_agent"
        assert agent.agent_config.temperature == 0.1
        assert agent.plan_cache == {}
        assert agent.resource_stats_cache == {}
        assert agent.optimization_history == []
        assert agent.active_executions == {}
        assert "max_memory_mb" in agent.resource_pool
    
    @pytest.mark.asyncio
    async def test_create_execution_plan_simple_query(self, query_planning_agent, sample_resources):
        """Test creating execution plan for simple query."""
        agent = query_planning_agent
        
        # Mock AI response for complexity analysis
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "complexity": "low",
            "operations": ["filtering"],
            "data_volume": "small",
            "computational_intensity": "low",
            "memory_pattern": "sequential",
            "io_pattern": "sequential_read",
            "parallelizable": False,
            "optimization_opportunities": ["predicate_pushdown"]
        })
        agent.client.chat.completions.create.return_value = mock_response
        
        # Mock metadata registry
        agent.metadata_registry.list_resources = Mock(return_value=sample_resources[:1])
        agent.metadata_registry.get_schema_info = Mock(return_value=None)
        
        # Create execution plan
        plan = await agent.create_execution_plan(
            user_id="test-user",
            client_id="test-client",
            query="SELECT * FROM sales_data WHERE amount > 100",
            query_type="analytical"
        )
        
        # Verify plan structure
        assert isinstance(plan, QueryPlan)
        assert plan.original_query == "SELECT * FROM sales_data WHERE amount > 100"
        assert plan.query_type == "analytical"
        assert plan.execution_strategy in ExecutionStrategy
        assert plan.estimated_cost >= 0
        assert plan.estimated_time_ms > 0
        assert plan.estimated_memory_mb > 0
        assert isinstance(plan.resource_requirements, ResourceRequirements)
        assert len(plan.execution_steps) > 0
        assert len(plan.optimization_notes) > 0
    
    @pytest.mark.asyncio
    async def test_create_execution_plan_complex_query(self, query_planning_agent, sample_resources):
        """Test creating execution plan for complex query."""
        agent = query_planning_agent
        
        # Mock AI response for high complexity
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "complexity": "high",
            "operations": ["joins", "aggregation", "sorting"],
            "data_volume": "large",
            "computational_intensity": "high",
            "memory_pattern": "random_access",
            "io_pattern": "random_read_write",
            "parallelizable": True,
            "optimization_opportunities": ["hash_join", "aggregation_pushdown", "parallel_execution"]
        })
        agent.client.chat.completions.create.return_value = mock_response
        
        # Mock metadata registry
        agent.metadata_registry.list_resources = Mock(return_value=sample_resources)
        agent.metadata_registry.get_schema_info = Mock(return_value=None)
        
        # Create execution plan
        plan = await agent.create_execution_plan(
            user_id="test-user",
            client_id="test-client",
            query="SELECT s.product, SUM(s.amount) FROM sales s JOIN customers c ON s.customer_id = c.id GROUP BY s.product ORDER BY SUM(s.amount) DESC",
            query_type="analytical"
        )
        
        # Verify complex plan characteristics
        assert plan.execution_strategy in [ExecutionStrategy.PARALLEL, ExecutionStrategy.HYBRID, ExecutionStrategy.STREAMING]
        assert plan.estimated_memory_mb > 500  # Should require more memory for complex operations
        assert any("joins" in step.operation for step in plan.execution_steps)
        assert any("aggregation" in step.operation for step in plan.execution_steps)
        
        # Should have streaming or parallel configuration for complex queries
        assert plan.streaming_config is not None or plan.parallel_config is not None
    
    @pytest.mark.asyncio
    async def test_query_complexity_analysis(self, query_planning_agent):
        """Test query complexity analysis."""
        agent = query_planning_agent
        
        # Mock AI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "complexity": "medium",
            "operations": ["filtering", "aggregation"],
            "data_volume": "medium",
            "computational_intensity": "medium",
            "memory_pattern": "sequential",
            "io_pattern": "sequential_read",
            "parallelizable": True,
            "optimization_opportunities": ["predicate_pushdown", "column_pruning"]
        })
        agent.client.chat.completions.create.return_value = mock_response
        
        # Test complexity analysis
        analysis = await agent._analyze_query_complexity(
            "SELECT category, COUNT(*) FROM products WHERE price > 50 GROUP BY category",
            "analytical",
            "test-user",
            "test-client"
        )
        
        assert analysis["complexity"] == QueryComplexity.MEDIUM
        assert "filtering" in analysis["operations"]
        assert "aggregation" in analysis["operations"]
        assert analysis["parallelizable"] is True
        assert "predicate_pushdown" in analysis["optimization_opportunities"]
    
    @pytest.mark.asyncio
    async def test_heuristic_complexity_analysis(self, query_planning_agent):
        """Test fallback heuristic complexity analysis."""
        agent = query_planning_agent
        
        # Test simple query
        simple_analysis = agent._heuristic_complexity_analysis(
            "SELECT * FROM table WHERE id = 1",
            "simple"
        )
        assert simple_analysis["complexity"] == QueryComplexity.LOW
        
        # Test complex query with joins and aggregation
        complex_analysis = agent._heuristic_complexity_analysis(
            "SELECT t1.name, COUNT(*), AVG(t2.value) FROM table1 t1 JOIN table2 t2 ON t1.id = t2.id JOIN table3 t3 ON t2.ref = t3.ref WHERE t1.status = 'active' GROUP BY t1.name ORDER BY COUNT(*) DESC",
            "analytical"
        )
        assert complex_analysis["complexity"] in [QueryComplexity.HIGH, QueryComplexity.VERY_HIGH]
        assert "joins" in complex_analysis["operations"]
        assert "aggregation" in complex_analysis["operations"]
        assert "sorting" in complex_analysis["operations"]
    
    def test_resource_relevance_calculation(self, query_planning_agent, sample_resources):
        """Test resource relevance calculation."""
        agent = query_planning_agent
        
        # Mock schema info
        agent.metadata_registry.get_schema_info = Mock(return_value=Mock(
            schema_json=json.dumps({
                "columns": {
                    "sales_amount": {"type": "float"},
                    "customer_id": {"type": "int"},
                    "product_name": {"type": "string"}
                }
            })
        ))
        
        # Test relevance for sales-related query
        relevance = agent._calculate_resource_relevance(
            sample_resources[0],  # sales_data.csv
            "analyze sales performance by product",
            {"sales_amount": "total sales", "product_name": "product identifier"}
        )
        
        assert relevance > 0.3  # Should be relevant
        
        # Test relevance for unrelated query
        relevance_low = agent._calculate_resource_relevance(
            sample_resources[0],
            "analyze weather patterns",
            {"temperature": "daily temperature", "humidity": "humidity level"}
        )
        
        assert relevance_low < relevance  # Should be less relevant
    
    @pytest.mark.asyncio
    async def test_resource_requirements_estimation(self, query_planning_agent, sample_resources):
        """Test resource requirements estimation."""
        agent = query_planning_agent
        
        # Test low complexity requirements
        low_complexity = {
            "complexity": QueryComplexity.LOW,
            "operations": ["filtering"],
            "parallelizable": False
        }
        
        requirements_low = await agent._estimate_resource_requirements(
            low_complexity, sample_resources[:1], None
        )
        
        assert requirements_low.estimated_memory_mb >= 128
        assert requirements_low.estimated_cpu_cores >= 1
        assert requirements_low.estimated_io_operations >= 50
        
        # Test high complexity requirements
        high_complexity = {
            "complexity": QueryComplexity.HIGH,
            "operations": ["joins", "aggregation", "sorting"],
            "parallelizable": True
        }
        
        requirements_high = await agent._estimate_resource_requirements(
            high_complexity, sample_resources, None
        )
        
        assert requirements_high.estimated_memory_mb > requirements_low.estimated_memory_mb
        assert requirements_high.estimated_cpu_cores >= requirements_low.estimated_cpu_cores
        assert requirements_high.estimated_io_operations > requirements_low.estimated_io_operations
    
    @pytest.mark.asyncio
    async def test_execution_steps_generation(self, query_planning_agent, sample_resources):
        """Test execution steps generation."""
        agent = query_planning_agent
        
        complexity_analysis = {
            "complexity": QueryComplexity.MEDIUM,
            "operations": ["filtering", "aggregation"],
            "parallelizable": True
        }
        
        steps = await agent._generate_execution_steps(
            "SELECT category, COUNT(*) FROM products WHERE price > 50 GROUP BY category",
            "analytical",
            complexity_analysis,
            sample_resources,
            {"category": "product category", "count": "number of products"}
        )
        
        assert len(steps) > 0
        
        # Check for expected step types
        step_types = [step.step_type for step in steps]
        assert "discovery" in step_types or "data_access" in step_types
        assert "synthesis" in step_types
        
        # Check for filtering and aggregation steps
        operations = [step.operation for step in steps]
        assert any("filter" in op for op in operations)
        
        # Verify step structure
        for step in steps:
            assert isinstance(step, ExecutionStep)
            assert step.step_id
            assert step.estimated_time_ms > 0
            assert step.estimated_memory_mb > 0
            assert isinstance(step.parallelizable, bool)
            assert isinstance(step.streaming_capable, bool)
    
    def test_execution_strategy_determination(self, query_planning_agent):
        """Test execution strategy determination."""
        agent = query_planning_agent
        
        # Test sequential strategy for low complexity
        low_complexity = {"complexity": QueryComplexity.LOW, "parallelizable": False}
        low_requirements = ResourceRequirements(
            estimated_memory_mb=256, estimated_cpu_cores=1, estimated_io_operations=50,
            estimated_network_mb=10, max_concurrent_connections=1, temporary_storage_mb=50
        )
        
        strategy_low = agent._determine_execution_strategy(low_complexity, low_requirements, 1)
        assert strategy_low == ExecutionStrategy.SEQUENTIAL
        
        # Test streaming strategy for high memory
        high_memory_requirements = ResourceRequirements(
            estimated_memory_mb=5000, estimated_cpu_cores=4, estimated_io_operations=1000,
            estimated_network_mb=100, max_concurrent_connections=4, temporary_storage_mb=1000
        )
        
        strategy_streaming = agent._determine_execution_strategy(
            {"complexity": QueryComplexity.HIGH, "parallelizable": True},
            high_memory_requirements, 1
        )
        assert strategy_streaming == ExecutionStrategy.STREAMING
        
        # Test parallel strategy for multiple resources
        parallel_requirements = ResourceRequirements(
            estimated_memory_mb=1500, estimated_cpu_cores=4, estimated_io_operations=500,
            estimated_network_mb=50, max_concurrent_connections=4, temporary_storage_mb=300
        )
        
        strategy_parallel = agent._determine_execution_strategy(
            {"complexity": QueryComplexity.HIGH, "parallelizable": True},
            parallel_requirements, 3
        )
        assert strategy_parallel == ExecutionStrategy.PARALLEL
    
    @pytest.mark.asyncio
    async def test_optimization_application(self, query_planning_agent, sample_resources):
        """Test optimization application to execution steps."""
        agent = query_planning_agent
        
        # Create sample execution steps
        original_steps = [
            ExecutionStep(
                step_id="step_1",
                step_type="data_access",
                operation="load_structured_data",
                input_dependencies=[],
                output_schema={"data": "table"},
                estimated_time_ms=1000.0,
                estimated_memory_mb=500.0,
                parallelizable=True,
                optimization_techniques=[],
                streaming_capable=True
            ),
            ExecutionStep(
                step_id="step_2",
                step_type="processing",
                operation="data_filtering",
                input_dependencies=["step_1"],
                output_schema={"filtered_data": "table"},
                estimated_time_ms=500.0,
                estimated_memory_mb=300.0,
                parallelizable=True,
                optimization_techniques=[],
                streaming_capable=True
            )
        ]
        
        complexity_analysis = {
            "complexity": QueryComplexity.MEDIUM,
            "operations": ["filtering"]
        }
        
        optimized_steps = await agent._apply_optimizations(
            original_steps, sample_resources, complexity_analysis
        )
        
        # Verify optimizations were applied
        assert len(optimized_steps) == len(original_steps)
        
        # Check that optimization techniques were added
        for step in optimized_steps:
            if "load_" in step.operation or step.operation == "data_filtering":
                assert len(step.optimization_techniques) > 0
        
        # Check that estimates were improved
        load_step = next(step for step in optimized_steps if "load_" in step.operation)
        filter_step = next(step for step in optimized_steps if step.operation == "data_filtering")
        
        assert OptimizationTechnique.COLUMN_PRUNING in load_step.optimization_techniques
        assert OptimizationTechnique.PREDICATE_PUSHDOWN in filter_step.optimization_techniques
    
    def test_streaming_pagination_configuration(self, query_planning_agent):
        """Test streaming and pagination configuration."""
        agent = query_planning_agent
        
        # Test high memory scenario (should enable streaming)
        high_memory_complexity = {"complexity": QueryComplexity.HIGH}
        high_memory_requirements = ResourceRequirements(
            estimated_memory_mb=3000, estimated_cpu_cores=4, estimated_io_operations=1000,
            estimated_network_mb=100, max_concurrent_connections=4, temporary_storage_mb=1000
        )
        
        streaming_config, pagination_config = agent._configure_streaming_pagination(
            high_memory_complexity, high_memory_requirements, ExecutionStrategy.STREAMING
        )
        
        assert streaming_config is not None
        assert streaming_config["chunk_size"] > 0
        assert streaming_config["buffer_size_mb"] > 0
        assert streaming_config["max_concurrent_streams"] > 0
        
        assert pagination_config is not None
        assert pagination_config["page_size"] > 0
        assert pagination_config["max_pages"] > 0
        
        # Test low memory scenario (should not enable streaming)
        low_memory_complexity = {"complexity": QueryComplexity.LOW}
        low_memory_requirements = ResourceRequirements(
            estimated_memory_mb=256, estimated_cpu_cores=1, estimated_io_operations=50,
            estimated_network_mb=10, max_concurrent_connections=1, temporary_storage_mb=50
        )
        
        streaming_config_low, pagination_config_low = agent._configure_streaming_pagination(
            low_memory_complexity, low_memory_requirements, ExecutionStrategy.SEQUENTIAL
        )
        
        assert streaming_config_low is None
        assert pagination_config_low is None
    
    def test_parallel_execution_configuration(self, query_planning_agent):
        """Test parallel execution configuration."""
        agent = query_planning_agent
        
        # Create parallelizable steps
        parallelizable_steps = [
            ExecutionStep(
                step_id="step_1", step_type="processing", operation="data_processing",
                input_dependencies=[], output_schema={}, estimated_time_ms=1000.0,
                estimated_memory_mb=500.0, parallelizable=True, optimization_techniques=[],
                streaming_capable=True
            ),
            ExecutionStep(
                step_id="step_2", step_type="processing", operation="data_aggregation",
                input_dependencies=["step_1"], output_schema={}, estimated_time_ms=800.0,
                estimated_memory_mb=400.0, parallelizable=True, optimization_techniques=[],
                streaming_capable=False
            )
        ]
        
        requirements = ResourceRequirements(
            estimated_memory_mb=1500, estimated_cpu_cores=4, estimated_io_operations=500,
            estimated_network_mb=50, max_concurrent_connections=4, temporary_storage_mb=300
        )
        
        # Test parallel strategy
        parallel_config = agent._configure_parallel_execution(
            ExecutionStrategy.PARALLEL, requirements, parallelizable_steps
        )
        
        assert parallel_config is not None
        assert parallel_config["max_workers"] > 0
        assert parallel_config["max_workers"] <= 8  # Should not exceed limit
        assert parallel_config["partition_strategy"] in ["hash", "range", "round_robin"]
        assert parallel_config["merge_strategy"] in ["union", "join", "aggregate"]
        
        # Test sequential strategy (should not enable parallel)
        sequential_config = agent._configure_parallel_execution(
            ExecutionStrategy.SEQUENTIAL, requirements, parallelizable_steps
        )
        
        assert sequential_config is None
    
    @pytest.mark.asyncio
    async def test_fallback_plans_generation(self, query_planning_agent, sample_resources):
        """Test fallback plans generation."""
        agent = query_planning_agent
        
        complexity_analysis = {
            "complexity": QueryComplexity.MEDIUM,
            "operations": ["filtering", "aggregation"]
        }
        
        fallback_plans = await agent._generate_fallback_plans(
            "SELECT category, COUNT(*) FROM products GROUP BY category",
            "analytical",
            complexity_analysis,
            sample_resources
        )
        
        assert len(fallback_plans) > 0
        
        # Verify fallback plan structure
        for plan in fallback_plans:
            assert isinstance(plan, QueryPlan)
            assert plan.plan_id.startswith("fallback_")
            assert plan.execution_strategy == ExecutionStrategy.SEQUENTIAL
            assert len(plan.execution_steps) > 0
            assert plan.estimated_cost >= 0
            assert plan.estimated_time_ms > 0
            assert plan.estimated_memory_mb > 0
        
        # Should have at least error recovery plan
        plan_types = [plan.query_type for plan in fallback_plans]
        assert "error_recovery" in plan_types
    
    def test_execution_cost_calculation(self, query_planning_agent):
        """Test execution cost calculation."""
        agent = query_planning_agent
        
        requirements = ResourceRequirements(
            estimated_memory_mb=1024, estimated_cpu_cores=2, estimated_io_operations=500,
            estimated_network_mb=50, max_concurrent_connections=2, temporary_storage_mb=200
        )
        
        cost = agent._calculate_execution_cost(5000.0, 1024.0, requirements)
        
        assert cost > 0
        assert isinstance(cost, float)
        
        # Higher resource usage should result in higher cost
        high_requirements = ResourceRequirements(
            estimated_memory_mb=4096, estimated_cpu_cores=8, estimated_io_operations=2000,
            estimated_network_mb=200, max_concurrent_connections=8, temporary_storage_mb=1000
        )
        
        high_cost = agent._calculate_execution_cost(10000.0, 4096.0, high_requirements)
        assert high_cost > cost
    
    def test_resource_availability_check(self, query_planning_agent):
        """Test resource availability checking."""
        agent = query_planning_agent
        
        # Test with available resources
        low_requirements = ResourceRequirements(
            estimated_memory_mb=512, estimated_cpu_cores=2, estimated_io_operations=100,
            estimated_network_mb=20, max_concurrent_connections=1, temporary_storage_mb=100
        )
        
        availability = agent.check_resource_availability(low_requirements)
        
        assert "can_execute" in availability
        assert "available_resources" in availability
        assert "required_resources" in availability
        assert "current_usage" in availability
        
        # Should be able to execute with low requirements
        assert availability["can_execute"] is True
        
        # Test with excessive requirements
        excessive_requirements = ResourceRequirements(
            estimated_memory_mb=50000, estimated_cpu_cores=100, estimated_io_operations=10000,
            estimated_network_mb=1000, max_concurrent_connections=1, temporary_storage_mb=10000
        )
        
        availability_excessive = agent.check_resource_availability(excessive_requirements)
        assert availability_excessive["can_execute"] is False
    
    def test_resource_reservation_and_release(self, query_planning_agent):
        """Test resource reservation and release."""
        agent = query_planning_agent
        
        requirements = ResourceRequirements(
            estimated_memory_mb=512, estimated_cpu_cores=2, estimated_io_operations=100,
            estimated_network_mb=20, max_concurrent_connections=1, temporary_storage_mb=100
        )
        
        execution_id = "test-execution-123"
        
        # Test reservation
        reserved = agent.reserve_resources(execution_id, requirements)
        assert reserved is True
        assert execution_id in agent.active_executions
        
        # Test that resources are now in use
        availability = agent.check_resource_availability(requirements)
        assert availability["current_usage"]["memory_mb"] == 512
        assert availability["current_usage"]["cpu_cores"] == 2
        
        # Test release
        agent.release_resources(execution_id)
        assert execution_id not in agent.active_executions
        
        # Test that resources are available again
        availability_after = agent.check_resource_availability(requirements)
        assert availability_after["current_usage"]["memory_mb"] == 0
        assert availability_after["current_usage"]["cpu_cores"] == 0
    
    @pytest.mark.asyncio
    async def test_plan_optimization(self, query_planning_agent):
        """Test plan optimization based on execution metrics."""
        agent = query_planning_agent
        
        # Create original plan
        original_plan = QueryPlan(
            plan_id="original-plan-123",
            original_query="SELECT * FROM test",
            query_type="analytical",
            execution_steps=[
                ExecutionStep(
                    step_id="step_1", step_type="processing", operation="data_processing",
                    input_dependencies=[], output_schema={}, estimated_time_ms=1000.0,
                    estimated_memory_mb=500.0, parallelizable=True, optimization_techniques=[],
                    streaming_capable=True
                )
            ],
            execution_strategy=ExecutionStrategy.SEQUENTIAL,
            estimated_cost=100.0,
            estimated_time_ms=1000.0,
            estimated_memory_mb=500.0,
            resource_requirements=ResourceRequirements(
                estimated_memory_mb=500, estimated_cpu_cores=2, estimated_io_operations=100,
                estimated_network_mb=20, max_concurrent_connections=1, temporary_storage_mb=100
            ),
            optimization_notes=["Original plan"],
            fallback_plans=[]
        )
        
        # Add to cache
        agent.plan_cache["test-key"] = original_plan
        
        # Create execution metrics
        metrics = ExecutionMetrics(
            actual_time_ms=800.0,  # Better than estimated
            actual_memory_mb=400.0,  # Better than estimated
            rows_processed=10000,
            bytes_processed=1024 * 1024,
            cache_hits=100,
            cache_misses=10,
            optimization_effectiveness=0.9,
            resource_utilization={"cpu": 0.4, "memory": 0.6}
        )
        
        # Optimize plan
        optimized_plan = await agent.optimize_existing_plan("original-plan-123", metrics)
        
        assert optimized_plan is not None
        assert optimized_plan.plan_id != original_plan.plan_id
        assert optimized_plan.plan_id.startswith("original-plan-123_optimized_")
        
        # Should have better estimates based on actual performance
        assert optimized_plan.estimated_time_ms < original_plan.estimated_time_ms
        assert optimized_plan.estimated_memory_mb < original_plan.estimated_memory_mb
        
        # Should have optimization history
        assert len(agent.optimization_history) > 0
        assert agent.optimization_history[-1]["original_plan_id"] == "original-plan-123"
    
    def test_execution_statistics(self, query_planning_agent):
        """Test execution statistics generation."""
        agent = query_planning_agent
        
        # Add some test data
        agent.plan_cache["test-plan"] = Mock()
        agent.active_executions["test-exec"] = {
            "memory_mb": 512,
            "cpu_cores": 2,
            "start_time": time.time()
        }
        agent.optimization_history.append({"test": "data"})
        
        stats = agent.get_execution_statistics()
        
        assert "cached_plans" in stats
        assert "active_executions" in stats
        assert "optimization_history_count" in stats
        assert "resource_pool" in stats
        assert "current_resource_usage" in stats
        
        assert stats["cached_plans"] == 1
        assert stats["active_executions"] == 1
        assert stats["optimization_history_count"] == 1
        assert stats["current_resource_usage"]["memory_mb"] == 512
        assert stats["current_resource_usage"]["cpu_cores"] == 2
    
    @pytest.mark.asyncio
    async def test_health_check(self, query_planning_agent):
        """Test agent health check."""
        agent = query_planning_agent
        
        # Mock successful response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Query analysis completed"
        agent.client.chat.completions.create.return_value = mock_response
        
        health = await agent.health_check()
        
        assert "status" in health
        assert health["status"] == "healthy"
        assert "agent_info" in health
        assert "cache_stats" in health
        assert "resource_stats" in health
        assert "test_response_length" in health
    
    @pytest.mark.asyncio
    async def test_error_handling_in_plan_creation(self, query_planning_agent):
        """Test error handling during plan creation."""
        agent = query_planning_agent
        
        # Mock failure in AI response
        agent.client.chat.completions.create.side_effect = Exception("AI service unavailable")
        
        # Should return fallback plan instead of raising exception
        plan = await agent.create_execution_plan(
            user_id="test-user",
            client_id="test-client",
            query="SELECT * FROM test",
            query_type="analytical"
        )
        
        assert isinstance(plan, QueryPlan)
        assert plan.execution_strategy == ExecutionStrategy.SEQUENTIAL
        assert "Planning failed" in plan.optimization_notes[0]
        assert plan.estimated_cost == 0.0
    
    def test_plan_cache_key_generation(self, query_planning_agent):
        """Test plan cache key generation."""
        agent = query_planning_agent
        
        key1 = agent._generate_plan_cache_key("SELECT * FROM test", "analytical", "user1", "client1")
        key2 = agent._generate_plan_cache_key("SELECT * FROM test", "analytical", "user1", "client1")
        key3 = agent._generate_plan_cache_key("SELECT * FROM test", "analytical", "user2", "client1")
        
        # Same inputs should generate same key
        assert key1 == key2
        
        # Different inputs should generate different keys
        assert key1 != key3
        
        # Keys should be valid MD5 hashes
        assert len(key1) == 32
        assert all(c in "0123456789abcdef" for c in key1)


# Property-based tests for correctness properties
class TestQueryPlanningAgentProperties:
    """Property-based tests for Query Planning Agent correctness."""
    
    @pytest.mark.asyncio
    async def test_property_execution_plan_consistency(self, query_planning_agent, sample_resources):
        """
        Property: For any valid query, the execution plan should be consistent and complete.
        **Validates: Requirements 5.1, 5.2**
        """
        agent = query_planning_agent
        
        # Mock AI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "complexity": "medium",
            "operations": ["filtering"],
            "data_volume": "medium",
            "computational_intensity": "medium",
            "memory_pattern": "sequential",
            "io_pattern": "sequential_read",
            "parallelizable": True,
            "optimization_opportunities": ["predicate_pushdown"]
        })
        agent.client.chat.completions.create.return_value = mock_response
        agent.metadata_registry.list_resources = Mock(return_value=sample_resources)
        agent.metadata_registry.get_schema_info = Mock(return_value=None)
        
        # Test multiple queries
        test_queries = [
            "SELECT * FROM table1",
            "SELECT COUNT(*) FROM table1 WHERE id > 100",
            "SELECT a.name, b.value FROM table1 a JOIN table2 b ON a.id = b.ref_id"
        ]
        
        for query in test_queries:
            plan = await agent.create_execution_plan(
                user_id="test-user",
                client_id="test-client",
                query=query,
                query_type="analytical"
            )
            
            # Plan should be complete and consistent
            assert isinstance(plan, QueryPlan)
            assert plan.plan_id
            assert plan.original_query == query
            assert plan.execution_strategy in ExecutionStrategy
            assert plan.estimated_cost >= 0
            assert plan.estimated_time_ms > 0
            assert plan.estimated_memory_mb > 0
            assert isinstance(plan.resource_requirements, ResourceRequirements)
            assert len(plan.execution_steps) > 0
            
            # All execution steps should be valid
            for step in plan.execution_steps:
                assert step.step_id
                assert step.step_type
                assert step.operation
                assert step.estimated_time_ms >= 0
                assert step.estimated_memory_mb >= 0
                assert isinstance(step.parallelizable, bool)
                assert isinstance(step.streaming_capable, bool)
    
    def test_property_resource_allocation_conservation(self, query_planning_agent):
        """
        Property: For any resource allocation and release cycle, total resources should be conserved.
        **Validates: Requirements 5.3, 10.3**
        """
        agent = query_planning_agent
        
        # Record initial state
        initial_stats = agent.get_execution_statistics()
        initial_memory = initial_stats["current_resource_usage"]["memory_mb"]
        initial_cpu = initial_stats["current_resource_usage"]["cpu_cores"]
        
        # Perform multiple allocation/release cycles
        requirements_list = [
            ResourceRequirements(256, 1, 50, 10, 1, 50),
            ResourceRequirements(512, 2, 100, 20, 2, 100),
            ResourceRequirements(1024, 4, 200, 40, 4, 200)
        ]
        
        execution_ids = []
        
        # Allocate resources
        for i, requirements in enumerate(requirements_list):
            execution_id = f"test-exec-{i}"
            reserved = agent.reserve_resources(execution_id, requirements)
            if reserved:
                execution_ids.append(execution_id)
        
        # Release all resources
        for execution_id in execution_ids:
            agent.release_resources(execution_id)
        
        # Check final state
        final_stats = agent.get_execution_statistics()
        final_memory = final_stats["current_resource_usage"]["memory_mb"]
        final_cpu = final_stats["current_resource_usage"]["cpu_cores"]
        
        # Resources should be conserved (back to initial state)
        assert final_memory == initial_memory
        assert final_cpu == initial_cpu
        assert len(agent.active_executions) == 0
    
    def test_property_optimization_effectiveness(self, query_planning_agent, sample_resources):
        """
        Property: For any execution steps, applying optimizations should not increase resource requirements.
        **Validates: Requirements 5.4, 5.5**
        """
        agent = query_planning_agent
        
        # Create sample execution steps
        original_steps = [
            ExecutionStep(
                step_id="step_1",
                step_type="data_access",
                operation="load_structured_data",
                input_dependencies=[],
                output_schema={"data": "table"},
                estimated_time_ms=1000.0,
                estimated_memory_mb=500.0,
                parallelizable=True,
                optimization_techniques=[],
                streaming_capable=True
            ),
            ExecutionStep(
                step_id="step_2",
                step_type="processing",
                operation="data_filtering",
                input_dependencies=["step_1"],
                output_schema={"filtered_data": "table"},
                estimated_time_ms=500.0,
                estimated_memory_mb=300.0,
                parallelizable=True,
                optimization_techniques=[],
                streaming_capable=True
            )
        ]
        
        # Record original resource requirements
        original_total_time = sum(step.estimated_time_ms for step in original_steps)
        original_max_memory = max(step.estimated_memory_mb for step in original_steps)
        
        # Apply optimizations
        complexity_analysis = {
            "complexity": QueryComplexity.MEDIUM,
            "operations": ["filtering"]
        }
        
        optimized_steps = asyncio.run(agent._apply_optimizations(
            original_steps, sample_resources, complexity_analysis
        ))
        
        # Calculate optimized resource requirements
        optimized_total_time = sum(step.estimated_time_ms for step in optimized_steps)
        optimized_max_memory = max(step.estimated_memory_mb for step in optimized_steps)
        
        # Optimizations should not increase requirements (may stay same or improve)
        assert optimized_total_time <= original_total_time * 1.1  # Allow 10% tolerance
        assert optimized_max_memory <= original_max_memory * 1.1  # Allow 10% tolerance
        
        # Should have optimization techniques applied
        total_techniques = sum(len(step.optimization_techniques) for step in optimized_steps)
        assert total_techniques > 0
    
    def test_property_complexity_monotonicity(self, query_planning_agent):
        """
        Property: For any query, higher complexity should result in higher resource estimates.
        **Validates: Requirements 5.1, 10.1**
        """
        agent = query_planning_agent
        
        # Test different complexity levels
        complexity_levels = [
            {"complexity": QueryComplexity.LOW, "operations": ["filtering"]},
            {"complexity": QueryComplexity.MEDIUM, "operations": ["filtering", "aggregation"]},
            {"complexity": QueryComplexity.HIGH, "operations": ["filtering", "aggregation", "joins"]},
            {"complexity": QueryComplexity.VERY_HIGH, "operations": ["filtering", "aggregation", "joins", "sorting"]}
        ]
        
        sample_resources = [Mock(file_size_bytes=1024*1024, row_count=1000)]  # 1MB, 1000 rows
        
        previous_memory = 0
        previous_cpu = 0
        
        for complexity in complexity_levels:
            requirements = asyncio.run(agent._estimate_resource_requirements(
                complexity, sample_resources, None
            ))
            
            # Higher complexity should require more resources
            assert requirements.estimated_memory_mb >= previous_memory
            assert requirements.estimated_cpu_cores >= previous_cpu
            
            previous_memory = requirements.estimated_memory_mb
            previous_cpu = requirements.estimated_cpu_cores
#!/usr/bin/env python3
"""
Query Planning Agent Demo

Demonstrates the Query Planning Agent's capabilities for optimal query execution
planning, cost-based optimization, streaming and pagination strategies, parallel
execution planning, and resource allocation management.
"""

import asyncio
import json
import time
from datetime import datetime
from unittest.mock import Mock

from light_ai.agents.query_planning_agent import (
    QueryPlanningAgent, QueryComplexity, ExecutionStrategy, 
    ResourceRequirements, ExecutionMetrics
)
from light_ai.core.models import ResourceMetadata, ResourceType, DataType, AccessLevel
from light_ai.config import Config


def create_mock_config():
    """Create a mock configuration for demo purposes."""
    config = Mock(spec=Config)
    config.openrouter = Mock()
    config.openrouter.api_key = "demo-key"
    config.openrouter.base_url = "https://openrouter.ai/api/v1"
    config.openrouter.default_model = "anthropic/claude-3.5-sonnet"
    config.logging = Mock()
    config.logging.level = "INFO"
    config.database = Mock()
    config.database.duckdb_path = ":memory:"
    config.storage = Mock()
    config.storage.base_directory = "/tmp/demo"
    config.storage.base_path = "/tmp/demo"
    return config


def create_sample_resources():
    """Create sample resource metadata for demo."""
    import uuid
    return [
        ResourceMetadata(
            resource_id=str(uuid.uuid4()),
            client_id="demo-client",
            user_id="demo-user",
            original_filename="sales_data.csv",
            resource_type=ResourceType.STRUCTURED,
            data_type=DataType.CSV,
            file_size_bytes=10 * 1024 * 1024,  # 10MB
            storage_path="/tmp/demo/sales_data.csv",
            row_count=100000,
            column_count=8,
            chunk_count=0,
            created_at=datetime.utcnow(),
            processing_status="completed",
            version=1
        ),
        ResourceMetadata(
            resource_id=str(uuid.uuid4()),
            client_id="demo-client",
            user_id="demo-user",
            original_filename="customer_data.json",
            resource_type=ResourceType.JSON,
            data_type=DataType.JSON,
            file_size_bytes=5 * 1024 * 1024,  # 5MB
            storage_path="/tmp/demo/customer_data.json",
            row_count=50000,
            column_count=0,
            chunk_count=200,
            created_at=datetime.utcnow(),
            processing_status="completed",
            version=1
        ),
        ResourceMetadata(
            resource_id=str(uuid.uuid4()),
            client_id="demo-client",
            user_id="demo-user",
            original_filename="product_catalog.xlsx",
            resource_type=ResourceType.STRUCTURED,
            data_type=DataType.EXCEL,
            file_size_bytes=20 * 1024 * 1024,  # 20MB
            storage_path="/tmp/demo/product_catalog.xlsx",
            row_count=200000,
            column_count=12,
            chunk_count=0,
            created_at=datetime.utcnow(),
            processing_status="completed",
            version=1
        )
    ]


async def demo_query_planning():
    """Demonstrate Query Planning Agent capabilities."""
    print("🚀 Query Planning Agent Demo")
    print("=" * 50)
    
    # Create mock configuration and agent
    config = create_mock_config()
    agent = QueryPlanningAgent(config)
    
    # Mock the dependencies
    agent.metadata_registry = Mock()
    agent.storage_router = Mock()
    agent.db_managers = Mock()
    agent.activity_logger = Mock()
    
    # Mock the OpenAI client for AI responses
    agent.client = Mock()
    agent.client.chat = Mock()
    agent.client.chat.completions = Mock()
    agent.client.chat.completions.create = Mock()
    
    # Create sample resources
    sample_resources = create_sample_resources()
    agent.metadata_registry.list_resources = Mock(return_value=sample_resources)
    agent.metadata_registry.get_schema_info = Mock(return_value=None)
    
    print("\n📊 Sample Resources:")
    for resource in sample_resources:
        print(f"  • {resource.original_filename} ({resource.resource_type.value})")
        print(f"    Size: {resource.file_size_bytes / (1024*1024):.1f}MB, Rows: {resource.row_count:,}")
    
    # Demo 1: Simple Query Planning
    print("\n🔍 Demo 1: Simple Query Planning")
    print("-" * 30)
    
    # Mock AI response for simple query
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
    
    simple_query = "SELECT * FROM sales_data WHERE amount > 1000"
    print(f"Query: {simple_query}")
    
    start_time = time.time()
    simple_plan = await agent.create_execution_plan(
        user_id="demo-user",
        client_id="demo-client",
        query=simple_query,
        query_type="analytical"
    )
    planning_time = (time.time() - start_time) * 1000
    
    print(f"✅ Plan created in {planning_time:.2f}ms")
    print(f"   Strategy: {simple_plan.execution_strategy.value}")
    print(f"   Estimated time: {simple_plan.estimated_time_ms:.0f}ms")
    print(f"   Estimated memory: {simple_plan.estimated_memory_mb:.0f}MB")
    print(f"   Execution steps: {len(simple_plan.execution_steps)}")
    print(f"   Cost: ${simple_plan.estimated_cost:.2f}")
    
    # Demo 2: Complex Query Planning
    print("\n🔥 Demo 2: Complex Query Planning")
    print("-" * 30)
    
    # Mock AI response for complex query
    mock_response.choices[0].message.content = json.dumps({
        "complexity": "high",
        "operations": ["joins", "aggregation", "sorting", "filtering"],
        "data_volume": "large",
        "computational_intensity": "high",
        "memory_pattern": "random_access",
        "io_pattern": "random_read_write",
        "parallelizable": True,
        "optimization_opportunities": ["hash_join", "aggregation_pushdown", "parallel_execution"]
    })
    
    complex_query = """
    SELECT 
        p.category,
        COUNT(s.sale_id) as total_sales,
        SUM(s.amount) as total_revenue,
        AVG(s.amount) as avg_sale_amount
    FROM sales_data s
    JOIN product_catalog p ON s.product_id = p.product_id
    JOIN customer_data c ON s.customer_id = c.customer_id
    WHERE s.sale_date >= '2024-01-01'
    GROUP BY p.category
    ORDER BY total_revenue DESC
    """
    
    print(f"Query: Complex multi-table analysis with joins and aggregation")
    
    start_time = time.time()
    complex_plan = await agent.create_execution_plan(
        user_id="demo-user",
        client_id="demo-client",
        query=complex_query,
        query_type="analytical",
        desired_fields={
            "category": "product category",
            "total_sales": "number of sales",
            "total_revenue": "sum of sales amounts",
            "avg_sale_amount": "average sale amount"
        }
    )
    planning_time = (time.time() - start_time) * 1000
    
    print(f"✅ Plan created in {planning_time:.2f}ms")
    print(f"   Strategy: {complex_plan.execution_strategy.value}")
    print(f"   Estimated time: {complex_plan.estimated_time_ms:.0f}ms")
    print(f"   Estimated memory: {complex_plan.estimated_memory_mb:.0f}MB")
    print(f"   Execution steps: {len(complex_plan.execution_steps)}")
    print(f"   Cost: ${complex_plan.estimated_cost:.2f}")
    
    if complex_plan.streaming_config:
        print(f"   Streaming: Enabled (chunk size: {complex_plan.streaming_config['chunk_size']:,})")
    
    if complex_plan.parallel_config:
        print(f"   Parallel: Enabled (workers: {complex_plan.parallel_config['max_workers']})")
    
    print(f"   Optimizations: {len(complex_plan.optimization_notes)} applied")
    
    # Demo 3: Resource Management
    print("\n⚡ Demo 3: Resource Management")
    print("-" * 30)
    
    # Check resource availability
    resource_requirements = complex_plan.resource_requirements
    availability = agent.check_resource_availability(resource_requirements)
    
    print(f"Resource Requirements:")
    print(f"   Memory: {resource_requirements.estimated_memory_mb:.0f}MB")
    print(f"   CPU cores: {resource_requirements.estimated_cpu_cores}")
    print(f"   I/O operations: {resource_requirements.estimated_io_operations}")
    
    print(f"Resource Availability:")
    print(f"   Can execute: {availability['can_execute']}")
    print(f"   Available memory: {availability['available_resources']['memory_mb']:.0f}MB")
    print(f"   Available CPU: {availability['available_resources']['cpu_cores']}")
    
    # Reserve resources
    execution_id = "demo-execution-123"
    reserved = agent.reserve_resources(execution_id, resource_requirements)
    print(f"   Resources reserved: {reserved}")
    
    # Show resource usage
    stats = agent.get_execution_statistics()
    print(f"   Current usage: {stats['current_resource_usage']['memory_mb']:.0f}MB memory, {stats['current_resource_usage']['cpu_cores']} CPU cores")
    
    # Release resources
    agent.release_resources(execution_id)
    print(f"   Resources released")
    
    # Demo 4: Plan Optimization
    print("\n🎯 Demo 4: Plan Optimization")
    print("-" * 30)
    
    # Simulate execution metrics
    execution_metrics = ExecutionMetrics(
        actual_time_ms=complex_plan.estimated_time_ms * 0.8,  # 20% better than estimated
        actual_memory_mb=complex_plan.estimated_memory_mb * 0.9,  # 10% better than estimated
        rows_processed=150000,
        bytes_processed=25 * 1024 * 1024,  # 25MB
        cache_hits=1000,
        cache_misses=100,
        optimization_effectiveness=0.85,
        resource_utilization={"cpu": 0.7, "memory": 0.6}
    )
    
    print(f"Execution Metrics:")
    print(f"   Actual time: {execution_metrics.actual_time_ms:.0f}ms (vs estimated {complex_plan.estimated_time_ms:.0f}ms)")
    print(f"   Actual memory: {execution_metrics.actual_memory_mb:.0f}MB (vs estimated {complex_plan.estimated_memory_mb:.0f}MB)")
    print(f"   Cache hit ratio: {execution_metrics.cache_hits / (execution_metrics.cache_hits + execution_metrics.cache_misses):.1%}")
    
    # Optimize the plan based on metrics
    optimized_plan = await agent.optimize_existing_plan(complex_plan.plan_id, execution_metrics)
    
    if optimized_plan:
        print(f"✅ Plan optimized:")
        print(f"   New estimated time: {optimized_plan.estimated_time_ms:.0f}ms")
        print(f"   New estimated memory: {optimized_plan.estimated_memory_mb:.0f}MB")
        print(f"   Cost improvement: ${complex_plan.estimated_cost - optimized_plan.estimated_cost:.2f}")
        print(f"   Optimization history: {len(agent.optimization_history)} entries")
    
    # Demo 5: Execution Steps Analysis
    print("\n🔧 Demo 5: Execution Steps Analysis")
    print("-" * 30)
    
    print(f"Execution Steps for Complex Query:")
    for i, step in enumerate(complex_plan.execution_steps, 1):
        print(f"   {i}. {step.operation} ({step.step_type})")
        print(f"      Time: {step.estimated_time_ms:.0f}ms, Memory: {step.estimated_memory_mb:.0f}MB")
        print(f"      Parallelizable: {step.parallelizable}, Streaming: {step.streaming_capable}")
        if step.optimization_techniques:
            print(f"      Optimizations: {[opt.value for opt in step.optimization_techniques]}")
        if step.batch_size:
            print(f"      Batch size: {step.batch_size:,}")
    
    # Demo 6: Fallback Plans
    print("\n🛡️ Demo 6: Fallback Plans")
    print("-" * 30)
    
    print(f"Fallback Plans Available: {len(complex_plan.fallback_plans)}")
    for i, fallback in enumerate(complex_plan.fallback_plans, 1):
        print(f"   {i}. {fallback.query_type} strategy")
        print(f"      Strategy: {fallback.execution_strategy.value}")
        print(f"      Steps: {len(fallback.execution_steps)}")
        print(f"      Estimated time: {fallback.estimated_time_ms:.0f}ms")
    
    # Demo 7: Agent Statistics
    print("\n📈 Demo 7: Agent Statistics")
    print("-" * 30)
    
    final_stats = agent.get_execution_statistics()
    print(f"Agent Statistics:")
    print(f"   Cached plans: {final_stats['cached_plans']}")
    print(f"   Active executions: {final_stats['active_executions']}")
    print(f"   Optimization history: {final_stats['optimization_history_count']}")
    print(f"   Resource pool capacity:")
    print(f"     Max memory: {final_stats['resource_pool']['max_memory_mb']:,}MB")
    print(f"     Max CPU cores: {final_stats['resource_pool']['max_cpu_cores']}")
    print(f"     Max concurrent queries: {final_stats['resource_pool']['max_concurrent_queries']}")
    
    print("\n✨ Demo completed successfully!")
    print("The Query Planning Agent demonstrates:")
    print("  • Intelligent query complexity analysis")
    print("  • Cost-based execution planning")
    print("  • Streaming and pagination strategies")
    print("  • Parallel execution planning")
    print("  • Resource allocation and management")
    print("  • Plan optimization based on execution metrics")
    print("  • Fallback strategies for error recovery")


if __name__ == "__main__":
    asyncio.run(demo_query_planning())
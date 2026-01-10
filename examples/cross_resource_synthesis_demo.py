#!/usr/bin/env python3
"""
Cross-Resource Synthesis Agent Demo

Demonstrates the Cross-Resource Synthesis Agent's ability to:
1. Analyze multiple data sources for synthesis opportunities
2. Detect and resolve schema conflicts
3. Generate unified views with lineage tracking
4. Create intelligent join strategies
"""

import asyncio
import json
from datetime import datetime
from light_ai.config import get_config
from light_ai.agents.cross_resource_synthesis_agent import (
    CrossResourceSynthesisAgent, SynthesisStrategy, JoinStrategy
)
from light_ai.core.models import ResourceMetadata, ResourceType, DataType


def create_sample_resources():
    """Create sample resources for demonstration."""
    import uuid
    
    # Customer data resource
    customer_resource = ResourceMetadata(
        resource_id=str(uuid.uuid4()),
        user_id="demo-user",
        client_id="demo-client",
        resource_type=ResourceType.STRUCTURED,
        data_type=DataType.CSV,
        original_filename="customers.csv",
        file_size_bytes=5120,
        storage_path="/data/customers.csv",
        row_count=500,
        column_count=6,
        processing_status="completed"
    )
    
    # Orders data resource
    orders_resource = ResourceMetadata(
        resource_id=str(uuid.uuid4()),
        user_id="demo-user",
        client_id="demo-client",
        resource_type=ResourceType.STRUCTURED,
        data_type=DataType.CSV,
        original_filename="orders.csv",
        file_size_bytes=8192,
        storage_path="/data/orders.csv",
        row_count=1200,
        column_count=8,
        processing_status="completed"
    )
    
    # Product data resource
    products_resource = ResourceMetadata(
        resource_id=str(uuid.uuid4()),
        user_id="demo-user",
        client_id="demo-client",
        resource_type=ResourceType.JSON,
        data_type=DataType.JSON,
        original_filename="products.json",
        file_size_bytes=3072,
        storage_path="/data/products.json",
        row_count=150,
        column_count=10,
        processing_status="completed"
    )
    
    return [customer_resource, orders_resource, products_resource]


class MockMetadataRegistry:
    """Mock metadata registry for demo purposes."""
    
    def __init__(self, resources):
        self.resources = {r.resource_id: r for r in resources}
        self.schema_info = self._create_mock_schemas(resources)
    
    def get_resource_metadata(self, resource_id):
        return self.resources.get(resource_id)
    
    def get_schema_info(self, resource_id):
        return self.schema_info.get(resource_id)
    
    def initialize(self):
        pass
    
    def _create_mock_schemas(self, resources):
        """Create mock schema information for resources."""
        schemas = {}
        
        for resource in resources:
            if resource.original_filename == "customers.csv":
                schema_json = json.dumps({
                    "columns": {
                        "customer_id": {
                            "type": "integer",
                            "nullable": False,
                            "unique_values": 500,
                            "sample_values": [1, 2, 3, 4, 5]
                        },
                        "customer_name": {
                            "type": "string",
                            "nullable": False,
                            "unique_values": 485,
                            "sample_values": ["John Doe", "Jane Smith", "Bob Wilson"]
                        },
                        "email": {
                            "type": "string",
                            "nullable": True,
                            "unique_values": 490,
                            "sample_values": ["john@example.com", "jane@example.com"]
                        },
                        "phone": {
                            "type": "string",
                            "nullable": True,
                            "unique_values": 480,
                            "sample_values": ["555-1234", "555-5678"]
                        },
                        "registration_date": {
                            "type": "date",
                            "nullable": False,
                            "unique_values": 365,
                            "sample_values": ["2023-01-15", "2023-02-20"]
                        },
                        "status": {
                            "type": "string",
                            "nullable": False,
                            "unique_values": 3,
                            "sample_values": ["active", "inactive", "pending"]
                        }
                    }
                })
            
            elif resource.original_filename == "orders.csv":
                schema_json = json.dumps({
                    "columns": {
                        "order_id": {
                            "type": "integer",
                            "nullable": False,
                            "unique_values": 1200,
                            "sample_values": [1001, 1002, 1003]
                        },
                        "customer_id": {
                            "type": "integer",
                            "nullable": False,
                            "unique_values": 450,
                            "sample_values": [1, 2, 3, 4, 5]
                        },
                        "product_id": {
                            "type": "string",  # Different type - will cause conflict
                            "nullable": False,
                            "unique_values": 120,
                            "sample_values": ["PROD001", "PROD002", "PROD003"]
                        },
                        "quantity": {
                            "type": "integer",
                            "nullable": False,
                            "unique_values": 50,
                            "sample_values": [1, 2, 3, 5, 10]
                        },
                        "order_date": {
                            "type": "date",
                            "nullable": False,
                            "unique_values": 300,
                            "sample_values": ["2023-03-01", "2023-03-15"]
                        },
                        "total_amount": {
                            "type": "decimal",
                            "nullable": False,
                            "unique_values": 800,
                            "sample_values": [29.99, 149.50, 75.25]
                        },
                        "order_status": {
                            "type": "string",
                            "nullable": False,
                            "unique_values": 5,
                            "sample_values": ["pending", "shipped", "delivered", "cancelled"]
                        },
                        "shipping_address": {
                            "type": "string",
                            "nullable": True,
                            "unique_values": 400,
                            "sample_values": ["123 Main St", "456 Oak Ave"]
                        }
                    }
                })
            
            else:  # products.json
                schema_json = json.dumps({
                    "columns": {
                        "product_id": {
                            "type": "integer",  # Different type from orders - will cause conflict
                            "nullable": False,
                            "unique_values": 150,
                            "sample_values": [1, 2, 3, 4, 5]
                        },
                        "product_name": {
                            "type": "string",
                            "nullable": False,
                            "unique_values": 150,
                            "sample_values": ["Laptop", "Mouse", "Keyboard"]
                        },
                        "category": {
                            "type": "string",
                            "nullable": False,
                            "unique_values": 15,
                            "sample_values": ["Electronics", "Accessories", "Software"]
                        },
                        "price": {
                            "type": "decimal",
                            "nullable": False,
                            "unique_values": 120,
                            "sample_values": [999.99, 29.99, 79.99]
                        },
                        "description": {
                            "type": "string",
                            "nullable": True,
                            "unique_values": 145,
                            "sample_values": ["High-performance laptop", "Wireless mouse"]
                        }
                    }
                })
            
            # Create mock schema info object
            class MockSchemaInfo:
                def __init__(self, schema_json):
                    self.schema_json = schema_json
            
            schemas[resource.resource_id] = MockSchemaInfo(schema_json)
        
        return schemas


class MockStorageRouter:
    """Mock storage router for demo purposes."""
    
    def initialize(self):
        pass
    
    def query_json_data(self, table_name, client_id, user_id):
        # Return sample JSON data for products
        return [
            {
                "product_id": 1,
                "product_name": "Laptop Pro",
                "category": "Electronics",
                "price": 1299.99,
                "description": "High-performance laptop for professionals"
            },
            {
                "product_id": 2,
                "product_name": "Wireless Mouse",
                "category": "Accessories", 
                "price": 29.99,
                "description": "Ergonomic wireless mouse"
            }
        ]


class MockDatabaseManagers:
    """Mock database managers for demo purposes."""
    
    def initialize_all(self):
        pass


async def demonstrate_cross_resource_synthesis():
    """Demonstrate cross-resource synthesis capabilities."""
    print("🔄 Cross-Resource Synthesis Agent Demo")
    print("=" * 50)
    
    # Create sample resources
    resources = create_sample_resources()
    print(f"📊 Created {len(resources)} sample resources:")
    for resource in resources:
        print(f"  - {resource.original_filename} ({resource.resource_type.value}, {resource.row_count} rows)")
    
    # Create synthesis agent with mocked dependencies
    config = get_config()
    agent = CrossResourceSynthesisAgent(config)
    
    # Mock the dependencies
    agent.metadata_registry = MockMetadataRegistry(resources)
    agent.storage_router = MockStorageRouter()
    agent.db_managers = MockDatabaseManagers()
    
    # Mock the AI execute method for demo
    agent.execute = lambda prompt: f"AI Analysis: {prompt[:100]}... [Mocked response for demo]"
    
    print("\n🤖 Initializing Cross-Resource Synthesis Agent...")
    agent.initialize()
    
    # Test 1: Synthesize customer and order data (join-based)
    print("\n📋 Test 1: Customer-Order Join Synthesis")
    print("-" * 40)
    
    try:
        synthesis_result = await agent.synthesize_resources(
            client_id="demo-client",
            user_id="demo-user",
            resource_ids=[resources[0].resource_id, resources[1].resource_id],
            synthesis_goal="Join customer data with order data to analyze customer purchasing patterns",
            desired_fields={
                "customer_name": "Full name of the customer",
                "email": "Customer email address",
                "order_total": "Total amount of each order",
                "order_date": "Date when order was placed"
            }
        )
        
        print(f"✅ Synthesis Strategy: {synthesis_result.unified_view.synthesis_strategy.value}")
        print(f"📊 Unified Schema Fields: {len(synthesis_result.unified_view.unified_schema)}")
        print(f"🔗 Join Conditions: {len(synthesis_result.unified_view.join_conditions)}")
        print(f"⚠️  Conflicts Resolved: {len(synthesis_result.conflicts_resolved)}")
        print(f"🔄 Harmonizations Applied: {len(synthesis_result.harmonizations_applied)}")
        print(f"📈 Quality Score: {synthesis_result.unified_view.quality_score:.2f}")
        print(f"⚡ Performance Impact: {synthesis_result.unified_view.performance_impact}")
        
        # Show execution plan
        print("\n📋 Execution Plan:")
        for i, step in enumerate(synthesis_result.execution_plan, 1):
            print(f"  {i}. {step}")
        
        # Show recommendations
        if synthesis_result.recommendations:
            print("\n💡 Recommendations:")
            for rec in synthesis_result.recommendations:
                print(f"  • {rec}")
        
        # Show warnings
        if synthesis_result.warnings:
            print("\n⚠️  Warnings:")
            for warning in synthesis_result.warnings:
                print(f"  • {warning}")
    
    except Exception as e:
        print(f"❌ Synthesis failed: {e}")
    
    # Test 2: Three-way synthesis with conflict resolution
    print("\n\n📋 Test 2: Three-Way Synthesis (Customer-Order-Product)")
    print("-" * 50)
    
    try:
        synthesis_result = await agent.synthesize_resources(
            client_id="demo-client",
            user_id="demo-user",
            resource_ids=[r.resource_id for r in resources],
            synthesis_goal="Create comprehensive view combining customer, order, and product data for business intelligence",
            desired_fields={
                "customer_name": "Customer full name",
                "product_name": "Product name",
                "category": "Product category",
                "order_total": "Order total amount",
                "quantity": "Quantity ordered"
            }
        )
        
        print(f"✅ Synthesis Strategy: {synthesis_result.unified_view.synthesis_strategy.value}")
        print(f"📊 Source Resources: {len(synthesis_result.unified_view.source_resources)}")
        print(f"🏗️  Unified Schema Fields: {len(synthesis_result.unified_view.unified_schema)}")
        print(f"⚠️  Conflicts Detected & Resolved: {len(synthesis_result.conflicts_resolved)}")
        
        # Show schema conflicts and resolutions
        if synthesis_result.conflicts_resolved:
            print("\n🔧 Schema Conflicts Resolved:")
            for conflict in synthesis_result.conflicts_resolved:
                print(f"  • {conflict.conflict_type} conflict in field '{conflict.field_names[0]}'")
                print(f"    Data types: {conflict.data_types}")
                print(f"    Resolution: {conflict.resolution_strategy}")
        
        # Show data type harmonizations
        if synthesis_result.harmonizations_applied:
            print("\n🔄 Data Type Harmonizations:")
            for harm in synthesis_result.harmonizations_applied:
                print(f"  • {harm.source_types} → {harm.target_type}")
                print(f"    Logic: {harm.conversion_logic}")
        
        # Show lineage tracking
        print("\n🔍 Data Lineage Tracking:")
        for field, lineage in synthesis_result.unified_view.lineage_tracking.items():
            if lineage:  # Only show fields with lineage
                print(f"  • {field}: {' + '.join(lineage)}")
        
        print(f"\n📈 Overall Quality Score: {synthesis_result.unified_view.quality_score:.2f}")
        print(f"📊 Estimated Result Rows: {synthesis_result.unified_view.estimated_row_count:,}")
    
    except Exception as e:
        print(f"❌ Three-way synthesis failed: {e}")
    
    # Test 3: Agent health check
    print("\n\n🏥 Agent Health Check")
    print("-" * 25)
    
    try:
        health_status = await agent.health_check()
        print(f"Status: {health_status['status']}")
        print(f"Cache Stats: {health_status.get('cache_stats', {})}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    print("\n✨ Cross-Resource Synthesis Demo Complete!")
    print("\nKey Capabilities Demonstrated:")
    print("  ✅ Multi-source data analysis and schema detection")
    print("  ✅ Intelligent join strategy selection")
    print("  ✅ Schema conflict detection and resolution")
    print("  ✅ Data type harmonization with precision tracking")
    print("  ✅ Unified view generation with complete lineage")
    print("  ✅ Quality assessment and performance impact analysis")


if __name__ == "__main__":
    asyncio.run(demonstrate_cross_resource_synthesis())
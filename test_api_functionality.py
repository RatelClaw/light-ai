#!/usr/bin/env python3
"""
Test script to verify the Universal Data Handler API functionality.
"""

import uuid
import json
import tempfile
import os
from pathlib import Path

from light_ai.api import create_api
from light_ai.config import Config

def test_basic_functionality():
    """Test basic API functionality."""
    print("🧪 Testing Universal Data Handler API")
    print("=" * 50)
    
    # Initialize API
    config = Config.load()
    api = create_api(config=config)
    print("✅ API initialized successfully")
    
    # Generate test IDs - using human-readable identifiers as per design
    client_id = "acme-corp"
    user_id = "john.doe"
    print(f"📋 Client ID: {client_id}")
    print(f"👤 User ID: {user_id}")
    
    # Test 1: Upload JSON data
    print("\n1️⃣ Testing JSON upload...")
    test_json = {
        "products": [
            {"id": 1, "name": "Laptop", "price": 999.99, "category": "Electronics"},
            {"id": 2, "name": "Mouse", "price": 29.99, "category": "Electronics"},
            {"id": 3, "name": "Desk", "price": 199.99, "category": "Furniture"}
        ],
        "metadata": {
            "source": "test_data",
            "created": "2024-01-01"
        }
    }
    
    response = api.upload_json(
        client_id=client_id,
        user_id=user_id,
        json_data=test_json,
        resource_name="test_products"
    )
    
    if response.success:
        print("✅ JSON upload successful")
        resource_id = response.data.get('resource_id')
        print(f"   📄 Resource ID: {resource_id}")
    else:
        print(f"❌ JSON upload failed: {response.error}")
        return False
    
    # Test 2: List resources
    print("\n2️⃣ Testing resource listing...")
    response = api.list_resources(client_id=client_id, user_id=user_id)
    
    if response.success:
        resources = response.data.get('resources', [])
        print(f"✅ Found {len(resources)} resources")
        for resource in resources:
            print(f"   📄 {resource.get('original_filename')} ({resource.get('resource_type')})")
    else:
        print(f"❌ Resource listing failed: {response.error}")
        return False
    
    # Test 3: Get resource metadata
    print("\n3️⃣ Testing metadata retrieval...")
    if resource_id:
        response = api.get_resource_metadata(
            resource_id=resource_id,
            client_id=client_id,
            user_id=user_id
        )
        
        if response.success:
            print("✅ Metadata retrieved successfully")
            metadata = response.data
            print(f"   📊 File size: {metadata.get('file_size_bytes', 0)} bytes")
            print(f"   📅 Created: {metadata.get('created_at')}")
        else:
            print(f"❌ Metadata retrieval failed: {response.error}")
    
    # Test 4: SQL query
    print("\n4️⃣ Testing SQL query...")
    sql_query = "SELECT name, price FROM products WHERE category = 'Electronics'"
    
    response = api.query_structured(
        client_id=client_id,
        user_id=user_id,
        sql_query=sql_query,
        output_format="json"
    )
    
    if response.success:
        print("✅ SQL query successful")
        results = response.data.get('results', [])
        print(f"   📊 Found {len(results)} results")
        for result in results[:3]:  # Show first 3
            print(f"   📄 {result}")
    else:
        print(f"❌ SQL query failed: {response.error}")
    
    # Test 5: Natural language query
    print("\n5️⃣ Testing natural language query...")
    question = "What products cost more than $100?"
    
    response = api.query_natural(
        client_id=client_id,
        user_id=user_id,
        question=question,
        output_format="json"
    )
    
    if response.success:
        print("✅ Natural language query successful")
        print(f"   🤖 Generated SQL: {response.data.get('generated_sql', 'N/A')}")
        results = response.data.get('results', [])
        print(f"   📊 Found {len(results)} results")
    else:
        print(f"❌ Natural language query failed: {response.error}")
    
    # Test 6: System statistics
    print("\n6️⃣ Testing system statistics...")
    response = api.get_statistics(client_id=client_id, user_id=user_id)
    
    if response.success:
        print("✅ Statistics retrieved successfully")
        stats = response.data
        print(f"   📊 Total resources: {stats.get('total_resources', 0)}")
        print(f"   💾 Total size: {stats.get('total_size_bytes', 0)} bytes")
    else:
        print(f"❌ Statistics retrieval failed: {response.error}")
    
    print("\n🎉 API functionality test completed!")
    return True

if __name__ == "__main__":
    success = test_basic_functionality()
    exit(0 if success else 1)
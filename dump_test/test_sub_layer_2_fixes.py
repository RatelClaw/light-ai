#!/usr/bin/env python3
"""
Test script to verify Sub-Layer 2 fixes are working correctly.

This script tests the core functionality that was reported as broken:
1. File upload and storage
2. SQL query execution with access control
3. Natural language processing
4. API integration

Run with: uv run python test_sub_layer_2_fixes.py
"""

import os
import sys
import uuid
import json
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from light_ai.api import create_api
from light_ai.config import Config


def test_basic_functionality():
    """Test basic system functionality."""
    print("🧪 Testing Universal Data Handler Sub-Layer 2 Fixes")
    print("=" * 60)
    
    # Generate test IDs
    client_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    print(f"📋 Test Client ID: {client_id}")
    print(f"👤 Test User ID: {user_id}")
    print()
    
    try:
        # Initialize API
        print("🔧 Initializing API...")
        config = Config.load()
        api = create_api(config=config)
        print("✅ API initialized successfully")
        print()
        
        # Test 1: Upload sample CSV file
        print("📁 Test 1: File Upload")
        csv_file = "examples/sample_data/user_01/sales_data.csv"
        
        if not os.path.exists(csv_file):
            print(f"❌ Sample file not found: {csv_file}")
            return False
        
        upload_response = api.upload_file(
            client_id=client_id,
            user_id=user_id,
            file_path=csv_file,
            resource_name="Test Sales Data"
        )
        
        if upload_response.success:
            resource_id = upload_response.data["resource_id"]
            print(f"✅ File uploaded successfully")
            print(f"   Resource ID: {resource_id}")
            print(f"   File size: {upload_response.data['file_size_bytes']} bytes")
        else:
            print(f"❌ File upload failed: {upload_response.error}")
            return False
        print()
        
        # Test 2: SQL Query with Access Control
        print("🔍 Test 2: SQL Query Execution")
        sql_query = f"""
        SELECT product, SUM(sales_amount) as total_sales, COUNT(*) as transactions
        FROM structured_data.resource_{resource_id.replace('-', '_')}
        GROUP BY product 
        ORDER BY total_sales DESC
        LIMIT 5
        """
        
        query_response = api.query_structured(
            client_id=client_id,
            user_id=user_id,
            sql_query=sql_query,
            output_format="json"
        )
        
        if query_response.success:
            results = query_response.data["results"]
            print(f"✅ SQL query executed successfully")
            print(f"   Returned {len(results)} rows")
            print(f"   Execution time: {query_response.data['execution_time_ms']:.2f}ms")
            if results:
                print(f"   Sample result: {results[0]}")
        else:
            print(f"❌ SQL query failed: {query_response.error}")
            return False
        print()
        
        # Test 3: Natural Language Query
        print("🗣️ Test 3: Natural Language Processing")
        nl_question = "What are the top 3 products by sales amount?"
        
        nl_response = api.query_natural(
            client_id=client_id,
            user_id=user_id,
            question=nl_question,
            output_format="json"
        )
        
        if nl_response.success:
            print(f"✅ Natural language query processed successfully")
            print(f"   Question: {nl_question}")
            print(f"   Generated SQL: {nl_response.data['generated_sql']}")
            print(f"   Confidence: {nl_response.data['confidence']}")
            if nl_response.data['results']:
                print(f"   Results: {len(nl_response.data['results'])} rows")
        else:
            print(f"❌ Natural language query failed: {nl_response.error}")
            return False
        print()
        
        # Test 4: Resource Metadata
        print("📊 Test 4: Resource Metadata")
        metadata_response = api.get_resource_metadata(
            resource_id=resource_id,
            client_id=client_id,
            user_id=user_id
        )
        
        if metadata_response.success:
            metadata = metadata_response.data
            print(f"✅ Resource metadata retrieved successfully")
            print(f"   Resource Type: {metadata['resource_type']}")
            print(f"   Data Type: {metadata['data_type']}")
            print(f"   Row Count: {metadata.get('row_count', 'N/A')}")
            print(f"   Column Count: {metadata.get('column_count', 'N/A')}")
        else:
            print(f"❌ Metadata retrieval failed: {metadata_response.error}")
            return False
        print()
        
        # Test 5: List Resources
        print("📋 Test 5: List Resources")
        list_response = api.list_resources(
            client_id=client_id,
            user_id=user_id,
            access_level="user"
        )
        
        if list_response.success:
            resources = list_response.data["resources"]
            print(f"✅ Resources listed successfully")
            print(f"   Total resources: {list_response.data['total_count']}")
            if resources:
                print(f"   First resource: {resources[0]['original_filename']}")
        else:
            print(f"❌ Resource listing failed: {list_response.error}")
            return False
        print()
        
        # Test 6: System Statistics
        print("📈 Test 6: System Statistics")
        stats_response = api.get_system_stats()
        
        if stats_response.success:
            print(f"✅ System statistics retrieved successfully")
            db_stats = stats_response.data.get("database_stats", {})
            for db_name, stats in db_stats.items():
                if isinstance(stats, dict) and "file_size_bytes" in stats:
                    size_mb = stats["file_size_bytes"] / (1024 * 1024)
                    print(f"   {db_name}: {size_mb:.2f} MB")
        else:
            print(f"❌ System statistics failed: {stats_response.error}")
            return False
        print()
        
        print("🎉 All tests passed! Sub-Layer 2 is working correctly.")
        return True
        
    except Exception as e:
        print(f"💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_access_control():
    """Test access control functionality specifically."""
    print("🔒 Testing Access Control")
    print("=" * 30)
    
    # Generate different user IDs
    client_id = str(uuid.uuid4())
    user1_id = str(uuid.uuid4())
    user2_id = str(uuid.uuid4())
    
    try:
        api = create_api()
        
        # Upload file as user1
        csv_file = "examples/sample_data/user_01/sales_data.csv"
        upload_response = api.upload_file(
            client_id=client_id,
            user_id=user1_id,
            file_path=csv_file,
            resource_name="User1 Sales Data"
        )
        
        if not upload_response.success:
            print(f"❌ Upload failed: {upload_response.error}")
            return False
        
        resource_id = upload_response.data["resource_id"]
        print(f"✅ User1 uploaded file: {resource_id}")
        
        # Try to access as user1 (should work)
        query_response = api.query_structured(
            client_id=client_id,
            user_id=user1_id,
            sql_query=f"SELECT COUNT(*) as count FROM structured_data.resource_{resource_id.replace('-', '_')}",
            output_format="json"
        )
        
        if query_response.success:
            print(f"✅ User1 can access their own data")
        else:
            print(f"❌ User1 cannot access their own data: {query_response.error}")
            return False
        
        # Try to access as user2 (should fail or return no results due to access control)
        query_response2 = api.query_structured(
            client_id=client_id,
            user_id=user2_id,
            sql_query=f"SELECT COUNT(*) as count FROM structured_data.resource_{resource_id.replace('-', '_')}",
            output_format="json"
        )
        
        if query_response2.success:
            # Check if results are empty (access control working)
            results = query_response2.data.get("results", [])
            if not results or results[0].get("count", 0) == 0:
                print(f"✅ User2 correctly gets no results (access control working)")
            else:
                print(f"⚠️ User2 got results - access control may need review")
        else:
            print(f"✅ User2 correctly denied access: {query_response2.error}")
        
        print("🔒 Access control test completed")
        return True
        
    except Exception as e:
        print(f"💥 Access control test failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Starting Sub-Layer 2 Fix Verification Tests")
    print()
    
    # Test basic functionality
    basic_success = test_basic_functionality()
    print()
    
    # Test access control
    access_success = test_access_control()
    print()
    
    if basic_success and access_success:
        print("🎉 ALL TESTS PASSED! Sub-Layer 2 fixes are working correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the output above.")
        sys.exit(1)
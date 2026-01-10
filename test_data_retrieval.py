#!/usr/bin/env python3
"""
Test the new data retrieval engine to verify it can access all stored data
"""

import sys
import json
from pathlib import Path

# Add the light_ai module to the path
sys.path.append(str(Path(__file__).parent))

from light_ai.data_retrieval_engine import DataRetrievalEngine

def test_data_retrieval():
    """Test the data retrieval engine with actual stored data"""
    print("🔍 Testing Data Retrieval Engine")
    print("=" * 50)
    
    # Initialize the retrieval engine
    engine = DataRetrievalEngine()
    
    # Test with the most recent data from logs
    client_id = "97951dcf-2365-48dd-b522-bdfe8b7e7842"
    user_id = "a0758013-49f1-4a61-8849-04320afd4c7b"
    resource_id = "dc23a113-37a7-4cd4-bd4b-9b883a3eee5e"
    
    print(f"Testing with:")
    print(f"  Client ID: {client_id}")
    print(f"  User ID: {user_id}")
    print(f"  Resource ID: {resource_id}")
    
    # Test 1: Get all user resources
    print(f"\n📋 Test 1: Get User Resources")
    resources = engine.get_user_resources(client_id, user_id)
    print(f"Found {len(resources)} resources:")
    
    for resource in resources:
        print(f"  • {resource.resource_id}")
        print(f"    Type: {resource.resource_type}/{resource.data_type}")
        print(f"    File: {resource.original_filename}")
        print(f"    Size: {resource.file_size_bytes} bytes")
        print(f"    Created: {resource.created_at}")
    
    if not resources:
        print("❌ No resources found!")
        return False
    
    # Test 2: Get specific resource data
    print(f"\n📄 Test 2: Get Specific Resource Data")
    result = engine.get_resource_by_id(resource_id)
    
    if result.success:
        print("✅ Successfully retrieved resource data!")
        print(f"Source: {result.source}")
        print(f"Data preview:")
        print(json.dumps(result.data, indent=2)[:500] + "..." if len(str(result.data)) > 500 else json.dumps(result.data, indent=2))
    else:
        print(f"❌ Failed to retrieve resource: {result.error}")
    
    # Test 3: Get all user data
    print(f"\n🗂️  Test 3: Get All User Data")
    all_data = engine.get_all_user_data(client_id, user_id)
    
    print(f"Total resources: {all_data['total_resources']}")
    print(f"JSON files: {len(all_data['data_by_source']['json_files'])}")
    print(f"DuckDB tables: {len(all_data['data_by_source']['duckdb_tables'])}")
    print(f"Errors: {len(all_data['data_by_source']['errors'])}")
    
    if all_data['data_by_source']['errors']:
        print("Errors encountered:")
        for error in all_data['data_by_source']['errors']:
            print(f"  • {error['source']}: {error['error']}")
    
    # Test 4: Search user data
    print(f"\n🔍 Test 4: Search User Data")
    search_query = "Alice Johnson Computer Science"
    search_results = engine.search_user_data(client_id, user_id, search_query)
    
    print(f"Search query: '{search_query}'")
    print(f"Resources searched: {search_results['total_resources_searched']}")
    print(f"Matches found: {len(search_results['matches'])}")
    print(f"Summary: {search_results['summary']}")
    
    for match in search_results['matches']:
        print(f"  • Resource {match['resource_id']}")
        print(f"    Relevance: {match['relevance_score']:.2f}")
        print(f"    Matched keywords: {match['matched_keywords']}")
        print(f"    Data preview: {str(match['data'])[:200]}...")
    
    # Test 5: Test with different user IDs from the data
    print(f"\n🔄 Test 5: Test Other Users")
    
    # Get some other user IDs from the directory structure
    other_test_cases = [
        ("cd8b154c-818e-4089-9783-dca56c2324f8", "6e1b50a6-669d-47d8-9258-def11ac7ef6b"),
        ("040f5f41-b386-4dcd-96e3-d01186c19fa8", "3d5f91c4-9d11-4e39-a15e-e1bf36f2f506"),
    ]
    
    for test_client_id, test_user_id in other_test_cases:
        print(f"\nTesting {test_client_id[:8]}.../{test_user_id[:8]}...")
        test_resources = engine.get_user_resources(test_client_id, test_user_id)
        print(f"  Found {len(test_resources)} resources")
        
        if test_resources:
            # Try to get data from the first resource
            first_resource = test_resources[0]
            test_result = engine.get_resource_by_id(first_resource.resource_id)
            if test_result.success:
                print(f"  ✅ Successfully retrieved data from {first_resource.resource_id}")
            else:
                print(f"  ❌ Failed to retrieve data: {test_result.error}")
    
    print(f"\n" + "=" * 50)
    print("🎉 Data Retrieval Engine Test Complete!")
    
    return True

if __name__ == "__main__":
    success = test_data_retrieval()
    exit(0 if success else 1)
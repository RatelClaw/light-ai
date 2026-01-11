#!/usr/bin/env python3
"""
Debug script to test data retrieval for the specific user.
"""

import sys
import os
sys.path.append('.')

from light_ai.data_retrieval_engine import get_retrieval_engine
import json

def main():
    client_id = "e5711eef-7d8f-4768-b4cc-c13403a2fd06"
    user_id = "2f8a029b-b375-4303-8371-ba297c0b754d"
    
    print(f"Testing data retrieval for client_id: {client_id}")
    print(f"Testing data retrieval for user_id: {user_id}")
    print("=" * 80)
    
    # Get the retrieval engine
    engine = get_retrieval_engine()
    
    # Test 1: Get user resources
    print("1. Getting user resources...")
    resources = engine.get_user_resources(client_id, user_id)
    print(f"Found {len(resources)} resources:")
    for resource in resources:
        print(f"  - Resource ID: {resource.resource_id}")
        print(f"    Filename: {resource.original_filename}")
        print(f"    Data Type: {resource.data_type}")
        print(f"    Storage Path: {resource.storage_path}")
        print(f"    File exists: {os.path.exists(resource.storage_path)}")
        print()
    
    # Test 2: Get all user data
    print("2. Getting all user data...")
    all_data = engine.get_all_user_data(client_id, user_id)
    print(f"Total resources: {all_data['total_resources']}")
    print(f"JSON files found: {len(all_data['data_by_source']['json_files'])}")
    print(f"Errors: {len(all_data['data_by_source']['errors'])}")
    
    # Print errors if any
    if all_data['data_by_source']['errors']:
        print("Errors encountered:")
        for error in all_data['data_by_source']['errors']:
            print(f"  - Resource {error['resource_id']}: {error['error']}")
    
    # Print JSON data if found
    if all_data['data_by_source']['json_files']:
        print("JSON data found:")
        for json_item in all_data['data_by_source']['json_files']:
            print(f"  - Resource {json_item['resource_id']}:")
            print(f"    Data keys: {list(json_item['data'].keys()) if json_item['data'] else 'None'}")
            if json_item['data']:
                print(f"    Sample data: {str(json_item['data'])[:200]}...")
    
    # Test 3: Test individual resource retrieval
    print("\n3. Testing individual resource retrieval...")
    for resource in resources:
        print(f"Testing resource {resource.resource_id}...")
        result = engine.get_json_data(resource)
        print(f"  Success: {result.success}")
        if result.success:
            print(f"  Data keys: {list(result.data.keys()) if result.data else 'None'}")
        else:
            print(f"  Error: {result.error}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Debug script to test JSON data analysis directly.
"""

import sys
import os
import json
sys.path.append('.')

from light_ai.sub_layer_2.ai_data_analyst import AIDataAnalyst
from light_ai.core.models import ResourceMetadata, ResourceType, DataType
from light_ai.config import get_config

def main():
    client_id = "e5711eef-7d8f-4768-b4cc-c13403a2fd06"
    user_id = "2f8a029b-b375-4303-8371-ba297c0b754d"
    
    print("Testing JSON data analysis directly...")
    print("=" * 80)
    
    # Create mock ResourceMetadata objects for the JSON files
    resource1 = ResourceMetadata(
        resource_id="82e32121-257f-4fd6-9a18-31c19cffab4b",
        client_id=client_id,
        user_id=user_id,
        original_filename="tmpqdjonvrv.json",
        resource_type=ResourceType.JSON,
        data_type=DataType.JSON,
        storage_path="data/json/e5711eef-7d8f-4768-b4cc-c13403a2fd06/2f8a029b-b375-4303-8371-ba297c0b754d/82e32121-257f-4fd6-9a18-31c19cffab4b/v1_tmpqdjonvrv.json",
        file_size_bytes=1000,
        row_count=None,
        column_count=None
    )
    
    resource2 = ResourceMetadata(
        resource_id="8ca33e92-13d5-436f-bbff-ac5d4f44a8d1",
        client_id=client_id,
        user_id=user_id,
        original_filename="tmppajhb0oc.json",
        resource_type=ResourceType.JSON,
        data_type=DataType.JSON,
        storage_path="data/json/e5711eef-7d8f-4768-b4cc-c13403a2fd06/2f8a029b-b375-4303-8371-ba297c0b754d/8ca33e92-13d5-436f-bbff-ac5d4f44a8d1/v1_tmppajhb0oc.json",
        file_size_bytes=1000,
        row_count=None,
        column_count=None
    )
    
    # Get the AI analyst
    config = get_config()
    analyst = AIDataAnalyst(config)
    
    print("1. Testing _get_json_sample_data method...")
    try:
        sample_data1 = analyst._get_json_sample_data(resource1)
        print(f"Resource 1 sample data length: {len(sample_data1)}")
        if sample_data1:
            print(f"Resource 1 sample data keys: {list(sample_data1[0].keys())}")
            print(f"Resource 1 sample data preview: {str(sample_data1[0])[:200]}...")
        
        sample_data2 = analyst._get_json_sample_data(resource2)
        print(f"Resource 2 sample data length: {len(sample_data2)}")
        if sample_data2:
            print(f"Resource 2 sample data keys: {list(sample_data2[0].keys())}")
    except Exception as e:
        print(f"Error getting sample data: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n2. Testing _build_data_source_contexts method...")
    try:
        data_sources = analyst._build_data_source_contexts([resource1, resource2])
        print(f"Built {len(data_sources)} data source contexts:")
        for ds in data_sources:
            print(f"  - Resource ID: {ds.resource_id}")
            print(f"    Resource Type: {ds.resource_type}")
            print(f"    Sample Data Length: {len(ds.sample_data) if ds.sample_data else 0}")
            if ds.sample_data:
                print(f"    Sample Data Keys: {list(ds.sample_data[0].keys()) if isinstance(ds.sample_data[0], dict) else 'N/A'}")
    except Exception as e:
        print(f"Error building data source contexts: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n3. Testing _analyze_json_data method...")
    try:
        if 'data_sources' in locals():
            json_sources = [ds for ds in data_sources if ds.resource_type == ResourceType.JSON]
            if json_sources:
                json_results = analyst._analyze_json_data("analyze persona and context", json_sources, client_id, user_id)
                print(f"JSON analysis results: {len(json_results)} results")
                for result in json_results:
                    print(f"  - Resource: {result['filename']}")
                    print(f"    Data items: {result['row_count']}")
                    if result.get('analysis', {}).get('insights'):
                        print(f"    Insights: {result['analysis']['insights'][:2]}")  # First 2 insights
    except Exception as e:
        print(f"Error analyzing JSON data: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n4. Testing _analyze_json_content method...")
    try:
        # Load the actual JSON data
        with open("data/json/e5711eef-7d8f-4768-b4cc-c13403a2fd06/2f8a029b-b375-4303-8371-ba297c0b754d/82e32121-257f-4fd6-9a18-31c19cffab4b/v1_tmpqdjonvrv.json", 'r') as f:
            json_data = json.load(f)
        
        analysis = analyst._analyze_json_content("analyze persona and context", [json_data])
        print(f"JSON content analysis:")
        print(f"  - Relevant fields: {analysis.get('relevant_fields', [])}")
        print(f"  - Insights: {analysis.get('insights', [])}")
        print(f"  - Field summary count: {len(analysis.get('field_summary', {}))}")
    except Exception as e:
        print(f"Error analyzing JSON content: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
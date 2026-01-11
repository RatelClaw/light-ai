#!/usr/bin/env python3
"""
Debug script to test the AI Data Analyst with the specific user.
"""

import sys
import os
sys.path.append('.')

from light_ai.sub_layer_2.ai_data_analyst import AIDataAnalyst
from light_ai.config import get_config

def main():
    client_id = "e5711eef-7d8f-4768-b4cc-c13403a2fd06"
    user_id = "2f8a029b-b375-4303-8371-ba297c0b754d"
    question = "analyze persona and context"
    
    print(f"Testing AI Data Analyst for client_id: {client_id}")
    print(f"Testing AI Data Analyst for user_id: {user_id}")
    print(f"Question: {question}")
    print("=" * 80)
    
    # Get the AI analyst
    config = get_config()
    analyst = AIDataAnalyst(config)
    
    # Test the analysis
    try:
        print("1. Initializing AI Data Analyst...")
        analyst.initialize()
        
        print("2. Identifying relevant resources...")
        resources = analyst._identify_relevant_resources(question, client_id, user_id)
        print(f"Found {len(resources)} resources:")
        for resource in resources:
            print(f"  - Resource ID: {resource.resource_id}")
            print(f"    Filename: {resource.original_filename}")
            print(f"    Resource Type: {resource.resource_type}")
            print(f"    Data Type: {resource.data_type}")
            print(f"    Storage Path: {resource.storage_path}")
            print()
        
        print("3. Building data source contexts...")
        data_sources = analyst._build_data_source_contexts(resources)
        print(f"Built {len(data_sources)} data source contexts:")
        for ds in data_sources:
            print(f"  - Resource ID: {ds.resource_id}")
            print(f"    Resource Type: {ds.resource_type}")
            print(f"    Sample Data Length: {len(ds.sample_data) if ds.sample_data else 0}")
            if ds.sample_data:
                print(f"    Sample Data Keys: {list(ds.sample_data[0].keys()) if ds.sample_data and isinstance(ds.sample_data[0], dict) else 'N/A'}")
            print()
        
        print("4. Running full analysis...")
        report = analyst.analyze_data(question, client_id, user_id)
        print(f"Analysis Type: {report.analysis_type}")
        print(f"Executive Summary: {report.executive_summary}")
        print(f"Number of Insights: {len(report.key_insights)}")
        print(f"Number of Data Sources: {len(report.data_sources_used)}")
        
        if report.key_insights:
            print("\nInsights:")
            for insight in report.key_insights:
                print(f"  - {insight.title}: {insight.description}")
        
        if report.data_sources_used:
            print("\nData Sources Used:")
            for ds in report.data_sources_used:
                print(f"  - {ds.filename} (Sample Data: {len(ds.sample_data) if ds.sample_data else 0} items)")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
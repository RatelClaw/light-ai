#!/usr/bin/env python3
"""
Test real conversation analysis using the existing API system.
Upload conversation JSON and analyze it with the new intelligent analyzer.
"""

import json
import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from light_ai.api import UniversalDataHandler, APIResponse
from light_ai.agents.enhanced_analysis_agent import get_analysis_agent, AnalysisRequest

# Sample conversation data
CONVERSATION_DATA = {
    "conversation_id": "CONV-009",
    "messages": [
        {
            "role": "user",
            "timestamp": "2026-01-11T09:00:00Z",
            "content": "Hey, before we start, I want to tell you a bit about myself so you can respond better."
        },
        {
            "role": "assistant",
            "timestamp": "2026-01-11T09:00:05Z",
            "content": "Sure! Go ahead—I'll tailor my responses based on what you share."
        },
        {
            "role": "user",
            "timestamp": "2026-01-11T09:01:00Z",
            "content": "I'm a 31-year-old data analyst working in the retail sector. I've been in this field for around 7 years."
        },
        {
            "role": "assistant",
            "timestamp": "2026-01-11T09:01:10Z",
            "content": "Nice! I'll keep the retail and data-analytics context in mind."
        },
        {
            "role": "user",
            "timestamp": "2026-01-11T09:02:00Z",
            "content": "I mostly work with SQL, Python, and Power BI. I prefer short, practical answers instead of long theory."
        },
        {
            "role": "assistant",
            "timestamp": "2026-01-11T09:02:10Z",
            "content": "Got it—concise, practical, and tool-focused responses coming up."
        },
        {
            "role": "user",
            "timestamp": "2026-01-11T09:03:00Z",
            "content": "My current goal is to move into a senior analytics role and eventually lead a small team."
        },
        {
            "role": "assistant",
            "timestamp": "2026-01-11T09:03:10Z",
            "content": "That's a great goal. I'll align my advice toward leadership growth and senior-level thinking."
        },
        {
            "role": "user",
            "timestamp": "2026-01-11T09:04:00Z",
            "content": "One challenge I face is explaining technical insights to non-technical stakeholders."
        },
        {
            "role": "assistant",
            "timestamp": "2026-01-11T09:04:15Z",
            "content": "Understood. I'll focus on simple explanations, analogies, and business-friendly language for you."
        }
    ]
}

def main():
    print("=" * 80)
    print("REAL CONVERSATION ANALYSIS TEST")
    print("=" * 80)
    print()
    
    # Test credentials
    client_id = "test_client_conv"
    user_id = "test_user_conv"
    
    try:
        # Step 1: Initialize the Universal Data Handler
        print("Step 1: Initializing Universal Data Handler...")
        handler = UniversalDataHandler()
        print("✓ Handler initialized")
        print()
        
        # Step 2: Save conversation to a temporary JSON file
        print("Step 2: Preparing conversation data...")
        temp_file = Path("temp_conversation.json")
        with open(temp_file, "w") as f:
            json.dump(CONVERSATION_DATA, f, indent=2)
        print(f"✓ Conversation saved to {temp_file}")
        print()
        
        # Step 3: Upload the conversation JSON
        print("Step 3: Uploading conversation data...")
        upload_response = handler.upload_file(
            client_id=client_id,
            user_id=user_id,
            file_path=str(temp_file),
            resource_name="conversation.json"
        )
        
        if not upload_response.success:
            print(f"✗ Upload failed: {upload_response.error}")
            return 1
        
        resource_id = upload_response.data.get("resource_id")
        print(f"✓ Upload successful! Resource ID: {resource_id}")
        print()
        
        # Step 4: Analyze with the enhanced analysis agent
        print("Step 4: Analyzing conversation with intelligent analyzer...")
        analysis_agent = get_analysis_agent()
        
        analysis_request = AnalysisRequest(
            client_id=client_id,
            user_id=user_id,
            query="Extract persona and context from conversation",
            desired_fields={"persona": "User characteristics", "context": "Situational context"}
        )
        
        analysis_result = analysis_agent.analyze_user_data(analysis_request)
        print()
        
        # Step 5: Display results
        print("=" * 80)
        print("ANALYSIS RESULTS")
        print("=" * 80)
        print()
        
        if analysis_result.success:
            print("✓ Analysis successful!")
            print()
            
            if analysis_result.persona:
                print("PERSONA:")
                print("-" * 80)
                print(analysis_result.persona)
                print()
                print()
            
            if analysis_result.context:
                print("CONTEXT:")
                print("-" * 80)
                print(analysis_result.context)
                print()
                print()
            
            if analysis_result.insights:
                print("INSIGHTS:")
                print("-" * 80)
                print(analysis_result.insights)
                print()
                print()
            
            if analysis_result.recommendations:
                print("RECOMMENDATIONS:")
                print("-" * 80)
                print(analysis_result.recommendations)
                print()
                print()
            
            if analysis_result.data_summary:
                print("DATA SUMMARY:")
                print("-" * 80)
                print(json.dumps(analysis_result.data_summary, indent=2))
                print()
        else:
            print(f"✗ Analysis failed: {analysis_result.error}")
            return 1
        
        # Cleanup
        print("Cleaning up temporary file...")
        temp_file.unlink()
        print("✓ Cleanup complete")
        print()
        
        print("=" * 80)
        print("TEST COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        
        # Cleanup on error
        if temp_file.exists():
            temp_file.unlink()
        
        return 1

if __name__ == "__main__":
    sys.exit(main())

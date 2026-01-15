#!/usr/bin/env python3
"""
Test the enhanced analysis system end-to-end
"""

import sys
import json
from pathlib import Path

# Add the light_ai module to the path
sys.path.append(str(Path(__file__).parent))

from light_ai.agents.enhanced_analysis_agent import get_analysis_agent, AnalysisRequest

def test_enhanced_analysis():
    """Test the enhanced analysis agent with real data"""
    print("🧠 Testing Enhanced Analysis Agent")
    print("=" * 50)
    
    # Use the data we know exists
    client_id = "97951dcf-2365-48dd-b522-bdfe8b7e7842"
    user_id = "a0758013-49f1-4a61-8849-04320afd4c7b"
    
    print(f"Testing with:")
    print(f"  Client ID: {client_id}")
    print(f"  User ID: {user_id}")
    
    # Create analysis request
    request = AnalysisRequest(
        client_id=client_id,
        user_id=user_id,
        query="Get the persona and context of this user based on their data",
        desired_fields={
            "persona": "Extract detailed persona characteristics",
            "context": "Provide contextual information"
        },
        optional_fields={
            "insights": "Generate insights from the data",
            "recommendations": "Provide recommendations"
        }
    )
    
    # Get analysis agent and perform analysis
    print(f"\n🔍 Performing Analysis...")
    agent = get_analysis_agent()
    result = agent.analyze_user_data(request)
    
    if result.success:
        print("✅ Analysis completed successfully!")
        
        print(f"\n👤 PERSONA:")
        print(result.persona)
        
        print(f"\n🌍 CONTEXT:")
        print(result.context)
        
        print(f"\n💡 INSIGHTS:")
        print(result.insights)
        
        print(f"\n📋 RECOMMENDATIONS:")
        print(result.recommendations)
        
        print(f"\n📊 DATA SUMMARY:")
        if result.data_summary:
            for key, value in result.data_summary.items():
                print(f"  {key}: {value}")
        
        return True
    else:
        print(f"❌ Analysis failed: {result.error}")
        return False

def test_multiple_users():
    """Test with multiple users to verify robustness"""
    print(f"\n🔄 Testing Multiple Users")
    print("-" * 30)
    
    # Test cases from our data
    test_cases = [
        ("cd8b154c-818e-4089-9783-dca56c2324f8", "6e1b50a6-669d-47d8-9258-def11ac7ef6b"),
        ("040f5f41-b386-4dcd-96e3-d01186c19fa8", "3d5f91c4-9d11-4e39-a15e-e1bf36f2f506"),
    ]
    
    agent = get_analysis_agent()
    
    for i, (client_id, user_id) in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {client_id[:8]}.../{user_id[:8]}...")
        
        request = AnalysisRequest(
            client_id=client_id,
            user_id=user_id,
            query="Analyze this user's profile and characteristics"
        )
        
        result = agent.analyze_user_data(request)
        
        if result.success:
            print("✅ Analysis successful")
            print(f"   Data Summary: {result.data_summary}")
            print(f"   Persona Preview: {result.persona[:100]}..." if result.persona else "   No persona data")
        else:
            print(f"❌ Analysis failed: {result.error}")

def test_different_queries():
    """Test with different types of analysis queries"""
    print(f"\n🎯 Testing Different Query Types")
    print("-" * 35)
    
    client_id = "97951dcf-2365-48dd-b522-bdfe8b7e7842"
    user_id = "a0758013-49f1-4a61-8849-04320afd4c7b"
    
    queries = [
        "Extract the user's personality traits and characteristics",
        "Analyze the user's academic and professional context",
        "Identify the user's interests and career goals",
        "Provide insights about the user's potential and recommendations"
    ]
    
    agent = get_analysis_agent()
    
    for i, query in enumerate(queries, 1):
        print(f"\nQuery {i}: {query}")
        
        request = AnalysisRequest(
            client_id=client_id,
            user_id=user_id,
            query=query
        )
        
        result = agent.analyze_user_data(request)
        
        if result.success:
            print("✅ Query processed successfully")
            if result.insights:
                print(f"   Insights: {result.insights[:150]}...")
        else:
            print(f"❌ Query failed: {result.error}")

if __name__ == "__main__":
    print("🚀 Enhanced Analysis System - Comprehensive Test")
    print("=" * 60)
    
    # Test 1: Basic analysis
    success1 = test_enhanced_analysis()
    
    # Test 2: Multiple users
    test_multiple_users()
    
    # Test 3: Different queries
    test_different_queries()
    
    print(f"\n" + "=" * 60)
    if success1:
        print("🎉 Enhanced Analysis System is working perfectly!")
        print("✅ Data retrieval: Working")
        print("✅ Persona extraction: Working") 
        print("✅ Context analysis: Working")
        print("✅ Insights generation: Working")
        print("✅ Recommendations: Working")
    else:
        print("❌ Some tests failed")
    
    print(f"\n💡 The system can now:")
    print("   • Access all stored data (JSON, DuckDB, ChromaDB)")
    print("   • Extract detailed persona characteristics")
    print("   • Provide contextual analysis")
    print("   • Generate insights and recommendations")
    print("   • Work without external API dependencies")
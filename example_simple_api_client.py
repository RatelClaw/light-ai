#!/usr/bin/env python3
"""
Example client for Simple Analysis API.

This shows how to call the Simple Analysis API from another Python application.
"""

import requests
import json
import uuid


class SimpleAnalysisClient:
    """Client for Simple Analysis API."""
    
    def __init__(self, upload_api_url="http://127.0.0.1:8000", analysis_api_url="http://127.0.0.1:5000"):
        self.upload_api_url = upload_api_url
        self.analysis_api_url = analysis_api_url
    
    def upload_json_data(self, client_id, user_id, json_data, resource_name):
        """Upload JSON data to the system."""
        url = f"{self.upload_api_url}/api/v1/upload/json"
        payload = {
            "client_id": client_id,
            "user_id": user_id,
            "json_data": json_data,
            "resource_name": resource_name,
            "flatten": False
        }
        
        response = requests.post(url, json=payload)
        return response.json(), response.status_code
    
    def analyze(self, client_id, user_id, query, desired_fields=None, optional_fields=None):
        """Run analysis on user's data."""
        url = f"{self.analysis_api_url}/analyze"
        payload = {
            "client_id": client_id,
            "user_id": user_id,
            "query": query
        }
        
        if desired_fields:
            payload["desired_fields"] = desired_fields
        if optional_fields:
            payload["optional_fields"] = optional_fields
        
        response = requests.post(url, json=payload)
        return response.json(), response.status_code
    
    def analyze_simple(self, client_id, user_id, query):
        """Run simple analysis (minimal response)."""
        url = f"{self.analysis_api_url}/analyze/simple"
        payload = {
            "client_id": client_id,
            "user_id": user_id,
            "query": query
        }
        
        response = requests.post(url, json=payload)
        return response.json(), response.status_code
    
    def health_check(self):
        """Check if the analysis API is healthy."""
        url = f"{self.analysis_api_url}/health"
        response = requests.get(url)
        return response.json(), response.status_code


def main():
    """Example usage of the Simple Analysis API client."""
    
    # Initialize client
    client = SimpleAnalysisClient()
    
    # Generate IDs (or use existing ones)
    client_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    print("🚀 Simple Analysis API Client Example")
    print("=" * 50)
    print(f"Client ID: {client_id}")
    print(f"User ID: {user_id}")
    print()
    
    # Step 1: Health check
    print("1️⃣  Checking API health...")
    health, status = client.health_check()
    print(f"   Status: {status}")
    print(f"   Response: {json.dumps(health, indent=2)}")
    print()
    
    # Step 2: Upload data
    print("2️⃣  Uploading user data...")
    user_data = {
        "user_profile": {
            "name": "Jane Smith",
            "age": 28,
            "occupation": "Data Scientist",
            "interests": ["Machine Learning", "Python", "Data Visualization"],
            "skills": ["Python", "SQL", "TensorFlow", "Pandas"],
            "experience_years": 5,
            "education": "MS in Computer Science"
        }
    }
    
    upload_result, status = client.upload_json_data(
        client_id=client_id,
        user_id=user_id,
        json_data=user_data,
        resource_name="user_profile_data"
    )
    
    print(f"   Status: {status}")
    if upload_result.get("success"):
        print(f"   ✅ Upload successful!")
        print(f"   Resource ID: {upload_result['data']['resource_id']}")
    else:
        print(f"   ❌ Upload failed: {upload_result.get('error')}")
    print()
    
    # Step 3: Run full analysis
    print("3️⃣  Running full analysis...")
    analysis_result, status = client.analyze(
        client_id=client_id,
        user_id=user_id,
        query="Extract detailed persona characteristics and provide career insights for this data scientist"
    )
    
    print(f"   Status: {status}")
    if analysis_result.get("success"):
        print(f"   ✅ Analysis successful!")
        data = analysis_result["data"]
        print(f"\n   📊 Persona: {data.get('persona', 'N/A')[:100]}...")
        print(f"\n   🌍 Context: {data.get('context', 'N/A')[:100]}...")
        print(f"\n   💡 Insights: {data.get('insights', 'N/A')[:100]}...")
        print(f"\n   🎯 Recommendations: {data.get('recommendations', 'N/A')[:100]}...")
        
        summary = data.get('data_summary', {})
        print(f"\n   📈 Summary:")
        print(f"      - Sources used: {summary.get('sources_used', 0)}")
        print(f"      - Confidence: {summary.get('confidence_score', 0):.2f}")
        print(f"      - Execution time: {summary.get('execution_time_ms', 0):.0f}ms")
    else:
        print(f"   ❌ Analysis failed: {analysis_result.get('error')}")
    print()
    
    # Step 4: Run simple analysis
    print("4️⃣  Running simple analysis...")
    simple_result, status = client.analyze_simple(
        client_id=client_id,
        user_id=user_id,
        query="What are the key strengths of this person?"
    )
    
    print(f"   Status: {status}")
    if simple_result.get("success"):
        print(f"   ✅ Simple analysis successful!")
        print(f"   Insights: {simple_result.get('insights', [])}")
        print(f"   Confidence: {simple_result.get('confidence', 0):.2f}")
    else:
        print(f"   ❌ Analysis failed: {simple_result.get('error')}")
    print()
    
    print("=" * 50)
    print("✅ Example complete!")
    print()
    print("💡 You can now integrate this client into your application:")
    print("   - Import SimpleAnalysisClient")
    print("   - Upload data with upload_json_data()")
    print("   - Run analysis with analyze() or analyze_simple()")
    print("   - Process the results in your application")


if __name__ == "__main__":
    main()

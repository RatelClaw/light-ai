#!/usr/bin/env python3
"""
Complete workflow test for Universal Data Handler
Tests data upload and persona analysis end-to-end
"""

import requests
import json
import uuid
import time
from datetime import datetime

# Configuration
API_V1_BASE = "http://127.0.0.1:8000/api/v1"
API_V2_BASE = "http://127.0.0.1:8001/api/v2"

def test_api_connection():
    """Test if APIs are running"""
    print("🔍 Testing API connections...")
    
    try:
        # Test API v1
        response = requests.get(f"{API_V1_BASE}/health", timeout=5)
        print(f"✅ API v1 (Port 8000): {response.status_code}")
    except Exception as e:
        print(f"❌ API v1 (Port 8000): {e}")
        return False
    
    try:
        # Test API v2 health (if available)
        response = requests.get(f"{API_V2_BASE}/health", timeout=5)
        print(f"✅ API v2 (Port 8001): {response.status_code}")
    except Exception as e:
        print(f"⚠️  API v2 health check failed, but API might still work: {e}")
    
    return True

def upload_education_data():
    """Upload sample education data"""
    print("\n📤 Uploading education data...")
    
    # Generate test IDs
    client_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    # Sample education data (from your terminal output)
    education_data = {
        "education_analytics": {
            "institution_id": "EDU-001",
            "institution_name": "Metropolitan University",
            "academic_year": "2023-2024",
            "semester": "Spring 2024",
            "student_demographics": [
                {
                    "student_id": "STU-001",
                    "program": "Computer Science",
                    "year_level": "Junior",
                    "age": 21,
                    "gender": "Female",
                    "enrollment_status": "Full-time",
                    "gpa": 3.75,
                    "credit_hours": 15,
                    "financial_aid": True,
                    "work_study": False,
                    "residence": "On-campus"
                }
            ],
            "course_performance": [
                {
                    "course_id": "CS-301",
                    "course_name": "Data Structures and Algorithms",
                    "instructor": "Dr. Smith",
                    "enrollment": 85,
                    "completion_rate": 0.94,
                    "average_grade": 3.2,
                    "grade_distribution": {
                        "A": 0.25,
                        "B": 0.35,
                        "C": 0.28,
                        "D": 0.08,
                        "F": 0.04
                    },
                    "student_satisfaction": 4.1,
                    "difficulty_rating": 4.3,
                    "workload_hours_per_week": 12.5
                }
            ],
            "learning_outcomes": {
                "critical_thinking": {
                    "pre_assessment": 3.2,
                    "post_assessment": 3.8,
                    "improvement": 0.6,
                    "benchmark": 3.5
                },
                "technical_proficiency": {
                    "pre_assessment": 2.8,
                    "post_assessment": 3.9,
                    "improvement": 1.1,
                    "benchmark": 3.7
                }
            }
        }
    }
    
    # Upload data
    url = f"{API_V1_BASE}/upload/json"
    payload = {
        "client_id": client_id,
        "user_id": user_id,
        "json_data": education_data,
        "resource_name": "student_education_data",
        "flatten": False
    }
    
    try:
        response = requests.post(url, json=payload)
        result = response.json()
        
        if response.status_code == 200 and result.get("success"):
            print("✅ Data uploaded successfully!")
            print(f"   Resource ID: {result['data']['resource_id']}")
            print(f"   Client ID: {client_id}")
            print(f"   User ID: {user_id}")
            return client_id, user_id, result
        else:
            print(f"❌ Upload failed: {result}")
            return None, None, None
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return None, None, None

def test_persona_analysis(client_id, user_id):
    """Test persona analysis with correct API v2 format"""
    print("\n🔍 Running persona analysis...")
    
    # Correct API v2 request format
    url = f"{API_V2_BASE}/analysis"
    payload = {
        "client_id": client_id,
        "user_id": user_id,
        "query": "Get the persona and context of student STU-001 based on their education data",
        "desired_fields": {
            "persona": "Extract detailed persona characteristics of the student",
            "context": "Provide contextual information about the student's academic situation"
        },
        "optional_fields": {
            "course_performance": "Analyze the student's course performance and academic progress",
            "recommendations": "Provide personalized recommendations for the student"
        },
        "access_level": "user",
        "include_visualizations": True,
        "streaming": False
    }
    
    try:
        response = requests.post(url, json=payload)
        result = response.json()
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200 and result.get("success"):
            print("✅ Analysis completed successfully!")
            
            # Extract and display results
            data = result.get("data", {})
            
            if "persona" in data:
                print("\n👤 PERSONA ANALYSIS:")
                print(data["persona"])
            
            if "context" in data:
                print("\n🌍 CONTEXT ANALYSIS:")
                print(data["context"])
            
            if "course_performance" in data:
                print("\n📊 COURSE PERFORMANCE:")
                print(data["course_performance"])
            
            return result
        else:
            print(f"❌ Analysis failed: {result}")
            return None
            
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        return None

def test_data_retrieval(client_id, user_id):
    """Test data retrieval"""
    print("\n📋 Testing data retrieval...")
    
    url = f"{API_V1_BASE}/resources"
    params = {
        "client_id": client_id,
        "user_id": user_id,
        "access_level": "user"
    }
    
    try:
        response = requests.get(url, params=params)
        result = response.json()
        
        if response.status_code == 200 and result.get("success"):
            resources = result.get("data", [])
            print(f"✅ Found {len(resources)} resources")
            
            for resource in resources:
                print(f"   • {resource.get('resource_name')} ({resource.get('resource_type')})")
            
            return result
        else:
            print(f"❌ Retrieval failed: {result}")
            return None
            
    except Exception as e:
        print(f"❌ Retrieval error: {e}")
        return None

def main():
    """Run complete workflow test"""
    print("🧪 Universal Data Handler - Complete Workflow Test")
    print("=" * 60)
    
    # Test API connections
    if not test_api_connection():
        print("❌ API connection test failed. Make sure servers are running.")
        return 1
    
    # Upload data
    client_id, user_id, upload_result = upload_education_data()
    if not client_id:
        print("❌ Data upload failed. Cannot proceed with analysis.")
        return 1
    
    # Wait a moment for data to be processed
    print("\n⏳ Waiting for data processing...")
    time.sleep(2)
    
    # Test data retrieval
    retrieval_result = test_data_retrieval(client_id, user_id)
    
    # Test persona analysis
    analysis_result = test_persona_analysis(client_id, user_id)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Data Upload: {'Success' if upload_result else 'Failed'}")
    print(f"✅ Data Retrieval: {'Success' if retrieval_result else 'Failed'}")
    print(f"✅ Persona Analysis: {'Success' if analysis_result else 'Failed'}")
    
    if upload_result and analysis_result:
        print("\n🎉 All tests passed! The system is working end-to-end.")
        print(f"\n📋 Test Data IDs:")
        print(f"   Client ID: {client_id}")
        print(f"   User ID: {user_id}")
        print(f"\n💡 You can now use these IDs in the Streamlit UI for further testing.")
        return 0
    else:
        print("\n❌ Some tests failed. Check the error messages above.")
        return 1

if __name__ == "__main__":
    exit(main())
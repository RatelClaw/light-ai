#!/usr/bin/env python3
"""
Simple test workflow that focuses on working functionality
"""

import requests
import json
import uuid
import time

# Configuration
API_V1_BASE = "http://127.0.0.1:8000/api/v1"

def test_basic_workflow():
    """Test basic upload and retrieval workflow"""
    print("🧪 Simple Workflow Test")
    print("=" * 40)
    
    # Generate test IDs
    client_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    print(f"Client ID: {client_id}")
    print(f"User ID: {user_id}")
    
    # Simple student data
    student_data = {
        "student_profile": {
            "student_id": "STU-001",
            "name": "Alice Johnson",
            "program": "Computer Science",
            "year_level": "Junior",
            "age": 21,
            "gender": "Female",
            "gpa": 3.75,
            "credit_hours": 15,
            "interests": ["AI", "Web Development", "Data Science"],
            "career_goals": "Software Engineer at tech company",
            "skills": ["Python", "JavaScript", "Machine Learning"],
            "personality_traits": ["Analytical", "Creative", "Detail-oriented"],
            "learning_style": "Visual and hands-on",
            "academic_performance": {
                "current_semester_gpa": 3.8,
                "cumulative_gpa": 3.75,
                "favorite_subjects": ["Data Structures", "AI", "Web Development"],
                "challenging_subjects": ["Calculus", "Physics"]
            }
        }
    }
    
    # Upload data
    print("\n📤 Uploading student data...")
    url = f"{API_V1_BASE}/upload/json"
    payload = {
        "client_id": client_id,
        "user_id": user_id,
        "json_data": student_data,
        "resource_name": "alice_student_profile",
        "flatten": False
    }
    
    try:
        response = requests.post(url, json=payload)
        result = response.json()
        
        if response.status_code == 200 and result.get("success"):
            print("✅ Data uploaded successfully!")
            print(f"   Resource ID: {result['data']['resource_id']}")
        else:
            print(f"❌ Upload failed: {result}")
            return False
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False
    
    # Wait for processing
    time.sleep(1)
    
    # Test data retrieval
    print("\n📋 Retrieving user data...")
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
                if isinstance(resource, dict):
                    print(f"   • {resource.get('resource_name', 'Unknown')} ({resource.get('resource_type', 'Unknown')})")
                    print(f"     Size: {resource.get('file_size_bytes', 0)} bytes")
                else:
                    print(f"   • Resource: {resource}")
        else:
            print(f"❌ Retrieval failed: {result}")
            return False
    except Exception as e:
        print(f"❌ Retrieval error: {e}")
        return False
    
    # Test natural language query (API v1)
    print("\n🔍 Testing natural language query...")
    url = f"{API_V1_BASE}/query/natural"
    payload = {
        "client_id": client_id,
        "user_id": user_id,
        "question": "What can you tell me about Alice Johnson's academic profile and interests?",
        "output_format": "json"
    }
    
    try:
        response = requests.post(url, json=payload)
        result = response.json()
        
        if response.status_code == 200 and result.get("success"):
            print("✅ Natural language query successful!")
            print("📊 Analysis Result:")
            
            # Display the analysis
            data = result.get("data", {})
            if isinstance(data, dict):
                if "answer" in data:
                    print(f"   Answer: {data['answer']}")
                if "insights" in data:
                    print(f"   Insights: {data['insights']}")
                if "summary" in data:
                    print(f"   Summary: {data['summary']}")
            else:
                print(f"   Result: {data}")
        else:
            print(f"❌ Query failed: {result}")
    except Exception as e:
        print(f"❌ Query error: {e}")
    
    print("\n" + "=" * 40)
    print("✅ Basic workflow test completed!")
    print(f"\n💡 Use these IDs in Streamlit UI:")
    print(f"   Client ID: {client_id}")
    print(f"   User ID: {user_id}")
    
    return True

if __name__ == "__main__":
    test_basic_workflow()
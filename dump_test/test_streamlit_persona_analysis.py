#!/usr/bin/env python3
"""
Test the Streamlit UI's get_persona_analysis function directly.
"""

import json
import uuid
from pathlib import Path
import sys

# Add the project root to the path
sys.path.append(str(Path(__file__).parent))

from light_ai.api import UniversalDataHandler
from light_ai.config import get_config
from streamlit_data_handler_ui import get_persona_analysis

def test_streamlit_persona_analysis():
    """Test the Streamlit UI's persona analysis function."""
    
    print("🧠 Testing Streamlit UI Persona Analysis Function")
    print("=" * 60)
    
    # Generate test IDs
    client_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    print(f"Test IDs:")
    print(f"  Client ID: {client_id}")
    print(f"  User ID: {user_id}")
    print()
    
    # Sample data to upload
    sample_data = {
        "student_profile": {
            "student_id": "STU-001",
            "name": "Alice Johnson",
            "program": "Computer Science",
            "year_level": "Junior",
            "age": 21,
            "gender": "Female",
            "gpa": 3.75,
            "interests": ["AI", "Web Development", "Data Science"],
            "career_goals": "Software Engineer at tech company"
        }
    }
    
    try:
        # Step 1: Upload data using Universal Data Handler
        print("📤 Step 1: Upload data using Universal Data Handler")
        config = get_config()
        data_handler = UniversalDataHandler(config)
        
        upload_result = data_handler.upload_json(
            client_id=client_id,
            user_id=user_id,
            json_data=sample_data,
            resource_name="test_student_profile"
        )
        
        if not upload_result.success:
            print(f"❌ Upload failed: {upload_result.error}")
            return False
        
        print(f"✅ Data uploaded successfully!")
        print(f"   Resource ID: {upload_result.data.get('resource_id')}")
        print()
        
        # Step 2: Test Streamlit persona analysis function
        print("🔍 Step 2: Test Streamlit persona analysis function")
        
        result, status_code = get_persona_analysis(
            client_id=client_id,
            user_id=user_id,
            query="Get the persona and context of this user based on their data"
        )
        
        print(f"Status Code: {status_code}")
        print(f"Result: {json.dumps(result, indent=2)}")
        
        if status_code == 200 and result.get("success"):
            print("✅ Persona analysis completed successfully!")
            
            data = result.get("data", {})
            print(f"\n👤 PERSONA:")
            print(f"   {data.get('persona', 'No persona data')[:200]}...")
            
            print(f"\n🌍 CONTEXT:")
            print(f"   {data.get('context', 'No context data')[:200]}...")
            
            print(f"\n💡 INSIGHTS:")
            print(f"   {data.get('insights', 'No insights')[:200]}...")
            
            print(f"\n📊 DATA SUMMARY:")
            summary = data.get('data_summary', {})
            print(f"   Sources used: {summary.get('sources_used', 0)}")
            print(f"   Confidence: {summary.get('confidence_score', 0)}")
            print(f"   Execution time: {summary.get('execution_time_ms', 0)}ms")
            
            return True
        else:
            print(f"❌ Persona analysis failed: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_streamlit_persona_analysis()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Streamlit UI persona analysis is working!")
    else:
        print("❌ Streamlit UI persona analysis test failed")
    
    sys.exit(0 if success else 1)
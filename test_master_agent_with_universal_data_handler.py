#!/usr/bin/env python3
"""
Test the MasterDataAnalystAgent with Universal Data Handler integration.
"""

import asyncio
import json
import uuid
from pathlib import Path
import sys

# Add the project root to the path
sys.path.append(str(Path(__file__).parent))

from light_ai.agents.master_agent import MasterDataAnalystAgent, AnalysisRequest
from light_ai.core.models import AccessLevel
from light_ai.config import get_config
from light_ai.api import UniversalDataHandler

def test_master_agent_with_universal_data_handler():
    """Test that MasterDataAnalystAgent uses Universal Data Handler properly."""
    
    print("🧠 Testing MasterDataAnalystAgent with Universal Data Handler")
    print("=" * 70)
    
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
        
        # Step 2: Test MasterDataAnalystAgent analysis
        print("🔍 Step 2: Test MasterDataAnalystAgent analysis")
        
        # Create analysis request
        request = AnalysisRequest(
            user_id=user_id,
            client_id=client_id,
            query="Analyze this student's profile and extract persona characteristics",
            desired_fields={
                "persona": "Extract detailed persona characteristics and traits",
                "context": "Provide academic and personal context"
            },
            access_level=AccessLevel.USER,
            include_visualizations=False
        )
        
        # Initialize and run the master agent
        agent = MasterDataAnalystAgent(config)
        
        # Run the analysis
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(agent.analyze_data(request))
        finally:
            loop.close()
        
        # Check results
        if result.results or result.insights:
            print("✅ Analysis completed successfully!")
            print(f"   Insights: {len(result.insights)} generated")
            print(f"   Sources used: {len(result.sources_used)}")
            print(f"   Execution time: {result.execution_time_ms:.2f}ms")
            
            if result.insights:
                print("\n📊 Sample insights:")
                for i, insight in enumerate(result.insights[:3], 1):
                    print(f"   {i}. {insight}")
            
            return True
        else:
            print("❌ Analysis returned no results")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_master_agent_with_universal_data_handler()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 MasterDataAnalystAgent is properly integrated with Universal Data Handler!")
    else:
        print("❌ Integration test failed")
    
    sys.exit(0 if success else 1)
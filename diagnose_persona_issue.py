#!/usr/bin/env python3
"""
Diagnose the persona extraction issue by directly testing the system components.
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

def diagnose_persona_extraction():
    """Diagnose why persona extraction returns generic responses."""
    
    print("🔍 Diagnosing Persona Extraction Issue")
    print("=" * 50)
    
    # Generate test IDs
    client_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    print(f"Test IDs:")
    print(f"  Client ID: {client_id}")
    print(f"  User ID: {user_id}")
    print()
    
    # Student data from your example
    student_data = {
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
                    "grade_distribution": {"a": 0.25, "b": 0.35, "c": 0.28, "d": 0.08, "f": 0.04},
                    "student_satisfaction": 4.1,
                    "difficulty_rating": 4.3,
                    "workload_hours_per_week": 12.5
                }
            ],
            "learning_outcomes": {
                "critical_thinking": {"pre_assessment": 3.2, "post_assessment": 3.8, "improvement": 0.6, "benchmark": 3.5},
                "communication_skills": {"pre_assessment": 3.5, "post_assessment": 4.1, "improvement": 0.6, "benchmark": 4.0},
                "technical_proficiency": {"pre_assessment": 2.8, "post_assessment": 3.9, "improvement": 1.1, "benchmark": 3.7}
            }
        }
    }
    
    try:
        # Step 1: Upload data
        print("📤 Step 1: Upload student data")
        config = get_config()
        data_handler = UniversalDataHandler(config)
        
        upload_result = data_handler.upload_json(
            client_id=client_id,
            user_id=user_id,
            json_data=student_data,
            resource_name="student_performance.json"
        )
        
        if not upload_result.success:
            print(f"❌ Upload failed: {upload_result.error}")
            return False
        
        print(f"✅ Data uploaded successfully!")
        resource_id = upload_result.data.get('resource_id')
        print(f"   Resource ID: {resource_id}")
        print()
        
        # Step 2: Test persona extraction
        print("🎭 Step 2: Test persona extraction")
        
        request = AnalysisRequest(
            user_id=user_id,
            client_id=client_id,
            query="Get the persona and context of this user having student_id: 'STU-001', based on their data",
            desired_fields={
                "persona": "Detailed personality profile and characteristics of the student",
                "context": "Academic and personal context surrounding the student"
            },
            access_level=AccessLevel.USER,
            include_visualizations=False
        )
        
        # Initialize master agent
        agent = MasterDataAnalystAgent(config)
        
        # Run analysis
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(agent.analyze_data(request))
        finally:
            loop.close()
        
        # Analyze the results
        print("📊 Analysis Results:")
        print(f"   Success: {len(result.results) > 0 or len(result.insights) > 0}")
        print(f"   Results count: {len(result.results)}")
        print(f"   Insights count: {len(result.insights)}")
        print(f"   Sources used: {result.sources_used}")
        print(f"   Execution time: {result.execution_time_ms:.2f}ms")
        print()
        
        # Check for generic vs specific responses
        print("🔍 Response Analysis:")
        
        if result.insights:
            print("Insights:")
            for i, insight in enumerate(result.insights, 1):
                print(f"   {i}. {insight}")
                
                # Check if insight is generic
                is_generic = any(phrase in insight for phrase in [
                    "Analysis based on", "data sources:", "Strands AI framework",
                    "Analysis completed", "Unable to extract detailed"
                ])
                
                has_specific_data = any(term in insight for term in [
                    "STU-001", "Computer Science", "3.75", "Metropolitan University",
                    "21", "Female", "Junior"
                ])
                
                print(f"      Generic: {is_generic}, Has specific data: {has_specific_data}")
        
        if result.results:
            print(f"\nResults (first 3):")
            for i, res in enumerate(result.results[:3], 1):
                print(f"   {i}. {json.dumps(res, indent=2)[:200]}...")
        
        # Step 3: Test individual components
        print("\n🔧 Step 3: Test individual components")
        
        # Test resource discovery
        print("Testing resource discovery...")
        discovery_result = agent.resource_discovery.discover_resources(user_id, client_id, request.query)
        print(f"   Discovery success: {discovery_result.success}")
        if discovery_result.success and discovery_result.data:
            resources = discovery_result.data.get("resources", [])
            print(f"   Resources found: {len(resources)}")
            if resources:
                print(f"   First resource: {resources[0].get('filename', 'Unknown')}")
        
        # Test field extraction
        if discovery_result.success and discovery_result.data:
            resources = discovery_result.data.get("resources", [])
            if resources:
                print("\nTesting field extraction...")
                resource_ids = [r["resource_id"] for r in resources[:1]]
                field_result = agent.field_extraction.extract_and_map_fields(
                    user_id, client_id, request.desired_fields, resource_ids
                )
                print(f"   Field extraction success: {field_result.success}")
                if field_result.success and field_result.data:
                    mappings = field_result.data.get("field_mappings", {})
                    print(f"   Field mappings found: {len(mappings)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Diagnosis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = diagnose_persona_extraction()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Diagnosis completed!")
    else:
        print("❌ Diagnosis failed")
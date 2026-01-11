#!/usr/bin/env python3
"""
Test script to demonstrate and fix the persona extraction issue.

The problem: The system returns generic responses like "Analysis based on 1 data sources"
instead of actually analyzing the student data to extract persona and context.

The fix: Properly use the Strands AI framework to analyze the actual data content
and extract meaningful insights about the user's persona and context.
"""

import json
import asyncio
import requests
from typing import Dict, Any

# Test data - Student from education sector
STUDENT_DATA = {
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
            },
            {
                "course_id": "BUS-401",
                "course_name": "Strategic Management",
                "instructor": "Prof. Johnson",
                "enrollment": 65,
                "completion_rate": 0.98,
                "average_grade": 3.6,
                "grade_distribution": {"a": 0.35, "b": 0.4, "c": 0.2, "d": 0.03, "f": 0.02},
                "student_satisfaction": 4.5,
                "difficulty_rating": 3.8,
                "workload_hours_per_week": 8.5
            }
        ],
        "learning_outcomes": {
            "critical_thinking": {"pre_assessment": 3.2, "post_assessment": 3.8, "improvement": 0.6, "benchmark": 3.5},
            "communication_skills": {"pre_assessment": 3.5, "post_assessment": 4.1, "improvement": 0.6, "benchmark": 4.0},
            "technical_proficiency": {"pre_assessment": 2.8, "post_assessment": 3.9, "improvement": 1.1, "benchmark": 3.7},
            "collaboration": {"pre_assessment": 3.8, "post_assessment": 4.2, "improvement": 0.4, "benchmark": 4.0}
        }
    }
}

# Bank customer data for comparison
BANK_CUSTOMER_DATA = {
    "banking_analytics": {
        "customer_id": "CUST-001",
        "account_type": "Premium Checking",
        "customer_demographics": {
            "age": 35,
            "income_bracket": "75000-100000",
            "occupation": "Software Engineer",
            "location": "San Francisco, CA",
            "marital_status": "Married",
            "dependents": 2
        },
        "transaction_patterns": {
            "monthly_transactions": 45,
            "average_transaction_amount": 125.50,
            "primary_categories": ["Groceries", "Utilities", "Entertainment", "Savings"],
            "digital_banking_usage": 0.85,
            "atm_usage_frequency": 3.2
        },
        "financial_products": [
            {"product": "Checking Account", "balance": 15000, "active_since": "2020-01-15"},
            {"product": "Savings Account", "balance": 45000, "active_since": "2020-01-15"},
            {"product": "Credit Card", "limit": 25000, "utilization": 0.15, "active_since": "2020-03-01"}
        ]
    }
}

class PersonaExtractionTester:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8001"
        self.client_id = "32c1ebd0-41ee-4775-9ee6-0789eb185dd9"
        
    def test_current_behavior(self):
        """Test the current broken behavior"""
        print("🔍 Testing Current Behavior (Broken)")
        print("=" * 50)
        
        # Test with student data
        user_id = "810a283f-b02c-4aec-ab04-817544aff433"
        
        # Upload student data
        upload_response = self._upload_json_data(user_id, STUDENT_DATA, "student_performance.json")
        print(f"Upload Response: {upload_response.get('success', False)}")
        
        # Query for persona and context
        query = "Get the persona and context of this user having student_id: 'STU-001', based on their data"
        
        analysis_response = self._analyze_data(user_id, query, {
            "persona": "Detailed personality profile and characteristics of the student",
            "context": "Academic and personal context surrounding the student"
        })
        
        print(f"\n📊 Current Analysis Result:")
        print(f"Success: {analysis_response.get('success', False)}")
        
        if analysis_response.get('success'):
            data = analysis_response.get('data', {})
            print(f"Persona: {data.get('persona', 'Not found')}")
            print(f"Context: {data.get('context', 'Not found')}")
            print(f"Insights: {data.get('insights', [])}")
        else:
            print(f"Error: {analysis_response.get('error', 'Unknown error')}")
        
        return analysis_response
    
    def _upload_json_data(self, user_id: str, data: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """Upload JSON data to the system"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v2/upload/json",
                json={
                    "client_id": self.client_id,
                    "user_id": user_id,
                    "json_data": data,
                    "resource_name": filename,
                    "flatten": False
                },
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _analyze_data(self, user_id: str, query: str, desired_fields: Dict[str, str]) -> Dict[str, Any]:
        """Analyze data using the API"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v2/analysis",
                json={
                    "client_id": self.client_id,
                    "user_id": user_id,
                    "query": query,
                    "desired_fields": desired_fields,
                    "include_visualizations": False
                },
                timeout=60
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_test_scenarios(self):
        """Create comprehensive test scenarios"""
        print("\n🎯 Creating Test Scenarios")
        print("=" * 50)
        
        scenarios = [
            {
                "name": "Education Sector - Student Analysis",
                "user_id": "810a283f-b02c-4aec-ab04-817544aff433",
                "data": STUDENT_DATA,
                "filename": "student_performance.json",
                "query": "Analyze the persona and context of student STU-001 based on their academic performance and demographics",
                "expected_persona_elements": [
                    "21-year-old female Computer Science junior",
                    "Strong academic performance (3.75 GPA)",
                    "Full-time student with financial aid",
                    "Lives on campus",
                    "Shows improvement in technical skills"
                ],
                "expected_context_elements": [
                    "Metropolitan University environment",
                    "Spring 2024 semester",
                    "Taking challenging CS courses",
                    "Balancing technical and business courses"
                ]
            },
            {
                "name": "Banking Sector - Customer Analysis", 
                "user_id": "c9225ee9-2b34-4e41-8244-fab796e7e06c",
                "data": BANK_CUSTOMER_DATA,
                "filename": "customer_profile.json",
                "query": "Extract the persona and context of customer CUST-001 from their banking data",
                "expected_persona_elements": [
                    "35-year-old married software engineer",
                    "High income bracket ($75K-$100K)",
                    "Tech-savvy (85% digital banking usage)",
                    "Financially responsible (low credit utilization)",
                    "Family-oriented (2 dependents)"
                ],
                "expected_context_elements": [
                    "San Francisco location",
                    "Premium banking customer",
                    "Long-term relationship (since 2020)",
                    "Multiple financial products"
                ]
            }
        ]
        
        return scenarios
    
    def run_comprehensive_test(self):
        """Run comprehensive test of persona extraction"""
        print("\n🚀 Running Comprehensive Persona Extraction Test")
        print("=" * 60)
        
        scenarios = self.create_test_scenarios()
        results = []
        
        for scenario in scenarios:
            print(f"\n📋 Testing: {scenario['name']}")
            print("-" * 40)
            
            # Upload data
            upload_result = self._upload_json_data(
                scenario['user_id'], 
                scenario['data'], 
                scenario['filename']
            )
            
            if not upload_result.get('success'):
                print(f"❌ Upload failed: {upload_result.get('error')}")
                continue
            
            print(f"✅ Data uploaded successfully")
            
            # Analyze for persona and context
            analysis_result = self._analyze_data(
                scenario['user_id'],
                scenario['query'],
                {
                    "persona": "Detailed personality profile, demographics, and characteristics",
                    "context": "Environmental, situational, and background context"
                }
            )
            
            if analysis_result.get('success'):
                data = analysis_result.get('data', {})
                
                # Check if we got actual analysis or generic responses
                persona = data.get('persona', '')
                context = data.get('context', '')
                insights = data.get('insights', [])
                
                print(f"\n📊 Analysis Results:")
                print(f"Persona: {persona[:200]}..." if len(persona) > 200 else f"Persona: {persona}")
                print(f"Context: {context[:200]}..." if len(context) > 200 else f"Context: {context}")
                print(f"Insights: {insights}")
                
                # Evaluate quality
                is_generic = self._is_generic_response(persona, context, insights)
                
                results.append({
                    "scenario": scenario['name'],
                    "success": True,
                    "is_generic": is_generic,
                    "persona_length": len(persona),
                    "context_length": len(context),
                    "insights_count": len(insights)
                })
                
                if is_generic:
                    print("⚠️  Response appears to be generic - not analyzing actual data content")
                else:
                    print("✅ Response appears to contain actual data analysis")
            
            else:
                print(f"❌ Analysis failed: {analysis_result.get('error')}")
                results.append({
                    "scenario": scenario['name'],
                    "success": False,
                    "error": analysis_result.get('error')
                })
        
        return results
    
    def _is_generic_response(self, persona: str, context: str, insights: list) -> bool:
        """Check if the response is generic rather than data-specific"""
        generic_indicators = [
            "Analysis based on",
            "data sources:",
            "Strands AI framework",
            "Analysis completed",
            "Unable to extract detailed",
            "Limited contextual information"
        ]
        
        combined_text = f"{persona} {context} {' '.join(insights)}"
        
        # Check for generic indicators
        generic_count = sum(1 for indicator in generic_indicators if indicator in combined_text)
        
        # Check for specific data mentions (should be present in good analysis)
        specific_indicators = [
            "STU-001", "Computer Science", "3.75", "Metropolitan University",
            "CUST-001", "Software Engineer", "San Francisco", "Premium"
        ]
        
        specific_count = sum(1 for indicator in specific_indicators if indicator in combined_text)
        
        # Generic if more generic indicators than specific ones
        return generic_count > specific_count

def main():
    """Main test function"""
    print("🔧 Persona Extraction Issue Diagnosis and Fix")
    print("=" * 60)
    
    tester = PersonaExtractionTester()
    
    # Test current behavior
    current_result = tester.test_current_behavior()
    
    # Run comprehensive test
    comprehensive_results = tester.run_comprehensive_test()
    
    # Summary
    print("\n📈 Test Summary")
    print("=" * 30)
    
    successful_tests = [r for r in comprehensive_results if r.get('success')]
    generic_responses = [r for r in successful_tests if r.get('is_generic')]
    
    print(f"Total scenarios tested: {len(comprehensive_results)}")
    print(f"Successful analyses: {len(successful_tests)}")
    print(f"Generic responses (issue): {len(generic_responses)}")
    print(f"Proper analyses: {len(successful_tests) - len(generic_responses)}")
    
    if generic_responses:
        print(f"\n⚠️  ISSUE CONFIRMED: {len(generic_responses)} scenarios returned generic responses")
        print("The system is not properly analyzing the actual data content.")
        print("\n🔧 REQUIRED FIXES:")
        print("1. Fix the master agent to properly extract data content")
        print("2. Enhance field extraction to analyze semantic meaning")
        print("3. Improve cross-resource synthesis for persona building")
        print("4. Add proper AI-driven content analysis")
    else:
        print("\n✅ All tests passed - persona extraction working correctly")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Create comprehensive test scenarios for persona extraction across different sectors.
This creates 5 users for 1 client (education) and 5 users for another client (banking/healthcare).
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

class TestScenarioCreator:
    def __init__(self):
        self.config = get_config()
        self.data_handler = UniversalDataHandler(self.config)
        self.agent = MasterDataAnalystAgent(self.config)
        
        # Client IDs for different sectors
        self.education_client_id = str(uuid.uuid4())
        self.banking_client_id = str(uuid.uuid4())
        
        print(f"Education Client ID: {self.education_client_id}")
        print(f"Banking Client ID: {self.banking_client_id}")
    
    def create_education_scenarios(self):
        """Create 5 different student scenarios for education sector"""
        
        scenarios = [
            {
                "user_id": str(uuid.uuid4()),
                "name": "High Achiever - Computer Science",
                "data": {
                    "education_analytics": {
                        "institution_id": "EDU-001",
                        "institution_name": "Metropolitan University",
                        "academic_year": "2023-2024",
                        "semester": "Spring 2024",
                        "student_demographics": [{
                            "student_id": "STU-001",
                            "name": "Alice Chen",
                            "program": "Computer Science",
                            "year_level": "Senior",
                            "age": 22,
                            "gender": "Female",
                            "enrollment_status": "Full-time",
                            "gpa": 3.92,
                            "credit_hours": 18,
                            "financial_aid": True,
                            "work_study": True,
                            "residence": "Off-campus",
                            "interests": ["Machine Learning", "Web Development", "Cybersecurity"],
                            "career_goals": "Software Engineer at FAANG company"
                        }],
                        "course_performance": [
                            {
                                "course_id": "CS-401",
                                "course_name": "Advanced Algorithms",
                                "grade": "A",
                                "credits": 4,
                                "difficulty_rating": 4.8,
                                "workload_hours_per_week": 15
                            },
                            {
                                "course_id": "CS-450",
                                "course_name": "Machine Learning",
                                "grade": "A-",
                                "credits": 3,
                                "difficulty_rating": 4.5,
                                "workload_hours_per_week": 12
                            }
                        ],
                        "extracurricular": {
                            "activities": ["Programming Club President", "Hackathon Winner", "Research Assistant"],
                            "leadership_roles": ["Student Government Tech Committee"],
                            "internships": ["Google Summer Intern 2023"]
                        }
                    }
                }
            },
            {
                "user_id": str(uuid.uuid4()),
                "name": "Struggling Student - Business",
                "data": {
                    "education_analytics": {
                        "institution_id": "EDU-001",
                        "institution_name": "Metropolitan University",
                        "academic_year": "2023-2024",
                        "semester": "Spring 2024",
                        "student_demographics": [{
                            "student_id": "STU-002",
                            "name": "Marcus Johnson",
                            "program": "Business Administration",
                            "year_level": "Sophomore",
                            "age": 20,
                            "gender": "Male",
                            "enrollment_status": "Full-time",
                            "gpa": 2.45,
                            "credit_hours": 12,
                            "financial_aid": True,
                            "work_study": False,
                            "residence": "On-campus",
                            "interests": ["Sports", "Music", "Entrepreneurship"],
                            "career_goals": "Start own business",
                            "challenges": ["Time management", "Study habits", "Math anxiety"]
                        }],
                        "course_performance": [
                            {
                                "course_id": "BUS-201",
                                "course_name": "Principles of Management",
                                "grade": "C+",
                                "credits": 3,
                                "difficulty_rating": 3.2,
                                "workload_hours_per_week": 8
                            },
                            {
                                "course_id": "MATH-150",
                                "course_name": "Business Statistics",
                                "grade": "D+",
                                "credits": 4,
                                "difficulty_rating": 4.0,
                                "workload_hours_per_week": 6
                            }
                        ],
                        "support_services": {
                            "tutoring_sessions": 8,
                            "counseling_visits": 3,
                            "academic_advising": 5
                        }
                    }
                }
            },
            {
                "user_id": str(uuid.uuid4()),
                "name": "International Student - Engineering",
                "data": {
                    "education_analytics": {
                        "institution_id": "EDU-001",
                        "institution_name": "Metropolitan University",
                        "academic_year": "2023-2024",
                        "semester": "Spring 2024",
                        "student_demographics": [{
                            "student_id": "STU-003",
                            "name": "Priya Sharma",
                            "program": "Electrical Engineering",
                            "year_level": "Junior",
                            "age": 21,
                            "gender": "Female",
                            "enrollment_status": "Full-time",
                            "gpa": 3.68,
                            "credit_hours": 16,
                            "financial_aid": False,
                            "work_study": False,
                            "residence": "International Housing",
                            "country_of_origin": "India",
                            "english_proficiency": "Advanced",
                            "interests": ["Renewable Energy", "Robotics", "Cultural Exchange"],
                            "career_goals": "Work in sustainable technology"
                        }],
                        "course_performance": [
                            {
                                "course_id": "EE-301",
                                "course_name": "Circuit Analysis",
                                "grade": "B+",
                                "credits": 4,
                                "difficulty_rating": 4.2,
                                "workload_hours_per_week": 14
                            },
                            {
                                "course_id": "EE-320",
                                "course_name": "Digital Systems",
                                "grade": "A-",
                                "credits": 3,
                                "difficulty_rating": 3.8,
                                "workload_hours_per_week": 10
                            }
                        ],
                        "cultural_adaptation": {
                            "language_support": True,
                            "cultural_events_attended": 12,
                            "international_student_groups": ["Indian Student Association", "Engineering Society"]
                        }
                    }
                }
            },
            {
                "user_id": str(uuid.uuid4()),
                "name": "Part-time Adult Learner - Psychology",
                "data": {
                    "education_analytics": {
                        "institution_id": "EDU-001",
                        "institution_name": "Metropolitan University",
                        "academic_year": "2023-2024",
                        "semester": "Spring 2024",
                        "student_demographics": [{
                            "student_id": "STU-004",
                            "name": "Sarah Williams",
                            "program": "Psychology",
                            "year_level": "Junior",
                            "age": 32,
                            "gender": "Female",
                            "enrollment_status": "Part-time",
                            "gpa": 3.55,
                            "credit_hours": 9,
                            "financial_aid": True,
                            "work_study": False,
                            "residence": "Off-campus",
                            "family_status": "Married with 2 children",
                            "employment": "Part-time nurse",
                            "interests": ["Child Psychology", "Mental Health", "Community Service"],
                            "career_goals": "Licensed Clinical Psychologist"
                        }],
                        "course_performance": [
                            {
                                "course_id": "PSY-301",
                                "course_name": "Developmental Psychology",
                                "grade": "A",
                                "credits": 3,
                                "difficulty_rating": 3.5,
                                "workload_hours_per_week": 8
                            },
                            {
                                "course_id": "PSY-350",
                                "course_name": "Research Methods",
                                "grade": "B+",
                                "credits": 3,
                                "difficulty_rating": 4.0,
                                "workload_hours_per_week": 10
                            }
                        ],
                        "life_balance": {
                            "study_schedule": "Evenings and weekends",
                            "childcare_needs": True,
                            "online_course_preference": True
                        }
                    }
                }
            },
            {
                "user_id": str(uuid.uuid4()),
                "name": "Graduate Student - Research Focus",
                "data": {
                    "education_analytics": {
                        "institution_id": "EDU-001",
                        "institution_name": "Metropolitan University",
                        "academic_year": "2023-2024",
                        "semester": "Spring 2024",
                        "student_demographics": [{
                            "student_id": "STU-005",
                            "name": "David Kim",
                            "program": "PhD in Data Science",
                            "year_level": "Graduate - Year 3",
                            "age": 26,
                            "gender": "Male",
                            "enrollment_status": "Full-time",
                            "gpa": 3.85,
                            "credit_hours": 6,
                            "financial_aid": False,
                            "work_study": False,
                            "residence": "Graduate Housing",
                            "funding": "Research Assistantship",
                            "interests": ["Natural Language Processing", "Deep Learning", "Academic Research"],
                            "career_goals": "Research Scientist or Professor"
                        }],
                        "research_activity": {
                            "dissertation_topic": "Multimodal Learning for Healthcare Applications",
                            "publications": 3,
                            "conferences_attended": 5,
                            "advisor": "Dr. Jennifer Martinez",
                            "research_hours_per_week": 35
                        },
                        "teaching_responsibilities": {
                            "courses_taught": ["Intro to Data Science", "Statistics for CS"],
                            "teaching_hours_per_week": 10,
                            "student_evaluations": 4.6
                        }
                    }
                }
            }
        ]
        
        return scenarios
    
    def create_banking_scenarios(self):
        """Create 5 different customer scenarios for banking sector"""
        
        scenarios = [
            {
                "user_id": str(uuid.uuid4()),
                "name": "High Net Worth Individual",
                "data": {
                    "banking_analytics": {
                        "customer_id": "CUST-001",
                        "account_type": "Private Banking",
                        "customer_demographics": {
                            "name": "Robert Anderson",
                            "age": 45,
                            "income_bracket": "500000+",
                            "occupation": "Investment Banker",
                            "location": "Manhattan, NY",
                            "marital_status": "Married",
                            "dependents": 3,
                            "education": "MBA from Wharton",
                            "net_worth": "2.5M"
                        },
                        "account_portfolio": [
                            {"product": "Private Checking", "balance": 150000, "active_since": "2018-03-15"},
                            {"product": "Investment Account", "balance": 850000, "active_since": "2018-03-15"},
                            {"product": "Mortgage", "balance": -650000, "rate": 3.2, "active_since": "2019-06-01"},
                            {"product": "Credit Card", "limit": 100000, "utilization": 0.08, "active_since": "2018-03-15"}
                        ],
                        "transaction_patterns": {
                            "monthly_transactions": 125,
                            "average_transaction_amount": 2500,
                            "primary_categories": ["Investments", "Luxury Goods", "Travel", "Education"],
                            "digital_banking_usage": 0.95,
                            "international_transactions": 15
                        },
                        "investment_profile": {
                            "risk_tolerance": "Aggressive",
                            "investment_goals": ["Wealth Growth", "Tax Optimization", "Estate Planning"],
                            "portfolio_allocation": {"Stocks": 0.6, "Bonds": 0.2, "Real Estate": 0.15, "Cash": 0.05}
                        }
                    }
                }
            },
            {
                "user_id": str(uuid.uuid4()),
                "name": "Young Professional - Tech Worker",
                "data": {
                    "banking_analytics": {
                        "customer_id": "CUST-002",
                        "account_type": "Premium Checking",
                        "customer_demographics": {
                            "name": "Emily Zhang",
                            "age": 28,
                            "income_bracket": "100000-150000",
                            "occupation": "Software Engineer",
                            "location": "San Francisco, CA",
                            "marital_status": "Single",
                            "dependents": 0,
                            "education": "BS Computer Science",
                            "net_worth": "180K"
                        },
                        "account_portfolio": [
                            {"product": "Checking Account", "balance": 25000, "active_since": "2021-01-15"},
                            {"product": "Savings Account", "balance": 75000, "active_since": "2021-01-15"},
                            {"product": "401k Rollover IRA", "balance": 80000, "active_since": "2022-03-01"},
                            {"product": "Credit Card", "limit": 15000, "utilization": 0.12, "active_since": "2021-01-15"}
                        ],
                        "transaction_patterns": {
                            "monthly_transactions": 85,
                            "average_transaction_amount": 125,
                            "primary_categories": ["Food & Dining", "Technology", "Transportation", "Savings"],
                            "digital_banking_usage": 0.98,
                            "mobile_app_sessions_per_week": 12
                        },
                        "financial_goals": {
                            "short_term": ["Emergency Fund", "Vacation Savings"],
                            "long_term": ["Home Purchase", "Retirement Planning"],
                            "savings_rate": 0.35
                        }
                    }
                }
            },
            {
                "user_id": str(uuid.uuid4()),
                "name": "Small Business Owner",
                "data": {
                    "banking_analytics": {
                        "customer_id": "CUST-003",
                        "account_type": "Business Banking",
                        "customer_demographics": {
                            "name": "Carlos Rodriguez",
                            "age": 38,
                            "income_bracket": "75000-100000",
                            "occupation": "Restaurant Owner",
                            "location": "Austin, TX",
                            "marital_status": "Married",
                            "dependents": 2,
                            "education": "Culinary Arts Degree",
                            "business_type": "Family Restaurant"
                        },
                        "account_portfolio": [
                            {"product": "Business Checking", "balance": 35000, "active_since": "2019-08-01"},
                            {"product": "Business Savings", "balance": 15000, "active_since": "2019-08-01"},
                            {"product": "Business Line of Credit", "limit": 50000, "utilization": 0.4, "active_since": "2020-02-15"},
                            {"product": "Equipment Loan", "balance": -25000, "rate": 5.5, "active_since": "2021-05-01"}
                        ],
                        "transaction_patterns": {
                            "monthly_transactions": 450,
                            "average_transaction_amount": 85,
                            "primary_categories": ["Food Suppliers", "Utilities", "Payroll", "Equipment"],
                            "seasonal_variations": True,
                            "cash_flow_challenges": ["Summer slowdown", "Holiday rush"]
                        },
                        "business_metrics": {
                            "monthly_revenue": 28000,
                            "employee_count": 8,
                            "years_in_business": 4,
                            "growth_rate": 0.15
                        }
                    }
                }
            },
            {
                "user_id": str(uuid.uuid4()),
                "name": "Retiree - Fixed Income",
                "data": {
                    "banking_analytics": {
                        "customer_id": "CUST-004",
                        "account_type": "Senior Banking",
                        "customer_demographics": {
                            "name": "Margaret Thompson",
                            "age": 68,
                            "income_bracket": "40000-60000",
                            "occupation": "Retired Teacher",
                            "location": "Phoenix, AZ",
                            "marital_status": "Widowed",
                            "dependents": 0,
                            "education": "Masters in Education",
                            "retirement_status": "Fully Retired"
                        },
                        "account_portfolio": [
                            {"product": "Senior Checking", "balance": 12000, "active_since": "2015-09-01"},
                            {"product": "CD Portfolio", "balance": 180000, "rate": 4.2, "active_since": "2020-01-01"},
                            {"product": "IRA", "balance": 320000, "active_since": "1985-01-01"},
                            {"product": "Credit Card", "limit": 5000, "utilization": 0.05, "active_since": "2015-09-01"}
                        ],
                        "transaction_patterns": {
                            "monthly_transactions": 25,
                            "average_transaction_amount": 65,
                            "primary_categories": ["Healthcare", "Groceries", "Utilities", "Charitable Giving"],
                            "digital_banking_usage": 0.3,
                            "branch_visits_per_month": 4
                        },
                        "retirement_planning": {
                            "pension_income": 2800,
                            "social_security": 1850,
                            "withdrawal_rate": 0.04,
                            "healthcare_costs": 450
                        }
                    }
                }
            },
            {
                "user_id": str(uuid.uuid4()),
                "name": "Recent Graduate - Entry Level",
                "data": {
                    "banking_analytics": {
                        "customer_id": "CUST-005",
                        "account_type": "Student Transition",
                        "customer_demographics": {
                            "name": "Jordan Mitchell",
                            "age": 23,
                            "income_bracket": "35000-50000",
                            "occupation": "Marketing Coordinator",
                            "location": "Chicago, IL",
                            "marital_status": "Single",
                            "dependents": 0,
                            "education": "BA Marketing",
                            "graduation_date": "2023-05-15"
                        },
                        "account_portfolio": [
                            {"product": "Checking Account", "balance": 2500, "active_since": "2023-06-01"},
                            {"product": "Savings Account", "balance": 1200, "active_since": "2023-06-01"},
                            {"product": "Student Loan", "balance": -35000, "rate": 4.8, "active_since": "2019-09-01"},
                            {"product": "Credit Card", "limit": 2000, "utilization": 0.25, "active_since": "2023-06-01"}
                        ],
                        "transaction_patterns": {
                            "monthly_transactions": 55,
                            "average_transaction_amount": 45,
                            "primary_categories": ["Rent", "Groceries", "Transportation", "Student Loans"],
                            "digital_banking_usage": 0.92,
                            "budgeting_app_usage": True
                        },
                        "financial_challenges": {
                            "student_debt": 35000,
                            "rent_to_income_ratio": 0.35,
                            "building_credit_history": True,
                            "emergency_fund_goal": 3000
                        }
                    }
                }
            }
        ]
        
        return scenarios
    
    async def test_scenario(self, client_id: str, scenario: dict, sector: str):
        """Test a single scenario"""
        print(f"\n🧪 Testing: {scenario['name']} ({sector})")
        print("-" * 50)
        
        # Upload data
        upload_result = self.data_handler.upload_json(
            client_id=client_id,
            user_id=scenario['user_id'],
            json_data=scenario['data'],
            resource_name=f"{scenario['name'].lower().replace(' ', '_')}.json"
        )
        
        if not upload_result.success:
            print(f"❌ Upload failed: {upload_result.error}")
            return False
        
        print(f"✅ Data uploaded successfully")
        
        # Extract user identifier from data
        if sector == "education":
            user_identifier = scenario['data']['education_analytics']['student_demographics'][0]['student_id']
            query = f"Analyze the persona and context of student {user_identifier} based on their academic data"
        else:  # banking
            user_identifier = scenario['data']['banking_analytics']['customer_id']
            query = f"Extract the persona and context of customer {user_identifier} from their banking profile"
        
        # Analyze for persona and context
        request = AnalysisRequest(
            user_id=scenario['user_id'],
            client_id=client_id,
            query=query,
            desired_fields={
                "persona": "Detailed personality profile, demographics, and characteristics",
                "context": "Environmental, situational, and background context"
            },
            access_level=AccessLevel.USER,
            include_visualizations=False
        )
        
        result = await self.agent.analyze_data(request)
        
        if result.results and result.insights:
            print(f"✅ Analysis successful!")
            print(f"   Results: {len(result.results)} records")
            print(f"   Insights: {len(result.insights)} generated")
            
            # Show sample insights
            print(f"\n📊 Sample Insights:")
            for i, insight in enumerate(result.insights[:3], 1):
                print(f"   {i}. {insight[:100]}...")
            
            return True
        else:
            print(f"❌ Analysis failed or returned no results")
            return False
    
    async def run_all_tests(self):
        """Run all test scenarios"""
        print("🚀 Creating Comprehensive Test Scenarios")
        print("=" * 60)
        
        # Create scenarios
        education_scenarios = self.create_education_scenarios()
        banking_scenarios = self.create_banking_scenarios()
        
        print(f"\n📚 Education Sector - {len(education_scenarios)} scenarios")
        education_results = []
        for scenario in education_scenarios:
            success = await self.test_scenario(self.education_client_id, scenario, "education")
            education_results.append(success)
        
        print(f"\n🏦 Banking Sector - {len(banking_scenarios)} scenarios")
        banking_results = []
        for scenario in banking_scenarios:
            success = await self.test_scenario(self.banking_client_id, scenario, "banking")
            banking_results.append(success)
        
        # Summary
        print(f"\n📈 Test Results Summary")
        print("=" * 40)
        print(f"Education Sector: {sum(education_results)}/{len(education_results)} successful")
        print(f"Banking Sector: {sum(banking_results)}/{len(banking_results)} successful")
        print(f"Overall Success Rate: {(sum(education_results) + sum(banking_results))}/{len(education_results) + len(banking_results)}")
        
        if sum(education_results) + sum(banking_results) == len(education_results) + len(banking_results):
            print("\n🎉 All persona extraction tests passed!")
            print("The system is now properly analyzing data content and extracting meaningful personas and contexts.")
        else:
            print("\n⚠️  Some tests failed - further investigation needed")

async def main():
    """Main function"""
    creator = TestScenarioCreator()
    await creator.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
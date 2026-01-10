#!/usr/bin/env python3
"""
System Integration Validation Demo.

This script demonstrates the complete integration of the Intelligent AI Data Analyst System
by running through key workflows and validating system components.

Task 15: Final integration and system validation
"""

import asyncio
import uuid
import time
from typing import Dict, Any
from pathlib import Path

from light_ai.config import Config
from light_ai.agents.master_agent import MasterDataAnalystAgent, AnalysisRequest
from light_ai.security.security_manager import SecurityManager
from light_ai.api_v2 import create_comprehensive_api
from light_ai.core.models import AccessLevel
from fastapi.testclient import TestClient


class SystemIntegrationValidator:
    """Validates complete system integration."""
    
    def __init__(self):
        """Initialize the validator."""
        self.config = Config.load()
        self.results = {}
        
    def run_validation(self) -> Dict[str, Any]:
        """Run complete system validation."""
        print("🚀 Starting System Integration Validation")
        print("=" * 60)
        
        # Test 1: Component Initialization
        print("\n1. Testing Component Initialization...")
        self.test_component_initialization()
        
        # Test 2: Security and Data Isolation
        print("\n2. Testing Security and Data Isolation...")
        self.test_security_and_isolation()
        
        # Test 3: AI Agent Integration
        print("\n3. Testing AI Agent Integration...")
        asyncio.run(self.test_ai_agent_integration())
        
        # Test 4: API Layer Integration
        print("\n4. Testing API Layer Integration...")
        self.test_api_integration()
        
        # Test 5: End-to-End Workflow
        print("\n5. Testing End-to-End Workflow...")
        asyncio.run(self.test_end_to_end_workflow())
        
        # Generate Summary
        print("\n" + "=" * 60)
        self.print_validation_summary()
        
        return self.results
    
    def test_component_initialization(self):
        """Test that all system components initialize correctly."""
        try:
            # Test Security Manager
            security_manager = SecurityManager(self.config)
            self.results['security_manager'] = {
                'status': 'success',
                'message': 'Security manager initialized successfully'
            }
            
            # Test Master Agent
            master_agent = MasterDataAnalystAgent(self.config)
            self.results['master_agent'] = {
                'status': 'success',
                'message': 'Master AI agent initialized successfully'
            }
            
            # Test API v2
            api_v2 = create_comprehensive_api(self.config)
            self.results['api_v2'] = {
                'status': 'success',
                'message': 'API v2 initialized successfully'
            }
            
            print("✅ All components initialized successfully")
            
            # Cleanup
            security_manager.shutdown()
            
        except Exception as e:
            self.results['component_initialization'] = {
                'status': 'error',
                'message': f'Component initialization failed: {str(e)}'
            }
            print(f"❌ Component initialization failed: {e}")
    
    def test_security_and_isolation(self):
        """Test security and data isolation features."""
        try:
            security_manager = SecurityManager(self.config)
            
            # Create test client and users
            client_id = str(uuid.uuid4())
            
            # Test user creation
            user1 = security_manager.create_user(client_id, "test_user_1")
            user2 = security_manager.create_user(client_id, "test_user_2")
            
            # Test data isolation
            namespace1 = security_manager.data_isolation.get_user_namespace(user1.user_id, client_id)
            namespace2 = security_manager.data_isolation.get_user_namespace(user2.user_id, client_id)
            
            # Verify isolation
            isolation_verified = (
                namespace1.user_id != namespace2.user_id and
                namespace1.database_schema != namespace2.database_schema and
                namespace1.storage_path != namespace2.storage_path
            )
            
            # Test encryption
            test_data = "Sensitive user data"
            encrypted = security_manager.encrypt_user_data(test_data, user1.user_id, client_id)
            decrypted = security_manager.decrypt_user_data(encrypted, user1.user_id, client_id)
            
            encryption_verified = decrypted.decode() == test_data
            
            if isolation_verified and encryption_verified:
                self.results['security_isolation'] = {
                    'status': 'success',
                    'message': 'Data isolation and encryption verified'
                }
                print("✅ Security and data isolation working correctly")
            else:
                raise Exception("Security validation failed")
            
            # Cleanup
            security_manager.shutdown()
            
        except Exception as e:
            self.results['security_isolation'] = {
                'status': 'error',
                'message': f'Security test failed: {str(e)}'
            }
            print(f"❌ Security test failed: {e}")
    
    async def test_ai_agent_integration(self):
        """Test AI agent integration and functionality."""
        try:
            security_manager = SecurityManager(self.config)
            master_agent = MasterDataAnalystAgent(self.config)
            
            # Create test user
            client_id = str(uuid.uuid4())
            user = security_manager.create_user(client_id, "ai_test_user")
            
            # Test AI analysis
            request = AnalysisRequest(
                user_id=user.user_id,
                client_id=client_id,
                query="What insights can you provide about the available data?",
                access_level=AccessLevel.USER
            )
            
            start_time = time.time()
            result = await master_agent.analyze_data(request)
            execution_time = time.time() - start_time
            
            # Validate result
            if (result and result.query_id and 
                len(result.insights) > 0 and 
                result.confidence_score >= 0.0):
                
                self.results['ai_agent'] = {
                    'status': 'success',
                    'message': f'AI agent analysis completed in {execution_time:.2f}s',
                    'execution_time': execution_time,
                    'insights_count': len(result.insights)
                }
                print(f"✅ AI agent working correctly (execution time: {execution_time:.2f}s)")
            else:
                raise Exception("AI agent validation failed")
            
            # Cleanup
            security_manager.shutdown()
            
        except Exception as e:
            self.results['ai_agent'] = {
                'status': 'error',
                'message': f'AI agent test failed: {str(e)}'
            }
            print(f"❌ AI agent test failed: {e}")
    
    def test_api_integration(self):
        """Test API layer integration."""
        try:
            api_v2 = create_comprehensive_api(self.config)
            client = TestClient(api_v2)
            
            # Test health endpoint
            health_response = client.get("/api/v2/health")
            
            # Test metrics endpoint  
            metrics_response = client.get("/api/v2/metrics")
            
            # Validate responses
            api_working = (
                health_response.status_code in [200, 429] and  # Allow rate limiting
                metrics_response.status_code in [200, 429]
            )
            
            if api_working:
                self.results['api_integration'] = {
                    'status': 'success',
                    'message': 'API endpoints accessible',
                    'health_status': health_response.status_code,
                    'metrics_status': metrics_response.status_code
                }
                print("✅ API integration working correctly")
            else:
                raise Exception("API validation failed")
                
        except Exception as e:
            self.results['api_integration'] = {
                'status': 'error',
                'message': f'API test failed: {str(e)}'
            }
            print(f"❌ API test failed: {e}")
    
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow."""
        try:
            # Initialize all components
            security_manager = SecurityManager(self.config)
            master_agent = MasterDataAnalystAgent(self.config)
            api_v2 = create_comprehensive_api(self.config)
            client = TestClient(api_v2)
            
            # Create test user
            client_id = str(uuid.uuid4())
            user = security_manager.create_user(client_id, "e2e_test_user")
            
            # Test workflow: User creation -> Authentication -> Analysis
            
            # 1. User authentication
            auth_user = security_manager.authenticate_user(client_id, "e2e_test_user")
            if not auth_user:
                raise Exception("User authentication failed")
            
            # 2. AI Analysis through master agent
            analysis_request = AnalysisRequest(
                user_id=user.user_id,
                client_id=client_id,
                query="Analyze the current system status and provide insights",
                access_level=AccessLevel.USER
            )
            
            analysis_result = await master_agent.analyze_data(analysis_request)
            if not analysis_result or not analysis_result.query_id:
                raise Exception("AI analysis failed")
            
            # 3. API health check
            health_response = client.get("/api/v2/health")
            if health_response.status_code not in [200, 429]:
                raise Exception("API health check failed")
            
            self.results['end_to_end'] = {
                'status': 'success',
                'message': 'Complete end-to-end workflow validated',
                'user_created': True,
                'user_authenticated': True,
                'ai_analysis_completed': True,
                'api_accessible': True
            }
            print("✅ End-to-end workflow working correctly")
            
            # Cleanup
            security_manager.shutdown()
            
        except Exception as e:
            self.results['end_to_end'] = {
                'status': 'error',
                'message': f'End-to-end test failed: {str(e)}'
            }
            print(f"❌ End-to-end test failed: {e}")
    
    def print_validation_summary(self):
        """Print validation summary."""
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result['status'] == 'success')
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nDetailed Results:")
        for test_name, result in self.results.items():
            status_icon = "✅" if result['status'] == 'success' else "❌"
            print(f"{status_icon} {test_name}: {result['message']}")
        
        if failed_tests == 0:
            print("\n🎉 ALL TESTS PASSED - System integration validated successfully!")
        else:
            print(f"\n⚠️  {failed_tests} test(s) failed - Review system configuration")


def main():
    """Main function to run system validation."""
    validator = SystemIntegrationValidator()
    results = validator.run_validation()
    
    # Return exit code based on results
    failed_tests = sum(1 for result in results.values() if result['status'] != 'success')
    return 0 if failed_tests == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
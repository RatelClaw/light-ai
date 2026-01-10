"""
Error Recovery System Demonstration.

This example demonstrates the comprehensive error handling and recovery capabilities
of the Intelligent Data Analyst system, including AI-powered error diagnosis,
automatic fallback query generation, partial result delivery, user guidance,
and graceful degradation under system stress.
"""

import asyncio
import time
from typing import Dict, Any
from light_ai.agents.error_recovery_agent import ErrorRecoveryAgent
from light_ai.agents.error_handler import ErrorHandler, with_error_recovery
from light_ai.config import get_config


async def demonstrate_error_diagnosis():
    """Demonstrate AI-powered error diagnosis capabilities."""
    print("=== Error Diagnosis Demonstration ===")
    
    recovery_agent = ErrorRecoveryAgent(get_config())
    
    # Test different types of errors
    test_errors = [
        (PermissionError("Access denied to table 'sensitive_data'"), "Permission Error"),
        (ValueError("Column 'invalid_field' not found in schema"), "Schema Mismatch"),
        (TimeoutError("Query execution timeout after 30 seconds"), "Timeout Error"),
        (ConnectionError("Database connection failed"), "Connection Error"),
        (RuntimeError("System overload detected"), "System Overload")
    ]
    
    for error, error_type in test_errors:
        print(f"\n--- Diagnosing {error_type} ---")
        
        context = {
            "user_id": "demo_user",
            "client_id": "demo_client",
            "operation": "data_query",
            "query": "SELECT * FROM test_table WHERE condition = 'value'",
            "timestamp": time.time()
        }
        
        try:
            diagnosis = await recovery_agent.diagnose_error(error, context)
            
            print(f"Error ID: {diagnosis.error_id}")
            print(f"Category: {diagnosis.error_category.value}")
            print(f"Severity: {diagnosis.severity.value}")
            print(f"Confidence: {diagnosis.confidence_score:.2f}")
            print(f"User Explanation: {diagnosis.user_friendly_explanation}")
            print(f"Suggested Actions: {', '.join(diagnosis.suggested_actions)}")
            print(f"Recovery Strategies: {[s.value for s in diagnosis.recovery_strategies]}")
            
        except Exception as e:
            print(f"Diagnosis failed (expected in demo): {e}")


async def demonstrate_fallback_queries():
    """Demonstrate automatic fallback query generation."""
    print("\n=== Fallback Query Generation Demonstration ===")
    
    recovery_agent = ErrorRecoveryAgent(get_config())
    
    # Test complex queries that might need fallbacks
    test_queries = [
        "SELECT complex_calculation(field1, field2) FROM large_table WHERE complex_condition",
        "SELECT * FROM table1 t1 JOIN table2 t2 ON t1.id = t2.foreign_id WHERE t1.status = 'active'",
        "SELECT AVG(revenue), COUNT(*) FROM sales GROUP BY region, product_category HAVING COUNT(*) > 100"
    ]
    
    for query in test_queries:
        print(f"\n--- Generating fallback for: {query[:50]}... ---")
        
        error_context = {
            "user_id": "demo_user",
            "client_id": "demo_client",
            "original_query": query,
            "error_type": "complexity_error",
            "tables_involved": ["large_table", "table1", "table2", "sales"]
        }
        
        try:
            fallback = await recovery_agent.generate_fallback_query(query, error_context)
            
            if fallback:
                print(f"Fallback Query: {fallback.fallback_query}")
                print(f"Confidence: {fallback.confidence_score:.2f}")
                print(f"Success Estimate: {fallback.estimated_success_rate:.2f}")
                print(f"Limitations: {', '.join(fallback.expected_limitations)}")
            else:
                print("No fallback generated (expected in demo without API)")
                
        except Exception as e:
            print(f"Fallback generation failed (expected in demo): {e}")


async def demonstrate_partial_results():
    """Demonstrate partial result delivery with limitations."""
    print("\n=== Partial Result Delivery Demonstration ===")
    
    recovery_agent = ErrorRecoveryAgent(get_config())
    
    # Simulate different partial result scenarios
    test_scenarios = [
        {
            "name": "Timeout with Partial Data",
            "data": [
                {"id": 1, "name": "Product A", "sales": 1000},
                {"id": 2, "name": "Product B", "sales": 1500},
                {"id": 3, "name": "Product C", "sales": 800}
            ],
            "limitations": [
                "Query timeout after 30 seconds",
                "Only first 3 records retrieved out of estimated 1000",
                "Complex calculations not performed"
            ],
            "context": {"expected_record_count": 1000, "user_id": "demo_user"}
        },
        {
            "name": "Permission Limited Data",
            "data": [
                {"id": 1, "public_info": "Available", "category": "Public"},
                {"id": 2, "public_info": "Available", "category": "Public"}
            ],
            "limitations": [
                "Access denied to sensitive fields",
                "Only public data returned",
                "Financial data excluded due to permissions"
            ],
            "context": {"expected_record_count": 50, "user_id": "demo_user"}
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n--- {scenario['name']} ---")
        
        partial_result = await recovery_agent.deliver_partial_results(
            scenario["data"], scenario["limitations"], scenario["context"]
        )
        
        print(f"Records Retrieved: {len(partial_result.partial_data)}")
        print(f"Completeness: {partial_result.completeness_percentage:.1f}%")
        print(f"Reliability Score: {partial_result.reliability_score:.2f}")
        print(f"Limitations: {', '.join(partial_result.limitations)}")
        print(f"Missing Components: {', '.join(partial_result.missing_components)}")
        print(f"Next Steps: {', '.join(partial_result.suggested_next_steps)}")


async def demonstrate_user_guidance():
    """Demonstrate user guidance generation."""
    print("\n=== User Guidance Demonstration ===")
    
    recovery_agent = ErrorRecoveryAgent(get_config())
    
    # Create sample error diagnoses for guidance generation
    from light_ai.agents.error_recovery_agent import ErrorDiagnosis, ErrorCategory, ErrorSeverity, RecoveryStrategy
    
    test_diagnoses = [
        ErrorDiagnosis(
            error_id="perm_error_123",
            original_error="Access denied to table 'financial_data'",
            error_category=ErrorCategory.PERMISSION_DENIED,
            severity=ErrorSeverity.HIGH,
            root_cause="User lacks required permissions for financial data access",
            technical_explanation="Database access control denied for table 'financial_data'",
            user_friendly_explanation="You don't have permission to access the requested financial data",
            suggested_actions=["Contact your administrator", "Request access permissions"],
            recovery_strategies=[RecoveryStrategy.USER_GUIDANCE],
            confidence_score=0.9,
            diagnosis_time_ms=150.0,
            context_factors={"user_id": "demo_user", "table": "financial_data"}
        ),
        ErrorDiagnosis(
            error_id="timeout_error_456",
            original_error="Query execution timeout",
            error_category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            root_cause="Query complexity exceeds system timeout limits",
            technical_explanation="Query execution exceeded 30-second timeout limit",
            user_friendly_explanation="Your query is taking too long to process",
            suggested_actions=["Simplify your query", "Add filters to reduce data scope"],
            recovery_strategies=[RecoveryStrategy.FALLBACK_QUERY, RecoveryStrategy.USER_GUIDANCE],
            confidence_score=0.8,
            diagnosis_time_ms=100.0,
            context_factors={"user_id": "demo_user", "timeout": 30}
        )
    ]
    
    for diagnosis in test_diagnoses:
        print(f"\n--- Guidance for {diagnosis.error_category.value} ---")
        
        context = {
            "user_id": "demo_user",
            "client_id": "demo_client",
            "user_skill_level": "intermediate"
        }
        
        try:
            guidance = await recovery_agent.provide_user_guidance(diagnosis, context)
            
            print(f"Guidance ID: {guidance.guidance_id}")
            print(f"Error Context: {guidance.error_context}")
            print("Step-by-Step Guidance:")
            for i, step in enumerate(guidance.step_by_step_guidance, 1):
                print(f"  {i}. {step}")
            print(f"Alternative Approaches: {', '.join(guidance.alternative_approaches)}")
            print(f"Prevention Tips: {', '.join(guidance.prevention_tips)}")
            print(f"Estimated Resolution Time: {guidance.estimated_resolution_time}")
            
        except Exception as e:
            print(f"Guidance generation failed (expected in demo): {e}")


async def demonstrate_system_stress_handling():
    """Demonstrate system stress monitoring and graceful degradation."""
    print("\n=== System Stress Handling Demonstration ===")
    
    recovery_agent = ErrorRecoveryAgent(get_config())
    
    # Get current system metrics
    print("--- Current System Metrics ---")
    metrics = recovery_agent.get_system_metrics()
    
    print(f"CPU Usage: {metrics.cpu_usage_percent:.1f}%")
    print(f"Memory Usage: {metrics.memory_usage_percent:.1f}%")
    print(f"Disk Usage: {metrics.disk_usage_percent:.1f}%")
    print(f"Active Connections: {metrics.active_connections}")
    print(f"Error Rate: {metrics.error_rate_percent:.1f}%")
    print(f"Stress Level: {metrics.stress_level}")
    
    # Simulate high stress scenarios
    from light_ai.agents.error_recovery_agent import SystemStressMetrics
    
    stress_scenarios = [
        SystemStressMetrics(
            cpu_usage_percent=85.0,
            memory_usage_percent=80.0,
            disk_usage_percent=70.0,
            active_connections=100,
            query_queue_length=25,
            average_response_time_ms=3000.0,
            error_rate_percent=12.0,
            stress_level="high"
        ),
        SystemStressMetrics(
            cpu_usage_percent=95.0,
            memory_usage_percent=92.0,
            disk_usage_percent=85.0,
            active_connections=200,
            query_queue_length=50,
            average_response_time_ms=8000.0,
            error_rate_percent=25.0,
            stress_level="critical"
        )
    ]
    
    for i, stress_metrics in enumerate(stress_scenarios, 1):
        print(f"\n--- Stress Scenario {i}: {stress_metrics.stress_level.upper()} ---")
        
        stress_result = await recovery_agent.handle_system_stress(stress_metrics)
        
        print(f"Degradation Level: {stress_result['degradation_level']}")
        print("Actions Taken:")
        for action in stress_result["actions_taken"]:
            print(f"  - {action}")
        print("Recommendations:")
        for rec in stress_result.get("recommendations", []):
            print(f"  - {rec}")
        print(f"Estimated Recovery Time: {stress_result.get('estimated_recovery_time', 'Unknown')}")


async def demonstrate_integrated_error_handling():
    """Demonstrate integrated error handling with the ErrorHandler."""
    print("\n=== Integrated Error Handling Demonstration ===")
    
    error_handler = ErrorHandler(get_config())
    
    # Test the decorator functionality
    @error_handler.with_error_recovery("demo_operation", {"demo": True})
    async def sample_operation(should_fail: bool = False, failure_type: str = "generic"):
        """Sample operation that might fail."""
        if should_fail:
            if failure_type == "permission":
                raise PermissionError("Access denied to demo resource")
            elif failure_type == "timeout":
                raise TimeoutError("Demo operation timeout")
            elif failure_type == "schema":
                raise ValueError("Schema mismatch in demo data")
            else:
                raise RuntimeError("Generic demo error")
        
        return {"success": True, "data": [{"id": 1, "value": "demo"}]}
    
    # Test successful operation
    print("--- Successful Operation ---")
    try:
        result = await sample_operation(False)
        print(f"Operation succeeded: {result}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    # Test error handling with different error types
    error_types = ["permission", "timeout", "schema", "generic"]
    
    for error_type in error_types:
        print(f"\n--- Handling {error_type} Error ---")
        try:
            result = await sample_operation(True, error_type)
            print(f"Unexpected success: {result}")
        except Exception as e:
            print(f"Error handled: {str(e)[:100]}...")
    
    # Test direct error handling
    print("\n--- Direct Error Handling ---")
    test_error = ConnectionError("Database connection lost")
    context = {
        "user_id": "demo_user",
        "client_id": "demo_client",
        "operation": "database_query"
    }
    
    try:
        recovery_response = await error_handler.handle_error(test_error, context)
        print(f"Recovery Success: {recovery_response.get('success', False)}")
        print(f"Error Category: {recovery_response.get('error_category', 'unknown')}")
        print(f"Recovery Strategy: {recovery_response.get('recovery_strategy', 'none')}")
        print(f"User Message: {recovery_response.get('message', 'No message')}")
    except Exception as e:
        print(f"Error handling failed (expected in demo): {e}")


async def demonstrate_performance_monitoring():
    """Demonstrate performance monitoring and statistics."""
    print("\n=== Performance Monitoring Demonstration ===")
    
    error_handler = ErrorHandler(get_config())
    
    # Get error handling statistics
    print("--- Error Handling Statistics ---")
    stats = error_handler.get_error_statistics()
    
    print(f"Total Errors Intercepted: {stats['total_errors']}")
    print(f"Recovery Success Rate: {stats['recovery_success_rate']:.1f}%")
    print(f"System Health: {stats['system_health']}")
    
    print("\nError Handler Stats:")
    for key, value in stats["error_handler_stats"].items():
        print(f"  {key}: {value}")
    
    print("\nRecovery Agent Stats:")
    for key, value in stats["recovery_agent_stats"].items():
        print(f"  {key}: {value}")
    
    # Perform health check
    print("\n--- System Health Check ---")
    try:
        health = await error_handler.health_check()
        print(f"Overall Status: {health['status']}")
        print(f"Error Handler Active: {health['error_handler_active']}")
        print("Available Features:")
        for feature in health.get("features_available", []):
            print(f"  - {feature}")
    except Exception as e:
        print(f"Health check failed (expected in demo): {e}")


async def main():
    """Run all error recovery demonstrations."""
    print("🔧 Intelligent Data Analyst - Error Recovery System Demo")
    print("=" * 60)
    
    try:
        await demonstrate_error_diagnosis()
        await demonstrate_fallback_queries()
        await demonstrate_partial_results()
        await demonstrate_user_guidance()
        await demonstrate_system_stress_handling()
        await demonstrate_integrated_error_handling()
        await demonstrate_performance_monitoring()
        
        print("\n" + "=" * 60)
        print("✅ Error Recovery System Demo Completed Successfully!")
        print("\nKey Features Demonstrated:")
        print("- AI-powered error diagnosis and explanation")
        print("- Automatic fallback query generation")
        print("- Partial result delivery with limitations")
        print("- User guidance and suggestion system")
        print("- Graceful degradation under system stress")
        print("- Integrated error handling with decorators")
        print("- Performance monitoring and statistics")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
"""
Tests for the robust error handling and recovery system.

This test suite validates all aspects of the error recovery system including
AI-powered error diagnosis, automatic fallback query generation, partial result
delivery, user guidance, and graceful degradation under system stress.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

from light_ai.agents.error_recovery_agent import (
    ErrorRecoveryAgent, ErrorCategory, ErrorSeverity, RecoveryStrategy,
    ErrorDiagnosis, FallbackQuery, PartialResult, UserGuidance, SystemStressMetrics
)
from light_ai.agents.error_handler import ErrorHandler, get_error_handler, with_error_recovery
from light_ai.config import get_config


class TestErrorRecoveryAgent:
    """Test the Error Recovery Agent functionality."""
    
    @pytest.fixture
    def recovery_agent(self):
        """Create a test recovery agent."""
        config = get_config()
        return ErrorRecoveryAgent(config)
    
    @pytest.fixture
    def sample_error_context(self):
        """Sample error context for testing."""
        return {
            "user_id": "test_user",
            "client_id": "test_client",
            "operation": "data_query",
            "query": "SELECT * FROM test_table",
            "timestamp": time.time()
        }
    
    @pytest.mark.asyncio
    async def test_error_diagnosis_basic(self, recovery_agent, sample_error_context):
        """Test basic error diagnosis functionality."""
        # Test with a permission error
        error = PermissionError("Access denied to table test_table")
        
        diagnosis = await recovery_agent.diagnose_error(error, sample_error_context)
        
        assert diagnosis.error_id is not None
        assert diagnosis.error_category == ErrorCategory.PERMISSION_DENIED
        assert diagnosis.severity in [ErrorSeverity.HIGH, ErrorSeverity.MEDIUM]
        assert len(diagnosis.suggested_actions) > 0
        assert len(diagnosis.recovery_strategies) > 0
        assert 0.0 <= diagnosis.confidence_score <= 1.0
        assert diagnosis.diagnosis_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_error_categorization(self, recovery_agent, sample_error_context):
        """Test error categorization accuracy."""
        test_cases = [
            (ValueError("Column 'invalid_field' not found"), ErrorCategory.SCHEMA_MISMATCH),
            (ConnectionError("Database connection failed"), ErrorCategory.DATA_ACCESS),
            (TimeoutError("Query timeout after 30 seconds"), ErrorCategory.TIMEOUT),
            (PermissionError("Access denied"), ErrorCategory.PERMISSION_DENIED),
            (SyntaxError("Invalid SQL syntax"), ErrorCategory.QUERY_SYNTAX),
        ]
        
        for error, expected_category in test_cases:
            diagnosis = await recovery_agent.diagnose_error(error, sample_error_context)
            assert diagnosis.error_category == expected_category
    
    @pytest.mark.asyncio
    async def test_fallback_query_generation(self, recovery_agent, sample_error_context):
        """Test automatic fallback query generation."""
        original_query = "SELECT complex_field, derived_value FROM complex_table WHERE complex_condition = 'test'"
        
        with patch.object(recovery_agent, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = """
FALLBACK_QUERY: SELECT * FROM complex_table LIMIT 100
LIMITATIONS: Limited to 100 records, complex calculations removed
CONFIDENCE: 0.8
SUCCESS_RATE: 0.9
EXPLANATION: Simplified query by removing complex conditions and limiting results
"""
            
            fallback = await recovery_agent.generate_fallback_query(original_query, sample_error_context)
            
            assert fallback is not None
            assert fallback.fallback_query == "SELECT * FROM complex_table LIMIT 100"
            assert len(fallback.expected_limitations) > 0
            assert 0.0 <= fallback.confidence_score <= 1.0
            assert 0.0 <= fallback.estimated_success_rate <= 1.0
    
    @pytest.mark.asyncio
    async def test_partial_result_delivery(self, recovery_agent, sample_error_context):
        """Test partial result delivery with limitations."""
        partial_data = [
            {"id": 1, "name": "Test 1", "value": 100},
            {"id": 2, "name": "Test 2", "value": 200}
        ]
        limitations = [
            "Only first 2 records retrieved due to timeout",
            "Complex calculations not performed"
        ]
        
        partial_result = await recovery_agent.deliver_partial_results(
            partial_data, limitations, sample_error_context
        )
        
        assert partial_result.partial_data == partial_data
        assert partial_result.limitations == limitations
        assert 0.0 <= partial_result.completeness_percentage <= 100.0
        assert 0.0 <= partial_result.reliability_score <= 1.0
        assert len(partial_result.suggested_next_steps) > 0
        assert len(partial_result.missing_components) >= 0
    
    @pytest.mark.asyncio
    async def test_user_guidance_generation(self, recovery_agent, sample_error_context):
        """Test user guidance generation."""
        error_diagnosis = ErrorDiagnosis(
            error_id="test_error_123",
            original_error="Permission denied",
            error_category=ErrorCategory.PERMISSION_DENIED,
            severity=ErrorSeverity.HIGH,
            root_cause="User lacks access permissions",
            technical_explanation="Database access control denied",
            user_friendly_explanation="You don't have permission to access this data",
            suggested_actions=["Contact administrator", "Check permissions"],
            recovery_strategies=[RecoveryStrategy.USER_GUIDANCE],
            confidence_score=0.9,
            diagnosis_time_ms=100.0,
            context_factors=sample_error_context
        )
        
        with patch.object(recovery_agent, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = """
STEP_BY_STEP: 1. Contact your administrator
2. Request access to the required data
3. Wait for permission approval
4. Try your query again
ALTERNATIVES: Use publicly available data, Request sample data
PREVENTION: Check permissions before querying, Use authorized data sources
RESOURCES: User manual, Administrator contact
TIME_ESTIMATE: 15-30 minutes
"""
            
            guidance = await recovery_agent.provide_user_guidance(error_diagnosis, sample_error_context)
            
            assert guidance.guidance_id is not None
            assert len(guidance.step_by_step_guidance) > 0
            assert len(guidance.alternative_approaches) > 0
            assert len(guidance.prevention_tips) > 0
            assert guidance.estimated_resolution_time is not None
    
    def test_system_metrics_collection(self, recovery_agent):
        """Test system metrics collection."""
        metrics = recovery_agent.get_system_metrics()
        
        assert isinstance(metrics, SystemStressMetrics)
        assert 0.0 <= metrics.cpu_usage_percent <= 100.0
        assert 0.0 <= metrics.memory_usage_percent <= 100.0
        assert 0.0 <= metrics.disk_usage_percent <= 100.0
        assert metrics.active_connections >= 0
        assert metrics.stress_level in ["low", "medium", "high", "critical", "unknown"]
    
    @pytest.mark.asyncio
    async def test_system_stress_handling(self, recovery_agent):
        """Test system stress handling and graceful degradation."""
        # Create high stress metrics
        high_stress_metrics = SystemStressMetrics(
            cpu_usage_percent=90.0,
            memory_usage_percent=85.0,
            disk_usage_percent=75.0,
            active_connections=100,
            query_queue_length=50,
            average_response_time_ms=5000.0,
            error_rate_percent=15.0,
            stress_level="high"
        )
        
        stress_result = await recovery_agent.handle_system_stress(high_stress_metrics)
        
        assert "degradation_level" in stress_result
        assert "actions_taken" in stress_result
        assert len(stress_result["actions_taken"]) > 0
        assert "recommendations" in stress_result
        assert "estimated_recovery_time" in stress_result
    
    @pytest.mark.asyncio
    async def test_comprehensive_recovery_attempt(self, recovery_agent, sample_error_context):
        """Test comprehensive recovery attempt with multiple strategies."""
        error = ValueError("Schema mismatch in query")
        
        # Mock the diagnosis
        with patch.object(recovery_agent, 'diagnose_error', new_callable=AsyncMock) as mock_diagnose:
            mock_diagnosis = ErrorDiagnosis(
                error_id="test_error_456",
                original_error=str(error),
                error_category=ErrorCategory.SCHEMA_MISMATCH,
                severity=ErrorSeverity.MEDIUM,
                root_cause="Field name mismatch",
                technical_explanation="Query references non-existent field",
                user_friendly_explanation="The query references a field that doesn't exist",
                suggested_actions=["Check field names", "Update query"],
                recovery_strategies=[RecoveryStrategy.FALLBACK_QUERY, RecoveryStrategy.USER_GUIDANCE],
                confidence_score=0.8,
                diagnosis_time_ms=150.0,
                context_factors=sample_error_context
            )
            mock_diagnose.return_value = mock_diagnosis
            
            # Mock fallback query generation
            with patch.object(recovery_agent, 'generate_fallback_query', new_callable=AsyncMock) as mock_fallback:
                mock_fallback.return_value = FallbackQuery(
                    query_id="fallback_123",
                    original_query="SELECT invalid_field FROM table",
                    fallback_query="SELECT * FROM table LIMIT 10",
                    fallback_type="ai_generated",
                    expected_limitations=["All fields returned", "Limited to 10 records"],
                    confidence_score=0.7,
                    estimated_success_rate=0.85
                )
                
                recovery_result = await recovery_agent.attempt_recovery(mock_diagnosis, sample_error_context)
                
                assert recovery_result.recovery_id is not None
                assert recovery_result.original_error_id == mock_diagnosis.error_id
                assert recovery_result.strategy_used in [RecoveryStrategy.FALLBACK_QUERY, RecoveryStrategy.USER_GUIDANCE]
                assert recovery_result.recovery_time_ms > 0
    
    def test_performance_statistics(self, recovery_agent):
        """Test performance statistics collection."""
        stats = recovery_agent.get_performance_statistics()
        
        required_keys = [
            "total_errors_handled",
            "successful_recoveries", 
            "recovery_success_rate",
            "fallback_queries_generated",
            "partial_results_delivered",
            "user_guidance_provided",
            "system_degradations"
        ]
        
        for key in required_keys:
            assert key in stats
            assert isinstance(stats[key], (int, float))
    
    @pytest.mark.asyncio
    async def test_health_check(self, recovery_agent):
        """Test recovery agent health check."""
        health = await recovery_agent.health_check()
        
        assert "status" in health
        assert health["status"] in ["healthy", "unhealthy"]
        assert "diagnosis_working" in health
        assert "performance_statistics" in health


class TestErrorHandler:
    """Test the Error Handler integration layer."""
    
    @pytest.fixture
    def error_handler(self):
        """Create a test error handler."""
        config = get_config()
        return ErrorHandler(config)
    
    @pytest.fixture
    def sample_context(self):
        """Sample context for testing."""
        return {
            "user_id": "test_user",
            "client_id": "test_client",
            "operation": "test_operation"
        }
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, error_handler, sample_context):
        """Test integrated error handling."""
        error = RuntimeError("Test error for integration")
        
        with patch.object(error_handler.recovery_agent, 'diagnose_error', new_callable=AsyncMock) as mock_diagnose, \
             patch.object(error_handler.recovery_agent, 'attempt_recovery', new_callable=AsyncMock) as mock_recover:
            
            # Mock diagnosis
            mock_diagnosis = Mock()
            mock_diagnosis.error_id = "test_error_789"
            mock_diagnosis.error_category = ErrorCategory.UNKNOWN
            mock_diagnosis.severity = ErrorSeverity.MEDIUM
            mock_diagnosis.user_friendly_explanation = "A test error occurred"
            mock_diagnosis.suggested_actions = ["Try again", "Contact support"]
            mock_diagnosis.confidence_score = 0.7
            mock_diagnose.return_value = mock_diagnosis
            
            # Mock recovery
            mock_recovery = Mock()
            mock_recovery.recovery_id = "recovery_789"
            mock_recovery.success = True
            mock_recovery.strategy_used = RecoveryStrategy.USER_GUIDANCE
            mock_recovery.recovery_time_ms = 200.0
            mock_recovery.user_message = "Recovery successful"
            mock_recovery.fallback_query = None
            mock_recovery.partial_result = None
            mock_recovery.user_guidance = None
            mock_recovery.system_actions_taken = ["Generated guidance"]
            mock_recover.return_value = mock_recovery
            
            result = await error_handler.handle_error(error, sample_context)
            
            assert result["success"] == True
            assert result["error_id"] == "test_error_789"
            assert result["recovery_id"] == "recovery_789"
            assert result["message"] == "Recovery successful"
            assert "suggested_actions" in result
    
    @pytest.mark.asyncio
    async def test_fallback_query_integration(self, error_handler, sample_context):
        """Test fallback query generation integration."""
        query = "SELECT complex_calculation FROM difficult_table"
        
        with patch.object(error_handler.recovery_agent, 'generate_fallback_query', new_callable=AsyncMock) as mock_fallback:
            mock_fallback.return_value = FallbackQuery(
                query_id="fallback_456",
                original_query=query,
                fallback_query="SELECT * FROM difficult_table LIMIT 50",
                fallback_type="ai_generated",
                expected_limitations=["Simplified query", "Limited results"],
                confidence_score=0.8,
                estimated_success_rate=0.9
            )
            
            result = await error_handler.generate_fallback_for_query(query, sample_context)
            
            assert result["success"] == True
            assert result["fallback_query"] == "SELECT * FROM difficult_table LIMIT 50"
            assert len(result["limitations"]) > 0
            assert 0.0 <= result["confidence"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_partial_results_integration(self, error_handler, sample_context):
        """Test partial results delivery integration."""
        data = [{"id": 1, "value": "test"}]
        limitations = ["Incomplete data due to timeout"]
        
        with patch.object(error_handler.recovery_agent, 'deliver_partial_results', new_callable=AsyncMock) as mock_partial:
            mock_partial.return_value = PartialResult(
                result_id="partial_123",
                partial_data=data,
                limitations=limitations,
                completeness_percentage=60.0,
                missing_components=["Additional records"],
                reliability_score=0.7,
                suggested_next_steps=["Try simpler query"]
            )
            
            result = await error_handler.deliver_partial_results(data, limitations, sample_context)
            
            assert result["success"] == True
            assert result["result_type"] == "partial"
            assert result["data"] == data
            assert result["completeness_percentage"] == 60.0
            assert result["reliability_score"] == 0.7
    
    @pytest.mark.asyncio
    async def test_user_guidance_integration(self, error_handler, sample_context):
        """Test user guidance integration."""
        error = PermissionError("Access denied")
        
        with patch.object(error_handler.recovery_agent, 'diagnose_error', new_callable=AsyncMock) as mock_diagnose, \
             patch.object(error_handler.recovery_agent, 'provide_user_guidance', new_callable=AsyncMock) as mock_guidance:
            
            # Mock diagnosis
            mock_diagnosis = Mock()
            mock_diagnosis.error_category = ErrorCategory.PERMISSION_DENIED
            mock_diagnosis.severity = ErrorSeverity.HIGH
            mock_diagnose.return_value = mock_diagnosis
            
            # Mock guidance
            mock_guidance.return_value = UserGuidance(
                guidance_id="guidance_123",
                error_context="Permission denied",
                step_by_step_guidance=["Contact admin", "Request access"],
                alternative_approaches=["Use public data"],
                prevention_tips=["Check permissions first"],
                related_resources=["User manual"],
                estimated_resolution_time="10-15 minutes"
            )
            
            result = await error_handler.provide_user_guidance(error, sample_context)
            
            assert result["success"] == True
            assert len(result["step_by_step_guidance"]) > 0
            assert len(result["alternative_approaches"]) > 0
            assert result["error_category"] == "permission_denied"
    
    @pytest.mark.asyncio
    async def test_decorator_functionality(self, error_handler):
        """Test the error recovery decorator."""
        
        @error_handler.with_error_recovery("test_operation", {"test": True})
        async def test_function(should_fail: bool = False):
            if should_fail:
                raise ValueError("Test error")
            return "success"
        
        # Test successful execution
        result = await test_function(False)
        assert result == "success"
        
        # Test error handling (this will raise an error with recovery info)
        with pytest.raises(RuntimeError) as exc_info:
            await test_function(True)
        
        assert "Operation failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_system_stress_monitoring(self, error_handler):
        """Test system stress monitoring integration."""
        with patch.object(error_handler.recovery_agent, 'get_system_metrics') as mock_metrics, \
             patch.object(error_handler.recovery_agent, 'handle_system_stress', new_callable=AsyncMock) as mock_stress:
            
            # Mock high stress metrics
            mock_metrics.return_value = SystemStressMetrics(
                cpu_usage_percent=85.0,
                memory_usage_percent=80.0,
                disk_usage_percent=70.0,
                active_connections=50,
                query_queue_length=20,
                average_response_time_ms=3000.0,
                error_rate_percent=12.0,
                stress_level="high"
            )
            
            mock_stress.return_value = {
                "degradation_level": "moderate",
                "actions_taken": ["Reduced concurrent queries", "Enabled caching"],
                "recommendations": ["Scale resources", "Optimize queries"],
                "estimated_recovery_time": "5-10 minutes"
            }
            
            result = await error_handler.handle_system_stress()
            
            assert result["stress_detected"] == True
            assert result["stress_level"] == "high"
            assert len(result["actions_taken"]) > 0
    
    def test_error_statistics(self, error_handler):
        """Test error statistics collection."""
        stats = error_handler.get_error_statistics()
        
        assert "error_handler_stats" in stats
        assert "recovery_agent_stats" in stats
        assert "total_errors" in stats
        assert "recovery_success_rate" in stats
        assert "system_health" in stats
    
    @pytest.mark.asyncio
    async def test_health_check_integration(self, error_handler):
        """Test integrated health check."""
        with patch.object(error_handler.recovery_agent, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = {"status": "healthy"}
            
            health = await error_handler.health_check()
            
            assert health["status"] == "healthy"
            assert health["error_handler_active"] == True
            assert "features_available" in health
            assert len(health["features_available"]) > 0


class TestErrorRecoveryIntegration:
    """Test integration with existing system components."""
    
    def test_global_error_handler(self):
        """Test global error handler singleton."""
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        
        assert handler1 is handler2  # Should be the same instance
        assert isinstance(handler1, ErrorHandler)
    
    @pytest.mark.asyncio
    async def test_convenience_decorator(self):
        """Test convenience decorator function."""
        
        @with_error_recovery("test_op")
        async def test_func():
            return "test_result"
        
        result = await test_func()
        assert result == "test_result"
    
    @pytest.mark.asyncio
    async def test_convenience_error_handler(self):
        """Test convenience error handling function."""
        from light_ai.agents.error_handler import handle_error_with_recovery
        
        error = ValueError("Test error")
        context = {"test": True}
        
        with patch('light_ai.agents.error_handler.get_error_handler') as mock_get_handler:
            mock_handler = Mock()
            mock_handler.handle_error = AsyncMock(return_value={"success": True})
            mock_get_handler.return_value = mock_handler
            
            result = await handle_error_with_recovery(error, context)
            
            assert result["success"] == True
            mock_handler.handle_error.assert_called_once_with(error, context)


# Property-based tests for error recovery system
class TestErrorRecoveryProperties:
    """Property-based tests for error recovery system correctness."""
    
    @pytest.fixture
    def recovery_agent(self):
        """Create a test recovery agent."""
        return ErrorRecoveryAgent(get_config())
    
    @pytest.mark.asyncio
    async def test_error_diagnosis_consistency_property(self, recovery_agent):
        """
        Property: For any error and context, diagnosis should be consistent and complete.
        **Validates: Requirements 9.1**
        """
        # Test with various error types
        test_errors = [
            ValueError("Test value error"),
            PermissionError("Access denied"),
            TimeoutError("Operation timeout"),
            ConnectionError("Network failure"),
            RuntimeError("Runtime issue")
        ]
        
        context = {"user_id": "test", "client_id": "test", "operation": "test"}
        
        for error in test_errors:
            diagnosis = await recovery_agent.diagnose_error(error, context)
            
            # Property: Diagnosis should always be complete and valid
            assert diagnosis.error_id is not None
            assert diagnosis.error_category in ErrorCategory
            assert diagnosis.severity in ErrorSeverity
            assert isinstance(diagnosis.suggested_actions, list)
            assert len(diagnosis.suggested_actions) > 0
            assert isinstance(diagnosis.recovery_strategies, list)
            assert len(diagnosis.recovery_strategies) > 0
            assert 0.0 <= diagnosis.confidence_score <= 1.0
            assert diagnosis.diagnosis_time_ms >= 0
    
    @pytest.mark.asyncio
    async def test_partial_result_reliability_property(self, recovery_agent):
        """
        Property: Partial results should always have valid reliability scores and completeness.
        **Validates: Requirements 9.3**
        """
        test_cases = [
            ([], ["No data available"]),  # Empty data
            ([{"id": 1}], ["Incomplete record"]),  # Minimal data
            ([{"id": i, "value": f"test_{i}"} for i in range(10)], ["Limited to 10 records"])  # Normal data
        ]
        
        context = {"expected_record_count": 100}
        
        for data, limitations in test_cases:
            partial_result = await recovery_agent.deliver_partial_results(data, limitations, context)
            
            # Property: Partial results should always be valid and informative
            assert 0.0 <= partial_result.completeness_percentage <= 100.0
            assert 0.0 <= partial_result.reliability_score <= 1.0
            assert isinstance(partial_result.limitations, list)
            assert isinstance(partial_result.missing_components, list)
            assert isinstance(partial_result.suggested_next_steps, list)
            assert len(partial_result.suggested_next_steps) > 0
    
    def test_system_metrics_validity_property(self, recovery_agent):
        """
        Property: System metrics should always be within valid ranges.
        **Validates: Requirements 9.5**
        """
        metrics = recovery_agent.get_system_metrics()
        
        # Property: All metrics should be within valid ranges
        assert 0.0 <= metrics.cpu_usage_percent <= 100.0
        assert 0.0 <= metrics.memory_usage_percent <= 100.0
        assert 0.0 <= metrics.disk_usage_percent <= 100.0
        assert metrics.active_connections >= 0
        assert metrics.query_queue_length >= 0
        assert metrics.average_response_time_ms >= 0.0
        assert metrics.error_rate_percent >= 0.0
        assert metrics.stress_level in ["low", "medium", "high", "critical", "unknown"]
    
    @pytest.mark.asyncio
    async def test_recovery_strategy_selection_property(self, recovery_agent):
        """
        Property: Recovery strategies should be appropriate for error categories.
        **Validates: Requirements 9.2, 9.4**
        """
        # Test that each error category gets appropriate recovery strategies
        for category in ErrorCategory:
            if category in recovery_agent.recovery_strategies:
                strategies = recovery_agent.recovery_strategies[category]
                
                # Property: Each category should have at least one recovery strategy
                assert len(strategies) > 0
                assert all(isinstance(s, RecoveryStrategy) for s in strategies)
                
                # Property: Strategies should be logically appropriate for the category
                if category == ErrorCategory.PERMISSION_DENIED:
                    assert RecoveryStrategy.USER_GUIDANCE in strategies
                elif category == ErrorCategory.QUERY_SYNTAX:
                    assert RecoveryStrategy.FALLBACK_QUERY in strategies
                elif category == ErrorCategory.SYSTEM_OVERLOAD:
                    assert RecoveryStrategy.GRACEFUL_DEGRADATION in strategies


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
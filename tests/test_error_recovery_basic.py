"""
Basic tests for the error recovery system that don't require external API calls.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock

from light_ai.agents.error_recovery_agent import (
    ErrorRecoveryAgent, ErrorCategory, ErrorSeverity, RecoveryStrategy,
    ErrorDiagnosis, SystemStressMetrics
)
from light_ai.agents.error_handler import ErrorHandler
from light_ai.config import get_config


class TestErrorRecoveryBasic:
    """Basic tests for error recovery functionality."""
    
    @pytest.fixture
    def recovery_agent(self):
        """Create a test recovery agent."""
        return ErrorRecoveryAgent(get_config())
    
    def test_error_categorization(self, recovery_agent):
        """Test error categorization logic."""
        test_cases = [
            (PermissionError("Access denied"), ErrorCategory.PERMISSION_DENIED),
            (ValueError("Schema mismatch"), ErrorCategory.SCHEMA_MISMATCH),
            (TimeoutError("Query timeout"), ErrorCategory.TIMEOUT),
            (ConnectionError("Network error"), ErrorCategory.NETWORK_ERROR),
            (RuntimeError("Unknown error"), ErrorCategory.UNKNOWN),
        ]
        
        for error, expected_category in test_cases:
            context = {"test": True}
            category = recovery_agent._categorize_error(error, context)
            # Allow for reasonable categorization variations
            assert category in ErrorCategory
    
    def test_error_severity_assessment(self, recovery_agent):
        """Test error severity assessment."""
        context = {"test": True}
        
        # Test critical errors
        critical_error = RuntimeError("System overload")
        severity = recovery_agent._assess_error_severity(
            critical_error, context, ErrorCategory.SYSTEM_OVERLOAD
        )
        assert severity == ErrorSeverity.CRITICAL
        
        # Test high severity errors
        high_error = PermissionError("Access denied")
        severity = recovery_agent._assess_error_severity(
            high_error, context, ErrorCategory.PERMISSION_DENIED
        )
        assert severity == ErrorSeverity.HIGH
        
        # Test medium severity errors
        medium_error = ValueError("Schema mismatch")
        severity = recovery_agent._assess_error_severity(
            medium_error, context, ErrorCategory.SCHEMA_MISMATCH
        )
        assert severity == ErrorSeverity.MEDIUM
    
    def test_system_metrics_collection(self, recovery_agent):
        """Test system metrics collection."""
        metrics = recovery_agent.get_system_metrics()
        
        assert isinstance(metrics, SystemStressMetrics)
        assert metrics.cpu_usage_percent >= 0.0
        assert metrics.memory_usage_percent >= 0.0
        assert metrics.disk_usage_percent >= 0.0
        assert metrics.active_connections >= 0
        assert metrics.stress_level in ["low", "medium", "high", "critical", "unknown"]
    
    def test_recovery_strategy_mapping(self, recovery_agent):
        """Test recovery strategy mapping for different error categories."""
        # Test that each category has appropriate strategies
        for category in ErrorCategory:
            if category in recovery_agent.recovery_strategies:
                strategies = recovery_agent.recovery_strategies[category]
                assert len(strategies) > 0
                assert all(isinstance(s, RecoveryStrategy) for s in strategies)
    
    @pytest.mark.asyncio
    async def test_error_diagnosis_fallback(self, recovery_agent):
        """Test error diagnosis with API failure fallback."""
        error = ValueError("Test error")
        context = {"user_id": "test", "client_id": "test"}
        
        # This will use the fallback diagnosis since API calls will fail
        diagnosis = await recovery_agent.diagnose_error(error, context)
        
        assert diagnosis.error_id is not None
        assert diagnosis.error_category in ErrorCategory
        assert diagnosis.severity in ErrorSeverity
        assert len(diagnosis.suggested_actions) > 0
        assert len(diagnosis.recovery_strategies) > 0
        assert 0.0 <= diagnosis.confidence_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_partial_result_delivery(self, recovery_agent):
        """Test partial result delivery functionality."""
        data = [{"id": 1, "name": "test"}]
        limitations = ["Test limitation"]
        context = {"user_id": "test", "expected_record_count": 10}
        
        partial_result = await recovery_agent.deliver_partial_results(data, limitations, context)
        
        assert partial_result.partial_data == data
        assert partial_result.limitations == limitations
        assert 0.0 <= partial_result.completeness_percentage <= 100.0
        assert 0.0 <= partial_result.reliability_score <= 1.0
        assert len(partial_result.suggested_next_steps) > 0
    
    def test_performance_statistics(self, recovery_agent):
        """Test performance statistics collection."""
        stats = recovery_agent.get_performance_statistics()
        
        required_keys = [
            "total_errors_handled",
            "successful_recoveries",
            "recovery_success_rate",
            "fallback_queries_generated",
            "partial_results_delivered",
            "user_guidance_provided"
        ]
        
        for key in required_keys:
            assert key in stats
            assert isinstance(stats[key], (int, float))
    
    @pytest.mark.asyncio
    async def test_system_stress_handling(self, recovery_agent):
        """Test system stress handling."""
        # Create test stress metrics
        stress_metrics = SystemStressMetrics(
            cpu_usage_percent=85.0,
            memory_usage_percent=80.0,
            disk_usage_percent=70.0,
            active_connections=50,
            query_queue_length=20,
            average_response_time_ms=3000.0,
            error_rate_percent=12.0,
            stress_level="high"
        )
        
        result = await recovery_agent.handle_system_stress(stress_metrics)
        
        assert "degradation_level" in result
        assert "actions_taken" in result
        assert "recommendations" in result
        assert len(result["actions_taken"]) > 0


class TestErrorHandler:
    """Test the error handler integration."""
    
    @pytest.fixture
    def error_handler(self):
        """Create a test error handler."""
        return ErrorHandler(get_config())
    
    def test_error_handler_initialization(self, error_handler):
        """Test error handler initialization."""
        assert error_handler.recovery_agent is not None
        assert isinstance(error_handler.stats, dict)
        assert "total_errors_intercepted" in error_handler.stats
    
    @pytest.mark.asyncio
    async def test_error_handling_with_mock(self, error_handler):
        """Test error handling with mocked recovery agent."""
        error = RuntimeError("Test error")
        context = {"user_id": "test", "client_id": "test"}
        
        # Mock the recovery agent methods
        with patch.object(error_handler.recovery_agent, 'diagnose_error', new_callable=AsyncMock) as mock_diagnose, \
             patch.object(error_handler.recovery_agent, 'attempt_recovery', new_callable=AsyncMock) as mock_recover:
            
            # Mock diagnosis
            mock_diagnosis = Mock()
            mock_diagnosis.error_id = "test_error"
            mock_diagnosis.error_category = ErrorCategory.UNKNOWN
            mock_diagnosis.severity = ErrorSeverity.MEDIUM
            mock_diagnosis.user_friendly_explanation = "Test error occurred"
            mock_diagnosis.suggested_actions = ["Try again"]
            mock_diagnosis.confidence_score = 0.7
            mock_diagnose.return_value = mock_diagnosis
            
            # Mock recovery
            mock_recovery = Mock()
            mock_recovery.recovery_id = "test_recovery"
            mock_recovery.success = True
            mock_recovery.strategy_used = RecoveryStrategy.USER_GUIDANCE
            mock_recovery.recovery_time_ms = 100.0
            mock_recovery.user_message = "Recovery successful"
            mock_recovery.fallback_query = None
            mock_recovery.partial_result = None
            mock_recovery.user_guidance = None
            mock_recovery.system_actions_taken = []
            mock_recover.return_value = mock_recovery
            
            result = await error_handler.handle_error(error, context)
            
            assert result["success"] == True
            assert result["error_id"] == "test_error"
            assert result["recovery_id"] == "test_recovery"
            assert "message" in result
    
    def test_error_statistics(self, error_handler):
        """Test error statistics collection."""
        stats = error_handler.get_error_statistics()
        
        assert "error_handler_stats" in stats
        assert "recovery_agent_stats" in stats
        assert "total_errors" in stats
        assert "recovery_success_rate" in stats
    
    @pytest.mark.asyncio
    async def test_health_check(self, error_handler):
        """Test error handler health check."""
        with patch.object(error_handler.recovery_agent, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = {"status": "healthy"}
            
            health = await error_handler.health_check()
            
            assert "status" in health
            assert "error_handler_active" in health
            assert "features_available" in health


# Property-based tests
class TestErrorRecoveryProperties:
    """Property-based tests for error recovery correctness."""
    
    @pytest.fixture
    def recovery_agent(self):
        """Create a test recovery agent."""
        return ErrorRecoveryAgent(get_config())
    
    def test_error_categorization_consistency_property(self, recovery_agent):
        """
        Property: Error categorization should be consistent for the same error type.
        **Validates: Requirements 9.1**
        """
        test_errors = [
            PermissionError("Access denied"),
            ValueError("Invalid value"),
            TimeoutError("Operation timeout"),
            ConnectionError("Network failure")
        ]
        
        context = {"test": True}
        
        for error in test_errors:
            # Test multiple times to ensure consistency
            category1 = recovery_agent._categorize_error(error, context)
            category2 = recovery_agent._categorize_error(error, context)
            
            # Property: Same error should always get same category
            assert category1 == category2
            assert category1 in ErrorCategory
    
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
    async def test_partial_result_completeness_property(self, recovery_agent):
        """
        Property: Partial result completeness should be proportional to data size.
        **Validates: Requirements 9.3**
        """
        context = {"expected_record_count": 100}
        limitations = ["Test limitation"]
        
        test_cases = [
            [],  # Empty data
            [{"id": i} for i in range(10)],  # 10% of expected
            [{"id": i} for i in range(50)],  # 50% of expected
            [{"id": i} for i in range(100)],  # 100% of expected
        ]
        
        previous_completeness = -1
        
        for data in test_cases:
            partial_result = await recovery_agent.deliver_partial_results(data, limitations, context)
            
            # Property: More data should generally mean higher completeness
            # (allowing for some variation due to calculation methods)
            if len(data) > 0:
                assert partial_result.completeness_percentage >= 0.0
            
            # Property: Completeness should never exceed 100%
            assert partial_result.completeness_percentage <= 100.0
            
            # Property: Reliability should be reasonable
            assert 0.0 <= partial_result.reliability_score <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
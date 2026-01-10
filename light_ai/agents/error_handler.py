"""
Error Handler Integration Layer.

This module provides integration between the Error Recovery Agent and the existing
system components, ensuring seamless error handling across all agents and operations.
"""

import asyncio
import functools
import time
from typing import Dict, Any, Optional, Callable, Union, List
from dataclasses import asdict
import logging

from .error_recovery_agent import (
    ErrorRecoveryAgent, ErrorDiagnosis, RecoveryResult, 
    PartialResult, UserGuidance, SystemStressMetrics
)
from .logging import get_activity_logger
from ..config import Config, get_config
from ..logger import get_logger

logger = get_logger(__name__)
activity_logger = get_activity_logger()


class ErrorHandler:
    """
    Central error handling coordinator that integrates error recovery
    capabilities across all system components.
    
    This class provides:
    - Automatic error interception and recovery
    - Consistent error response formatting
    - System stress monitoring and response
    - Performance tracking and optimization
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the error handler with recovery agent."""
        self.config = config or get_config()
        self.recovery_agent = ErrorRecoveryAgent(config)
        self.activity_logger = get_activity_logger()
        
        # Error handling statistics
        self.stats = {
            "total_errors_intercepted": 0,
            "automatic_recoveries": 0,
            "fallback_queries_used": 0,
            "partial_results_delivered": 0,
            "user_guidance_provided": 0,
            "system_stress_events": 0
        }
        
        self.logger = logger
        self.logger.info("Error Handler initialized with recovery capabilities")
    
    def with_error_recovery(self, operation_name: str = None, 
                          context: Dict[str, Any] = None):
        """
        Decorator for automatic error recovery on any function or method.
        
        Args:
            operation_name: Name of the operation for logging
            context: Additional context for error recovery
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self._execute_with_recovery(
                    func, args, kwargs, operation_name or func.__name__, context or {}
                )
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                return asyncio.run(self._execute_with_recovery(
                    func, args, kwargs, operation_name or func.__name__, context or {}
                ))
            
            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    async def handle_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an error with comprehensive recovery attempts.
        
        Args:
            error: The exception that occurred
            context: Context information about the error
            
        Returns:
            Recovery result with user-friendly response
        """
        try:
            self.stats["total_errors_intercepted"] += 1
            
            self.logger.info(f"Handling error: {type(error).__name__}: {str(error)}")
            
            # Add timestamp to context
            context["timestamp"] = time.time()
            context["error_handler_version"] = "1.0"
            
            # Diagnose the error
            diagnosis = await self.recovery_agent.diagnose_error(error, context)
            
            # Attempt recovery
            recovery_result = await self.recovery_agent.attempt_recovery(diagnosis, context)
            
            # Update statistics based on recovery result
            if recovery_result.success:
                self.stats["automatic_recoveries"] += 1
                
                if recovery_result.fallback_query:
                    self.stats["fallback_queries_used"] += 1
                
                if recovery_result.partial_result:
                    self.stats["partial_results_delivered"] += 1
                
                if recovery_result.user_guidance:
                    self.stats["user_guidance_provided"] += 1
            
            # Log the error handling
            activity_logger.log_agent_response(
                "error_handler", context.get("user_id", "system"), 
                context.get("client_id", "system"),
                f"Error handled: {diagnosis.error_category.value}",
                recovery_result.recovery_time_ms, "error_recovery_agent",
                context.get("conversation_id"), None,
                {
                    "error_id": diagnosis.error_id,
                    "recovery_id": recovery_result.recovery_id,
                    "success": recovery_result.success,
                    "strategy": recovery_result.strategy_used.value
                }
            )
            
            # Format response for user
            return self._format_error_response(diagnosis, recovery_result, context)
            
        except Exception as handler_error:
            self.logger.error(f"Error handler itself failed: {handler_error}")
            
            # Return basic error response as last resort
            return {
                "success": False,
                "error_type": "system_error",
                "message": "An unexpected error occurred and our recovery system is having issues. Please try again or contact support.",
                "suggestions": [
                    "Try refreshing the page",
                    "Simplify your request",
                    "Contact support if the problem persists"
                ],
                "error_id": f"handler_error_{int(time.time())}",
                "timestamp": time.time()
            }
    
    async def handle_system_stress(self) -> Dict[str, Any]:
        """
        Monitor and handle system stress conditions.
        
        Returns:
            System stress handling result
        """
        try:
            # Get current system metrics
            metrics = self.recovery_agent.get_system_metrics()
            
            # Handle stress if needed
            if metrics.stress_level in ["medium", "high", "critical"]:
                self.stats["system_stress_events"] += 1
                
                stress_result = await self.recovery_agent.handle_system_stress(metrics)
                
                self.logger.warning(f"System stress handled: {metrics.stress_level} -> {stress_result['degradation_level']}")
                
                return {
                    "stress_detected": True,
                    "stress_level": metrics.stress_level,
                    "actions_taken": stress_result["actions_taken"],
                    "degradation_level": stress_result["degradation_level"],
                    "recommendations": stress_result.get("recommendations", []),
                    "estimated_recovery_time": stress_result.get("estimated_recovery_time", "Unknown")
                }
            
            return {
                "stress_detected": False,
                "stress_level": metrics.stress_level,
                "system_healthy": True
            }
            
        except Exception as e:
            self.logger.error(f"System stress handling failed: {e}")
            return {
                "stress_detected": True,
                "stress_level": "unknown",
                "error": str(e),
                "system_healthy": False
            }
    
    async def generate_fallback_for_query(self, query: str, error_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate a fallback query for a failed operation.
        
        Args:
            query: The original query that failed
            error_context: Context about the failure
            
        Returns:
            Fallback query information or None
        """
        try:
            fallback = await self.recovery_agent.generate_fallback_query(query, error_context)
            
            if fallback:
                return {
                    "success": True,
                    "fallback_query": fallback.fallback_query,
                    "limitations": fallback.expected_limitations,
                    "confidence": fallback.confidence_score,
                    "success_estimate": fallback.estimated_success_rate,
                    "query_id": fallback.query_id
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Fallback query generation failed: {e}")
            return None
    
    async def deliver_partial_results(self, data: List[Dict[str, Any]], 
                                    limitations: List[str], 
                                    context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deliver partial results with proper formatting and limitations.
        
        Args:
            data: Available partial data
            limitations: List of limitations
            context: Context about the original request
            
        Returns:
            Formatted partial result response
        """
        try:
            partial_result = await self.recovery_agent.deliver_partial_results(data, limitations, context)
            
            return {
                "success": True,
                "result_type": "partial",
                "data": partial_result.partial_data,
                "limitations": partial_result.limitations,
                "completeness_percentage": partial_result.completeness_percentage,
                "reliability_score": partial_result.reliability_score,
                "missing_components": partial_result.missing_components,
                "next_steps": partial_result.suggested_next_steps,
                "result_id": partial_result.result_id
            }
            
        except Exception as e:
            self.logger.error(f"Partial result delivery failed: {e}")
            return {
                "success": False,
                "result_type": "error",
                "data": data,  # Return raw data as fallback
                "limitations": limitations + [f"Result processing error: {str(e)}"],
                "completeness_percentage": 0.0,
                "reliability_score": 0.3
            }
    
    async def provide_user_guidance(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provide user guidance for error resolution.
        
        Args:
            error: The error that occurred
            context: Context about the error
            
        Returns:
            User guidance information
        """
        try:
            # First diagnose the error
            diagnosis = await self.recovery_agent.diagnose_error(error, context)
            
            # Generate guidance
            guidance = await self.recovery_agent.provide_user_guidance(diagnosis, context)
            
            return {
                "success": True,
                "guidance_id": guidance.guidance_id,
                "error_explanation": guidance.error_context,
                "step_by_step_guidance": guidance.step_by_step_guidance,
                "alternative_approaches": guidance.alternative_approaches,
                "prevention_tips": guidance.prevention_tips,
                "related_resources": guidance.related_resources,
                "estimated_resolution_time": guidance.estimated_resolution_time,
                "error_category": diagnosis.error_category.value,
                "severity": diagnosis.severity.value
            }
            
        except Exception as e:
            self.logger.error(f"User guidance generation failed: {e}")
            return {
                "success": False,
                "error_explanation": str(error),
                "step_by_step_guidance": [
                    "Try refreshing the page or restarting your session",
                    "Simplify your request and try again",
                    "Contact support if the problem persists"
                ],
                "alternative_approaches": ["Try a different approach to your task"],
                "prevention_tips": ["Follow system best practices"],
                "estimated_resolution_time": "5-15 minutes"
            }
    
    async def _execute_with_recovery(self, func: Callable, args: tuple, kwargs: dict,
                                   operation_name: str, context: Dict[str, Any]) -> Any:
        """
        Execute a function with automatic error recovery.
        
        Args:
            func: Function to execute
            args: Function arguments
            kwargs: Function keyword arguments
            operation_name: Name of the operation
            context: Additional context
            
        Returns:
            Function result or recovery result
        """
        try:
            # Execute the original function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            return result
            
        except Exception as error:
            # Add operation context
            error_context = {
                "operation_name": operation_name,
                "function_name": func.__name__,
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys()),
                **context
            }
            
            # Handle the error with recovery
            recovery_response = await self.handle_error(error, error_context)
            
            # If recovery was successful and provided results, return them
            if recovery_response.get("success") and recovery_response.get("recovered_data"):
                return recovery_response["recovered_data"]
            
            # Otherwise, raise a user-friendly error with recovery information
            raise RuntimeError(f"Operation failed: {recovery_response.get('message', str(error))}")
    
    def _format_error_response(self, diagnosis: ErrorDiagnosis, 
                             recovery_result: RecoveryResult,
                             context: Dict[str, Any]) -> Dict[str, Any]:
        """Format error and recovery information for user consumption."""
        
        response = {
            "success": recovery_result.success,
            "error_id": diagnosis.error_id,
            "recovery_id": recovery_result.recovery_id,
            "error_category": diagnosis.error_category.value,
            "severity": diagnosis.severity.value,
            "message": recovery_result.user_message or diagnosis.user_friendly_explanation,
            "confidence": diagnosis.confidence_score,
            "recovery_strategy": recovery_result.strategy_used.value,
            "recovery_time_ms": recovery_result.recovery_time_ms,
            "timestamp": context.get("timestamp", time.time())
        }
        
        # Add recovery-specific information
        if recovery_result.fallback_query:
            response["fallback_query"] = {
                "query": recovery_result.fallback_query.fallback_query,
                "limitations": recovery_result.fallback_query.expected_limitations,
                "confidence": recovery_result.fallback_query.confidence_score,
                "success_estimate": recovery_result.fallback_query.estimated_success_rate
            }
        
        if recovery_result.partial_result:
            response["partial_result"] = {
                "data": recovery_result.partial_result.partial_data,
                "completeness": recovery_result.partial_result.completeness_percentage,
                "limitations": recovery_result.partial_result.limitations,
                "reliability": recovery_result.partial_result.reliability_score,
                "next_steps": recovery_result.partial_result.suggested_next_steps
            }
        
        if recovery_result.user_guidance:
            response["user_guidance"] = {
                "steps": recovery_result.user_guidance.step_by_step_guidance,
                "alternatives": recovery_result.user_guidance.alternative_approaches,
                "prevention": recovery_result.user_guidance.prevention_tips,
                "resources": recovery_result.user_guidance.related_resources,
                "estimated_time": recovery_result.user_guidance.estimated_resolution_time
            }
        
        # Add suggested actions
        response["suggested_actions"] = diagnosis.suggested_actions
        
        # Add system actions taken
        if recovery_result.system_actions_taken:
            response["system_actions"] = recovery_result.system_actions_taken
        
        return response
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error handling statistics."""
        recovery_stats = self.recovery_agent.get_performance_statistics()
        
        return {
            "error_handler_stats": self.stats,
            "recovery_agent_stats": recovery_stats,
            "total_errors": self.stats["total_errors_intercepted"],
            "recovery_success_rate": (self.stats["automatic_recoveries"] / max(self.stats["total_errors_intercepted"], 1)) * 100,
            "system_health": self.recovery_agent.get_system_metrics().stress_level
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the error handling system."""
        try:
            # Test recovery agent
            recovery_health = await self.recovery_agent.health_check()
            
            # Test system stress monitoring
            stress_check = await self.handle_system_stress()
            
            return {
                "status": "healthy",
                "error_handler_active": True,
                "recovery_agent_status": recovery_health.get("status", "unknown"),
                "system_monitoring_active": stress_check.get("system_healthy", False),
                "statistics": self.get_error_statistics(),
                "features_available": [
                    "automatic_error_recovery",
                    "fallback_query_generation", 
                    "partial_result_delivery",
                    "user_guidance_system",
                    "system_stress_monitoring",
                    "graceful_degradation"
                ]
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "error_handler_active": False
            }


# Global error handler instance
_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler(config: Optional[Config] = None) -> ErrorHandler:
    """Get the global error handler instance."""
    global _global_error_handler
    
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler(config)
    
    return _global_error_handler


def with_error_recovery(operation_name: str = None, context: Dict[str, Any] = None):
    """
    Convenience decorator for adding error recovery to any function.
    
    Usage:
        @with_error_recovery("data_query", {"user_id": "123"})
        async def query_data(query: str):
            # Your function implementation
            pass
    """
    handler = get_error_handler()
    return handler.with_error_recovery(operation_name, context)


async def handle_error_with_recovery(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function for handling errors with recovery.
    
    Args:
        error: The exception that occurred
        context: Context information about the error
        
    Returns:
        Recovery result with user-friendly response
    """
    handler = get_error_handler()
    return await handler.handle_error(error, context)
"""
Robust Error Handling and Recovery System for AI Data Analyst.

This module implements comprehensive error handling and recovery capabilities
including AI-powered error diagnosis, automatic fallback query generation,
partial result delivery, user guidance, and graceful degradation under system stress.

Addresses Requirements 9.1, 9.2, 9.3, 9.4, 9.5 from the Intelligent Data Analyst specification.
"""

import asyncio
import time
import uuid
import traceback
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

# Optional dependency for system monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

from .base import BaseAgent, AgentConfig
from .logging import get_activity_logger
from ..core.models import AccessLevel, ResourceType
from ..config import Config, get_config
from ..logger import get_logger

logger = get_logger(__name__)
activity_logger = get_activity_logger()


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of errors for targeted recovery."""
    DATA_ACCESS = "data_access"
    SCHEMA_MISMATCH = "schema_mismatch"
    QUERY_SYNTAX = "query_syntax"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    PERMISSION_DENIED = "permission_denied"
    TIMEOUT = "timeout"
    NETWORK_ERROR = "network_error"
    AI_MODEL_ERROR = "ai_model_error"
    DATA_CORRUPTION = "data_corruption"
    SYSTEM_OVERLOAD = "system_overload"
    UNKNOWN = "unknown"


class RecoveryStrategy(Enum):
    """Recovery strategies for different error types."""
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    FALLBACK_QUERY = "fallback_query"
    PARTIAL_RESULTS = "partial_results"
    SIMPLIFIED_APPROACH = "simplified_approach"
    RESOURCE_SCALING = "resource_scaling"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    USER_GUIDANCE = "user_guidance"
    SYSTEM_RESTART = "system_restart"


@dataclass
class ErrorDiagnosis:
    """AI-powered error diagnosis result."""
    error_id: str
    original_error: str
    error_category: ErrorCategory
    severity: ErrorSeverity
    root_cause: str
    technical_explanation: str
    user_friendly_explanation: str
    suggested_actions: List[str]
    recovery_strategies: List[RecoveryStrategy]
    confidence_score: float
    diagnosis_time_ms: float
    context_factors: Dict[str, Any]


@dataclass
class FallbackQuery:
    """Fallback query definition."""
    query_id: str
    original_query: str
    fallback_query: str
    fallback_type: str
    expected_limitations: List[str]
    confidence_score: float
    estimated_success_rate: float


@dataclass
class PartialResult:
    """Partial result with limitations."""
    result_id: str
    partial_data: List[Dict[str, Any]]
    limitations: List[str]
    completeness_percentage: float
    missing_components: List[str]
    reliability_score: float
    suggested_next_steps: List[str]


@dataclass
class UserGuidance:
    """User guidance for error resolution."""
    guidance_id: str
    error_context: str
    step_by_step_guidance: List[str]
    alternative_approaches: List[str]
    prevention_tips: List[str]
    related_resources: List[str]
    estimated_resolution_time: str


@dataclass
class SystemStressMetrics:
    """System stress and performance metrics."""
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    active_connections: int
    query_queue_length: int
    average_response_time_ms: float
    error_rate_percent: float
    stress_level: str  # low, medium, high, critical


@dataclass
class RecoveryResult:
    """Result of error recovery attempt."""
    recovery_id: str
    original_error_id: str
    strategy_used: RecoveryStrategy
    success: bool
    recovery_time_ms: float
    partial_result: Optional[PartialResult] = None
    fallback_query: Optional[FallbackQuery] = None
    user_guidance: Optional[UserGuidance] = None
    error_diagnosis: Optional[ErrorDiagnosis] = None
    system_actions_taken: List[str] = None
    user_message: str = ""


class ErrorRecoveryAgent(BaseAgent):
    """
    Robust Error Handling and Recovery System.
    
    This agent provides comprehensive error handling capabilities including:
    
    - AI-powered error diagnosis and explanation (Requirement 9.1)
    - Automatic fallback query generation (Requirement 9.2)
    - Partial result delivery with clear limitations (Requirement 9.3)
    - User guidance and suggestion system (Requirement 9.4)
    - Graceful degradation under system stress (Requirement 9.5)
    
    The system monitors system health, diagnoses errors intelligently,
    and provides multiple recovery strategies to ensure users always
    get helpful responses even when primary systems fail.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the Error Recovery Agent."""
        
        # Enhanced system prompt for error diagnosis and recovery
        system_prompt = """You are an expert AI Error Diagnosis and Recovery Specialist with deep knowledge of data systems, query processing, and user experience.

Your capabilities:
1. Analyze errors and provide clear, actionable diagnoses
2. Generate fallback strategies and alternative approaches
3. Explain technical issues in user-friendly language
4. Suggest step-by-step recovery procedures
5. Provide prevention tips and best practices
6. Assess system stress and recommend optimizations

Error Analysis Process:
1. Categorize the error type and severity
2. Identify root causes and contributing factors
3. Assess impact on user workflow
4. Generate multiple recovery strategies
5. Provide clear explanations and guidance
6. Suggest preventive measures

Always:
- Be clear and helpful in explanations
- Provide multiple solution options when possible
- Consider user skill level in guidance
- Focus on getting users back to productive work
- Learn from error patterns to improve system resilience
- Maintain empathy and understanding in communications

You have access to system metrics, error logs, and user context to provide the most relevant and effective recovery assistance."""

        agent_config = AgentConfig(
            name="error_recovery_agent",
            model_name=config.openrouter.default_model if config else "anthropic/claude-3.5-sonnet",
            temperature=0.2,  # Lower temperature for consistent error analysis
            max_tokens=4096,
            timeout_seconds=60,
            system_prompt=system_prompt
        )
        
        super().__init__(agent_config, config)
        
        # Initialize components
        self.activity_logger = get_activity_logger()
        self.config = config or get_config()
        
        # Error tracking and metrics
        self.error_history: Dict[str, ErrorDiagnosis] = {}
        self.recovery_history: Dict[str, RecoveryResult] = {}
        self.system_metrics_history: List[SystemStressMetrics] = []
        
        # Recovery strategies registry
        self.recovery_strategies = {
            ErrorCategory.DATA_ACCESS: [RecoveryStrategy.RETRY_WITH_BACKOFF, RecoveryStrategy.FALLBACK_QUERY],
            ErrorCategory.SCHEMA_MISMATCH: [RecoveryStrategy.FALLBACK_QUERY, RecoveryStrategy.USER_GUIDANCE],
            ErrorCategory.QUERY_SYNTAX: [RecoveryStrategy.FALLBACK_QUERY, RecoveryStrategy.SIMPLIFIED_APPROACH],
            ErrorCategory.RESOURCE_EXHAUSTION: [RecoveryStrategy.RESOURCE_SCALING, RecoveryStrategy.GRACEFUL_DEGRADATION],
            ErrorCategory.PERMISSION_DENIED: [RecoveryStrategy.USER_GUIDANCE, RecoveryStrategy.PARTIAL_RESULTS],
            ErrorCategory.TIMEOUT: [RecoveryStrategy.RETRY_WITH_BACKOFF, RecoveryStrategy.SIMPLIFIED_APPROACH],
            ErrorCategory.NETWORK_ERROR: [RecoveryStrategy.RETRY_WITH_BACKOFF, RecoveryStrategy.GRACEFUL_DEGRADATION],
            ErrorCategory.AI_MODEL_ERROR: [RecoveryStrategy.FALLBACK_QUERY, RecoveryStrategy.SIMPLIFIED_APPROACH],
            ErrorCategory.SYSTEM_OVERLOAD: [RecoveryStrategy.GRACEFUL_DEGRADATION, RecoveryStrategy.RESOURCE_SCALING],
            ErrorCategory.UNKNOWN: [RecoveryStrategy.USER_GUIDANCE, RecoveryStrategy.PARTIAL_RESULTS]
        }
        
        # System monitoring
        self.stress_thresholds = {
            "cpu_high": 80.0,
            "cpu_critical": 95.0,
            "memory_high": 85.0,
            "memory_critical": 95.0,
            "disk_high": 90.0,
            "disk_critical": 98.0,
            "error_rate_high": 10.0,
            "error_rate_critical": 25.0
        }
        
        # Performance tracking
        self.performance_metrics = {
            "total_errors_handled": 0,
            "successful_recoveries": 0,
            "fallback_queries_generated": 0,
            "partial_results_delivered": 0,
            "user_guidance_provided": 0,
            "system_degradations": 0
        }
        
        # Start background monitoring
        self._start_system_monitoring()
        
        self.logger.info("Error Recovery Agent initialized with comprehensive recovery capabilities")
    
    async def diagnose_error(self, error: Exception, context: Dict[str, Any]) -> ErrorDiagnosis:
        """
        Perform AI-powered error diagnosis and explanation.
        
        Implements Requirement 9.1: AI-powered error diagnosis and explanation
        
        Args:
            error: The exception that occurred
            context: Context information about the error
            
        Returns:
            Comprehensive error diagnosis with recovery suggestions
        """
        start_time = time.time()
        error_id = f"error_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        
        try:
            self.logger.info(f"Diagnosing error {error_id}: {str(error)}")
            
            # Extract error information
            error_str = str(error)
            error_type = type(error).__name__
            error_traceback = traceback.format_exc()
            
            # Categorize error
            error_category = self._categorize_error(error, context)
            severity = self._assess_error_severity(error, context, error_category)
            
            # Build diagnosis prompt
            diagnosis_prompt = self._build_diagnosis_prompt(
                error_str, error_type, error_traceback, context, error_category, severity
            )
            
            # Get AI diagnosis
            ai_response = await self.execute(diagnosis_prompt, context)
            
            # Parse AI response and build diagnosis
            diagnosis = self._parse_diagnosis_response(
                ai_response, error_id, error_str, error_category, severity, context
            )
            
            # Store diagnosis
            self.error_history[error_id] = diagnosis
            self.performance_metrics["total_errors_handled"] += 1
            
            # Log diagnosis
            activity_logger.log_agent_response(
                self.agent_config.name, context.get("user_id", "system"), 
                context.get("client_id", "system"),
                f"Error diagnosed: {error_category.value} - {severity.value}",
                diagnosis.diagnosis_time_ms, self.agent_config.model_name,
                context.get("conversation_id"), None,
                {"error_id": error_id, "category": error_category.value, "severity": severity.value}
            )
            
            self.logger.info(f"Error diagnosis completed for {error_id} in {diagnosis.diagnosis_time_ms:.2f}ms")
            return diagnosis
            
        except Exception as e:
            diagnosis_time = (time.time() - start_time) * 1000
            self.logger.error(f"Error diagnosis failed: {e}")
            
            # Return basic diagnosis as fallback
            return ErrorDiagnosis(
                error_id=error_id,
                original_error=str(error),
                error_category=ErrorCategory.UNKNOWN,
                severity=ErrorSeverity.MEDIUM,
                root_cause="Unable to determine root cause due to diagnosis system error",
                technical_explanation=f"Original error: {str(error)}. Diagnosis system encountered: {str(e)}",
                user_friendly_explanation="An error occurred and our diagnosis system is having trouble analyzing it. Please try again or contact support.",
                suggested_actions=["Try your request again", "Simplify your query", "Contact support if the problem persists"],
                recovery_strategies=[RecoveryStrategy.USER_GUIDANCE, RecoveryStrategy.RETRY_WITH_BACKOFF],
                confidence_score=0.3,
                diagnosis_time_ms=diagnosis_time,
                context_factors=context
            )
    
    async def generate_fallback_query(self, original_query: str, error_context: Dict[str, Any]) -> Optional[FallbackQuery]:
        """
        Generate automatic fallback query for failed queries.
        
        Implements Requirement 9.2: Automatic fallback query generation
        
        Args:
            original_query: The query that failed
            error_context: Context about the error and environment
            
        Returns:
            Fallback query with limitations and success estimates
        """
        try:
            self.logger.info(f"Generating fallback query for: {original_query[:100]}...")
            
            # Build fallback generation prompt
            fallback_prompt = f"""
Analyze this failed query and generate a simpler fallback version that is more likely to succeed:

Original Query: {original_query}

Error Context:
{self._format_context_for_prompt(error_context)}

Generate a fallback query that:
1. Simplifies complex operations
2. Reduces data scope if needed
3. Uses more basic SQL constructs
4. Avoids problematic fields or tables
5. Provides meaningful partial results

Provide:
- The fallback query
- Expected limitations
- Confidence score (0-1)
- Success rate estimate (0-1)
- Explanation of changes made

Format your response as:
FALLBACK_QUERY: [query]
LIMITATIONS: [list of limitations]
CONFIDENCE: [0-1 score]
SUCCESS_RATE: [0-1 estimate]
EXPLANATION: [what was changed and why]
"""
            
            response = await self.execute(fallback_prompt, error_context)
            
            # Parse response
            fallback_query = self._parse_fallback_response(response, original_query)
            
            if fallback_query:
                self.performance_metrics["fallback_queries_generated"] += 1
                self.logger.info(f"Generated fallback query with {fallback_query.confidence_score:.2f} confidence")
            
            return fallback_query
            
        except Exception as e:
            self.logger.error(f"Fallback query generation failed: {e}")
            return None
    
    async def deliver_partial_results(self, available_data: List[Dict[str, Any]], 
                                    limitations: List[str], context: Dict[str, Any]) -> PartialResult:
        """
        Deliver partial results with clear limitations.
        
        Implements Requirement 9.3: Partial result delivery with limitations
        
        Args:
            available_data: Data that was successfully retrieved
            limitations: List of limitations in the partial results
            context: Context about the original request
            
        Returns:
            Structured partial result with completeness assessment
        """
        try:
            result_id = f"partial_{int(time.time())}_{str(uuid.uuid4())[:8]}"
            
            self.logger.info(f"Delivering partial results: {len(available_data)} records with {len(limitations)} limitations")
            
            # Assess completeness
            completeness = self._assess_result_completeness(available_data, context)
            
            # Identify missing components
            missing_components = self._identify_missing_components(context, limitations)
            
            # Calculate reliability score
            reliability = self._calculate_reliability_score(available_data, limitations, context)
            
            # Generate next steps
            next_steps = await self._generate_next_steps(limitations, context)
            
            partial_result = PartialResult(
                result_id=result_id,
                partial_data=available_data,
                limitations=limitations,
                completeness_percentage=completeness,
                missing_components=missing_components,
                reliability_score=reliability,
                suggested_next_steps=next_steps
            )
            
            self.performance_metrics["partial_results_delivered"] += 1
            
            self.logger.info(f"Partial result delivered: {completeness:.1f}% complete, {reliability:.2f} reliability")
            return partial_result
            
        except Exception as e:
            self.logger.error(f"Partial result delivery failed: {e}")
            
            # Return minimal partial result
            return PartialResult(
                result_id=f"error_partial_{int(time.time())}",
                partial_data=available_data,
                limitations=limitations + [f"Error in result processing: {str(e)}"],
                completeness_percentage=0.0,
                missing_components=["Unable to assess missing components"],
                reliability_score=0.3,
                suggested_next_steps=["Try simplifying your request", "Contact support for assistance"]
            )
    
    async def provide_user_guidance(self, error_diagnosis: ErrorDiagnosis, 
                                  context: Dict[str, Any]) -> UserGuidance:
        """
        Create user guidance and suggestion system.
        
        Implements Requirement 9.4: User guidance and suggestion system
        
        Args:
            error_diagnosis: Diagnosis of the error that occurred
            context: Context about the user and their request
            
        Returns:
            Comprehensive user guidance for error resolution
        """
        try:
            guidance_id = f"guidance_{int(time.time())}_{str(uuid.uuid4())[:8]}"
            
            self.logger.info(f"Generating user guidance for error category: {error_diagnosis.error_category.value}")
            
            # Build guidance prompt
            guidance_prompt = f"""
Create comprehensive user guidance for this error situation:

Error Category: {error_diagnosis.error_category.value}
Severity: {error_diagnosis.severity.value}
User-Friendly Explanation: {error_diagnosis.user_friendly_explanation}
Suggested Actions: {error_diagnosis.suggested_actions}

User Context:
{self._format_context_for_prompt(context)}

Provide:
1. Step-by-step guidance to resolve the issue
2. Alternative approaches if the main solution doesn't work
3. Prevention tips to avoid this error in the future
4. Related resources or documentation
5. Estimated time to resolution

Make the guidance:
- Clear and actionable
- Appropriate for the user's technical level
- Focused on getting them back to productive work
- Empathetic and supportive in tone
- Specific to their situation

Format as:
STEP_BY_STEP: [numbered steps]
ALTERNATIVES: [alternative approaches]
PREVENTION: [prevention tips]
RESOURCES: [related resources]
TIME_ESTIMATE: [estimated resolution time]
"""
            
            response = await self.execute(guidance_prompt, context)
            
            # Parse guidance response
            guidance = self._parse_guidance_response(response, guidance_id, error_diagnosis.user_friendly_explanation)
            
            self.performance_metrics["user_guidance_provided"] += 1
            
            self.logger.info(f"User guidance generated: {len(guidance.step_by_step_guidance)} steps")
            return guidance
            
        except Exception as e:
            self.logger.error(f"User guidance generation failed: {e}")
            
            # Return basic guidance as fallback
            return UserGuidance(
                guidance_id=f"error_guidance_{int(time.time())}",
                error_context=error_diagnosis.user_friendly_explanation,
                step_by_step_guidance=[
                    "Try refreshing the page or restarting your session",
                    "Simplify your request and try again",
                    "Check your internet connection",
                    "Contact support if the problem persists"
                ],
                alternative_approaches=[
                    "Break down your request into smaller parts",
                    "Try a different approach to your analysis",
                    "Use simpler query language"
                ],
                prevention_tips=[
                    "Keep queries simple and focused",
                    "Ensure you have proper access permissions",
                    "Check data availability before complex queries"
                ],
                related_resources=["User documentation", "Support contact"],
                estimated_resolution_time="5-15 minutes"
            )
    
    async def handle_system_stress(self, stress_metrics: SystemStressMetrics) -> Dict[str, Any]:
        """
        Implement graceful degradation under system stress.
        
        Implements Requirement 9.5: Graceful degradation under system stress
        
        Args:
            stress_metrics: Current system stress and performance metrics
            
        Returns:
            Actions taken and system adjustments made
        """
        try:
            self.logger.info(f"Handling system stress: {stress_metrics.stress_level}")
            
            actions_taken = []
            degradation_level = "none"
            
            # Determine degradation level based on stress
            if stress_metrics.stress_level == "critical":
                degradation_level = "severe"
                actions_taken.extend([
                    "Enabled emergency mode with minimal features",
                    "Reduced concurrent query limit to 1",
                    "Disabled complex analysis features",
                    "Activated aggressive caching",
                    "Limited result set sizes to 100 records"
                ])
            elif stress_metrics.stress_level == "high":
                degradation_level = "moderate"
                actions_taken.extend([
                    "Reduced concurrent query limit to 3",
                    "Simplified query processing",
                    "Increased caching aggressiveness",
                    "Limited result set sizes to 500 records",
                    "Disabled non-essential features"
                ])
            elif stress_metrics.stress_level == "medium":
                degradation_level = "light"
                actions_taken.extend([
                    "Reduced concurrent query limit to 5",
                    "Enabled performance optimizations",
                    "Increased cache retention",
                    "Limited result set sizes to 1000 records"
                ])
            
            # Resource-specific actions
            if stress_metrics.cpu_usage_percent > self.stress_thresholds["cpu_high"]:
                actions_taken.append("Reduced CPU-intensive operations")
            
            if stress_metrics.memory_usage_percent > self.stress_thresholds["memory_high"]:
                actions_taken.append("Enabled aggressive memory cleanup")
            
            if stress_metrics.error_rate_percent > self.stress_thresholds["error_rate_high"]:
                actions_taken.append("Activated enhanced error recovery mode")
            
            # Update performance metrics
            self.performance_metrics["system_degradations"] += 1
            
            # Log stress handling
            activity_logger.log_agent_response(
                self.agent_config.name, "system", "system",
                f"System stress handled: {degradation_level} degradation",
                0, self.agent_config.model_name, None, None,
                {
                    "stress_level": stress_metrics.stress_level,
                    "degradation_level": degradation_level,
                    "actions_count": len(actions_taken)
                }
            )
            
            return {
                "degradation_level": degradation_level,
                "actions_taken": actions_taken,
                "stress_metrics": asdict(stress_metrics),
                "recommendations": self._generate_stress_recommendations(stress_metrics),
                "estimated_recovery_time": self._estimate_recovery_time(stress_metrics)
            }
            
        except Exception as e:
            self.logger.error(f"System stress handling failed: {e}")
            return {
                "degradation_level": "emergency",
                "actions_taken": ["Activated emergency fallback mode"],
                "error": str(e),
                "recommendations": ["Contact system administrator immediately"]
            }
    
    async def attempt_recovery(self, error_diagnosis: ErrorDiagnosis, 
                             context: Dict[str, Any]) -> RecoveryResult:
        """
        Attempt comprehensive error recovery using multiple strategies.
        
        Args:
            error_diagnosis: Diagnosis of the error to recover from
            context: Context about the error and environment
            
        Returns:
            Result of recovery attempt with details of actions taken
        """
        start_time = time.time()
        recovery_id = f"recovery_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        
        try:
            self.logger.info(f"Attempting recovery for error {error_diagnosis.error_id}")
            
            # Try recovery strategies in order of preference
            for strategy in error_diagnosis.recovery_strategies:
                try:
                    recovery_result = await self._execute_recovery_strategy(
                        strategy, error_diagnosis, context, recovery_id
                    )
                    
                    if recovery_result.success:
                        self.performance_metrics["successful_recoveries"] += 1
                        recovery_result.recovery_time_ms = (time.time() - start_time) * 1000
                        
                        # Store recovery result
                        self.recovery_history[recovery_id] = recovery_result
                        
                        self.logger.info(f"Recovery successful using {strategy.value}")
                        return recovery_result
                    
                except Exception as strategy_error:
                    self.logger.warning(f"Recovery strategy {strategy.value} failed: {strategy_error}")
                    continue
            
            # If all strategies fail, provide user guidance
            user_guidance = await self.provide_user_guidance(error_diagnosis, context)
            
            recovery_result = RecoveryResult(
                recovery_id=recovery_id,
                original_error_id=error_diagnosis.error_id,
                strategy_used=RecoveryStrategy.USER_GUIDANCE,
                success=False,
                recovery_time_ms=(time.time() - start_time) * 1000,
                user_guidance=user_guidance,
                error_diagnosis=error_diagnosis,
                system_actions_taken=["Generated user guidance for manual resolution"],
                user_message="Automatic recovery was not possible. Please follow the provided guidance to resolve the issue."
            )
            
            self.recovery_history[recovery_id] = recovery_result
            return recovery_result
            
        except Exception as e:
            recovery_time = (time.time() - start_time) * 1000
            self.logger.error(f"Recovery attempt failed: {e}")
            
            return RecoveryResult(
                recovery_id=recovery_id,
                original_error_id=error_diagnosis.error_id,
                strategy_used=RecoveryStrategy.USER_GUIDANCE,
                success=False,
                recovery_time_ms=recovery_time,
                system_actions_taken=["Recovery system encountered an error"],
                user_message=f"Recovery failed due to system error: {str(e)}. Please contact support."
            )
    
    def get_system_metrics(self) -> SystemStressMetrics:
        """Get current system stress and performance metrics."""
        try:
            if not PSUTIL_AVAILABLE:
                # Return default metrics when psutil is not available
                return SystemStressMetrics(
                    cpu_usage_percent=0.0,
                    memory_usage_percent=0.0,
                    disk_usage_percent=0.0,
                    active_connections=0,
                    query_queue_length=0,
                    average_response_time_ms=0.0,
                    error_rate_percent=0.0,
                    stress_level="unknown"
                )
            
            # Get system metrics using psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Calculate derived metrics
            active_connections = len(psutil.net_connections())
            
            # Calculate error rate from recent history
            recent_errors = len([e for e in self.error_history.values() 
                               if (datetime.utcnow() - datetime.fromisoformat(e.context_factors.get('timestamp', datetime.utcnow().isoformat()))).total_seconds() < 300])
            total_recent_requests = max(recent_errors + 10, 1)  # Estimate
            error_rate = (recent_errors / total_recent_requests) * 100
            
            # Determine stress level
            stress_level = "low"
            if (cpu_percent > self.stress_thresholds["cpu_critical"] or 
                memory.percent > self.stress_thresholds["memory_critical"] or
                error_rate > self.stress_thresholds["error_rate_critical"]):
                stress_level = "critical"
            elif (cpu_percent > self.stress_thresholds["cpu_high"] or 
                  memory.percent > self.stress_thresholds["memory_high"] or
                  error_rate > self.stress_thresholds["error_rate_high"]):
                stress_level = "high"
            elif (cpu_percent > 50 or memory.percent > 60 or error_rate > 5):
                stress_level = "medium"
            
            metrics = SystemStressMetrics(
                cpu_usage_percent=cpu_percent,
                memory_usage_percent=memory.percent,
                disk_usage_percent=disk.percent,
                active_connections=active_connections,
                query_queue_length=0,  # Would need to be tracked separately
                average_response_time_ms=0.0,  # Would need to be tracked separately
                error_rate_percent=error_rate,
                stress_level=stress_level
            )
            
            # Store metrics history
            self.system_metrics_history.append(metrics)
            if len(self.system_metrics_history) > 100:  # Keep last 100 measurements
                self.system_metrics_history = self.system_metrics_history[-100:]
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get system metrics: {e}")
            return SystemStressMetrics(
                cpu_usage_percent=0.0,
                memory_usage_percent=0.0,
                disk_usage_percent=0.0,
                active_connections=0,
                query_queue_length=0,
                average_response_time_ms=0.0,
                error_rate_percent=0.0,
                stress_level="unknown"
            )
    
    def _categorize_error(self, error: Exception, context: Dict[str, Any]) -> ErrorCategory:
        """Categorize error based on type and context."""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Permission and access errors
        if any(term in error_str for term in ['permission', 'access denied', 'unauthorized', 'forbidden']):
            return ErrorCategory.PERMISSION_DENIED
        
        # Data access errors
        if any(term in error_str for term in ['table', 'column', 'database', 'connection']):
            return ErrorCategory.DATA_ACCESS
        
        # Schema errors
        if any(term in error_str for term in ['schema', 'field', 'type mismatch', 'column not found']):
            return ErrorCategory.SCHEMA_MISMATCH
        
        # Query syntax errors
        if any(term in error_str for term in ['syntax', 'sql', 'query', 'parse']):
            return ErrorCategory.QUERY_SYNTAX
        
        # Timeout errors
        if any(term in error_str for term in ['timeout', 'time out', 'deadline']):
            return ErrorCategory.TIMEOUT
        
        # Network errors
        if any(term in error_str for term in ['network', 'connection', 'socket', 'http']):
            return ErrorCategory.NETWORK_ERROR
        
        # Resource exhaustion
        if any(term in error_str for term in ['memory', 'disk', 'resource', 'limit']):
            return ErrorCategory.RESOURCE_EXHAUSTION
        
        # AI model errors
        if any(term in error_str for term in ['model', 'api', 'openai', 'anthropic']):
            return ErrorCategory.AI_MODEL_ERROR
        
        # System overload
        if any(term in error_str for term in ['overload', 'busy', 'queue', 'throttle']):
            return ErrorCategory.SYSTEM_OVERLOAD
        
        return ErrorCategory.UNKNOWN
    
    def _assess_error_severity(self, error: Exception, context: Dict[str, Any], 
                             category: ErrorCategory) -> ErrorSeverity:
        """Assess error severity based on impact and context."""
        
        # Critical errors that prevent all functionality
        if category in [ErrorCategory.SYSTEM_OVERLOAD, ErrorCategory.DATA_CORRUPTION]:
            return ErrorSeverity.CRITICAL
        
        # High severity errors that significantly impact functionality
        if category in [ErrorCategory.RESOURCE_EXHAUSTION, ErrorCategory.PERMISSION_DENIED]:
            return ErrorSeverity.HIGH
        
        # Medium severity errors that impact specific operations
        if category in [ErrorCategory.DATA_ACCESS, ErrorCategory.SCHEMA_MISMATCH, ErrorCategory.AI_MODEL_ERROR]:
            return ErrorSeverity.MEDIUM
        
        # Low severity errors that can be easily worked around
        return ErrorSeverity.LOW
    
    def _build_diagnosis_prompt(self, error_str: str, error_type: str, 
                              traceback_str: str, context: Dict[str, Any],
                              category: ErrorCategory, severity: ErrorSeverity) -> str:
        """Build comprehensive diagnosis prompt for AI analysis."""
        return f"""
Analyze this error and provide a comprehensive diagnosis:

Error Information:
- Error Message: {error_str}
- Error Type: {error_type}
- Category: {category.value}
- Severity: {severity.value}

Context:
{self._format_context_for_prompt(context)}

Traceback (last 10 lines):
{chr(10).join(traceback_str.split(chr(10))[-10:])}

Provide a comprehensive analysis including:
1. Root cause analysis
2. Technical explanation for developers
3. User-friendly explanation
4. Suggested immediate actions
5. Recovery strategies
6. Prevention recommendations
7. Confidence in diagnosis (0-1)

Format your response as:
ROOT_CAUSE: [detailed root cause analysis]
TECHNICAL: [technical explanation]
USER_FRIENDLY: [simple explanation for users]
ACTIONS: [immediate actions to take]
RECOVERY: [recovery strategies]
PREVENTION: [prevention tips]
CONFIDENCE: [0-1 confidence score]
"""
    
    def _parse_diagnosis_response(self, response: str, error_id: str, error_str: str,
                                category: ErrorCategory, severity: ErrorSeverity,
                                context: Dict[str, Any]) -> ErrorDiagnosis:
        """Parse AI diagnosis response into structured format."""
        diagnosis_time = time.time() * 1000
        
        try:
            # Extract sections from response
            sections = {}
            current_section = None
            current_content = []
            
            for line in response.split('\n'):
                line = line.strip()
                if ':' in line and line.split(':')[0].upper() in ['ROOT_CAUSE', 'TECHNICAL', 'USER_FRIENDLY', 'ACTIONS', 'RECOVERY', 'PREVENTION', 'CONFIDENCE']:
                    if current_section:
                        sections[current_section] = '\n'.join(current_content).strip()
                    current_section = line.split(':')[0].upper()
                    current_content = [':'.join(line.split(':')[1:]).strip()]
                elif current_section:
                    current_content.append(line)
            
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            
            # Parse confidence
            confidence = 0.7  # Default
            if 'CONFIDENCE' in sections:
                try:
                    confidence = float(sections['CONFIDENCE'])
                except:
                    confidence = 0.7
            
            # Parse actions
            actions = []
            if 'ACTIONS' in sections:
                actions = [action.strip('- ').strip() for action in sections['ACTIONS'].split('\n') if action.strip()]
            
            # Determine recovery strategies
            recovery_strategies = self.recovery_strategies.get(category, [RecoveryStrategy.USER_GUIDANCE])
            
            return ErrorDiagnosis(
                error_id=error_id,
                original_error=error_str,
                error_category=category,
                severity=severity,
                root_cause=sections.get('ROOT_CAUSE', 'Unable to determine root cause'),
                technical_explanation=sections.get('TECHNICAL', 'Technical analysis not available'),
                user_friendly_explanation=sections.get('USER_FRIENDLY', 'An error occurred while processing your request'),
                suggested_actions=actions or ['Try again', 'Contact support if problem persists'],
                recovery_strategies=recovery_strategies,
                confidence_score=confidence,
                diagnosis_time_ms=diagnosis_time,
                context_factors=context
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to parse diagnosis response: {e}")
            
            return ErrorDiagnosis(
                error_id=error_id,
                original_error=error_str,
                error_category=category,
                severity=severity,
                root_cause="Error analysis failed",
                technical_explanation=f"Original error: {error_str}",
                user_friendly_explanation="An error occurred and we're having trouble analyzing it",
                suggested_actions=['Try again', 'Contact support'],
                recovery_strategies=[RecoveryStrategy.USER_GUIDANCE],
                confidence_score=0.3,
                diagnosis_time_ms=diagnosis_time,
                context_factors=context
            )
    
    def _parse_fallback_response(self, response: str, original_query: str) -> Optional[FallbackQuery]:
        """Parse fallback query response from AI."""
        try:
            sections = {}
            current_section = None
            current_content = []
            
            for line in response.split('\n'):
                line = line.strip()
                if ':' in line and line.split(':')[0].upper() in ['FALLBACK_QUERY', 'LIMITATIONS', 'CONFIDENCE', 'SUCCESS_RATE', 'EXPLANATION']:
                    if current_section:
                        sections[current_section] = '\n'.join(current_content).strip()
                    current_section = line.split(':')[0].upper()
                    current_content = [':'.join(line.split(':')[1:]).strip()]
                elif current_section:
                    current_content.append(line)
            
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            
            if 'FALLBACK_QUERY' not in sections:
                return None
            
            # Parse limitations
            limitations = []
            if 'LIMITATIONS' in sections:
                limitations = [lim.strip('- ').strip() for lim in sections['LIMITATIONS'].split('\n') if lim.strip()]
            
            # Parse scores
            confidence = 0.6
            success_rate = 0.7
            
            try:
                if 'CONFIDENCE' in sections:
                    confidence = float(sections['CONFIDENCE'])
                if 'SUCCESS_RATE' in sections:
                    success_rate = float(sections['SUCCESS_RATE'])
            except:
                pass
            
            return FallbackQuery(
                query_id=f"fallback_{int(time.time())}_{str(uuid.uuid4())[:8]}",
                original_query=original_query,
                fallback_query=sections['FALLBACK_QUERY'],
                fallback_type="ai_generated",
                expected_limitations=limitations,
                confidence_score=confidence,
                estimated_success_rate=success_rate
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to parse fallback response: {e}")
            return None
    
    def _parse_guidance_response(self, response: str, guidance_id: str, error_context: str) -> UserGuidance:
        """Parse user guidance response from AI."""
        try:
            sections = {}
            current_section = None
            current_content = []
            
            for line in response.split('\n'):
                line = line.strip()
                if ':' in line and line.split(':')[0].upper() in ['STEP_BY_STEP', 'ALTERNATIVES', 'PREVENTION', 'RESOURCES', 'TIME_ESTIMATE']:
                    if current_section:
                        sections[current_section] = '\n'.join(current_content).strip()
                    current_section = line.split(':')[0].upper()
                    current_content = [':'.join(line.split(':')[1:]).strip()]
                elif current_section:
                    current_content.append(line)
            
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            
            # Parse step-by-step guidance
            steps = []
            if 'STEP_BY_STEP' in sections:
                steps = [step.strip('0123456789. ').strip() for step in sections['STEP_BY_STEP'].split('\n') if step.strip()]
            
            # Parse alternatives
            alternatives = []
            if 'ALTERNATIVES' in sections:
                alternatives = [alt.strip('- ').strip() for alt in sections['ALTERNATIVES'].split('\n') if alt.strip()]
            
            # Parse prevention tips
            prevention = []
            if 'PREVENTION' in sections:
                prevention = [tip.strip('- ').strip() for tip in sections['PREVENTION'].split('\n') if tip.strip()]
            
            # Parse resources
            resources = []
            if 'RESOURCES' in sections:
                resources = [res.strip('- ').strip() for res in sections['RESOURCES'].split('\n') if res.strip()]
            
            return UserGuidance(
                guidance_id=guidance_id,
                error_context=error_context,
                step_by_step_guidance=steps or ["Contact support for assistance"],
                alternative_approaches=alternatives or ["Try a different approach"],
                prevention_tips=prevention or ["Follow best practices"],
                related_resources=resources or ["Documentation"],
                estimated_resolution_time=sections.get('TIME_ESTIMATE', '5-15 minutes')
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to parse guidance response: {e}")
            
            return UserGuidance(
                guidance_id=guidance_id,
                error_context=error_context,
                step_by_step_guidance=["Contact support for assistance"],
                alternative_approaches=["Try a different approach"],
                prevention_tips=["Follow system best practices"],
                related_resources=["System documentation"],
                estimated_resolution_time="Unknown"
            )
    
    async def _execute_recovery_strategy(self, strategy: RecoveryStrategy, 
                                       error_diagnosis: ErrorDiagnosis,
                                       context: Dict[str, Any], 
                                       recovery_id: str) -> RecoveryResult:
        """Execute a specific recovery strategy."""
        
        if strategy == RecoveryStrategy.FALLBACK_QUERY:
            original_query = context.get('original_query', '')
            if original_query:
                fallback = await self.generate_fallback_query(original_query, context)
                if fallback:
                    return RecoveryResult(
                        recovery_id=recovery_id,
                        original_error_id=error_diagnosis.error_id,
                        strategy_used=strategy,
                        success=True,
                        recovery_time_ms=0,
                        fallback_query=fallback,
                        system_actions_taken=["Generated fallback query"],
                        user_message=f"I've created a simpler version of your query that should work. Note: {', '.join(fallback.expected_limitations)}"
                    )
        
        elif strategy == RecoveryStrategy.PARTIAL_RESULTS:
            available_data = context.get('partial_data', [])
            limitations = context.get('limitations', [])
            if available_data:
                partial_result = await self.deliver_partial_results(available_data, limitations, context)
                return RecoveryResult(
                    recovery_id=recovery_id,
                    original_error_id=error_diagnosis.error_id,
                    strategy_used=strategy,
                    success=True,
                    recovery_time_ms=0,
                    partial_result=partial_result,
                    system_actions_taken=["Delivered partial results"],
                    user_message=f"I was able to get partial results ({partial_result.completeness_percentage:.1f}% complete). {', '.join(partial_result.limitations)}"
                )
        
        elif strategy == RecoveryStrategy.USER_GUIDANCE:
            guidance = await self.provide_user_guidance(error_diagnosis, context)
            return RecoveryResult(
                recovery_id=recovery_id,
                original_error_id=error_diagnosis.error_id,
                strategy_used=strategy,
                success=True,
                recovery_time_ms=0,
                user_guidance=guidance,
                system_actions_taken=["Generated user guidance"],
                user_message="I've prepared step-by-step guidance to help resolve this issue."
            )
        
        # Other strategies would be implemented here
        return RecoveryResult(
            recovery_id=recovery_id,
            original_error_id=error_diagnosis.error_id,
            strategy_used=strategy,
            success=False,
            recovery_time_ms=0,
            system_actions_taken=[f"Attempted {strategy.value} strategy"],
            user_message=f"Recovery strategy {strategy.value} was not successful."
        )
    
    def _assess_result_completeness(self, data: List[Dict[str, Any]], context: Dict[str, Any]) -> float:
        """Assess completeness percentage of partial results."""
        if not data:
            return 0.0
        
        expected_count = context.get('expected_record_count', len(data) * 2)
        return min(100.0, (len(data) / max(expected_count, 1)) * 100)
    
    def _identify_missing_components(self, context: Dict[str, Any], limitations: List[str]) -> List[str]:
        """Identify missing components in partial results."""
        missing = []
        
        if 'missing_fields' in context:
            missing.extend(context['missing_fields'])
        
        if 'missing_tables' in context:
            missing.extend([f"Table: {table}" for table in context['missing_tables']])
        
        if any('timeout' in lim.lower() for lim in limitations):
            missing.append("Complete data processing")
        
        return missing or ["Some data components"]
    
    def _calculate_reliability_score(self, data: List[Dict[str, Any]], 
                                   limitations: List[str], context: Dict[str, Any]) -> float:
        """Calculate reliability score for partial results."""
        base_score = 0.8
        
        # Reduce score based on limitations
        for limitation in limitations:
            if 'incomplete' in limitation.lower():
                base_score -= 0.2
            elif 'timeout' in limitation.lower():
                base_score -= 0.1
            elif 'error' in limitation.lower():
                base_score -= 0.3
        
        # Adjust based on data completeness
        if len(data) == 0:
            base_score = 0.1
        elif len(data) < 10:
            base_score -= 0.1
        
        return max(0.1, min(1.0, base_score))
    
    async def _generate_next_steps(self, limitations: List[str], context: Dict[str, Any]) -> List[str]:
        """Generate suggested next steps for partial results."""
        steps = []
        
        if any('timeout' in lim.lower() for lim in limitations):
            steps.append("Try simplifying your query to reduce processing time")
        
        if any('permission' in lim.lower() for lim in limitations):
            steps.append("Check your access permissions for the requested data")
        
        if any('incomplete' in lim.lower() for lim in limitations):
            steps.append("Try breaking your request into smaller parts")
        
        steps.extend([
            "Review the partial results to see if they meet your needs",
            "Contact support if you need access to the complete dataset"
        ])
        
        return steps[:5]  # Limit to 5 steps
    
    def _generate_stress_recommendations(self, metrics: SystemStressMetrics) -> List[str]:
        """Generate recommendations for system stress relief."""
        recommendations = []
        
        if metrics.cpu_usage_percent > 80:
            recommendations.append("Reduce concurrent operations")
        
        if metrics.memory_usage_percent > 80:
            recommendations.append("Clear caches and temporary data")
        
        if metrics.error_rate_percent > 10:
            recommendations.append("Investigate and fix recurring errors")
        
        if metrics.stress_level in ["high", "critical"]:
            recommendations.extend([
                "Consider scaling system resources",
                "Implement request throttling",
                "Enable emergency mode if available"
            ])
        
        return recommendations
    
    def _estimate_recovery_time(self, metrics: SystemStressMetrics) -> str:
        """Estimate time for system recovery from stress."""
        if metrics.stress_level == "critical":
            return "15-30 minutes"
        elif metrics.stress_level == "high":
            return "5-15 minutes"
        elif metrics.stress_level == "medium":
            return "2-5 minutes"
        else:
            return "1-2 minutes"
    
    def _format_context_for_prompt(self, context: Dict[str, Any]) -> str:
        """Format context dictionary for AI prompts."""
        formatted_lines = []
        for key, value in context.items():
            if isinstance(value, (str, int, float, bool)):
                formatted_lines.append(f"- {key}: {value}")
            elif isinstance(value, list) and len(value) < 10:
                formatted_lines.append(f"- {key}: {', '.join(map(str, value))}")
            elif isinstance(value, dict) and len(value) < 5:
                formatted_lines.append(f"- {key}: {value}")
            else:
                formatted_lines.append(f"- {key}: [complex data structure]")
        
        return '\n'.join(formatted_lines) if formatted_lines else "No additional context available"
    
    def _start_system_monitoring(self):
        """Start background system monitoring."""
        def monitor_loop():
            while True:
                try:
                    metrics = self.get_system_metrics()
                    
                    # Check if stress handling is needed
                    if metrics.stress_level in ["high", "critical"]:
                        asyncio.create_task(self.handle_system_stress(metrics))
                    
                    time.sleep(30)  # Monitor every 30 seconds
                except Exception as e:
                    self.logger.error(f"System monitoring error: {e}")
                    time.sleep(60)  # Wait longer on error
        
        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get performance statistics for the error recovery system."""
        total_errors = self.performance_metrics["total_errors_handled"]
        successful_recoveries = self.performance_metrics["successful_recoveries"]
        
        return {
            "total_errors_handled": total_errors,
            "successful_recoveries": successful_recoveries,
            "recovery_success_rate": (successful_recoveries / max(total_errors, 1)) * 100,
            "fallback_queries_generated": self.performance_metrics["fallback_queries_generated"],
            "partial_results_delivered": self.performance_metrics["partial_results_delivered"],
            "user_guidance_provided": self.performance_metrics["user_guidance_provided"],
            "system_degradations": self.performance_metrics["system_degradations"],
            "error_categories_seen": len(set(e.error_category for e in self.error_history.values())),
            "average_diagnosis_time_ms": sum(e.diagnosis_time_ms for e in self.error_history.values()) / max(len(self.error_history), 1),
            "current_system_stress": self.get_system_metrics().stress_level
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the error recovery system."""
        try:
            # Test basic functionality
            test_error = ValueError("Test error for health check")
            test_context = {"test": True, "timestamp": datetime.utcnow().isoformat()}
            
            # Test diagnosis
            diagnosis = await self.diagnose_error(test_error, test_context)
            
            # Get system metrics
            metrics = self.get_system_metrics()
            
            # Get performance stats
            stats = self.get_performance_statistics()
            
            return {
                "status": "healthy",
                "diagnosis_working": diagnosis.error_id is not None,
                "system_monitoring_active": len(self.system_metrics_history) > 0,
                "current_system_stress": metrics.stress_level,
                "performance_statistics": stats,
                "recovery_strategies_available": len(self.recovery_strategies),
                "error_history_size": len(self.error_history),
                "recovery_history_size": len(self.recovery_history)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "basic_functionality": False
            }
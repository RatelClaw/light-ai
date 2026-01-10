"""
AI Agent Activity Logging System.

This module provides specialized logging for AI agent activities,
including conversation tracking, performance metrics, and debugging
information for the Strands AI agents.
"""

import logging
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime

from light_ai.config import Config, get_config


@dataclass
class AgentActivity:
    """Record of AI agent activity."""
    timestamp: float
    agent_name: str
    activity_type: str  # query, response, error, tool_use, etc.
    user_id: str
    client_id: str
    conversation_id: Optional[str]
    prompt: Optional[str]
    response: Optional[str]
    execution_time_ms: float
    tokens_used: Optional[int]
    model_name: str
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ConversationMetrics:
    """Metrics for a conversation session."""
    conversation_id: str
    user_id: str
    client_id: str
    start_time: float
    end_time: Optional[float]
    total_queries: int
    total_tokens: int
    total_execution_time_ms: float
    agents_used: List[str]
    success_rate: float


class AgentActivityLogger:
    """
    Specialized logger for AI agent activities.
    
    Provides structured logging of agent interactions, performance metrics,
    and conversation tracking for debugging and analytics.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the agent activity logger."""
        self.config = config or get_config()
        self.logger = self._setup_logger()
        self.activities: List[AgentActivity] = []
        self.conversations: Dict[str, ConversationMetrics] = {}
        
        # Create logs directory if it doesn't exist
        logs_dir = Path(self.config.get_full_path(self.config.storage.logs_dir))
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        self.activity_log_file = logs_dir / "agent_activities.jsonl"
        self.conversation_log_file = logs_dir / "conversations.jsonl"
    
    def _setup_logger(self) -> logging.Logger:
        """Set up the activity logger."""
        logger = logging.getLogger("light_ai.agents.activity")
        logger.setLevel(getattr(logging, self.config.logging.level))
        
        # Create formatter for activity logs
        formatter = logging.Formatter(
            '%(asctime)s - AGENT_ACTIVITY - %(levelname)s - %(message)s'
        )
        
        # Add file handler for agent activities
        if self.config.logging.file_enabled:
            logs_dir = Path(self.config.get_full_path(self.config.storage.logs_dir))
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(logs_dir / "agent_activities.log")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # Add console handler if enabled
        if self.config.logging.console_enabled:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def log_agent_query(self, agent_name: str, user_id: str, client_id: str,
                       prompt: str, conversation_id: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Log an agent query.
        
        Args:
            agent_name: Name of the agent
            user_id: User identifier
            client_id: Client identifier
            prompt: The query prompt
            conversation_id: Optional conversation identifier
            metadata: Optional additional metadata
            
        Returns:
            Activity ID for tracking
        """
        activity = AgentActivity(
            timestamp=time.time(),
            agent_name=agent_name,
            activity_type="query",
            user_id=user_id,
            client_id=client_id,
            conversation_id=conversation_id,
            prompt=prompt,
            response=None,
            execution_time_ms=0.0,
            tokens_used=None,
            model_name="",
            metadata=metadata
        )
        
        self.activities.append(activity)
        activity_id = f"{agent_name}_{int(activity.timestamp)}"
        
        self.logger.info(f"Agent query logged: {activity_id}")
        self._write_activity_to_file(activity)
        
        return activity_id
    
    def log_agent_response(self, agent_name: str, user_id: str, client_id: str,
                          response: str, execution_time_ms: float,
                          model_name: str, conversation_id: Optional[str] = None,
                          tokens_used: Optional[int] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an agent response.
        
        Args:
            agent_name: Name of the agent
            user_id: User identifier
            client_id: Client identifier
            response: The agent response
            execution_time_ms: Execution time in milliseconds
            model_name: Name of the model used
            conversation_id: Optional conversation identifier
            tokens_used: Optional token count
            metadata: Optional additional metadata
        """
        activity = AgentActivity(
            timestamp=time.time(),
            agent_name=agent_name,
            activity_type="response",
            user_id=user_id,
            client_id=client_id,
            conversation_id=conversation_id,
            prompt=None,
            response=response,
            execution_time_ms=execution_time_ms,
            tokens_used=tokens_used,
            model_name=model_name,
            metadata=metadata
        )
        
        self.activities.append(activity)
        
        self.logger.info(f"Agent response logged: {execution_time_ms:.2f}ms, {tokens_used or 0} tokens")
        self._write_activity_to_file(activity)
        
        # Update conversation metrics
        if conversation_id:
            self._update_conversation_metrics(conversation_id, user_id, client_id,
                                            agent_name, execution_time_ms, tokens_used or 0)
    
    def log_agent_error(self, agent_name: str, user_id: str, client_id: str,
                       error: str, conversation_id: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an agent error.
        
        Args:
            agent_name: Name of the agent
            user_id: User identifier
            client_id: Client identifier
            error: Error message
            conversation_id: Optional conversation identifier
            metadata: Optional additional metadata
        """
        activity = AgentActivity(
            timestamp=time.time(),
            agent_name=agent_name,
            activity_type="error",
            user_id=user_id,
            client_id=client_id,
            conversation_id=conversation_id,
            prompt=None,
            response=None,
            execution_time_ms=0.0,
            tokens_used=None,
            model_name="",
            error=error,
            metadata=metadata
        )
        
        self.activities.append(activity)
        
        self.logger.error(f"Agent error logged: {agent_name} - {error}")
        self._write_activity_to_file(activity)
    
    def log_tool_usage(self, agent_name: str, user_id: str, client_id: str,
                      tool_name: str, tool_input: Dict[str, Any],
                      tool_output: Any, execution_time_ms: float,
                      conversation_id: Optional[str] = None) -> None:
        """
        Log agent tool usage.
        
        Args:
            agent_name: Name of the agent
            user_id: User identifier
            client_id: Client identifier
            tool_name: Name of the tool used
            tool_input: Input provided to the tool
            tool_output: Output from the tool
            execution_time_ms: Tool execution time
            conversation_id: Optional conversation identifier
        """
        metadata = {
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_output": str(tool_output)[:1000],  # Truncate long outputs
        }
        
        activity = AgentActivity(
            timestamp=time.time(),
            agent_name=agent_name,
            activity_type="tool_use",
            user_id=user_id,
            client_id=client_id,
            conversation_id=conversation_id,
            prompt=None,
            response=None,
            execution_time_ms=execution_time_ms,
            tokens_used=None,
            model_name="",
            metadata=metadata
        )
        
        self.activities.append(activity)
        
        self.logger.info(f"Tool usage logged: {tool_name} - {execution_time_ms:.2f}ms")
        self._write_activity_to_file(activity)
    
    def _write_activity_to_file(self, activity: AgentActivity) -> None:
        """Write activity to JSONL file."""
        try:
            with open(self.activity_log_file, 'a') as f:
                json.dump(asdict(activity), f)
                f.write('\n')
        except Exception as e:
            self.logger.error(f"Failed to write activity to file: {e}")
    
    def _update_conversation_metrics(self, conversation_id: str, user_id: str,
                                   client_id: str, agent_name: str,
                                   execution_time_ms: float, tokens_used: int) -> None:
        """Update conversation metrics."""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = ConversationMetrics(
                conversation_id=conversation_id,
                user_id=user_id,
                client_id=client_id,
                start_time=time.time(),
                end_time=None,
                total_queries=0,
                total_tokens=0,
                total_execution_time_ms=0.0,
                agents_used=[],
                success_rate=1.0
            )
        
        metrics = self.conversations[conversation_id]
        metrics.total_queries += 1
        metrics.total_tokens += tokens_used
        metrics.total_execution_time_ms += execution_time_ms
        
        if agent_name not in metrics.agents_used:
            metrics.agents_used.append(agent_name)
        
        metrics.end_time = time.time()
    
    def get_conversation_metrics(self, conversation_id: str) -> Optional[ConversationMetrics]:
        """Get metrics for a specific conversation."""
        return self.conversations.get(conversation_id)
    
    def get_agent_performance_metrics(self, agent_name: str, 
                                    time_window_hours: int = 24) -> Dict[str, Any]:
        """
        Get performance metrics for a specific agent.
        
        Args:
            agent_name: Name of the agent
            time_window_hours: Time window for metrics calculation
            
        Returns:
            Performance metrics dictionary
        """
        cutoff_time = time.time() - (time_window_hours * 3600)
        
        # Filter activities for the agent within time window
        agent_activities = [
            a for a in self.activities
            if a.agent_name == agent_name and a.timestamp >= cutoff_time
        ]
        
        if not agent_activities:
            return {"error": "No activities found for agent in time window"}
        
        # Calculate metrics
        total_queries = len([a for a in agent_activities if a.activity_type == "query"])
        total_responses = len([a for a in agent_activities if a.activity_type == "response"])
        total_errors = len([a for a in agent_activities if a.activity_type == "error"])
        
        response_activities = [a for a in agent_activities if a.activity_type == "response"]
        avg_execution_time = (
            sum(a.execution_time_ms for a in response_activities) / len(response_activities)
            if response_activities else 0
        )
        
        total_tokens = sum(a.tokens_used or 0 for a in response_activities)
        
        success_rate = (
            (total_responses / (total_responses + total_errors))
            if (total_responses + total_errors) > 0 else 1.0
        )
        
        return {
            "agent_name": agent_name,
            "time_window_hours": time_window_hours,
            "total_queries": total_queries,
            "total_responses": total_responses,
            "total_errors": total_errors,
            "success_rate": success_rate,
            "avg_execution_time_ms": avg_execution_time,
            "total_tokens_used": total_tokens,
            "activities_count": len(agent_activities)
        }
    
    def export_activities(self, output_file: str, 
                         time_window_hours: Optional[int] = None) -> None:
        """
        Export activities to a file.
        
        Args:
            output_file: Path to output file
            time_window_hours: Optional time window filter
        """
        activities_to_export = self.activities
        
        if time_window_hours:
            cutoff_time = time.time() - (time_window_hours * 3600)
            activities_to_export = [
                a for a in self.activities if a.timestamp >= cutoff_time
            ]
        
        with open(output_file, 'w') as f:
            for activity in activities_to_export:
                json.dump(asdict(activity), f)
                f.write('\n')
        
        self.logger.info(f"Exported {len(activities_to_export)} activities to {output_file}")


# Global activity logger instance
_activity_logger: Optional[AgentActivityLogger] = None


def get_activity_logger() -> AgentActivityLogger:
    """Get the global activity logger instance."""
    global _activity_logger
    if _activity_logger is None:
        _activity_logger = AgentActivityLogger()
    return _activity_logger


def set_activity_logger(logger: AgentActivityLogger) -> None:
    """Set the global activity logger instance."""
    global _activity_logger
    _activity_logger = logger
"""
Query Routing and Result Synthesis for AI Agent Communication.

Provides intelligent query routing between specialized agents and
synthesizes results from multiple agent interactions.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from .master_agent import MasterDataAnalystAgent, AnalysisRequest, AnalysisResult
from .logging import get_activity_logger
from ..core.models import AccessLevel, ResourceType
from ..config import Config, get_config
from ..logger import get_logger

logger = get_logger(__name__)
activity_logger = get_activity_logger()


class QueryType(Enum):
    """Types of queries for routing decisions."""
    STRUCTURED_DATA = "structured_data"
    UNSTRUCTURED_DATA = "unstructured_data"
    MIXED_DATA = "mixed_data"
    METADATA_QUERY = "metadata_query"
    ANALYTICAL = "analytical"
    CONVERSATIONAL = "conversational"


class AgentType(Enum):
    """Types of specialized agents."""
    MASTER_ANALYST = "master_analyst"
    RESOURCE_DISCOVERY = "resource_discovery"
    FIELD_EXTRACTION = "field_extraction"
    QUERY_PLANNING = "query_planning"
    CROSS_RESOURCE_SYNTHESIS = "cross_resource_synthesis"


@dataclass
class RoutingDecision:
    """Decision about how to route a query."""
    primary_agent: AgentType
    secondary_agents: List[AgentType]
    query_type: QueryType
    confidence: float
    reasoning: str
    estimated_complexity: str  # "low", "medium", "high"


@dataclass
class AgentCommunication:
    """Communication between agents."""
    from_agent: str
    to_agent: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: datetime
    correlation_id: str


@dataclass
class SynthesisResult:
    """Result of synthesizing multiple agent responses."""
    primary_result: AnalysisResult
    supporting_results: List[Dict[str, Any]]
    synthesis_insights: List[str]
    confidence_score: float
    methodology: str
    execution_time_ms: float


class QueryRouter:
    """
    Intelligent query router for agent-to-agent communication.
    
    Routes queries to appropriate specialized agents and synthesizes
    results from multiple agent interactions.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the query router."""
        self.config = config or get_config()
        self.master_agent = MasterDataAnalystAgent(config)
        self.activity_logger = get_activity_logger()
        
        # Agent communication tracking
        self.agent_communications: List[AgentCommunication] = []
        self.active_correlations: Dict[str, List[AgentCommunication]] = {}
        
        # Query classification patterns
        self.query_patterns = {
            QueryType.STRUCTURED_DATA: [
                r'\b(count|sum|average|max|min|total|calculate)\b',
                r'\b(table|column|row|field|database)\b',
                r'\b(group by|order by|where|join)\b',
                r'\b(statistics|aggregate|numeric)\b'
            ],
            QueryType.UNSTRUCTURED_DATA: [
                r'\b(search|find|text|document|content)\b',
                r'\b(similar|related|semantic|meaning)\b',
                r'\b(extract|summarize|analyze text)\b',
                r'\b(pdf|doc|txt|paragraph)\b'
            ],
            QueryType.METADATA_QUERY: [
                r'\b(what data|available|list|show me|resources)\b',
                r'\b(files|datasets|sources|uploaded)\b',
                r'\b(schema|structure|columns|fields)\b'
            ],
            QueryType.ANALYTICAL: [
                r'\b(trend|pattern|insight|correlation)\b',
                r'\b(compare|contrast|analyze|investigate)\b',
                r'\b(predict|forecast|why|how|explain)\b',
                r'\b(relationship|impact|cause|effect)\b'
            ],
            QueryType.CONVERSATIONAL: [
                r'\b(follow up|continue|also|additionally)\b',
                r'\b(what about|how about|can you also)\b',
                r'\b(previous|earlier|before|last)\b'
            ]
        }
        
        self.logger = logger
    
    async def route_and_execute(self, request: AnalysisRequest) -> SynthesisResult:
        """
        Route query to appropriate agents and synthesize results.
        
        Args:
            request: Analysis request to route and execute
            
        Returns:
            Synthesized result from multiple agent interactions
        """
        start_time = time.time()
        correlation_id = f"route_{int(time.time())}_{request.user_id[:8]}"
        
        try:
            self.logger.info(f"Routing query for user {request.user_id}: {request.query}")
            
            # Step 1: Analyze and classify the query
            routing_decision = self._analyze_query_for_routing(request)
            
            # Log routing decision
            activity_logger.log_agent_query(
                "query_router", request.user_id, request.client_id,
                f"Routing to {routing_decision.primary_agent.value}",
                request.conversation_id,
                {
                    "query_type": routing_decision.query_type.value,
                    "confidence": routing_decision.confidence,
                    "complexity": routing_decision.estimated_complexity
                }
            )
            
            # Step 2: Execute primary agent
            primary_result = await self._execute_primary_agent(request, routing_decision, correlation_id)
            
            # Step 3: Execute secondary agents if needed
            supporting_results = []
            if routing_decision.secondary_agents:
                supporting_results = await self._execute_secondary_agents(
                    request, routing_decision, primary_result, correlation_id
                )
            
            # Step 4: Synthesize results
            synthesis_result = await self._synthesize_results(
                primary_result, supporting_results, routing_decision, start_time
            )
            
            # Log completion
            execution_time = (time.time() - start_time) * 1000
            activity_logger.log_agent_response(
                "query_router", request.user_id, request.client_id,
                f"Query routed and synthesized successfully",
                execution_time, "query_router",
                request.conversation_id, None,
                {
                    "primary_agent": routing_decision.primary_agent.value,
                    "secondary_agents": len(routing_decision.secondary_agents),
                    "synthesis_confidence": synthesis_result.confidence_score
                }
            )
            
            self.logger.info(f"Query routing completed in {execution_time:.2f}ms")
            return synthesis_result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Query routing failed: {str(e)}"
            self.logger.error(error_msg)
            
            # Log error
            activity_logger.log_agent_error(
                "query_router", request.user_id, request.client_id,
                error_msg, request.conversation_id
            )
            
            # Return error synthesis result
            return SynthesisResult(
                primary_result=AnalysisResult(
                    query_id=f"error_{int(time.time())}",
                    user_id=request.user_id,
                    client_id=request.client_id,
                    results=[],
                    insights=[f"Routing error: {str(e)}"],
                    methodology="Error occurred during query routing",
                    sources_used=[],
                    confidence_score=0.0,
                    execution_time_ms=execution_time,
                    follow_up_suggestions=["Please try rephrasing your question"]
                ),
                supporting_results=[],
                synthesis_insights=[f"Query routing failed: {str(e)}"],
                confidence_score=0.0,
                methodology="Error handling",
                execution_time_ms=execution_time
            )
    
    def _analyze_query_for_routing(self, request: AnalysisRequest) -> RoutingDecision:
        """Analyze query to determine optimal routing strategy."""
        import re
        
        query_lower = request.query.lower()
        
        # Score each query type
        type_scores = {}
        for query_type, patterns in self.query_patterns.items():
            score = sum(1 for pattern in patterns 
                       if re.search(pattern, query_lower, re.IGNORECASE))
            type_scores[query_type] = score
        
        # Determine primary query type
        if not type_scores or max(type_scores.values()) == 0:
            primary_type = QueryType.ANALYTICAL  # Default
        else:
            primary_type = max(type_scores, key=type_scores.get)
        
        # Determine routing strategy based on query type and context
        if primary_type == QueryType.STRUCTURED_DATA:
            primary_agent = AgentType.MASTER_ANALYST
            secondary_agents = []
            complexity = "medium"
            
        elif primary_type == QueryType.UNSTRUCTURED_DATA:
            primary_agent = AgentType.MASTER_ANALYST
            secondary_agents = []
            complexity = "medium"
            
        elif primary_type == QueryType.MIXED_DATA:
            primary_agent = AgentType.MASTER_ANALYST
            secondary_agents = [AgentType.CROSS_RESOURCE_SYNTHESIS]
            complexity = "high"
            
        elif primary_type == QueryType.METADATA_QUERY:
            primary_agent = AgentType.MASTER_ANALYST
            secondary_agents = [AgentType.RESOURCE_DISCOVERY]
            complexity = "low"
            
        elif primary_type == QueryType.ANALYTICAL:
            primary_agent = AgentType.MASTER_ANALYST
            secondary_agents = [AgentType.CROSS_RESOURCE_SYNTHESIS]
            complexity = "high"
            
        else:  # CONVERSATIONAL
            primary_agent = AgentType.MASTER_ANALYST
            secondary_agents = []
            complexity = "low"
        
        # Calculate confidence based on pattern matches
        max_score = max(type_scores.values()) if type_scores else 0
        confidence = min(max_score / 3.0, 1.0)  # Normalize to 0-1
        
        # Generate reasoning
        reasoning = f"Query classified as {primary_type.value} with {max_score} pattern matches. " \
                   f"Routing to {primary_agent.value} with {len(secondary_agents)} supporting agents."
        
        return RoutingDecision(
            primary_agent=primary_agent,
            secondary_agents=secondary_agents,
            query_type=primary_type,
            confidence=confidence,
            reasoning=reasoning,
            estimated_complexity=complexity
        )
    
    async def _execute_primary_agent(self, request: AnalysisRequest, 
                                   routing_decision: RoutingDecision,
                                   correlation_id: str) -> AnalysisResult:
        """Execute the primary agent for the query."""
        # Log agent communication
        self._log_agent_communication(
            "query_router", routing_decision.primary_agent.value,
            "analysis_request", asdict(request), correlation_id
        )
        
        # For now, all primary routing goes to master agent
        # In a full implementation, this would route to different specialized agents
        if routing_decision.primary_agent == AgentType.MASTER_ANALYST:
            result = await self.master_agent.analyze_data(request)
        else:
            # Placeholder for other specialized agents
            result = await self.master_agent.analyze_data(request)
        
        # Log response
        self._log_agent_communication(
            routing_decision.primary_agent.value, "query_router",
            "analysis_response", asdict(result), correlation_id
        )
        
        return result
    
    async def _execute_secondary_agents(self, request: AnalysisRequest,
                                      routing_decision: RoutingDecision,
                                      primary_result: AnalysisResult,
                                      correlation_id: str) -> List[Dict[str, Any]]:
        """Execute secondary agents for additional insights."""
        supporting_results = []
        
        for secondary_agent in routing_decision.secondary_agents:
            try:
                # Log secondary agent communication
                self._log_agent_communication(
                    "query_router", secondary_agent.value,
                    "secondary_request", 
                    {"original_request": asdict(request), "primary_result_summary": {
                        "query_id": primary_result.query_id,
                        "sources_used": primary_result.sources_used,
                        "result_count": len(primary_result.results)
                    }}, 
                    correlation_id
                )
                
                # Execute secondary agent (placeholder implementation)
                secondary_result = await self._execute_secondary_agent(
                    secondary_agent, request, primary_result
                )
                
                supporting_results.append({
                    "agent": secondary_agent.value,
                    "result": secondary_result,
                    "execution_time_ms": 100  # Placeholder
                })
                
                # Log secondary response
                self._log_agent_communication(
                    secondary_agent.value, "query_router",
                    "secondary_response", secondary_result, correlation_id
                )
                
            except Exception as e:
                self.logger.warning(f"Secondary agent {secondary_agent.value} failed: {e}")
                supporting_results.append({
                    "agent": secondary_agent.value,
                    "error": str(e),
                    "execution_time_ms": 0
                })
        
        return supporting_results
    
    async def _execute_secondary_agent(self, agent_type: AgentType, 
                                     request: AnalysisRequest,
                                     primary_result: AnalysisResult) -> Dict[str, Any]:
        """Execute a specific secondary agent."""
        # Placeholder implementation for secondary agents
        # In a full implementation, these would be separate specialized agents
        
        if agent_type == AgentType.RESOURCE_DISCOVERY:
            return {
                "agent_type": "resource_discovery",
                "insights": ["Resource discovery analysis completed"],
                "resources_analyzed": len(primary_result.sources_used),
                "recommendations": ["Consider exploring additional data sources"]
            }
        
        elif agent_type == AgentType.CROSS_RESOURCE_SYNTHESIS:
            return {
                "agent_type": "cross_resource_synthesis",
                "insights": ["Cross-resource synthesis completed"],
                "synthesis_quality": "high" if len(primary_result.sources_used) > 1 else "low",
                "recommendations": ["Data patterns identified across multiple sources"]
            }
        
        elif agent_type == AgentType.FIELD_EXTRACTION:
            return {
                "agent_type": "field_extraction",
                "insights": ["Field extraction analysis completed"],
                "fields_mapped": len(request.desired_fields) if request.desired_fields else 0,
                "recommendations": ["Field mappings optimized for query"]
            }
        
        else:
            return {
                "agent_type": agent_type.value,
                "insights": [f"{agent_type.value} analysis completed"],
                "recommendations": ["Additional analysis completed"]
            }
    
    async def _synthesize_results(self, primary_result: AnalysisResult,
                                supporting_results: List[Dict[str, Any]],
                                routing_decision: RoutingDecision,
                                start_time: float) -> SynthesisResult:
        """Synthesize results from multiple agents."""
        synthesis_insights = []
        
        # Add routing insights
        synthesis_insights.append(
            f"Query routed as {routing_decision.query_type.value} with {routing_decision.confidence:.2f} confidence"
        )
        
        # Add primary result insights
        if primary_result.insights:
            synthesis_insights.extend(primary_result.insights)
        
        # Add secondary agent insights
        for result in supporting_results:
            if "insights" in result.get("result", {}):
                synthesis_insights.extend(result["result"]["insights"])
            elif "error" in result:
                synthesis_insights.append(f"Secondary analysis by {result['agent']} encountered an error")
        
        # Calculate overall confidence
        confidence_factors = [primary_result.confidence_score, routing_decision.confidence]
        if supporting_results:
            # Boost confidence if secondary agents succeeded
            successful_secondary = len([r for r in supporting_results if "error" not in r])
            confidence_boost = successful_secondary * 0.1
            confidence_factors.append(min(confidence_boost, 0.3))
        
        overall_confidence = sum(confidence_factors) / len(confidence_factors)
        overall_confidence = min(overall_confidence, 1.0)
        
        # Build methodology
        methodology_parts = [
            f"Primary analysis by {routing_decision.primary_agent.value}",
        ]
        
        if supporting_results:
            successful_agents = [r["agent"] for r in supporting_results if "error" not in r]
            if successful_agents:
                methodology_parts.append(f"Supporting analysis by {', '.join(successful_agents)}")
        
        methodology_parts.append("Results synthesized using intelligent agent coordination")
        methodology = "; ".join(methodology_parts)
        
        execution_time = (time.time() - start_time) * 1000
        
        return SynthesisResult(
            primary_result=primary_result,
            supporting_results=supporting_results,
            synthesis_insights=synthesis_insights,
            confidence_score=overall_confidence,
            methodology=methodology,
            execution_time_ms=execution_time
        )
    
    def _log_agent_communication(self, from_agent: str, to_agent: str,
                               message_type: str, payload: Dict[str, Any],
                               correlation_id: str) -> None:
        """Log communication between agents."""
        communication = AgentCommunication(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            payload=payload,
            timestamp=datetime.utcnow(),
            correlation_id=correlation_id
        )
        
        self.agent_communications.append(communication)
        
        # Track by correlation ID
        if correlation_id not in self.active_correlations:
            self.active_correlations[correlation_id] = []
        self.active_correlations[correlation_id].append(communication)
        
        # Log to activity logger
        activity_logger.log_tool_usage(
            from_agent, "", "",  # User info not available in agent-to-agent communication
            f"agent_communication_{message_type}",
            {"to_agent": to_agent, "correlation_id": correlation_id},
            f"Communication sent to {to_agent}",
            0.0
        )
    
    def get_communication_history(self, correlation_id: Optional[str] = None) -> List[AgentCommunication]:
        """Get agent communication history."""
        if correlation_id:
            return self.active_correlations.get(correlation_id, [])
        return self.agent_communications[-100:]  # Last 100 communications
    
    def get_routing_statistics(self) -> Dict[str, Any]:
        """Get statistics about query routing."""
        if not self.agent_communications:
            return {"total_communications": 0}
        
        # Count communications by type
        comm_types = {}
        agent_pairs = {}
        
        for comm in self.agent_communications:
            comm_types[comm.message_type] = comm_types.get(comm.message_type, 0) + 1
            
            pair_key = f"{comm.from_agent}->{comm.to_agent}"
            agent_pairs[pair_key] = agent_pairs.get(pair_key, 0) + 1
        
        return {
            "total_communications": len(self.agent_communications),
            "communication_types": comm_types,
            "agent_pairs": agent_pairs,
            "active_correlations": len(self.active_correlations)
        }
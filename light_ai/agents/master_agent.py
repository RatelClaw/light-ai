"""
Master AI Data Analyst Agent with Strands Framework Integration.

This is the central orchestrating agent that coordinates all data analysis
activities using the Strands AI framework with specialized tools for
intelligent data operations.
"""

import asyncio
import time
import json
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime

from .base import BaseAgent, AgentConfig
from .strands_tools import (
    ResourceDiscoveryTool, FieldExtractionTool, QueryExecutionTool,
    DataSynthesisTool, CrossResourceSynthesisTool, VisualizationTool, ToolResult
)
from .logging import get_activity_logger
from ..core.models import ResourceType, AccessLevel
from light_ai.config import Config


@dataclass
class AnalysisRequest:
    """Request for AI data analysis."""
    user_id: str
    client_id: str
    query: str
    desired_fields: Optional[Dict[str, str]] = None
    optional_fields: Optional[Dict[str, str]] = None
    derived_fields: Optional[Dict[str, str]] = None
    context: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None
    access_level: AccessLevel = AccessLevel.USER
    include_visualizations: bool = True


@dataclass
class AnalysisResult:
    """Result of AI data analysis."""
    query_id: str
    user_id: str
    client_id: str
    results: List[Dict[str, Any]]
    insights: List[str]
    methodology: str
    sources_used: List[str]
    confidence_score: float
    execution_time_ms: float
    follow_up_suggestions: List[str]
    visualizations: Optional[List[Dict[str, Any]]] = None
    field_mappings: Optional[Dict[str, Any]] = None
    cross_resource_synthesis: Optional[Dict[str, Any]] = None


class MasterDataAnalystAgent(BaseAgent):
    """
    Master AI Data Analyst Agent using Strands Framework.
    
    This agent serves as the central coordinator for all data analysis
    activities, providing natural language understanding, intelligent
    query routing, and agent-to-agent communication using specialized tools.
    
    Features:
    - Natural language understanding for data queries
    - Automatic resource discovery and cataloging
    - Intelligent field extraction and mapping
    - Cross-resource data synthesis
    - Query planning and optimization
    - Conversation context management
    - Visualization generation
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the Master Data Analyst Agent with Strands tools."""
        
        # Define the enhanced system prompt for Strands integration
        system_prompt = """You are an expert AI Data Analyst with access to a user's complete dataset and specialized tools for intelligent data analysis.

Your capabilities:
1. Understand natural language queries about data
2. Automatically discover and catalog relevant data sources
3. Extract and map fields intelligently across data formats
4. Synthesize information from multiple data sources
5. Execute queries with safety validation
6. Generate insights, trends, and comprehensive analysis
7. Create visualization suggestions
8. Maintain conversation context for follow-up questions

Available Tools:
- resource_discovery: Find and catalog relevant data sources
- field_extraction: Map desired fields to available data
- query_execution: Execute queries safely with validation
- data_synthesis: Combine data from multiple sources
- cross_resource_synthesis: Advanced multi-source data combination with conflict resolution
- visualization_generation: Create visualization suggestions

Workflow for Analysis:
1. Use resource_discovery to find relevant data sources
2. Use field_extraction to map required fields
3. Use query_execution to get data
4. Use data_synthesis to combine multiple sources
5. Use cross_resource_synthesis for complex multi-source combinations
6. Use visualization_generation for visual insights
7. Provide comprehensive analysis with explanations

Always:
- Explain your reasoning and methodology
- Cite data sources used in analysis
- Ask clarifying questions when queries are ambiguous
- Provide actionable insights and recommendations
- Maintain conversation context for follow-up questions
- Use tools systematically for comprehensive analysis
- Ensure strict data isolation - users can only access their own data

Remember: You have specialized tools to help with each step of data analysis. Use them systematically to provide the most comprehensive and accurate analysis possible."""

        # Configure the agent with enhanced capabilities
        agent_config = AgentConfig(
            name="master_data_analyst_strands",
            model_name=config.openrouter.default_model if config else "anthropic/claude-3.5-sonnet",
            temperature=0.3,  # Lower for analytical tasks
            max_tokens=4096,
            timeout_seconds=120,  # Longer timeout for complex analysis
            system_prompt=system_prompt
        )
        
        super().__init__(agent_config, config)
        
        # Initialize specialized tools
        self.resource_discovery = ResourceDiscoveryTool(config)
        self.field_extraction = FieldExtractionTool(config)
        self.query_execution = QueryExecutionTool(config)
        self.data_synthesis = DataSynthesisTool(config)
        self.cross_resource_synthesis = CrossResourceSynthesisTool(config)
        self.visualization = VisualizationTool(config)
        
        # Initialize activity logger
        self.activity_logger = get_activity_logger()
        
        # Initialize conversation history
        self.conversation_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # Tool registry for dynamic tool calling
        self.tools = {
            "resource_discovery": self._tool_resource_discovery,
            "field_extraction": self._tool_field_extraction,
            "query_execution": self._tool_query_execution,
            "data_synthesis": self._tool_data_synthesis,
            "cross_resource_synthesis": self._tool_cross_resource_synthesis,
            "visualization_generation": self._tool_visualization_generation
        }
    
    async def analyze_data(self, request: AnalysisRequest) -> AnalysisResult:
        """
        Perform comprehensive data analysis using Strands framework and tools.
        
        Args:
            request: Analysis request with query and context
            
        Returns:
            Analysis result with insights and data
        """
        start_time = time.time()
        query_id = f"{request.user_id}_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        
        try:
            self.logger.info(f"Starting Strands analysis for user {request.user_id}: {request.query}")
            
            # Log analysis start
            self.activity_logger.log_agent_query(
                self.agent_config.name, request.user_id, request.client_id,
                request.query, request.conversation_id
            )
            
            # Build comprehensive context for the agent
            context = {
                "user_id": request.user_id,
                "client_id": request.client_id,
                "conversation_id": request.conversation_id,
                "access_level": request.access_level.value,
                "include_visualizations": request.include_visualizations,
                "available_tools": list(self.tools.keys())
            }
            
            if request.desired_fields:
                context["desired_fields"] = request.desired_fields
            if request.optional_fields:
                context["optional_fields"] = request.optional_fields
            if request.derived_fields:
                context["derived_fields"] = request.derived_fields
            if request.context:
                context.update(request.context)
            
            # Add conversation history if available
            if request.conversation_id and request.conversation_id in self.conversation_history:
                context["conversation_history"] = self.conversation_history[request.conversation_id][-3:]  # Last 3 exchanges
            
            # Execute the analysis using the agent with tool access
            analysis_prompt = self._build_analysis_prompt(request, context)
            response = await self._execute_with_tools(analysis_prompt, context, request)
            
            # Parse and structure the response
            execution_time = (time.time() - start_time) * 1000
            
            result = AnalysisResult(
                query_id=query_id,
                user_id=request.user_id,
                client_id=request.client_id,
                results=response.get("results", []),
                insights=response.get("insights", [response.get("analysis", "Analysis completed")]),
                methodology=response.get("methodology", "Strands AI framework with specialized tools"),
                sources_used=response.get("sources_used", []),
                confidence_score=response.get("confidence_score", 0.8),
                execution_time_ms=execution_time,
                follow_up_suggestions=response.get("follow_up_suggestions", [
                    "Would you like me to analyze trends over time?",
                    "Should I look for correlations with other data?",
                    "Would you like a detailed breakdown by category?"
                ]),
                visualizations=response.get("visualizations"),
                field_mappings=response.get("field_mappings"),
                cross_resource_synthesis=response.get("cross_resource_synthesis")
            )
            
            # Store in conversation history
            if request.conversation_id:
                if request.conversation_id not in self.conversation_history:
                    self.conversation_history[request.conversation_id] = []
                
                self.conversation_history[request.conversation_id].append({
                    "query": request.query,
                    "response": response.get("analysis", "Analysis completed"),
                    "timestamp": time.time(),
                    "query_id": query_id
                })
            
            # Log analysis completion
            self.activity_logger.log_agent_response(
                self.agent_config.name, request.user_id, request.client_id,
                f"Analysis completed with {len(result.results)} results",
                execution_time, self.agent_config.model_name,
                request.conversation_id, None,
                {"query_id": query_id, "sources_used": len(result.sources_used)}
            )
            
            self.logger.info(f"Strands analysis completed in {execution_time:.2f}ms")
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Strands analysis failed: {str(e)}"
            self.logger.error(error_msg)
            
            # Log error
            self.activity_logger.log_agent_error(
                self.agent_config.name, request.user_id, request.client_id,
                error_msg, request.conversation_id
            )
            
            # Return error result
            return AnalysisResult(
                query_id=query_id,
                user_id=request.user_id,
                client_id=request.client_id,
                results=[],
                insights=[f"Analysis failed: {str(e)}"],
                methodology="Error occurred during analysis",
                sources_used=[],
                confidence_score=0.0,
                execution_time_ms=execution_time,
                follow_up_suggestions=["Please try rephrasing your question", "Check if you have access to the required data"]
            )
    
    def _build_analysis_prompt(self, request: AnalysisRequest, context: Dict[str, Any]) -> str:
        """Build comprehensive analysis prompt for the agent."""
        prompt_parts = [
            f"User Query: {request.query}",
            "",
            "Context Information:",
            f"- User ID: {request.user_id}",
            f"- Client ID: {request.client_id}",
            f"- Access Level: {request.access_level.value}",
        ]
        
        if request.desired_fields:
            prompt_parts.append(f"- Desired Fields: {request.desired_fields}")
        
        if request.optional_fields:
            prompt_parts.append(f"- Optional Fields: {request.optional_fields}")
        
        if request.derived_fields:
            prompt_parts.append(f"- Derived Fields: {request.derived_fields}")
        
        if context.get("conversation_history"):
            prompt_parts.extend([
                "",
                "Previous Conversation:",
                *[f"Q: {h['query']} -> A: {h['response'][:100]}..." for h in context["conversation_history"]]
            ])
        
        prompt_parts.extend([
            "",
            "Instructions:",
            "1. Use the resource_discovery tool to find relevant data sources",
            "2. If specific fields are needed, use field_extraction tool",
            "3. Use query_execution tool to get data",
            "4. If multiple sources are involved, use data_synthesis tool",
            "5. If visualizations are requested, use visualization_generation tool",
            "6. Provide comprehensive analysis with insights and explanations",
            "",
            "Please analyze the user's query systematically using the available tools."
        ])
        
        return "\n".join(prompt_parts)
    
    async def _execute_with_tools(self, prompt: str, context: Dict[str, Any], 
                                 request: AnalysisRequest) -> Dict[str, Any]:
        """Execute analysis with tool integration."""
        # This is a simplified implementation of tool integration
        # In a full Strands implementation, this would use the Strands framework
        # for more sophisticated tool orchestration
        
        response = {
            "analysis": "",
            "results": [],
            "insights": [],
            "methodology": "Strands AI framework with specialized tools",
            "sources_used": [],
            "confidence_score": 0.8,
            "follow_up_suggestions": []
        }
        
        try:
            # Step 1: Discover relevant resources
            discovery_result = self.resource_discovery.discover_resources(
                request.user_id, request.client_id, request.query
            )
            
            if discovery_result.success and discovery_result.data:
                resources = discovery_result.data.get("resources", [])
                response["sources_used"] = [r["filename"] for r in resources]
                
                # Step 2: Field extraction if needed
                if request.desired_fields and resources:
                    resource_ids = [r["resource_id"] for r in resources[:5]]  # Top 5 resources
                    field_result = self.field_extraction.extract_and_map_fields(
                        request.user_id, request.client_id, request.desired_fields, resource_ids
                    )
                    
                    if field_result.success:
                        response["field_mappings"] = field_result.data
                
                # Step 3: Execute queries on structured data
                structured_resources = [r for r in resources if r["resource_type"] == "structured"]
                if structured_resources:
                    # Generate a simple query for demonstration
                    sample_resource = structured_resources[0]
                    table_name = f"structured_data.resource_{sample_resource['resource_id'].replace('-', '_')}_enhanced"
                    simple_query = f"SELECT * FROM {table_name} LIMIT 10"
                    
                    query_result = self.query_execution.execute_query(
                        request.user_id, request.client_id, simple_query, "sql",
                        access_level=request.access_level
                    )
                    
                    if query_result.success and query_result.data:
                        response["results"] = query_result.data.get("results", [])
                
                # Step 4: Data synthesis if multiple resources
                if len(resources) > 1:
                    resource_ids = [r["resource_id"] for r in resources[:3]]  # Top 3 resources
                    
                    # Use advanced cross-resource synthesis for complex combinations
                    if len(resources) > 2 or "join" in request.query.lower() or "combine" in request.query.lower():
                        synthesis_result = self.cross_resource_synthesis.synthesize_resources(
                            request.user_id, request.client_id, resource_ids, request.query, request.desired_fields
                        )
                        
                        if synthesis_result.success:
                            response["cross_resource_synthesis"] = synthesis_result.data
                    else:
                        # Use simple data synthesis for basic combinations
                        synthesis_result = self.data_synthesis.synthesize_data(
                            request.user_id, request.client_id, resource_ids, "summary"
                        )
                        
                        if synthesis_result.success:
                            response["cross_resource_synthesis"] = synthesis_result.data
                
                # Step 5: Generate visualizations if requested
                if request.include_visualizations and response["results"]:
                    viz_result = self.visualization.generate_visualizations(
                        request.user_id, request.client_id, response["results"][:10]  # Sample data
                    )
                    
                    if viz_result.success:
                        response["visualizations"] = viz_result.data.get("suggestions", [])
                
                # Generate insights based on the analysis
                response["insights"] = self._generate_insights(request, response)
                
                # Generate analysis summary
                response["analysis"] = self._generate_analysis_summary(request, response)
            
            else:
                response["analysis"] = "No relevant data sources found for your query."
                response["insights"] = ["Consider uploading relevant data to enable analysis"]
        
        except Exception as e:
            self.logger.error(f"Tool execution failed: {e}")
            response["analysis"] = f"Analysis encountered an error: {str(e)}"
            response["insights"] = ["Please try rephrasing your question"]
        
        return response
    
    def _generate_insights(self, request: AnalysisRequest, response: Dict[str, Any]) -> List[str]:
        """Generate insights based on analysis results."""
        insights = []
        
        # Data availability insights
        if response["sources_used"]:
            insights.append(f"Analysis based on {len(response['sources_used'])} data sources: {', '.join(response['sources_used'])}")
        
        # Results insights
        if response["results"]:
            insights.append(f"Retrieved {len(response['results'])} data records for analysis")
            
            # Sample data insight
            if len(response["results"]) > 0:
                sample_row = response["results"][0]
                non_system_fields = [k for k in sample_row.keys() if k not in ['client_id', 'user_id']]
                if non_system_fields:
                    insights.append(f"Data includes fields: {', '.join(non_system_fields[:5])}")
        
        # Field mapping insights
        if response.get("field_mappings"):
            mapped_fields = len(response["field_mappings"].get("field_mappings", {}))
            if mapped_fields > 0:
                insights.append(f"Successfully mapped {mapped_fields} requested fields to available data")
        
        # Cross-resource insights
        if response.get("cross_resource_synthesis"):
            synthesis = response["cross_resource_synthesis"]
            if synthesis.get("total_resources", 0) > 1:
                insights.append(f"Combined analysis across {synthesis['total_resources']} different data sources")
        
        # Visualization insights
        if response.get("visualizations"):
            viz_count = len(response["visualizations"])
            insights.append(f"Generated {viz_count} visualization suggestions to help explore the data")
        
        # Default insight if none generated
        if not insights:
            insights.append("Analysis completed - ready for follow-up questions")
        
        return insights
    
    def _generate_analysis_summary(self, request: AnalysisRequest, response: Dict[str, Any]) -> str:
        """Generate comprehensive analysis summary."""
        summary_parts = [
            f"Analysis of query: '{request.query}'",
            ""
        ]
        
        if response["sources_used"]:
            summary_parts.append(f"Data Sources: {', '.join(response['sources_used'])}")
        
        if response["results"]:
            summary_parts.append(f"Retrieved {len(response['results'])} records")
        
        if response.get("field_mappings"):
            summary_parts.append("Field mapping completed successfully")
        
        if response.get("cross_resource_synthesis"):
            summary_parts.append("Cross-resource data synthesis performed")
        
        if response.get("visualizations"):
            summary_parts.append(f"Generated {len(response['visualizations'])} visualization suggestions")
        
        summary_parts.extend([
            "",
            "Key Insights:",
            *[f"• {insight}" for insight in response.get("insights", [])]
        ])
        
        return "\n".join(summary_parts)
    
    # Tool wrapper methods for the agent
    def _tool_resource_discovery(self, user_id: str, client_id: str, **kwargs) -> Dict[str, Any]:
        """Wrapper for resource discovery tool."""
        result = self.resource_discovery.discover_resources(user_id, client_id, **kwargs)
        return asdict(result)
    
    def _tool_field_extraction(self, user_id: str, client_id: str, **kwargs) -> Dict[str, Any]:
        """Wrapper for field extraction tool."""
        result = self.field_extraction.extract_and_map_fields(user_id, client_id, **kwargs)
        return asdict(result)
    
    def _tool_query_execution(self, user_id: str, client_id: str, **kwargs) -> Dict[str, Any]:
        """Wrapper for query execution tool."""
        result = self.query_execution.execute_query(user_id, client_id, **kwargs)
        return asdict(result)
    
    def _tool_data_synthesis(self, user_id: str, client_id: str, **kwargs) -> Dict[str, Any]:
        """Wrapper for data synthesis tool."""
        result = self.data_synthesis.synthesize_data(user_id, client_id, **kwargs)
        return asdict(result)
    
    def _tool_cross_resource_synthesis(self, user_id: str, client_id: str, **kwargs) -> Dict[str, Any]:
        """Wrapper for cross-resource synthesis tool."""
        result = self.cross_resource_synthesis.synthesize_resources(user_id, client_id, **kwargs)
        return asdict(result)
    
    def _tool_visualization_generation(self, user_id: str, client_id: str, **kwargs) -> Dict[str, Any]:
        """Wrapper for visualization generation tool."""
        result = self.visualization.generate_visualizations(user_id, client_id, **kwargs)
        return asdict(result)
    
    async def continue_conversation(self, request: AnalysisRequest) -> AnalysisResult:
        """
        Continue a conversation with follow-up questions.
        
        Args:
            request: Follow-up request with conversation context
            
        Returns:
            Analysis result building on previous context
        """
        # This will use the conversation history automatically in analyze_data
        return await self.analyze_data(request)
    
    async def explain_methodology(self, query_id: str) -> str:
        """
        Explain the methodology used for a specific analysis.
        
        Args:
            query_id: ID of the query to explain
            
        Returns:
            Detailed explanation of methodology
        """
        explanation_prompt = f"""
        Please explain the methodology and reasoning used for query ID: {query_id}
        
        Include:
        1. What data sources were analyzed
        2. What analytical methods were applied
        3. How conclusions were reached
        4. What assumptions were made
        5. What limitations exist in the analysis
        """
        
        return await self.execute(explanation_prompt)
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a specific conversation."""
        return self.conversation_history.get(conversation_id, [])
    
    def clear_conversation_history(self, conversation_id: str) -> None:
        """Clear conversation history for a specific conversation."""
        if conversation_id in self.conversation_history:
            del self.conversation_history[conversation_id]
            self.logger.info(f"Cleared conversation history for {conversation_id}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check of the agent.
        
        Returns:
            Health status information
        """
        try:
            # Test basic agent functionality
            test_response = await self.execute("Hello, are you working correctly?")
            
            return {
                "status": "healthy",
                "agent_info": self.get_agent_info(),
                "test_response_length": len(test_response),
                "conversation_count": len(self.conversation_history),
                "total_conversations": sum(len(history) for history in self.conversation_history.values())
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "agent_info": self.get_agent_info()
            }
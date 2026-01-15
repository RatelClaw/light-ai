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
from .intelligent_content_analyzer import get_content_analyzer
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
        self.content_analyzer = get_content_analyzer(config)  # Intelligent content analyzer
        
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
                json_resources = [r for r in resources if r["resource_type"] == "json"]
                
                # Get data from JSON resources (which is what we uploaded)
                if json_resources:
                    query_result = self.query_execution.execute_query(
                        request.user_id, request.client_id, request.query, "data",
                        access_level=request.access_level
                    )
                    
                    if query_result.success and query_result.data:
                        json_data_results = query_result.data.get("results", [])
                        # Extract the actual data from the JSON files
                        for json_item in json_data_results:
                            if "data" in json_item:
                                response["results"].append(json_item["data"])
                
                # Also try structured data if available
                elif structured_resources:
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
                
                # Extract persona and context if requested
                if request.desired_fields:
                    extracted_fields = self._extract_desired_field_values(request, response)
                    response.update(extracted_fields)
                
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
        
        # If we have actual data results, analyze them for persona/context insights
        if response["results"]:
            insights.extend(self._analyze_data_for_insights(request, response["results"]))
        
        # If we have field mappings, use them to understand the data structure
        if response.get("field_mappings"):
            insights.extend(self._analyze_field_mappings_for_insights(request, response["field_mappings"]))
        
        # If we have cross-resource synthesis, analyze the combined data
        if response.get("cross_resource_synthesis"):
            insights.extend(self._analyze_synthesis_for_insights(request, response["cross_resource_synthesis"]))
        
        # If no specific insights were generated, provide data availability info
        if not insights:
            if response["sources_used"]:
                insights.append(f"Found data from {len(response['sources_used'])} sources but unable to extract specific insights for the requested analysis")
            else:
                insights.append("No relevant data found for the requested analysis")
        
        return insights
    
    def _analyze_data_for_insights(self, request: AnalysisRequest, results: List[Dict[str, Any]]) -> List[str]:
        """Analyze actual data results to generate meaningful insights."""
        insights = []
        
        if not results:
            return insights
        
        # Look for persona-related queries
        query_lower = request.query.lower()
        is_persona_query = any(term in query_lower for term in ['persona', 'profile', 'characteristics', 'traits'])
        is_context_query = any(term in query_lower for term in ['context', 'background', 'environment', 'situation'])
        
        # Analyze the first few records for patterns
        sample_data = results[:5]  # Analyze first 5 records
        
        for record in sample_data:
            # Skip system fields
            data_fields = {k: v for k, v in record.items() if k not in ['client_id', 'user_id', 'resource_id']}
            
            if is_persona_query:
                persona_insights = self._extract_persona_insights(data_fields)
                insights.extend(persona_insights)
            
            if is_context_query:
                context_insights = self._extract_context_insights(data_fields)
                insights.extend(context_insights)
            
            # General data insights
            if not is_persona_query and not is_context_query:
                general_insights = self._extract_general_insights(data_fields, request.query)
                insights.extend(general_insights)
        
        return list(set(insights))  # Remove duplicates
    
    def _extract_persona_insights(self, data: Dict[str, Any]) -> List[str]:
        """Extract persona-specific insights from data."""
        insights = []
        
        # Flatten nested data for analysis
        flattened_data = self._flatten_data_for_analysis(data)
        
        # Look for demographic information
        demographics = []
        for key, value in flattened_data.items():
            key_lower = key.lower()
            if any(demo_key in key_lower for demo_key in ['age', 'gender', 'program', 'occupation', 'role']):
                demographics.append(f"{key.replace('_', ' ').title()}: {value}")
        
        if demographics:
            insights.append(f"Demographics: {', '.join(demographics)}")
        
        # Look for performance/achievement indicators
        performance = []
        for key, value in flattened_data.items():
            key_lower = key.lower()
            if any(perf_key in key_lower for perf_key in ['gpa', 'grade', 'score', 'rating', 'performance']):
                if isinstance(value, (int, float)):
                    performance.append(f"{key.replace('_', ' ').title()}: {value}")
        
        if performance:
            insights.append(f"Performance indicators: {', '.join(performance)}")
        
        # Look for interests and goals
        interests = []
        for key, value in flattened_data.items():
            key_lower = key.lower()
            if any(interest_key in key_lower for interest_key in ['interest', 'goal', 'aspiration', 'hobby']):
                if isinstance(value, list):
                    interests.extend(value)
                else:
                    interests.append(str(value))
        
        if interests:
            insights.append(f"Interests/Goals: {', '.join(interests[:5])}")  # Limit to 5
        
        # Look for behavioral patterns
        behaviors = []
        for key, value in flattened_data.items():
            key_lower = key.lower()
            if any(behavior_key in key_lower for behavior_key in ['status', 'frequency', 'usage', 'participation']):
                behaviors.append(f"{key.replace('_', ' ').title()}: {value}")
        
        if behaviors:
            insights.append(f"Behavioral patterns: {', '.join(behaviors[:3])}")  # Limit to 3
        
        return insights
    
    def _extract_context_insights(self, data: Dict[str, Any]) -> List[str]:
        """Extract context-specific insights from data."""
        insights = []
        
        # Flatten nested data for analysis
        flattened_data = self._flatten_data_for_analysis(data)
        
        # Look for institutional/organizational context
        institutional = []
        for key, value in flattened_data.items():
            key_lower = key.lower()
            if any(inst_key in key_lower for inst_key in ['institution', 'university', 'company', 'organization']):
                institutional.append(f"{key.replace('_', ' ').title()}: {value}")
        
        if institutional:
            insights.append(f"Institutional context: {', '.join(institutional)}")
        
        # Look for temporal context
        temporal = []
        for key, value in flattened_data.items():
            key_lower = key.lower()
            if any(time_key in key_lower for time_key in ['year', 'semester', 'period', 'date', 'time']):
                temporal.append(f"{key.replace('_', ' ').title()}: {value}")
        
        if temporal:
            insights.append(f"Temporal context: {', '.join(temporal)}")
        
        # Look for environmental context
        environmental = []
        for key, value in flattened_data.items():
            key_lower = key.lower()
            if any(env_key in key_lower for env_key in ['location', 'residence', 'environment', 'setting']):
                environmental.append(f"{key.replace('_', ' ').title()}: {value}")
        
        if environmental:
            insights.append(f"Environmental context: {', '.join(environmental)}")
        
        return insights
    
    def _extract_general_insights(self, data: Dict[str, Any], query: str) -> List[str]:
        """Extract general insights based on the query and data."""
        insights = []
        
        # Flatten nested data for analysis
        flattened_data = self._flatten_data_for_analysis(data)
        
        # Look for query-relevant fields
        query_words = set(query.lower().split())
        relevant_fields = []
        
        for key, value in flattened_data.items():
            key_words = set(key.lower().replace('_', ' ').split())
            if query_words & key_words:  # Intersection of sets
                relevant_fields.append(f"{key.replace('_', ' ').title()}: {value}")
        
        if relevant_fields:
            insights.append(f"Query-relevant data: {', '.join(relevant_fields[:5])}")
        
        # Provide data summary
        total_fields = len(flattened_data)
        numeric_fields = sum(1 for v in flattened_data.values() if isinstance(v, (int, float)))
        text_fields = sum(1 for v in flattened_data.values() if isinstance(v, str))
        
        insights.append(f"Data summary: {total_fields} total fields ({numeric_fields} numeric, {text_fields} text)")
        
        return insights
    
    def _flatten_data_for_analysis(self, data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Flatten nested data structure for easier analysis."""
        flattened = {}
        
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                flattened.update(self._flatten_data_for_analysis(value, full_key))
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                # Handle list of objects - take first item
                flattened.update(self._flatten_data_for_analysis(value[0], full_key))
            else:
                flattened[full_key] = value
        
        return flattened
    
    def _analyze_field_mappings_for_insights(self, request: AnalysisRequest, field_mappings: Dict[str, Any]) -> List[str]:
        """Analyze field mappings to generate insights."""
        insights = []
        
        mappings = field_mappings.get("field_mappings", {})
        if mappings:
            insights.append(f"Successfully mapped {len(mappings)} requested fields to available data")
            
            # List the mapped fields
            mapped_field_names = list(mappings.keys())
            if mapped_field_names:
                insights.append(f"Mapped fields: {', '.join(mapped_field_names[:5])}")
        
        return insights
    
    def _analyze_synthesis_for_insights(self, request: AnalysisRequest, synthesis: Dict[str, Any]) -> List[str]:
        """Analyze cross-resource synthesis to generate insights."""
        insights = []
        
        total_resources = synthesis.get("total_resources", 0)
        if total_resources > 1:
            insights.append(f"Combined analysis across {total_resources} different data sources")
        
        return insights
    
    def _extract_desired_field_values(self, request: AnalysisRequest, response: Dict[str, Any]) -> Dict[str, str]:
        """Extract actual values for desired fields like persona and context using intelligent analysis."""
        extracted_values = {}
        
        if not request.desired_fields or not response.get("results"):
            return extracted_values
        
        # Get the data for analysis
        data_results = response["results"]
        
        # Use intelligent content analyzer for semantic extraction
        try:
            # Run async analysis in sync context
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, create a task
                analysis_result = asyncio.create_task(
                    self.content_analyzer.analyze_content(data_results, request.desired_fields)
                )
                # Note: This won't block, result will be available later
                # For now, fall back to pattern matching
                self.logger.info("Async loop running, using pattern matching fallback")
                return self._extract_with_pattern_matching(request, response)
            else:
                # Run the analysis
                analysis_result = loop.run_until_complete(
                    self.content_analyzer.analyze_content(data_results, request.desired_fields)
                )
                
                if analysis_result.success:
                    self.logger.info(f"Intelligent analysis succeeded with confidence {analysis_result.confidence_score:.2f}")
                    return analysis_result.extracted_fields
                else:
                    self.logger.warning(f"Intelligent analysis failed: {analysis_result.error}, falling back to pattern matching")
                    return self._extract_with_pattern_matching(request, response)
                    
        except Exception as e:
            self.logger.error(f"Content analyzer error: {e}, falling back to pattern matching")
            return self._extract_with_pattern_matching(request, response)
    
    def _extract_with_pattern_matching(self, request: AnalysisRequest, response: Dict[str, Any]) -> Dict[str, str]:
        """Fallback pattern matching extraction (original implementation)"""
        extracted_values = {}
        data_results = response["results"]
        insights = response.get("insights", [])
        
        for field_name, field_description in request.desired_fields.items():
            field_name_lower = field_name.lower()
            
            if field_name_lower == "persona":
                extracted_values["persona"] = self._extract_persona_value(data_results, insights, field_description)
            elif field_name_lower == "context":
                extracted_values["context"] = self._extract_context_value(data_results, insights, field_description)
            else:
                # For other desired fields, try to extract relevant information
                extracted_values[field_name] = self._extract_generic_field_value(
                    data_results, insights, field_name, field_description
                )
        
        return extracted_values
    
    def _extract_persona_value(self, data_results: List[Dict[str, Any]], insights: List[str], description: str) -> str:
        """Extract persona value from data and insights."""
        persona_parts = []
        
        # Extract persona information from data
        if data_results:
            persona_data = self._extract_persona_from_results(data_results)
            
            for category, items in persona_data.items():
                if items:
                    if category == "Demographics":
                        persona_parts.append(f"Demographics: {', '.join(items)}")
                    elif category == "Performance":
                        persona_parts.append(f"Performance: {', '.join(items[:3])}")  # Limit to top 3
                    elif category == "Interests & Goals":
                        persona_parts.append(f"Goals & Interests: {', '.join(items[:3])}")
                    elif category == "Behavioral Patterns":
                        persona_parts.append(f"Behavior: {', '.join(items[:2])}")  # Limit to top 2
        
        # Add relevant insights
        persona_insights = [insight for insight in insights if any(
            keyword in insight.lower() for keyword in [
                'demographics', 'age', 'gender', 'role', 'occupation', 'goals', 'interests',
                'behavior', 'personality', 'characteristics', 'traits'
            ]
        )]
        
        if persona_insights:
            persona_parts.extend(persona_insights[:3])  # Add top 3 relevant insights
        
        if persona_parts:
            return "; ".join(persona_parts)
        else:
            return "Unable to extract detailed persona information from available data"
    
    def _extract_context_value(self, data_results: List[Dict[str, Any]], insights: List[str], description: str) -> str:
        """Extract context value from data and insights."""
        context_parts = []
        
        # Extract context information from data
        if data_results:
            context_data = self._extract_context_from_results(data_results)
            
            for category, items in context_data.items():
                if items:
                    context_parts.append(f"{category}: {', '.join(items[:2])}")  # Limit to top 2 per category
        
        # Add relevant insights
        context_insights = [insight for insight in insights if any(
            keyword in insight.lower() for keyword in [
                'institutional', 'temporal', 'environmental', 'academic', 'professional',
                'context', 'background', 'setting', 'environment'
            ]
        )]
        
        if context_insights:
            context_parts.extend(context_insights[:2])  # Add top 2 relevant insights
        
        if context_parts:
            return "; ".join(context_parts)
        else:
            return "Limited contextual information available from current data"
    
    def _extract_generic_field_value(self, data_results: List[Dict[str, Any]], insights: List[str], 
                                    field_name: str, description: str) -> str:
        """Extract value for a generic desired field."""
        # Look for insights that mention the field name or related keywords
        field_keywords = field_name.lower().split('_') + description.lower().split()
        
        relevant_insights = []
        for insight in insights:
            insight_lower = insight.lower()
            if any(keyword in insight_lower for keyword in field_keywords):
                relevant_insights.append(insight)
        
        if relevant_insights:
            return "; ".join(relevant_insights[:3])  # Top 3 relevant insights
        
        # If no insights found, try to extract from data structure
        if data_results:
            flattened_data = self._flatten_data_for_analysis(data_results[0])
            
            # Look for fields that match the desired field name
            matching_values = []
            for key, value in flattened_data.items():
                if any(keyword in key.lower() for keyword in field_keywords):
                    matching_values.append(f"{key.replace('_', ' ').title()}: {value}")
            
            if matching_values:
                return "; ".join(matching_values[:3])
        
        return f"Unable to extract {field_name} information from available data"
    
    def _generate_analysis_summary(self, request: AnalysisRequest, response: Dict[str, Any]) -> str:
        """Generate comprehensive analysis summary."""
        
        # Check if this is a persona/context query
        query_lower = request.query.lower()
        is_persona_query = any(term in query_lower for term in ['persona', 'profile', 'characteristics', 'traits'])
        is_context_query = any(term in query_lower for term in ['context', 'background', 'environment', 'situation'])
        
        if is_persona_query or is_context_query:
            return self._generate_persona_context_summary(request, response)
        else:
            return self._generate_general_analysis_summary(request, response)
    
    def _generate_persona_context_summary(self, request: AnalysisRequest, response: Dict[str, Any]) -> str:
        """Generate persona and context specific analysis summary."""
        
        # Extract user identifier from query if present
        user_identifier = self._extract_user_identifier(request.query)
        
        # Analyze the data for persona and context
        if response["results"]:
            persona_data = self._extract_persona_from_results(response["results"])
            context_data = self._extract_context_from_results(response["results"])
            
            # Build comprehensive persona summary
            persona_parts = []
            
            if user_identifier:
                persona_parts.append(f"**User Profile: {user_identifier}**")
            else:
                persona_parts.append("**User Profile Analysis:**")
            
            persona_parts.append("")
            
            # Add persona information
            if persona_data:
                for category, items in persona_data.items():
                    if items:
                        persona_parts.append(f"**{category}:**")
                        for item in items:
                            persona_parts.append(f"- {item}")
                        persona_parts.append("")
            
            # Add context information
            if context_data:
                persona_parts.append("**Context:**")
                for category, items in context_data.items():
                    if items:
                        persona_parts.append(f"- {category}: {', '.join(items)}")
                persona_parts.append("")
            
            # Add insights if available
            if response.get("insights"):
                persona_parts.append("**Key Insights:**")
                for insight in response["insights"]:
                    persona_parts.append(f"• {insight}")
            
            return "\n".join(persona_parts)
        
        else:
            # Fallback to insights if no results
            if response.get("insights"):
                summary_parts = []
                if user_identifier:
                    summary_parts.append(f"**Analysis for {user_identifier}:**")
                else:
                    summary_parts.append("**User Analysis:**")
                summary_parts.append("")
                
                for insight in response["insights"]:
                    summary_parts.append(f"• {insight}")
                
                return "\n".join(summary_parts)
            
            return "Unable to generate comprehensive persona and context analysis from available data."
    
    def _generate_general_analysis_summary(self, request: AnalysisRequest, response: Dict[str, Any]) -> str:
        """Generate general analysis summary."""
        summary_parts = [
            f"**Analysis Results for:** {request.query}",
            ""
        ]
        
        if response["sources_used"]:
            summary_parts.append(f"**Data Sources:** {', '.join(response['sources_used'])}")
        
        if response["results"]:
            summary_parts.append(f"**Records Analyzed:** {len(response['results'])}")
        
        if response.get("field_mappings"):
            summary_parts.append("**Field Mapping:** Completed successfully")
        
        if response.get("cross_resource_synthesis"):
            summary_parts.append("**Cross-Resource Analysis:** Performed")
        
        if response.get("visualizations"):
            summary_parts.append(f"**Visualizations:** {len(response['visualizations'])} suggestions generated")
        
        summary_parts.extend([
            "",
            "**Key Insights:**"
        ])
        
        for insight in response.get("insights", []):
            summary_parts.append(f"• {insight}")
        
        return "\n".join(summary_parts)
    
    def _extract_user_identifier(self, query: str) -> str:
        """Extract user identifier from query."""
        import re
        
        # Look for patterns like "student_id: 'STU-001'" or "customer CUST-001"
        patterns = [
            r"student_id[:\s]+['\"]?([A-Z0-9-]+)['\"]?",
            r"customer[_\s]+['\"]?([A-Z0-9-]+)['\"]?",
            r"user[_\s]+['\"]?([A-Z0-9-]+)['\"]?",
            r"id[:\s]+['\"]?([A-Z0-9-]+)['\"]?"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""
    
    def _extract_persona_from_results(self, results: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Extract persona information from results."""
        persona_data = {
            "Demographics": [],
            "Performance": [],
            "Interests & Goals": [],
            "Behavioral Patterns": []
        }
        
        for result in results[:3]:  # Analyze first 3 records
            flattened = self._flatten_data_for_analysis(result)
            
            for key, value in flattened.items():
                key_lower = key.lower()
                
                # Demographics
                if any(demo_key in key_lower for demo_key in ['age', 'gender', 'program', 'occupation', 'role', 'year_level']):
                    persona_data["Demographics"].append(f"{key.replace('_', ' ').replace('.', ' ').title()}: {value}")
                
                # Performance metrics
                elif any(perf_key in key_lower for perf_key in ['gpa', 'grade', 'score', 'rating', 'performance']):
                    if isinstance(value, (int, float)):
                        persona_data["Performance"].append(f"{key.replace('_', ' ').replace('.', ' ').title()}: {value}")
                
                # Interests and goals
                elif any(interest_key in key_lower for interest_key in ['interest', 'goal', 'aspiration', 'career']):
                    if isinstance(value, list):
                        persona_data["Interests & Goals"].extend([str(v) for v in value])
                    else:
                        persona_data["Interests & Goals"].append(str(value))
                
                # Behavioral patterns
                elif any(behavior_key in key_lower for behavior_key in ['status', 'frequency', 'usage', 'participation', 'residence']):
                    persona_data["Behavioral Patterns"].append(f"{key.replace('_', ' ').replace('.', ' ').title()}: {value}")
        
        # Remove duplicates and limit items
        for category in persona_data:
            persona_data[category] = list(set(persona_data[category]))[:5]
        
        return persona_data
    
    def _extract_context_from_results(self, results: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Extract context information from results."""
        context_data = {
            "Institutional": [],
            "Temporal": [],
            "Environmental": [],
            "Academic/Professional": []
        }
        
        for result in results[:3]:  # Analyze first 3 records
            flattened = self._flatten_data_for_analysis(result)
            
            for key, value in flattened.items():
                key_lower = key.lower()
                
                # Institutional context
                if any(inst_key in key_lower for inst_key in ['institution', 'university', 'company', 'organization']):
                    context_data["Institutional"].append(f"{key.replace('_', ' ').replace('.', ' ').title()}: {value}")
                
                # Temporal context
                elif any(time_key in key_lower for time_key in ['year', 'semester', 'period', 'date', 'academic_year']):
                    context_data["Temporal"].append(f"{key.replace('_', ' ').replace('.', ' ').title()}: {value}")
                
                # Environmental context
                elif any(env_key in key_lower for env_key in ['location', 'residence', 'environment', 'setting']):
                    context_data["Environmental"].append(f"{key.replace('_', ' ').replace('.', ' ').title()}: {value}")
                
                # Academic/Professional context
                elif any(acad_key in key_lower for acad_key in ['course', 'class', 'department', 'program', 'credit']):
                    context_data["Academic/Professional"].append(f"{key.replace('_', ' ').replace('.', ' ').title()}: {value}")
        
        # Remove duplicates and limit items
        for category in context_data:
            context_data[category] = list(set(context_data[category]))[:5]
        
        return context_data
    
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
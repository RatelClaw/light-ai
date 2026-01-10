"""
Natural Language Interface for AI-powered conversational data analysis.

Provides a comprehensive conversational AI interface using the Strands framework
for natural language data queries with advanced conversation context management,
query intent recognition, clarification question generation, and result explanation.

This implementation addresses Requirements 1.1, 1.5, 6.1, 6.2, 6.3, 6.4 from the
Intelligent Data Analyst specification.
"""

import asyncio
import time
import uuid
import re
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

from .master_agent import MasterDataAnalystAgent, AnalysisRequest, AnalysisResult
from .logging import get_activity_logger
from ..core.models import AccessLevel
from ..config import Config, get_config
from ..logger import get_logger

logger = get_logger(__name__)
activity_logger = get_activity_logger()


class QueryIntent(Enum):
    """Types of query intents for natural language processing."""
    DATA_EXPLORATION = "data_exploration"
    SPECIFIC_QUERY = "specific_query"
    COMPARISON = "comparison"
    TREND_ANALYSIS = "trend_analysis"
    AGGREGATION = "aggregation"
    FILTERING = "filtering"
    CLARIFICATION = "clarification"
    FOLLOW_UP = "follow_up"
    VISUALIZATION = "visualization"
    EXPLANATION = "explanation"


class ConversationState(Enum):
    """States of conversation flow."""
    INITIAL = "initial"
    ACTIVE = "active"
    CLARIFYING = "clarifying"
    REFINING = "refining"
    EXPLAINING = "explaining"
    COMPLETED = "completed"


@dataclass
class ConversationContext:
    """Enhanced context for managing conversation state and history."""
    conversation_id: str
    user_id: str
    client_id: str
    created_at: datetime
    last_activity: datetime
    state: ConversationState = ConversationState.INITIAL
    query_count: int = 0
    total_execution_time_ms: float = 0.0
    context_data: Dict[str, Any] = None
    
    # Enhanced conversation tracking
    query_history: List[Dict[str, Any]] = None
    result_history: List[Dict[str, Any]] = None
    clarification_requests: List[str] = None
    user_preferences: Dict[str, Any] = None
    referenced_resources: List[str] = None
    derived_fields: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context_data is None:
            self.context_data = {}
        if self.query_history is None:
            self.query_history = []
        if self.result_history is None:
            self.result_history = []
        if self.clarification_requests is None:
            self.clarification_requests = []
        if self.user_preferences is None:
            self.user_preferences = {}
        if self.referenced_resources is None:
            self.referenced_resources = []
        if self.derived_fields is None:
            self.derived_fields = {}


@dataclass
class QueryIntentAnalysis:
    """Analysis of query intent and context."""
    intent: QueryIntent
    confidence: float
    entities: List[str]
    temporal_references: List[str]
    comparison_elements: List[str]
    requires_clarification: bool
    clarification_questions: List[str]
    suggested_refinements: List[str]


@dataclass
class ClarificationRequest:
    """Request for clarification from the user."""
    question: str
    options: Optional[List[str]] = None
    context: Optional[str] = None
    priority: str = "medium"  # low, medium, high
    clarification_type: str = "general"  # general, field_mapping, data_source, calculation


@dataclass
class NLQueryRequest:
    """Natural language query request."""
    user_id: str
    client_id: str
    query: str
    conversation_id: Optional[str] = None
    desired_fields: Optional[Dict[str, str]] = None
    optional_fields: Optional[Dict[str, str]] = None
    derived_fields: Optional[Dict[str, str]] = None
    access_level: AccessLevel = AccessLevel.USER
    include_visualizations: bool = True
    context: Optional[Dict[str, Any]] = None


@dataclass
class NLQueryResponse:
    """Enhanced natural language query response with conversational features."""
    query_id: str
    conversation_id: str
    user_id: str
    client_id: str
    original_query: str
    analysis_summary: str
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
    explanation: Optional[str] = None
    
    # Enhanced conversational features
    intent_analysis: Optional[QueryIntentAnalysis] = None
    clarification_requests: Optional[List[ClarificationRequest]] = None
    conversation_state: ConversationState = ConversationState.ACTIVE
    context_used: Optional[Dict[str, Any]] = None
    refinement_suggestions: Optional[List[str]] = None
    comparative_analysis: Optional[Dict[str, Any]] = None


class NaturalLanguageInterface:
    """
    Enhanced AI-powered natural language interface for conversational data analysis.
    
    This implementation provides comprehensive conversational AI capabilities using
    the Strands framework, including:
    
    - Advanced query intent recognition and parsing
    - Multi-turn conversation context management
    - Intelligent clarification question generation
    - Detailed result explanation and methodology description
    - Cross-temporal and cross-categorical comparative analysis
    - Visualization suggestion and generation
    - User preference learning and adaptation
    
    Addresses Requirements:
    - 1.1: Natural language understanding and intent identification
    - 1.5: Reasoning explanation and source citation
    - 6.1: Context maintenance for follow-up questions
    - 6.2: Detailed explanations of results and methods
    - 6.3: Intelligent modification understanding and application
    - 6.4: Comparative analysis and visualization generation
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the enhanced natural language interface."""
        self.config = config or get_config()
        self.master_agent = MasterDataAnalystAgent(config)
        self.activity_logger = get_activity_logger()
        
        # Enhanced conversation management
        self.conversations: Dict[str, ConversationContext] = {}
        self.conversation_ttl = 3600  # 1 hour TTL for conversations
        
        # Intent recognition patterns
        self.intent_patterns = self._initialize_intent_patterns()
        
        # Clarification templates
        self.clarification_templates = self._initialize_clarification_templates()
        
        self.logger = logger
    
    def _initialize_intent_patterns(self) -> Dict[QueryIntent, List[str]]:
        """Initialize patterns for query intent recognition."""
        return {
            QueryIntent.DATA_EXPLORATION: [
                r"what.*data.*have", r"show.*available", r"list.*resources",
                r"explore.*data", r"overview.*data", r"summary.*data"
            ],
            QueryIntent.SPECIFIC_QUERY: [
                r"show.*where", r"find.*with", r"get.*records",
                r"select.*from", r"retrieve.*data"
            ],
            QueryIntent.COMPARISON: [
                r"compare.*with", r"versus", r"vs\.", r"difference.*between",
                r"higher.*than", r"lower.*than", r"better.*than"
            ],
            QueryIntent.TREND_ANALYSIS: [
                r"trend.*over", r"change.*time", r"growth.*rate",
                r"increase.*decrease", r"pattern.*time", r"historical"
            ],
            QueryIntent.AGGREGATION: [
                r"total.*", r"sum.*", r"average.*", r"count.*",
                r"maximum.*", r"minimum.*", r"group.*by"
            ],
            QueryIntent.FILTERING: [
                r"filter.*by", r"where.*equals", r"only.*show",
                r"exclude.*", r"include.*only"
            ],
            QueryIntent.CLARIFICATION: [
                r"what.*mean", r"explain.*", r"clarify.*",
                r"don't.*understand", r"confused.*about"
            ],
            QueryIntent.FOLLOW_UP: [
                r"also.*show", r"additionally.*", r"furthermore.*",
                r"what.*about", r"how.*about", r"can.*also"
            ],
            QueryIntent.VISUALIZATION: [
                r"chart.*", r"graph.*", r"plot.*", r"visualize.*",
                r"show.*chart", r"create.*graph"
            ],
            QueryIntent.EXPLANATION: [
                r"why.*", r"how.*calculated", r"methodology.*",
                r"explain.*result", r"reasoning.*behind"
            ]
        }
    
    def _initialize_clarification_templates(self) -> Dict[str, List[str]]:
        """Initialize templates for clarification questions."""
        return {
            "field_mapping": [
                "I found several fields that might match '{field}'. Which one did you mean?",
                "Could you clarify which field you're referring to when you say '{field}'?",
                "I see multiple possible interpretations for '{field}'. Please specify:"
            ],
            "data_source": [
                "Which data source would you like me to focus on for this analysis?",
                "I found data in multiple sources. Should I combine them or focus on one?",
                "Would you like me to analyze data from all sources or specific ones?"
            ],
            "time_range": [
                "What time period are you interested in for this analysis?",
                "Should I look at recent data or a specific date range?",
                "Would you like to see trends over time or a snapshot?"
            ],
            "calculation": [
                "How would you like me to calculate '{calculation}'?",
                "What formula should I use for '{calculation}'?",
                "Should I include or exclude certain values in this calculation?"
            ],
            "ambiguous_query": [
                "Could you provide more details about what you're looking for?",
                "I need a bit more context to give you the best answer. Could you clarify?",
                "Your question could be interpreted in several ways. Which did you mean?"
            ]
        }
    
    def analyze_query_intent(self, query: str, context: ConversationContext) -> QueryIntentAnalysis:
        """
        Analyze query intent and extract relevant information.
        
        Args:
            query: Natural language query
            context: Conversation context
            
        Returns:
            QueryIntentAnalysis with intent classification and extracted information
        """
        query_lower = query.lower()
        
        # Determine primary intent
        intent_scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    score += 1
            intent_scores[intent] = score
        
        # Get highest scoring intent
        primary_intent = max(intent_scores, key=intent_scores.get)
        confidence = intent_scores[primary_intent] / max(len(self.intent_patterns[primary_intent]), 1)
        
        # If no clear intent and we have conversation history, likely a follow-up
        if confidence == 0 and len(context.query_history) > 0:
            primary_intent = QueryIntent.FOLLOW_UP
            confidence = 0.7
        
        # Extract entities (simplified implementation)
        entities = self._extract_entities(query)
        
        # Extract temporal references
        temporal_refs = self._extract_temporal_references(query)
        
        # Extract comparison elements
        comparison_elements = self._extract_comparison_elements(query)
        
        # Determine if clarification is needed
        requires_clarification = self._requires_clarification(query, context)
        
        # Generate clarification questions if needed
        clarification_questions = []
        if requires_clarification:
            clarification_questions = self._generate_clarification_questions(query, context)
        
        # Generate refinement suggestions
        refinements = self._generate_refinement_suggestions(query, context)
        
        return QueryIntentAnalysis(
            intent=primary_intent,
            confidence=confidence,
            entities=entities,
            temporal_references=temporal_refs,
            comparison_elements=comparison_elements,
            requires_clarification=requires_clarification,
            clarification_questions=clarification_questions,
            suggested_refinements=refinements
        )
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract entities from query (simplified implementation)."""
        entities = []
        
        # Common business entities
        entity_patterns = [
            r'\b(customer|client|user)s?\b',
            r'\b(product|item|service)s?\b',
            r'\b(order|purchase|transaction)s?\b',
            r'\b(employee|staff|worker)s?\b',
            r'\b(sale|revenue|income)s?\b',
            r'\b(date|time|period)\b',
            r'\b(amount|price|cost|value)s?\b'
        ]
        
        for pattern in entity_patterns:
            matches = re.findall(pattern, query.lower())
            entities.extend(matches)
        
        return list(set(entities))
    
    def _extract_temporal_references(self, query: str) -> List[str]:
        """Extract temporal references from query."""
        temporal_patterns = [
            r'\b(today|yesterday|tomorrow)\b',
            r'\b(last|this|next)\s+(week|month|year|quarter)\b',
            r'\b\d{4}(-\d{2})?(-\d{2})?\b',  # Date patterns
            r'\b(recent|latest|current|historical)\b',
            r'\b(over\s+time|trends?|growth|decline)\b'
        ]
        
        temporal_refs = []
        for pattern in temporal_patterns:
            matches = re.findall(pattern, query.lower())
            temporal_refs.extend([match if isinstance(match, str) else ' '.join(match) for match in matches])
        
        return list(set(temporal_refs))
    
    def _extract_comparison_elements(self, query: str) -> List[str]:
        """Extract comparison elements from query."""
        comparison_patterns = [
            r'\b(compare|versus|vs\.?|against)\s+(\w+)',
            r'\b(higher|lower|greater|less)\s+than\s+(\w+)',
            r'\b(better|worse)\s+than\s+(\w+)',
            r'\b(before|after)\s+(\w+)'
        ]
        
        comparisons = []
        for pattern in comparison_patterns:
            matches = re.findall(pattern, query.lower())
            comparisons.extend([match[1] if isinstance(match, tuple) else match for match in matches])
        
        return list(set(comparisons))
    
    def _requires_clarification(self, query: str, context: ConversationContext) -> bool:
        """Determine if query requires clarification."""
        # Check for ambiguous terms
        ambiguous_terms = ['it', 'that', 'this', 'them', 'those', 'these']
        query_words = query.lower().split()
        
        # If query contains ambiguous pronouns and no clear context
        if any(term in query_words for term in ambiguous_terms) and len(context.query_history) == 0:
            return True
        
        # If query is very short and vague
        if len(query_words) < 3 and not any(word in query.lower() for word in ['show', 'list', 'get', 'find']):
            return True
        
        # If query contains multiple possible interpretations
        if len(self._extract_entities(query)) > 3:
            return True
        
        return False
    
    def _generate_clarification_questions(self, query: str, context: ConversationContext) -> List[str]:
        """Generate clarification questions for ambiguous queries."""
        questions = []
        
        # Check for ambiguous field references
        entities = self._extract_entities(query)
        if len(entities) > 2:
            questions.append(f"I see you mentioned {', '.join(entities)}. Which one is most important for your analysis?")
        
        # Check for vague queries
        if len(query.split()) < 4:
            questions.extend(self.clarification_templates["ambiguous_query"])
        
        # Check for temporal ambiguity
        temporal_refs = self._extract_temporal_references(query)
        if not temporal_refs and any(word in query.lower() for word in ['trend', 'change', 'growth']):
            questions.extend(self.clarification_templates["time_range"])
        
        return questions[:3]  # Limit to 3 questions
    
    def _generate_refinement_suggestions(self, query: str, context: ConversationContext) -> List[str]:
        """Generate suggestions for query refinement."""
        suggestions = []
        
        # Suggest more specific queries
        if len(query.split()) < 5:
            suggestions.append("Try being more specific about what data you want to see")
        
        # Suggest time-based analysis
        if not self._extract_temporal_references(query):
            suggestions.append("Consider adding a time dimension to your analysis")
        
        # Suggest comparisons based on context
        if len(context.query_history) > 0:
            suggestions.append("Would you like to compare this with your previous query?")
        
        # Suggest visualizations
        if not any(word in query.lower() for word in ['chart', 'graph', 'plot', 'visualize']):
            suggestions.append("Would you like to see this data visualized?")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    async def process_query(self, request: NLQueryRequest) -> NLQueryResponse:
        """
        Process a natural language query with enhanced conversational AI intelligence.
        
        This method implements Requirements 1.1, 1.5, 6.1, 6.2, 6.3, 6.4 by providing:
        - Intent recognition and parsing (1.1)
        - Reasoning explanation and source citation (1.5)
        - Context maintenance for follow-up questions (6.1)
        - Detailed explanations of results and methods (6.2)
        - Intelligent modification understanding (6.3)
        - Comparative analysis and visualization generation (6.4)
        
        Args:
            request: Natural language query request
            
        Returns:
            Enhanced query response with conversational features
        """
        start_time = time.time()
        
        try:
            # Get or create conversation context
            conversation_id = request.conversation_id or str(uuid.uuid4())
            context = self._get_or_create_conversation(conversation_id, request.user_id, request.client_id)
            
            self.logger.info(f"Processing enhanced NL query for user {request.user_id}: {request.query}")
            
            # Analyze query intent (Requirement 1.1)
            intent_analysis = self.analyze_query_intent(request.query, context)
            
            # Log query start with intent information
            activity_logger.log_agent_query(
                "natural_language_interface", request.user_id, request.client_id,
                request.query, conversation_id,
                {
                    "access_level": request.access_level.value,
                    "intent": intent_analysis.intent.value,
                    "confidence": intent_analysis.confidence
                }
            )
            
            # Handle clarification requests if needed
            if intent_analysis.requires_clarification and context.state != ConversationState.CLARIFYING:
                return await self._handle_clarification_request(
                    request, context, intent_analysis, start_time
                )
            
            # Update conversation state
            context.state = ConversationState.ACTIVE
            
            # Build enhanced analysis request with conversation context
            analysis_request = AnalysisRequest(
                user_id=request.user_id,
                client_id=request.client_id,
                query=request.query,
                desired_fields=request.desired_fields,
                optional_fields=request.optional_fields,
                derived_fields=request.derived_fields,
                context=self._build_enhanced_context_for_agent(context, request.context, intent_analysis),
                conversation_id=conversation_id,
                access_level=request.access_level,
                include_visualizations=request.include_visualizations
            )
            
            # Execute analysis using master agent
            analysis_result = await self.master_agent.analyze_data(analysis_request)
            
            # Update conversation context with new interaction
            self._update_enhanced_conversation_context(context, request, analysis_result, intent_analysis)
            
            # Generate enhanced explanation (Requirement 1.5, 6.2)
            explanation = await self._generate_enhanced_explanation(request, analysis_result, intent_analysis)
            
            # Generate comparative analysis if applicable (Requirement 6.4)
            comparative_analysis = None
            if intent_analysis.intent == QueryIntent.COMPARISON or len(intent_analysis.comparison_elements) > 0:
                comparative_analysis = await self._generate_comparative_analysis(
                    request, analysis_result, context
                )
            
            # Generate refinement suggestions (Requirement 6.3)
            refinement_suggestions = self._generate_contextual_refinements(
                request, analysis_result, context, intent_analysis
            )
            
            # Build comprehensive response
            execution_time = (time.time() - start_time) * 1000
            
            response = NLQueryResponse(
                query_id=analysis_result.query_id,
                conversation_id=conversation_id,
                user_id=request.user_id,
                client_id=request.client_id,
                original_query=request.query,
                analysis_summary=self._generate_enhanced_analysis_summary(analysis_result, intent_analysis),
                results=analysis_result.results,
                insights=analysis_result.insights,
                methodology=analysis_result.methodology,
                sources_used=analysis_result.sources_used,
                confidence_score=analysis_result.confidence_score,
                execution_time_ms=execution_time,
                follow_up_suggestions=self._generate_enhanced_follow_up_suggestions(
                    analysis_result, context, intent_analysis
                ),
                visualizations=analysis_result.visualizations,
                field_mappings=analysis_result.field_mappings,
                cross_resource_synthesis=analysis_result.cross_resource_synthesis,
                explanation=explanation,
                
                # Enhanced conversational features
                intent_analysis=intent_analysis,
                clarification_requests=None,  # No clarification needed at this point
                conversation_state=context.state,
                context_used=self._summarize_context_usage(context),
                refinement_suggestions=refinement_suggestions,
                comparative_analysis=comparative_analysis
            )
            
            # Log successful completion
            activity_logger.log_agent_response(
                "natural_language_interface", request.user_id, request.client_id,
                f"Enhanced query processed with intent {intent_analysis.intent.value}",
                execution_time, "natural_language_interface",
                conversation_id, None,
                {
                    "query_id": analysis_result.query_id,
                    "confidence": analysis_result.confidence_score,
                    "intent": intent_analysis.intent.value,
                    "context_queries": len(context.query_history)
                }
            )
            
            self.logger.info(f"Enhanced NL query processed in {execution_time:.2f}ms with intent {intent_analysis.intent.value}")
            return response
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Enhanced natural language query processing failed: {str(e)}"
            self.logger.error(error_msg)
            
            # Log error
            activity_logger.log_agent_error(
                "natural_language_interface", request.user_id, request.client_id,
                error_msg, conversation_id
            )
            
            # Return enhanced error response
            return NLQueryResponse(
                query_id=f"error_{int(time.time())}",
                conversation_id=conversation_id,
                user_id=request.user_id,
                client_id=request.client_id,
                original_query=request.query,
                analysis_summary=f"Query processing failed: {str(e)}",
                results=[],
                insights=[f"Error: {str(e)}"],
                methodology="Error occurred during processing",
                sources_used=[],
                confidence_score=0.0,
                execution_time_ms=execution_time,
                follow_up_suggestions=[
                    "Please try rephrasing your question more specifically",
                    "Check if you have access to the required data",
                    "Try breaking down your query into simpler parts"
                ],
                explanation="An error occurred while processing your query. Please try again with a different approach.",
                conversation_state=ConversationState.ACTIVE,
                intent_analysis=QueryIntentAnalysis(
                    intent=QueryIntent.CLARIFICATION,
                    confidence=0.0,
                    entities=[],
                    temporal_references=[],
                    comparison_elements=[],
                    requires_clarification=True,
                    clarification_questions=["Could you rephrase your question?"],
                    suggested_refinements=["Try being more specific about what you're looking for"]
                )
            )
    
    async def _handle_clarification_request(self, request: NLQueryRequest, 
                                          context: ConversationContext,
                                          intent_analysis: QueryIntentAnalysis,
                                          start_time: float) -> NLQueryResponse:
        """Handle requests that require clarification."""
        context.state = ConversationState.CLARIFYING
        
        # Generate clarification requests
        clarification_requests = []
        for question in intent_analysis.clarification_questions:
            clarification_requests.append(ClarificationRequest(
                question=question,
                context="Query requires more specific information",
                priority="high",
                clarification_type="general"
            ))
        
        execution_time = (time.time() - start_time) * 1000
        
        return NLQueryResponse(
            query_id=f"clarification_{int(time.time())}",
            conversation_id=context.conversation_id,
            user_id=request.user_id,
            client_id=request.client_id,
            original_query=request.query,
            analysis_summary="Your query needs clarification to provide the best results.",
            results=[],
            insights=["Please provide more specific information to help me understand your request better."],
            methodology="Clarification request generation",
            sources_used=[],
            confidence_score=0.5,
            execution_time_ms=execution_time,
            follow_up_suggestions=intent_analysis.suggested_refinements,
            explanation="I need more information to provide accurate results for your query.",
            intent_analysis=intent_analysis,
            clarification_requests=clarification_requests,
            conversation_state=ConversationState.CLARIFYING,
            refinement_suggestions=intent_analysis.suggested_refinements
        )
    
    def _build_enhanced_context_for_agent(self, conversation: ConversationContext, 
                                        additional_context: Optional[Dict[str, Any]],
                                        intent_analysis: QueryIntentAnalysis) -> Dict[str, Any]:
        """Build enhanced context for the master agent with conversation history."""
        context = {
            "conversation_id": conversation.conversation_id,
            "query_count": conversation.query_count,
            "conversation_age_minutes": (datetime.utcnow() - conversation.created_at).total_seconds() / 60,
            "conversation_state": conversation.state.value,
            
            # Intent information
            "query_intent": intent_analysis.intent.value,
            "intent_confidence": intent_analysis.confidence,
            "extracted_entities": intent_analysis.entities,
            "temporal_references": intent_analysis.temporal_references,
            "comparison_elements": intent_analysis.comparison_elements,
            
            # Conversation history (last 3 interactions for context)
            "recent_queries": [q["query"] for q in conversation.query_history[-3:]],
            "recent_results_summary": [r.get("summary", "") for r in conversation.result_history[-3:]],
            
            # Referenced resources and derived fields
            "referenced_resources": conversation.referenced_resources,
            "derived_fields": conversation.derived_fields,
            
            # User preferences
            "user_preferences": conversation.user_preferences
        }
        
        # Add conversation-specific context data
        if conversation.context_data:
            context.update(conversation.context_data)
        
        # Add additional context
        if additional_context:
            context.update(additional_context)
        
        return context
    
    def _update_enhanced_conversation_context(self, context: ConversationContext, 
                                            request: NLQueryRequest, 
                                            result: AnalysisResult,
                                            intent_analysis: QueryIntentAnalysis) -> None:
        """Update conversation context with enhanced tracking."""
        context.query_count += 1
        context.total_execution_time_ms += result.execution_time_ms
        context.last_activity = datetime.utcnow()
        
        # Add to query history
        context.query_history.append({
            "query": request.query,
            "query_id": result.query_id,
            "intent": intent_analysis.intent.value,
            "confidence": intent_analysis.confidence,
            "timestamp": datetime.utcnow().isoformat(),
            "entities": intent_analysis.entities
        })
        
        # Add to result history
        context.result_history.append({
            "query_id": result.query_id,
            "summary": self._generate_enhanced_analysis_summary(result, intent_analysis),
            "sources_used": result.sources_used,
            "row_count": len(result.results),
            "confidence": result.confidence_score,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Update referenced resources
        if result.sources_used:
            context.referenced_resources.extend(result.sources_used)
            context.referenced_resources = list(set(context.referenced_resources))  # Remove duplicates
        
        # Update derived fields
        if result.field_mappings:
            context.derived_fields.update(result.field_mappings)
        
        # Store relevant information for future queries
        context.context_data["recent_sources"] = result.sources_used
        context.context_data["recent_field_mappings"] = result.field_mappings
        context.context_data["last_intent"] = intent_analysis.intent.value
        
        # Limit history size to prevent memory issues
        if len(context.query_history) > 10:
            context.query_history = context.query_history[-10:]
        if len(context.result_history) > 10:
            context.result_history = context.result_history[-10:]
    
    async def _generate_enhanced_explanation(self, request: NLQueryRequest, 
                                           result: AnalysisResult,
                                           intent_analysis: QueryIntentAnalysis) -> str:
        """Generate enhanced explanation with intent and methodology details."""
        try:
            explanation_parts = [
                f"Analysis Process for: '{request.query}'",
                f"Detected Intent: {intent_analysis.intent.value.replace('_', ' ').title()}",
                f"Confidence Level: {intent_analysis.confidence:.2f}",
                ""
            ]
            
            # Add intent-specific explanation
            if intent_analysis.intent == QueryIntent.COMPARISON:
                explanation_parts.append("Comparison Analysis Steps:")
                explanation_parts.extend([
                    "1. Identified comparison elements in your query",
                    "2. Located relevant data sources for comparison",
                    "3. Aligned data schemas for meaningful comparison",
                    "4. Generated comparative insights"
                ])
            elif intent_analysis.intent == QueryIntent.TREND_ANALYSIS:
                explanation_parts.append("Trend Analysis Steps:")
                explanation_parts.extend([
                    "1. Identified temporal elements in your query",
                    "2. Organized data chronologically",
                    "3. Calculated trend metrics and patterns",
                    "4. Generated trend insights and projections"
                ])
            else:
                explanation_parts.append("Analysis Steps:")
                explanation_parts.extend([
                    "1. Resource Discovery: Identified relevant data sources",
                    f"2. Data Analysis: Processed {len(result.results)} records",
                    "3. Insight Generation: Extracted key patterns and findings"
                ])
            
            # Add field mapping information
            if result.field_mappings:
                explanation_parts.append("4. Field Mapping: Mapped requested fields to available data")
            
            # Add cross-resource synthesis information
            if result.cross_resource_synthesis:
                explanation_parts.append("5. Cross-Resource Synthesis: Combined data from multiple sources")
            
            # Add visualization information
            if result.visualizations:
                explanation_parts.append("6. Visualization Generation: Created visual representation suggestions")
            
            # Add extracted entities and temporal references
            if intent_analysis.entities:
                explanation_parts.extend([
                    "",
                    f"Entities Identified: {', '.join(intent_analysis.entities)}"
                ])
            
            if intent_analysis.temporal_references:
                explanation_parts.extend([
                    f"Temporal References: {', '.join(intent_analysis.temporal_references)}"
                ])
            
            # Add data source and confidence information
            explanation_parts.extend([
                "",
                f"Data Sources Used: {', '.join(result.sources_used) if result.sources_used else 'None'}",
                f"Analysis Confidence: {result.confidence_score:.2f}",
                f"Execution Time: {result.execution_time_ms:.0f}ms"
            ])
            
            return "\n".join(explanation_parts)
            
        except Exception as e:
            self.logger.warning(f"Failed to generate enhanced explanation: {e}")
            return f"Analysis completed using AI-powered data processing with {intent_analysis.intent.value} intent."
    
    async def _generate_comparative_analysis(self, request: NLQueryRequest,
                                           result: AnalysisResult,
                                           context: ConversationContext) -> Optional[Dict[str, Any]]:
        """Generate comparative analysis when comparison intent is detected."""
        if len(context.result_history) == 0:
            return None
        
        try:
            # Compare with most recent result
            previous_result = context.result_history[-1]
            
            comparative_analysis = {
                "comparison_type": "temporal",
                "current_query": request.query,
                "previous_query": context.query_history[-1]["query"] if context.query_history else "",
                "current_results_count": len(result.results),
                "previous_results_count": previous_result.get("row_count", 0),
                "confidence_comparison": {
                    "current": result.confidence_score,
                    "previous": previous_result.get("confidence", 0.0),
                    "improvement": result.confidence_score - previous_result.get("confidence", 0.0)
                },
                "sources_comparison": {
                    "current_sources": result.sources_used,
                    "previous_sources": previous_result.get("sources_used", []),
                    "common_sources": list(set(result.sources_used) & set(previous_result.get("sources_used", []))),
                    "new_sources": list(set(result.sources_used) - set(previous_result.get("sources_used", [])))
                },
                "insights": [
                    f"Current analysis returned {len(result.results)} results vs {previous_result.get('row_count', 0)} previously",
                    f"Confidence improved by {result.confidence_score - previous_result.get('confidence', 0.0):.2f}" if result.confidence_score > previous_result.get('confidence', 0.0) else f"Confidence decreased by {previous_result.get('confidence', 0.0) - result.confidence_score:.2f}"
                ]
            }
            
            return comparative_analysis
            
        except Exception as e:
            self.logger.warning(f"Failed to generate comparative analysis: {e}")
            return None
    
    def _generate_contextual_refinements(self, request: NLQueryRequest,
                                       result: AnalysisResult,
                                       context: ConversationContext,
                                       intent_analysis: QueryIntentAnalysis) -> List[str]:
        """Generate contextual refinement suggestions based on results and history."""
        refinements = []
        
        # Based on result quality
        if result.confidence_score < 0.7:
            refinements.append("Try being more specific about the data you're looking for")
        
        if len(result.results) == 0:
            refinements.append("Consider broadening your search criteria or checking different data sources")
        elif len(result.results) > 100:
            refinements.append("Consider adding filters to narrow down the results")
        
        # Based on intent
        if intent_analysis.intent == QueryIntent.DATA_EXPLORATION:
            refinements.append("Try asking specific questions about the data you found")
        elif intent_analysis.intent == QueryIntent.SPECIFIC_QUERY:
            refinements.append("Consider asking for trends or comparisons in this data")
        
        # Based on conversation history
        if len(context.query_history) > 0:
            refinements.append("Would you like to combine this analysis with your previous query?")
        
        # Based on available sources
        if len(result.sources_used) > 1:
            refinements.append("Would you like to focus on data from a specific source?")
        
        return refinements[:4]  # Limit to 4 suggestions
    
    def _generate_enhanced_follow_up_suggestions(self, result: AnalysisResult,
                                               context: ConversationContext,
                                               intent_analysis: QueryIntentAnalysis) -> List[str]:
        """Generate enhanced follow-up suggestions based on intent and context."""
        suggestions = []
        
        # Intent-based suggestions
        if intent_analysis.intent == QueryIntent.DATA_EXPLORATION:
            suggestions.extend([
                "Would you like to see trends in this data over time?",
                "Should I look for correlations between different fields?",
                "Would you like to see a breakdown by category?"
            ])
        elif intent_analysis.intent == QueryIntent.SPECIFIC_QUERY:
            suggestions.extend([
                "Would you like to see similar data from other sources?",
                "Should I analyze trends in these results?",
                "Would you like to filter these results further?"
            ])
        elif intent_analysis.intent == QueryIntent.AGGREGATION:
            suggestions.extend([
                "Would you like to see this data broken down by time period?",
                "Should I compare these aggregations across different categories?",
                "Would you like to see the detailed records behind these numbers?"
            ])
        elif intent_analysis.intent == QueryIntent.TREND_ANALYSIS:
            suggestions.extend([
                "Would you like to see projections based on these trends?",
                "Should I identify factors that might influence these trends?",
                "Would you like to compare these trends with other metrics?"
            ])
        
        # Context-based suggestions
        if len(context.query_history) > 0:
            suggestions.append("Would you like to compare this with your previous analysis?")
        
        # Result-based suggestions
        if result.visualizations:
            suggestions.append("Would you like me to create a specific type of visualization?")
        
        if len(result.sources_used) > 1:
            suggestions.append("Should I focus on data from a specific source?")
        
        # Default suggestions
        if not suggestions:
            suggestions.extend([
                "Would you like me to analyze trends over time?",
                "Should I look for correlations with other data?",
                "Would you like a detailed breakdown by category?"
            ])
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def _generate_enhanced_analysis_summary(self, result: AnalysisResult, 
                                          intent_analysis: QueryIntentAnalysis) -> str:
        """Generate enhanced analysis summary with intent information."""
        summary_parts = []
        
        # Intent-based summary prefix
        intent_descriptions = {
            QueryIntent.DATA_EXPLORATION: "Explored available data and found",
            QueryIntent.SPECIFIC_QUERY: "Retrieved specific data showing",
            QueryIntent.COMPARISON: "Compared data and identified",
            QueryIntent.TREND_ANALYSIS: "Analyzed trends and discovered",
            QueryIntent.AGGREGATION: "Aggregated data and calculated",
            QueryIntent.FILTERING: "Filtered data and returned",
            QueryIntent.VISUALIZATION: "Prepared data for visualization with",
            QueryIntent.FOLLOW_UP: "Built upon previous analysis and found"
        }
        
        prefix = intent_descriptions.get(intent_analysis.intent, "Analyzed data and found")
        summary_parts.append(prefix)
        
        # Add result details
        if result.results:
            summary_parts.append(f"{len(result.results)} records")
        
        if result.sources_used:
            summary_parts.append(f"from {len(result.sources_used)} data sources")
        
        if result.insights:
            summary_parts.append(f"with {len(result.insights)} key insights")
        
        # Add confidence indicator
        if result.confidence_score >= 0.8:
            summary_parts.append("(high confidence)")
        elif result.confidence_score >= 0.6:
            summary_parts.append("(medium confidence)")
        else:
            summary_parts.append("(requires verification)")
        
        if not summary_parts or len(summary_parts) == 1:
            return "Analysis completed - ready for follow-up questions"
        
        return " ".join(summary_parts) + "."
    
    def _summarize_context_usage(self, context: ConversationContext) -> Dict[str, Any]:
        """Summarize how conversation context was used."""
        return {
            "queries_in_context": len(context.query_history),
            "resources_referenced": len(context.referenced_resources),
            "conversation_age_minutes": (datetime.utcnow() - context.created_at).total_seconds() / 60,
            "state": context.state.value,
            "derived_fields_count": len(context.derived_fields)
        }
    
    async def continue_conversation(self, request: NLQueryRequest) -> NLQueryResponse:
        """
        Continue a conversation with follow-up questions maintaining full context.
        
        This method implements Requirement 6.1 by maintaining context from previous
        queries and building upon earlier analysis.
        
        Args:
            request: Follow-up query request with conversation context
            
        Returns:
            Query response building on previous context
        """
        # Ensure we have a conversation ID for context continuity
        if not request.conversation_id:
            raise ValueError("Conversation ID required for follow-up questions")
        
        # This uses the enhanced processing with full conversation context
        return await self.process_query(request)
    
    async def explain_result(self, user_id: str, client_id: str, 
                           query_id: str, conversation_id: Optional[str] = None) -> str:
        """
        Provide detailed explanation of analysis methods and results.
        
        This method implements Requirement 6.2 by providing detailed explanations
        of results and methods used in the analysis.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            query_id: ID of the query to explain
            conversation_id: Optional conversation identifier
            
        Returns:
            Detailed explanation of methodology and results
        """
        try:
            # Look up the query in conversation history if available
            explanation_context = {}
            if conversation_id and conversation_id in self.conversations:
                context = self.conversations[conversation_id]
                
                # Find the specific query in history
                for query_record in context.query_history:
                    if query_record.get("query_id") == query_id:
                        explanation_context = {
                            "original_query": query_record.get("query", ""),
                            "intent": query_record.get("intent", "unknown"),
                            "confidence": query_record.get("confidence", 0.0),
                            "entities": query_record.get("entities", [])
                        }
                        break
                
                # Find corresponding result
                for result_record in context.result_history:
                    if result_record.get("query_id") == query_id:
                        explanation_context.update({
                            "sources_used": result_record.get("sources_used", []),
                            "row_count": result_record.get("row_count", 0),
                            "result_confidence": result_record.get("confidence", 0.0)
                        })
                        break
            
            # Generate detailed explanation using master agent
            explanation = await self.master_agent.explain_methodology(query_id)
            
            # Enhance with context information if available
            if explanation_context:
                enhanced_explanation = f"""
Detailed Analysis Explanation for Query ID: {query_id}

Original Query: "{explanation_context.get('original_query', 'Unknown')}"
Detected Intent: {explanation_context.get('intent', 'Unknown').replace('_', ' ').title()}
Query Confidence: {explanation_context.get('confidence', 0.0):.2f}

{explanation}

Additional Context:
- Data Sources: {', '.join(explanation_context.get('sources_used', []))}
- Records Analyzed: {explanation_context.get('row_count', 0)}
- Result Confidence: {explanation_context.get('result_confidence', 0.0):.2f}
- Entities Identified: {', '.join(explanation_context.get('entities', []))}
"""
                return enhanced_explanation.strip()
            
            self.logger.info(f"Generated explanation for query {query_id}")
            return explanation
            
        except Exception as e:
            self.logger.error(f"Failed to generate explanation for query {query_id}: {e}")
            return f"Unable to generate detailed explanation: {str(e)}"
    
    async def request_clarification(self, user_id: str, client_id: str,
                                  conversation_id: str, 
                                  clarification_response: str) -> NLQueryResponse:
        """
        Handle clarification responses from users.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            conversation_id: Conversation identifier
            clarification_response: User's response to clarification request
            
        Returns:
            Updated query response based on clarification
        """
        try:
            if conversation_id not in self.conversations:
                raise ValueError("Conversation not found")
            
            context = self.conversations[conversation_id]
            
            # Update conversation state
            context.state = ConversationState.ACTIVE
            context.clarification_requests.append(clarification_response)
            
            # Get the original query that needed clarification
            if not context.query_history:
                raise ValueError("No original query found for clarification")
            
            original_query = context.query_history[-1]["query"]
            
            # Create enhanced query with clarification
            enhanced_query = f"{original_query} (Clarification: {clarification_response})"
            
            # Process the clarified query
            request = NLQueryRequest(
                user_id=user_id,
                client_id=client_id,
                query=enhanced_query,
                conversation_id=conversation_id
            )
            
            return await self.process_query(request)
            
        except Exception as e:
            self.logger.error(f"Failed to handle clarification: {e}")
            raise
    
    def get_conversation_history(self, conversation_id: str) -> Optional[ConversationContext]:
        """Get enhanced conversation history for a specific conversation."""
        return self.conversations.get(conversation_id)
    
    def clear_conversation_history(self, conversation_id: str) -> bool:
        """Clear conversation history for a specific conversation."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            self.logger.info(f"Cleared enhanced conversation history for {conversation_id}")
            return True
        return False
    
    def _get_or_create_conversation(self, conversation_id: str, user_id: str, client_id: str) -> ConversationContext:
        """Get existing conversation or create a new enhanced one."""
        # Clean up expired conversations
        self._cleanup_expired_conversations()
        
        if conversation_id in self.conversations:
            context = self.conversations[conversation_id]
            context.last_activity = datetime.utcnow()
            return context
        
        # Create new enhanced conversation
        context = ConversationContext(
            conversation_id=conversation_id,
            user_id=user_id,
            client_id=client_id,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            state=ConversationState.INITIAL
        )
        
        self.conversations[conversation_id] = context
        return context
    
    def _cleanup_expired_conversations(self) -> None:
        """Clean up expired conversations."""
        current_time = datetime.utcnow()
        expired_conversations = []
        
        for conv_id, context in self.conversations.items():
            time_since_activity = (current_time - context.last_activity).total_seconds()
            if time_since_activity > self.conversation_ttl:
                expired_conversations.append(conv_id)
        
        for conv_id in expired_conversations:
            del self.conversations[conv_id]
            self.logger.debug(f"Cleaned up expired conversation: {conv_id}")
    
    def _build_context_for_agent(self, conversation: ConversationContext, 
                                additional_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build context for the master agent (legacy method for compatibility)."""
        return self._build_enhanced_context_for_agent(
            conversation, additional_context, 
            QueryIntentAnalysis(
                intent=QueryIntent.SPECIFIC_QUERY,
                confidence=0.5,
                entities=[],
                temporal_references=[],
                comparison_elements=[],
                requires_clarification=False,
                clarification_questions=[],
                suggested_refinements=[]
            )
        )
    
    def _update_conversation_context(self, context: ConversationContext, 
                                   request: NLQueryRequest, result: AnalysisResult) -> None:
        """Update conversation context (legacy method for compatibility)."""
        # Create a basic intent analysis for legacy compatibility
        intent_analysis = QueryIntentAnalysis(
            intent=QueryIntent.SPECIFIC_QUERY,
            confidence=0.5,
            entities=[],
            temporal_references=[],
            comparison_elements=[],
            requires_clarification=False,
            clarification_questions=[],
            suggested_refinements=[]
        )
        
        self._update_enhanced_conversation_context(context, request, result, intent_analysis)
    
    async def _generate_explanation(self, request: NLQueryRequest, result: AnalysisResult) -> str:
        """Generate explanation (legacy method for compatibility)."""
        # Create a basic intent analysis for legacy compatibility
        intent_analysis = QueryIntentAnalysis(
            intent=QueryIntent.SPECIFIC_QUERY,
            confidence=0.5,
            entities=[],
            temporal_references=[],
            comparison_elements=[],
            requires_clarification=False,
            clarification_questions=[],
            suggested_refinements=[]
        )
        
        return await self._generate_enhanced_explanation(request, result, intent_analysis)
    
    def _generate_analysis_summary(self, result: AnalysisResult) -> str:
        """Generate analysis summary (legacy method for compatibility)."""
        # Create a basic intent analysis for legacy compatibility
        intent_analysis = QueryIntentAnalysis(
            intent=QueryIntent.SPECIFIC_QUERY,
            confidence=0.5,
            entities=[],
            temporal_references=[],
            comparison_elements=[],
            requires_clarification=False,
            clarification_questions=[],
            suggested_refinements=[]
        )
        
        return self._generate_enhanced_analysis_summary(result, intent_analysis)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check of the enhanced natural language interface.
        
        Returns:
            Health status information including conversational features
        """
        try:
            # Test master agent
            agent_health = await self.master_agent.health_check()
            
            # Calculate conversation statistics
            active_conversations = len(self.conversations)
            total_queries = sum(len(c.query_history) for c in self.conversations.values())
            avg_queries_per_conversation = total_queries / max(active_conversations, 1)
            
            # Calculate state distribution
            state_distribution = {}
            for context in self.conversations.values():
                state = context.state.value
                state_distribution[state] = state_distribution.get(state, 0) + 1
            
            return {
                "status": "healthy",
                "active_conversations": active_conversations,
                "conversation_ttl_seconds": self.conversation_ttl,
                "master_agent_status": agent_health.get("status", "unknown"),
                "total_queries_processed": total_queries,
                "average_queries_per_conversation": round(avg_queries_per_conversation, 2),
                "conversation_state_distribution": state_distribution,
                "intent_patterns_loaded": len(self.intent_patterns),
                "clarification_templates_loaded": len(self.clarification_templates),
                "enhanced_features": [
                    "query_intent_recognition",
                    "conversation_context_management",
                    "clarification_generation",
                    "comparative_analysis",
                    "enhanced_explanations"
                ]
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "active_conversations": len(self.conversations)
            }
    
    def get_interface_statistics(self) -> Dict[str, Any]:
        """Get enhanced statistics about the natural language interface."""
        total_queries = sum(len(c.query_history) for c in self.conversations.values())
        total_execution_time = sum(c.total_execution_time_ms for c in self.conversations.values())
        
        # Calculate intent distribution
        intent_distribution = {}
        for context in self.conversations.values():
            for query in context.query_history:
                intent = query.get("intent", "unknown")
                intent_distribution[intent] = intent_distribution.get(intent, 0) + 1
        
        # Calculate conversation age distribution
        current_time = datetime.utcnow()
        age_distribution = {"< 1 hour": 0, "1-6 hours": 0, "6-24 hours": 0, "> 24 hours": 0}
        
        for context in self.conversations.values():
            age_hours = (current_time - context.created_at).total_seconds() / 3600
            if age_hours < 1:
                age_distribution["< 1 hour"] += 1
            elif age_hours < 6:
                age_distribution["1-6 hours"] += 1
            elif age_hours < 24:
                age_distribution["6-24 hours"] += 1
            else:
                age_distribution["> 24 hours"] += 1
        
        # Calculate resource usage statistics
        all_referenced_resources = []
        for context in self.conversations.values():
            all_referenced_resources.extend(context.referenced_resources)
        
        unique_resources = len(set(all_referenced_resources))
        
        return {
            "active_conversations": len(self.conversations),
            "total_queries_processed": total_queries,
            "total_execution_time_ms": total_execution_time,
            "average_execution_time_ms": total_execution_time / max(total_queries, 1),
            "conversation_ttl_seconds": self.conversation_ttl,
            "intent_distribution": intent_distribution,
            "conversation_age_distribution": age_distribution,
            "unique_resources_referenced": unique_resources,
            "total_resource_references": len(all_referenced_resources),
            "average_queries_per_conversation": total_queries / max(len(self.conversations), 1),
            "enhanced_features_active": True
        }
    
    def get_conversation_analytics(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed analytics for a specific conversation."""
        if conversation_id not in self.conversations:
            return None
        
        context = self.conversations[conversation_id]
        
        # Calculate query intent distribution for this conversation
        intent_counts = {}
        for query in context.query_history:
            intent = query.get("intent", "unknown")
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        # Calculate confidence trends
        confidences = [query.get("confidence", 0.0) for query in context.query_history]
        avg_confidence = sum(confidences) / max(len(confidences), 1)
        
        # Calculate conversation metrics
        conversation_duration = (context.last_activity - context.created_at).total_seconds()
        
        return {
            "conversation_id": conversation_id,
            "user_id": context.user_id,
            "client_id": context.client_id,
            "created_at": context.created_at.isoformat(),
            "last_activity": context.last_activity.isoformat(),
            "duration_seconds": conversation_duration,
            "current_state": context.state.value,
            "total_queries": len(context.query_history),
            "total_results": len(context.result_history),
            "intent_distribution": intent_counts,
            "average_confidence": round(avg_confidence, 3),
            "resources_referenced": len(context.referenced_resources),
            "derived_fields_created": len(context.derived_fields),
            "clarification_requests": len(context.clarification_requests),
            "total_execution_time_ms": context.total_execution_time_ms,
            "average_query_time_ms": context.total_execution_time_ms / max(len(context.query_history), 1)
        }
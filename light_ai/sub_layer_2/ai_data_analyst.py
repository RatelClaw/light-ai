"""
AI Data Analyst Agent for Universal Data Handler Sub-Layer 2.

Provides comprehensive data analysis capabilities with automatic resource identification,
cross-format data synthesis, report generation with insights and visualizations,
reasoning explanation, and source citation.
"""

import json
import re
import uuid
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import openai
from openai import OpenAI

from ..core.models import DataHierarchy, ResourceMetadata, ResourceType, AccessLevel
from ..storage.metadata_registry import MetadataRegistry
from ..storage.storage_router import StorageRouter
from .sql_query_engine import SQLQueryEngine, QueryResult
from .natural_language_processor import NaturalLanguageProcessor, NLQueryResult, QueryType
from .semantic_search_engine import SemanticSearchEngine, SearchStrategy, SearchResults
from ..config import Config, get_config
from ..logger import get_logger

logger = get_logger(__name__)


class AnalysisType(Enum):
    """Types of data analysis."""
    DESCRIPTIVE = "descriptive"        # What happened?
    DIAGNOSTIC = "diagnostic"          # Why did it happen?
    PREDICTIVE = "predictive"          # What will happen?
    PRESCRIPTIVE = "prescriptive"      # What should we do?
    EXPLORATORY = "exploratory"        # What patterns exist?


class InsightType(Enum):
    """Types of insights that can be generated."""
    TREND = "trend"
    CORRELATION = "correlation"
    ANOMALY = "anomaly"
    PATTERN = "pattern"
    SUMMARY = "summary"
    COMPARISON = "comparison"
    RECOMMENDATION = "recommendation"


@dataclass
class DataSource:
    """Information about a data source used in analysis."""
    resource_id: str
    resource_type: ResourceType
    filename: str
    data_type: str
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    chunk_count: Optional[int] = None
    relevance_score: float = 0.0
    sample_data: List[Dict[str, Any]] = field(default_factory=list)
    schema_info: Optional[Dict[str, Any]] = None


@dataclass
class Insight:
    """Individual insight generated from data analysis."""
    insight_type: InsightType
    title: str
    description: str
    confidence_score: float
    supporting_data: List[Dict[str, Any]] = field(default_factory=list)
    visualization_suggestion: Optional[str] = None
    source_citations: List[str] = field(default_factory=list)


@dataclass
class AnalysisReport:
    """Comprehensive analysis report with insights and visualizations."""
    analysis_id: str
    original_question: str
    analysis_type: AnalysisType
    executive_summary: str
    key_insights: List[Insight] = field(default_factory=list)
    data_sources_used: List[DataSource] = field(default_factory=list)
    methodology: str = ""
    limitations: str = ""
    recommendations: List[str] = field(default_factory=list)
    visualizations: List[Dict[str, Any]] = field(default_factory=list)
    confidence_score: float = 0.0
    execution_time_ms: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "analysis_id": self.analysis_id,
            "original_question": self.original_question,
            "analysis_type": self.analysis_type.value,
            "executive_summary": self.executive_summary,
            "key_insights": [
                {
                    "type": insight.insight_type.value,
                    "title": insight.title,
                    "description": insight.description,
                    "confidence_score": insight.confidence_score,
                    "supporting_data": insight.supporting_data,
                    "visualization_suggestion": insight.visualization_suggestion,
                    "source_citations": insight.source_citations
                }
                for insight in self.key_insights
            ],
            "data_sources_used": [
                {
                    "resource_id": ds.resource_id,
                    "resource_type": ds.resource_type.value,
                    "filename": ds.filename,
                    "data_type": ds.data_type,
                    "row_count": ds.row_count,
                    "column_count": ds.column_count,
                    "chunk_count": ds.chunk_count,
                    "relevance_score": ds.relevance_score
                }
                for ds in self.data_sources_used
            ],
            "methodology": self.methodology,
            "limitations": self.limitations,
            "recommendations": self.recommendations,
            "visualizations": self.visualizations,
            "confidence_score": self.confidence_score,
            "execution_time_ms": self.execution_time_ms,
            "created_at": self.created_at.isoformat()
        }


class AIDataAnalyst:
    """
    Advanced AI data analyst agent for comprehensive data analysis.
    
    Features:
    - Automatic resource identification for complex questions
    - Schema and sample data retrieval for context
    - Cross-format data synthesis (structured + unstructured)
    - Report generation with insights and visualizations
    - Reasoning explanation and source citation
    - Multiple analysis types (descriptive, diagnostic, predictive, etc.)
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize AI data analyst.
        
        Args:
            config: Optional configuration instance
        """
        self.config = config or get_config()
        self.metadata_registry = MetadataRegistry(config)
        self.storage_router = StorageRouter(config)
        self.sql_engine = SQLQueryEngine(config)
        self.nl_processor = NaturalLanguageProcessor(config)
        self.semantic_search = SemanticSearchEngine(config)
        
        # Initialize OpenRouter client
        self.openai_client = OpenAI(
            api_key=self.config.openrouter.api_key,
            base_url=self.config.openrouter.base_url
        )
        
        # Analysis patterns for classification
        self._analysis_patterns = {
            AnalysisType.DESCRIPTIVE: [
                r'\b(what|show|display|list|count|sum|average|total)\b',
                r'\b(statistics|summary|overview|breakdown)\b',
                r'\b(how many|how much|what are)\b'
            ],
            AnalysisType.DIAGNOSTIC: [
                r'\b(why|what caused|reason|because|due to)\b',
                r'\b(correlation|relationship|impact|effect)\b',
                r'\b(analyze|investigate|examine)\b'
            ],
            AnalysisType.PREDICTIVE: [
                r'\b(predict|forecast|estimate|project)\b',
                r'\b(will|future|next|upcoming|trend)\b',
                r'\b(likely|probability|chance)\b'
            ],
            AnalysisType.PRESCRIPTIVE: [
                r'\b(recommend|suggest|should|optimize)\b',
                r'\b(improve|increase|decrease|reduce)\b',
                r'\b(strategy|action|plan|solution)\b'
            ],
            AnalysisType.EXPLORATORY: [
                r'\b(explore|discover|find patterns|insights)\b',
                r'\b(unusual|anomaly|outlier|interesting)\b',
                r'\b(compare|contrast|difference|similar)\b'
            ]
        }
        
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize the AI data analyst and dependencies."""
        if not self._initialized:
            self.metadata_registry.initialize()
            self.storage_router.initialize()
            self.sql_engine.initialize()
            self.nl_processor.initialize()
            self.semantic_search.initialize()
            self._initialized = True
            logger.info("AI Data Analyst initialized")
    
    def analyze_data(self, question: str, client_id: str, user_id: str,
                    access_level: AccessLevel = AccessLevel.USER,
                    analysis_type: Optional[AnalysisType] = None,
                    include_visualizations: bool = True) -> AnalysisReport:
        """
        Perform comprehensive data analysis based on a natural language question.
        
        Args:
            question: Natural language question or analysis request
            client_id: Client ID for access control
            user_id: User ID for access control
            access_level: Access level for the user
            analysis_type: Optional specific analysis type (auto-detected if None)
            include_visualizations: Whether to include visualization suggestions
            
        Returns:
            AnalysisReport: Comprehensive analysis report
            
        Raises:
            ValueError: If question is invalid or access is denied
            RuntimeError: If analysis fails
        """
        self.initialize()
        
        start_time = datetime.utcnow()
        analysis_id = str(uuid.uuid4())
        
        try:
            # Step 1: Classify analysis type
            if not analysis_type:
                analysis_type = self._classify_analysis_type(question)
            
            # Step 2: Identify relevant resources
            relevant_resources = self._identify_relevant_resources(
                question, client_id, user_id, access_level
            )
            
            if not relevant_resources:
                return self._create_empty_report(
                    analysis_id, question, analysis_type, start_time,
                    "No relevant data sources found for this analysis."
                )
            
            # Step 3: Retrieve context for each resource
            data_sources = self._build_data_source_contexts(relevant_resources)
            
            # Step 4: Execute analysis across data sources
            analysis_results = self._execute_cross_format_analysis(
                question, data_sources, client_id, user_id, access_level, analysis_type
            )
            
            # Step 5: Generate insights
            insights = self._generate_insights(
                question, analysis_results, data_sources, analysis_type
            )
            
            # Step 6: Create comprehensive report
            report = self._create_analysis_report(
                analysis_id, question, analysis_type, insights, data_sources,
                analysis_results, include_visualizations, start_time
            )
            
            logger.info(f"Completed data analysis for user {user_id}: {analysis_type.value}")
            return report
            
        except Exception as e:
            logger.error(f"Failed to perform data analysis: {e}")
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return AnalysisReport(
                analysis_id=analysis_id,
                original_question=question,
                analysis_type=analysis_type or AnalysisType.EXPLORATORY,
                executive_summary=f"Analysis failed: {str(e)}",
                execution_time_ms=execution_time
            )
    
    def _classify_analysis_type(self, question: str) -> AnalysisType:
        """Classify the type of analysis based on the question."""
        question_lower = question.lower()
        
        # Score each analysis type
        type_scores = {}
        for analysis_type, patterns in self._analysis_patterns.items():
            score = sum(1 for pattern in patterns 
                       if re.search(pattern, question_lower, re.IGNORECASE))
            type_scores[analysis_type] = score
        
        # Return the highest scoring type, default to exploratory
        if not type_scores or max(type_scores.values()) == 0:
            return AnalysisType.EXPLORATORY
        
        return max(type_scores, key=type_scores.get)
    
    def _identify_relevant_resources(self, question: str, client_id: str, user_id: str,
                                   access_level: AccessLevel) -> List[ResourceMetadata]:
        """Identify resources relevant to the analysis question."""
        try:
            # Get all accessible resources
            all_resources = self.metadata_registry.list_resources(
                client_id, user_id if access_level == AccessLevel.USER else None
            )
            
            logger.info(f"Found {len(all_resources)} total resources for client_id={client_id}, user_id={user_id}")
            
            if not all_resources:
                return []
            
            # Score resources based on relevance to the question
            scored_resources = []
            
            for resource in all_resources:
                relevance_score = self._calculate_resource_relevance(question, resource)
                logger.info(f"Resource {resource.resource_id} ({resource.original_filename}) relevance score: {relevance_score}")
                if relevance_score >= 0.1:  # Minimum relevance threshold (inclusive)
                    scored_resources.append((resource, relevance_score))
            
            # Sort by relevance and return top resources
            scored_resources.sort(key=lambda x: x[1], reverse=True)
            
            logger.info(f"Found {len(scored_resources)} relevant resources above threshold")
            
            # Return top 10 most relevant resources
            return [resource for resource, score in scored_resources[:10]]
            
        except Exception as e:
            logger.error(f"Failed to identify relevant resources: {e}")
            return []
    
    def _calculate_resource_relevance(self, question: str, resource: ResourceMetadata) -> float:
        """Calculate relevance score for a resource based on the question."""
        score = 0.0
        question_lower = question.lower()
        
        # Check filename relevance
        filename_lower = resource.original_filename.lower()
        filename_words = re.findall(r'\w+', filename_lower)
        question_words = re.findall(r'\w+', question_lower)
        
        # Word overlap score
        common_words = set(filename_words) & set(question_words)
        if filename_words:
            score += len(common_words) / len(filename_words) * 0.4
        
        # Data type relevance
        if resource.resource_type == ResourceType.STRUCTURED:
            # Structured data is good for quantitative analysis
            if any(word in question_lower for word in ['count', 'sum', 'average', 'total', 'statistics']):
                score += 0.3
        elif resource.resource_type == ResourceType.UNSTRUCTURED:
            # Unstructured data is good for qualitative analysis
            if any(word in question_lower for word in ['content', 'text', 'document', 'information']):
                score += 0.3
        
        # Recent data gets slight boost
        days_old = (datetime.utcnow() - resource.created_at).days
        if days_old < 30:
            score += 0.1
        
        # Larger datasets get slight boost (more likely to contain relevant info)
        if resource.row_count and resource.row_count > 100:
            score += 0.1
        elif resource.chunk_count and resource.chunk_count > 10:
            score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _build_data_source_contexts(self, resources: List[ResourceMetadata]) -> List[DataSource]:
        """Build comprehensive context for each data source."""
        data_sources = []
        
        for resource in resources:
            try:
                data_source = DataSource(
                    resource_id=resource.resource_id,
                    resource_type=resource.resource_type,
                    filename=resource.original_filename,
                    data_type=resource.data_type.value,
                    row_count=resource.row_count,
                    column_count=resource.column_count,
                    chunk_count=resource.chunk_count
                )
                
                # Get schema information for structured data
                if resource.resource_type == ResourceType.STRUCTURED:
                    schema_info = self.metadata_registry.get_schema_info(resource.resource_id)
                    if schema_info:
                        data_source.schema_info = json.loads(schema_info.schema_json)
                    
                    # Get sample data
                    data_source.sample_data = self._get_sample_data(resource, limit=5)
                
                data_sources.append(data_source)
                
            except Exception as e:
                logger.warning(f"Failed to build context for resource {resource.resource_id}: {e}")
                continue
        
        return data_sources
    
    def _get_sample_data(self, resource: ResourceMetadata, limit: int = 5) -> List[Dict[str, Any]]:
        """Get sample data from a structured resource."""
        try:
            if resource.resource_type != ResourceType.STRUCTURED:
                return []
            
            table_name = f"structured_data.resource_{resource.resource_id.replace('-', '_')}_enhanced"
            sql = f"SELECT * FROM {table_name} LIMIT {limit}"
            
            results = self.storage_router.query_structured_data(
                sql, resource.client_id, resource.user_id
            )
            
            return results
            
        except Exception as e:
            logger.warning(f"Failed to get sample data for {resource.resource_id}: {e}")
            return []
    
    def _execute_cross_format_analysis(self, question: str, data_sources: List[DataSource],
                                     client_id: str, user_id: str, access_level: AccessLevel,
                                     analysis_type: AnalysisType) -> Dict[str, Any]:
        """Execute analysis across multiple data formats."""
        results = {
            "structured_results": [],
            "unstructured_results": [],
            "cross_format_insights": []
        }
        
        try:
            # Analyze structured data sources
            structured_sources = [ds for ds in data_sources if ds.resource_type == ResourceType.STRUCTURED]
            if structured_sources:
                results["structured_results"] = self._analyze_structured_data(
                    question, structured_sources, client_id, user_id, access_level
                )
            
            # Analyze unstructured data sources
            unstructured_sources = [ds for ds in data_sources if ds.resource_type == ResourceType.UNSTRUCTURED]
            if unstructured_sources:
                results["unstructured_results"] = self._analyze_unstructured_data(
                    question, unstructured_sources, client_id, user_id, access_level
                )
            
            # Generate cross-format insights if we have both types
            if structured_sources and unstructured_sources:
                results["cross_format_insights"] = self._generate_cross_format_insights(
                    question, results["structured_results"], results["unstructured_results"]
                )
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to execute cross-format analysis: {e}")
            return results
    
    def _analyze_structured_data(self, question: str, data_sources: List[DataSource],
                                client_id: str, user_id: str, access_level: AccessLevel) -> List[Dict[str, Any]]:
        """Analyze structured data sources using SQL queries."""
        results = []
        
        for data_source in data_sources:
            try:
                # Use natural language processor to generate and execute SQL
                nl_result = self.nl_processor.process_natural_query(
                    question, client_id, user_id, access_level=access_level
                )
                
                if nl_result.data:
                    results.append({
                        "resource_id": data_source.resource_id,
                        "filename": data_source.filename,
                        "query_type": nl_result.query_type.value,
                        "sql_query": nl_result.generated_sql,
                        "data": nl_result.data,
                        "row_count": nl_result.row_count,
                        "explanation": nl_result.explanation
                    })
                
            except Exception as e:
                logger.warning(f"Failed to analyze structured data source {data_source.resource_id}: {e}")
                continue
        
        return results
    
    def _analyze_unstructured_data(self, question: str, data_sources: List[DataSource],
                                 client_id: str, user_id: str, access_level: AccessLevel) -> List[Dict[str, Any]]:
        """Analyze unstructured data sources using semantic search."""
        results = []
        
        try:
            # Get resource IDs for unstructured sources
            resource_ids = [ds.resource_id for ds in data_sources]
            
            # Perform semantic search across unstructured sources
            search_results = self.semantic_search.search(
                question, client_id, user_id, 
                strategy=SearchStrategy.HYBRID,
                n_results=10,
                resource_ids=resource_ids
            )
            
            if search_results.results:
                # Group results by resource
                resource_results = {}
                for result in search_results.results:
                    resource_id = result.resource_id
                    if resource_id not in resource_results:
                        resource_results[resource_id] = []
                    resource_results[resource_id].append({
                        "chunk_text": result.document,
                        "relevance_score": result.relevance_score,
                        "metadata": result.metadata
                    })
                
                # Convert to results format
                for resource_id, chunks in resource_results.items():
                    data_source = next((ds for ds in data_sources if ds.resource_id == resource_id), None)
                    if data_source:
                        results.append({
                            "resource_id": resource_id,
                            "filename": data_source.filename,
                            "relevant_chunks": chunks,
                            "total_chunks": len(chunks)
                        })
            
        except Exception as e:
            logger.warning(f"Failed to analyze unstructured data: {e}")
        
        return results
    
    def _generate_cross_format_insights(self, question: str, structured_results: List[Dict[str, Any]],
                                       unstructured_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate insights that combine structured and unstructured data."""
        insights = []
        
        try:
            # Build context for LLM
            context_parts = [
                f"Question: {question}",
                "",
                "Structured Data Results:"
            ]
            
            for result in structured_results:
                context_parts.append(f"- {result['filename']}: {result['row_count']} rows")
                if result.get('data') and len(result['data']) > 0:
                    sample_row = result['data'][0]
                    context_parts.append(f"  Sample: {sample_row}")
            
            context_parts.append("\nUnstructured Data Results:")
            for result in unstructured_results:
                context_parts.append(f"- {result['filename']}: {result['total_chunks']} relevant chunks")
                if result.get('relevant_chunks'):
                    top_chunk = result['relevant_chunks'][0]
                    context_parts.append(f"  Top chunk: {top_chunk['chunk_text'][:200]}...")
            
            context_parts.extend([
                "",
                "Please identify connections, patterns, or insights that emerge from combining",
                "the structured and unstructured data. Focus on how they complement each other."
            ])
            
            # Generate insights using LLM
            response = self.openai_client.chat.completions.create(
                model=self.config.openrouter.default_model,
                messages=[
                    {"role": "system", "content": "You are a data analyst expert at finding connections between different types of data. Provide clear, actionable insights."},
                    {"role": "user", "content": "\n".join(context_parts)}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            insight_text = response.choices[0].message.content.strip()
            
            insights.append({
                "type": "cross_format_synthesis",
                "description": insight_text,
                "confidence_score": 0.7,
                "sources": [r["filename"] for r in structured_results + unstructured_results]
            })
            
        except Exception as e:
            logger.warning(f"Failed to generate cross-format insights: {e}")
        
        return insights
    
    def _generate_insights(self, question: str, analysis_results: Dict[str, Any],
                          data_sources: List[DataSource], analysis_type: AnalysisType) -> List[Insight]:
        """Generate insights from analysis results."""
        insights = []
        
        try:
            # Generate insights from structured data
            if analysis_results.get("structured_results"):
                insights.extend(self._generate_structured_insights(
                    analysis_results["structured_results"], analysis_type
                ))
            
            # Generate insights from unstructured data
            if analysis_results.get("unstructured_results"):
                insights.extend(self._generate_unstructured_insights(
                    analysis_results["unstructured_results"], analysis_type
                ))
            
            # Add cross-format insights
            if analysis_results.get("cross_format_insights"):
                for cf_insight in analysis_results["cross_format_insights"]:
                    insights.append(Insight(
                        insight_type=InsightType.PATTERN,
                        title="Cross-Format Analysis",
                        description=cf_insight["description"],
                        confidence_score=cf_insight["confidence_score"],
                        source_citations=cf_insight["sources"]
                    ))
            
            # Generate summary insight
            if insights:
                summary_insight = self._generate_summary_insight(question, insights, data_sources)
                insights.insert(0, summary_insight)  # Put summary first
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
            return []
    
    def _generate_structured_insights(self, structured_results: List[Dict[str, Any]],
                                    analysis_type: AnalysisType) -> List[Insight]:
        """Generate insights from structured data analysis."""
        insights = []
        
        for result in structured_results:
            try:
                if not result.get("data"):
                    continue
                
                data = result["data"]
                filename = result["filename"]
                
                # Generate different insights based on analysis type
                if analysis_type == AnalysisType.DESCRIPTIVE:
                    # Generate summary statistics
                    insights.append(Insight(
                        insight_type=InsightType.SUMMARY,
                        title=f"Data Summary: {filename}",
                        description=f"Dataset contains {len(data)} records with {len(data[0]) if data else 0} fields.",
                        confidence_score=0.9,
                        supporting_data=data[:3],  # Top 3 rows
                        source_citations=[filename]
                    ))
                
                elif analysis_type == AnalysisType.DIAGNOSTIC:
                    # Look for patterns or correlations
                    if len(data) > 1:
                        insights.append(Insight(
                            insight_type=InsightType.PATTERN,
                            title=f"Data Patterns: {filename}",
                            description=f"Analysis of {len(data)} records reveals data distribution patterns.",
                            confidence_score=0.7,
                            supporting_data=data[:5],
                            source_citations=[filename]
                        ))
                
                # Add trend analysis if data suggests time series
                if data and any(key for key in data[0].keys() if 'date' in key.lower() or 'time' in key.lower()):
                    insights.append(Insight(
                        insight_type=InsightType.TREND,
                        title=f"Temporal Analysis: {filename}",
                        description="Time-based data detected - temporal trends may be present.",
                        confidence_score=0.6,
                        visualization_suggestion="time_series_chart",
                        source_citations=[filename]
                    ))
                
            except Exception as e:
                logger.warning(f"Failed to generate structured insights for {result.get('filename', 'unknown')}: {e}")
                continue
        
        return insights
    
    def _generate_unstructured_insights(self, unstructured_results: List[Dict[str, Any]],
                                      analysis_type: AnalysisType) -> List[Insight]:
        """Generate insights from unstructured data analysis."""
        insights = []
        
        for result in unstructured_results:
            try:
                filename = result["filename"]
                chunks = result.get("relevant_chunks", [])
                
                if not chunks:
                    continue
                
                # Analyze content themes
                all_text = " ".join([chunk["chunk_text"] for chunk in chunks[:5]])  # Top 5 chunks
                
                insights.append(Insight(
                    insight_type=InsightType.SUMMARY,
                    title=f"Content Analysis: {filename}",
                    description=f"Found {len(chunks)} relevant text segments with high relevance to the query.",
                    confidence_score=0.8,
                    supporting_data=[{"text_preview": all_text[:300] + "..."}],
                    source_citations=[filename]
                ))
                
                # If high relevance chunks, suggest they contain key information
                high_relevance_chunks = [c for c in chunks if c["relevance_score"] > 0.8]
                if high_relevance_chunks:
                    insights.append(Insight(
                        insight_type=InsightType.RECOMMENDATION,
                        title=f"Key Information: {filename}",
                        description=f"Found {len(high_relevance_chunks)} highly relevant text segments that likely contain key information.",
                        confidence_score=0.9,
                        supporting_data=[{"chunk": c["chunk_text"][:200] + "..."} for c in high_relevance_chunks[:2]],
                        source_citations=[filename]
                    ))
                
            except Exception as e:
                logger.warning(f"Failed to generate unstructured insights for {result.get('filename', 'unknown')}: {e}")
                continue
        
        return insights
    
    def _generate_summary_insight(self, question: str, insights: List[Insight],
                                data_sources: List[DataSource]) -> Insight:
        """Generate an overall summary insight."""
        try:
            # Build summary based on available insights and data sources
            structured_count = len([ds for ds in data_sources if ds.resource_type == ResourceType.STRUCTURED])
            unstructured_count = len([ds for ds in data_sources if ds.resource_type == ResourceType.UNSTRUCTURED])
            
            summary_parts = [
                f"Analysis of {len(data_sources)} data sources ({structured_count} structured, {unstructured_count} unstructured)",
                f"Generated {len(insights)} insights across multiple data types"
            ]
            
            # Add insight type summary
            insight_types = {}
            for insight in insights:
                insight_types[insight.insight_type] = insight_types.get(insight.insight_type, 0) + 1
            
            if insight_types:
                type_summary = ", ".join([f"{count} {itype.value}" for itype, count in insight_types.items()])
                summary_parts.append(f"Insights include: {type_summary}")
            
            return Insight(
                insight_type=InsightType.SUMMARY,
                title="Executive Summary",
                description=". ".join(summary_parts) + ".",
                confidence_score=0.8,
                source_citations=[ds.filename for ds in data_sources]
            )
            
        except Exception as e:
            logger.warning(f"Failed to generate summary insight: {e}")
            return Insight(
                insight_type=InsightType.SUMMARY,
                title="Analysis Summary",
                description=f"Completed analysis of {len(data_sources)} data sources.",
                confidence_score=0.5
            )
    
    def _create_analysis_report(self, analysis_id: str, question: str, analysis_type: AnalysisType,
                              insights: List[Insight], data_sources: List[DataSource],
                              analysis_results: Dict[str, Any], include_visualizations: bool,
                              start_time: datetime) -> AnalysisReport:
        """Create comprehensive analysis report."""
        try:
            # Generate executive summary
            executive_summary = self._generate_executive_summary(question, insights, data_sources)
            
            # Generate methodology explanation
            methodology = self._generate_methodology_explanation(analysis_type, data_sources)
            
            # Generate limitations
            limitations = self._generate_limitations(data_sources, analysis_results)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(insights, analysis_type)
            
            # Generate visualizations if requested
            visualizations = []
            if include_visualizations:
                visualizations = self._generate_visualization_suggestions(insights, data_sources)
            
            # Calculate overall confidence score
            confidence_score = self._calculate_overall_confidence(insights)
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return AnalysisReport(
                analysis_id=analysis_id,
                original_question=question,
                analysis_type=analysis_type,
                executive_summary=executive_summary,
                key_insights=insights,
                data_sources_used=data_sources,
                methodology=methodology,
                limitations=limitations,
                recommendations=recommendations,
                visualizations=visualizations,
                confidence_score=confidence_score,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            logger.error(f"Failed to create analysis report: {e}")
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return AnalysisReport(
                analysis_id=analysis_id,
                original_question=question,
                analysis_type=analysis_type,
                executive_summary=f"Report generation failed: {str(e)}",
                execution_time_ms=execution_time
            )
    
    def _generate_executive_summary(self, question: str, insights: List[Insight],
                                  data_sources: List[DataSource]) -> str:
        """Generate executive summary using LLM."""
        try:
            # Build context for summary generation
            context_parts = [
                f"Original Question: {question}",
                f"Data Sources Analyzed: {len(data_sources)}",
                "",
                "Key Insights:"
            ]
            
            for i, insight in enumerate(insights[:5], 1):  # Top 5 insights
                context_parts.append(f"{i}. {insight.title}: {insight.description}")
            
            context_parts.extend([
                "",
                "Please generate a concise executive summary (2-3 sentences) that:",
                "1. Directly answers the original question",
                "2. Highlights the most important findings",
                "3. Uses business-friendly language"
            ])
            
            response = self.openai_client.chat.completions.create(
                model=self.config.openrouter.default_model,
                messages=[
                    {"role": "system", "content": "You are an executive analyst creating concise, actionable summaries for business leaders."},
                    {"role": "user", "content": "\n".join(context_parts)}
                ],
                max_tokens=300,
                temperature=0.2
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.warning(f"Failed to generate executive summary: {e}")
            return f"Analysis of {len(data_sources)} data sources generated {len(insights)} insights related to: {question}"
    
    def _generate_methodology_explanation(self, analysis_type: AnalysisType,
                                        data_sources: List[DataSource]) -> str:
        """Generate methodology explanation."""
        method_parts = [
            f"This {analysis_type.value} analysis was conducted using a multi-step approach:"
        ]
        
        if any(ds.resource_type == ResourceType.STRUCTURED for ds in data_sources):
            method_parts.append("1. Structured data analysis using SQL queries and statistical methods")
        
        if any(ds.resource_type == ResourceType.UNSTRUCTURED for ds in data_sources):
            method_parts.append("2. Unstructured data analysis using semantic search and natural language processing")
        
        if len([ds for ds in data_sources if ds.resource_type == ResourceType.STRUCTURED]) > 0 and \
           len([ds for ds in data_sources if ds.resource_type == ResourceType.UNSTRUCTURED]) > 0:
            method_parts.append("3. Cross-format synthesis to identify patterns across data types")
        
        method_parts.append("4. AI-powered insight generation and confidence scoring")
        
        return " ".join(method_parts)
    
    def _generate_limitations(self, data_sources: List[DataSource],
                            analysis_results: Dict[str, Any]) -> str:
        """Generate analysis limitations."""
        limitations = []
        
        # Data source limitations
        if len(data_sources) < 3:
            limitations.append("Limited number of data sources may affect comprehensiveness")
        
        # Check for small datasets
        small_datasets = [ds for ds in data_sources 
                         if ds.row_count and ds.row_count < 100]
        if small_datasets:
            limitations.append("Some datasets have limited sample sizes")
        
        # Check for missing structured data
        if not any(ds.resource_type == ResourceType.STRUCTURED for ds in data_sources):
            limitations.append("No structured data available for quantitative analysis")
        
        # Check for missing unstructured data
        if not any(ds.resource_type == ResourceType.UNSTRUCTURED for ds in data_sources):
            limitations.append("No unstructured data available for qualitative insights")
        
        # Default limitation
        if not limitations:
            limitations.append("Analysis is based on available data at the time of execution")
        
        return "; ".join(limitations) + "."
    
    def _generate_recommendations(self, insights: List[Insight],
                                analysis_type: AnalysisType) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Extract recommendations from insights
        recommendation_insights = [i for i in insights if i.insight_type == InsightType.RECOMMENDATION]
        for insight in recommendation_insights:
            recommendations.append(insight.description)
        
        # Add general recommendations based on analysis type
        if analysis_type == AnalysisType.DESCRIPTIVE:
            recommendations.append("Consider conducting diagnostic analysis to understand underlying causes")
        elif analysis_type == AnalysisType.DIAGNOSTIC:
            recommendations.append("Implement monitoring to track identified patterns over time")
        elif analysis_type == AnalysisType.EXPLORATORY:
            recommendations.append("Focus future analysis on the most promising patterns identified")
        
        # Ensure we have at least one recommendation
        if not recommendations:
            recommendations.append("Continue monitoring data trends and conduct regular analysis updates")
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def _generate_visualization_suggestions(self, insights: List[Insight],
                                          data_sources: List[DataSource]) -> List[Dict[str, Any]]:
        """Generate visualization suggestions."""
        visualizations = []
        
        # Extract visualization suggestions from insights
        for insight in insights:
            if insight.visualization_suggestion:
                visualizations.append({
                    "type": insight.visualization_suggestion,
                    "title": f"Visualization for: {insight.title}",
                    "description": f"Recommended visualization to illustrate {insight.description}",
                    "data_source": insight.source_citations[0] if insight.source_citations else "Multiple sources"
                })
        
        # Add general visualizations based on data types
        structured_sources = [ds for ds in data_sources if ds.resource_type == ResourceType.STRUCTURED]
        if structured_sources:
            visualizations.append({
                "type": "summary_dashboard",
                "title": "Data Overview Dashboard",
                "description": "Interactive dashboard showing key metrics from structured data sources",
                "data_source": "All structured sources"
            })
        
        unstructured_sources = [ds for ds in data_sources if ds.resource_type == ResourceType.UNSTRUCTURED]
        if unstructured_sources:
            visualizations.append({
                "type": "word_cloud",
                "title": "Content Themes",
                "description": "Word cloud showing key themes from unstructured content",
                "data_source": "All unstructured sources"
            })
        
        return visualizations[:5]  # Limit to 5 visualizations
    
    def _calculate_overall_confidence(self, insights: List[Insight]) -> float:
        """Calculate overall confidence score for the analysis."""
        if not insights:
            return 0.0
        
        # Weighted average of insight confidence scores
        total_weight = 0
        weighted_sum = 0
        
        for insight in insights:
            # Weight summary insights higher
            weight = 2.0 if insight.insight_type == InsightType.SUMMARY else 1.0
            weighted_sum += insight.confidence_score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _create_empty_report(self, analysis_id: str, question: str, analysis_type: AnalysisType,
                           start_time: datetime, message: str) -> AnalysisReport:
        """Create an empty report when no data is available."""
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return AnalysisReport(
            analysis_id=analysis_id,
            original_question=question,
            analysis_type=analysis_type,
            executive_summary=message,
            execution_time_ms=execution_time,
            recommendations=["Upload relevant data to enable comprehensive analysis"]
        )
    
    def get_analysis_capabilities(self) -> Dict[str, Any]:
        """Get information about analysis capabilities."""
        return {
            "analysis_types": [atype.value for atype in AnalysisType],
            "insight_types": [itype.value for itype in InsightType],
            "supported_data_types": ["structured", "json", "unstructured"],
            "features": [
                "Automatic resource identification",
                "Cross-format data synthesis",
                "AI-powered insight generation",
                "Visualization suggestions",
                "Source citation and reasoning",
                "Confidence scoring"
            ]
        }
    
    def close(self) -> None:
        """Close the AI data analyst and clean up resources."""
        self.sql_engine.close()
        self.nl_processor.close()
        self.storage_router.close()
        logger.info("AI Data Analyst closed")
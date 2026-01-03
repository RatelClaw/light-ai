"""
Natural Language Processing System for Universal Data Handler Sub-Layer 2.

Provides comprehensive natural language query processing with OpenRouter API integration,
schema-aware text-to-SQL generation, query explanation, result interpretation,
follow-up question context management, and error handling with helpful suggestions.
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
from ..config import Config, get_config
from ..logger import get_logger

logger = get_logger(__name__)


class QueryType(Enum):
    """Types of natural language queries."""
    STRUCTURED_DATA = "structured_data"
    UNSTRUCTURED_DATA = "unstructured_data"
    MIXED_DATA = "mixed_data"
    METADATA_QUERY = "metadata_query"
    ANALYTICAL = "analytical"


@dataclass
class QueryContext:
    """Context for managing follow-up questions and conversation state."""
    session_id: str
    user_id: str
    client_id: str
    previous_queries: List[str] = field(default_factory=list)
    previous_results: List[Dict[str, Any]] = field(default_factory=list)
    referenced_resources: List[str] = field(default_factory=list)
    conversation_summary: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class NLQueryResult:
    """Result of a natural language query processing."""
    original_question: str
    query_type: QueryType
    generated_sql: Optional[str] = None
    search_terms: Optional[List[str]] = None
    explanation: str = ""
    data: List[Dict[str, Any]] = field(default_factory=list)
    columns: List[str] = field(default_factory=list)
    row_count: int = 0
    execution_time_ms: float = 0.0
    confidence_score: float = 0.0
    suggestions: List[str] = field(default_factory=list)
    resources_used: List[str] = field(default_factory=list)
    follow_up_suggestions: List[str] = field(default_factory=list)


@dataclass
class SchemaContext:
    """Schema context for a resource to help with SQL generation."""
    resource_id: str
    resource_type: ResourceType
    table_name: str
    columns: List[Dict[str, str]]  # [{"name": "col_name", "type": "data_type", "description": "..."}]
    sample_data: List[Dict[str, Any]]
    statistics: Dict[str, Any]


class NaturalLanguageProcessor:
    """
    Advanced natural language processing system for data queries.
    
    Features:
    - OpenRouter API integration for LLM queries
    - Schema-aware text-to-SQL generation
    - Query explanation and result interpretation
    - Follow-up question context management
    - Error handling with helpful alternative suggestions
    - Multi-format data query support
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize natural language processor.
        
        Args:
            config: Optional configuration instance
        """
        self.config = config or get_config()
        self.metadata_registry = MetadataRegistry(config)
        self.storage_router = StorageRouter(config)
        self.sql_engine = SQLQueryEngine(config)
        
        # Initialize OpenRouter client
        self.openai_client = OpenAI(
            api_key=self.config.openrouter.api_key,
            base_url=self.config.openrouter.base_url
        )
        
        # Context management
        self._query_contexts: Dict[str, QueryContext] = {}
        self._context_ttl = 3600  # 1 hour context retention
        
        # Query patterns for classification
        self._structured_patterns = [
            r'\b(count|sum|average|max|min|total)\b',
            r'\b(group by|order by|where|having)\b',
            r'\b(join|merge|combine)\b',
            r'\b(table|column|row|field)\b',
            r'\b(calculate|compute|aggregate)\b'
        ]
        
        self._unstructured_patterns = [
            r'\b(search|find|look for|contains)\b',
            r'\b(document|text|content|paragraph)\b',
            r'\b(similar|related|relevant)\b',
            r'\b(extract|summarize|analyze)\b'
        ]
        
        self._analytical_patterns = [
            r'\b(trend|pattern|insight|correlation)\b',
            r'\b(compare|contrast|difference)\b',
            r'\b(predict|forecast|estimate)\b',
            r'\b(why|how|what if|explain)\b'
        ]
    
    def initialize(self) -> None:
        """Initialize the natural language processor and dependencies."""
        self.metadata_registry.initialize()
        self.storage_router.initialize()
        self.sql_engine.initialize()
        logger.info("Natural Language Processor initialized")
    
    def process_natural_query(self, question: str, client_id: str, user_id: str,
                            session_id: Optional[str] = None,
                            access_level: AccessLevel = AccessLevel.USER) -> NLQueryResult:
        """
        Process a natural language question and return structured results.
        
        Args:
            question: Natural language question
            client_id: Client ID for access control
            user_id: User ID for access control
            session_id: Optional session ID for context management
            access_level: Access level for the user
            
        Returns:
            NLQueryResult: Processed query result with data and explanations
            
        Raises:
            ValueError: If question is invalid or access is denied
            RuntimeError: If query processing fails
        """
        self.initialize()
        
        start_time = datetime.utcnow()
        
        try:
            # Get or create query context
            context = self._get_or_create_context(session_id, user_id, client_id)
            
            # Classify query type
            query_type = self._classify_query(question, context)
            
            # Get relevant schema context
            schema_contexts = self._get_relevant_schemas(question, client_id, user_id, access_level)
            
            # Process based on query type
            if query_type == QueryType.STRUCTURED_DATA:
                result = self._process_structured_query(
                    question, schema_contexts, client_id, user_id, access_level, context
                )
            elif query_type == QueryType.UNSTRUCTURED_DATA:
                result = self._process_unstructured_query(
                    question, client_id, user_id, access_level, context
                )
            elif query_type == QueryType.MIXED_DATA:
                result = self._process_mixed_query(
                    question, schema_contexts, client_id, user_id, access_level, context
                )
            elif query_type == QueryType.METADATA_QUERY:
                result = self._process_metadata_query(
                    question, client_id, user_id, access_level, context
                )
            else:  # ANALYTICAL
                result = self._process_analytical_query(
                    question, schema_contexts, client_id, user_id, access_level, context
                )
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.execution_time_ms = execution_time
            
            # Update context
            self._update_context(context, question, result)
            
            logger.info(f"Processed natural language query for user {user_id}: {query_type.value}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process natural language query: {e}")
            
            # Return error result with suggestions
            return NLQueryResult(
                original_question=question,
                query_type=QueryType.STRUCTURED_DATA,
                explanation=f"Failed to process query: {str(e)}",
                suggestions=self._generate_error_suggestions(question, str(e)),
                execution_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
            )
    
    def explain_query_result(self, result: NLQueryResult, context: Optional[QueryContext] = None) -> str:
        """
        Generate a natural language explanation of query results.
        
        Args:
            result: Query result to explain
            context: Optional query context for better explanations
            
        Returns:
            str: Natural language explanation of the results
        """
        try:
            # Build explanation prompt
            prompt = self._build_explanation_prompt(result, context)
            
            # Get explanation from LLM
            response = self.openai_client.chat.completions.create(
                model=self.config.openrouter.default_model,
                messages=[
                    {"role": "system", "content": "You are a data analyst explaining query results to business users. Be clear, concise, and focus on insights."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            explanation = response.choices[0].message.content.strip()
            logger.debug(f"Generated query explanation: {len(explanation)} characters")
            return explanation
            
        except Exception as e:
            logger.error(f"Failed to generate query explanation: {e}")
            return f"Query returned {result.row_count} rows. Unable to generate detailed explanation."
    
    def generate_follow_up_suggestions(self, result: NLQueryResult, 
                                     context: Optional[QueryContext] = None) -> List[str]:
        """
        Generate follow-up question suggestions based on query results.
        
        Args:
            result: Previous query result
            context: Optional query context
            
        Returns:
            List[str]: List of suggested follow-up questions
        """
        suggestions = []
        
        try:
            # Build suggestions based on query type and results
            if result.query_type == QueryType.STRUCTURED_DATA:
                if result.row_count > 0:
                    suggestions.extend([
                        "Can you show me trends over time?",
                        "What are the top 10 results?",
                        "Can you group this data by category?",
                        "Show me the summary statistics"
                    ])
                else:
                    suggestions.extend([
                        "Are there similar records in other time periods?",
                        "Can you broaden the search criteria?",
                        "What data is available for this topic?"
                    ])
            
            elif result.query_type == QueryType.UNSTRUCTURED_DATA:
                suggestions.extend([
                    "Can you find more documents like this?",
                    "What are the key themes in these results?",
                    "Are there related topics I should explore?",
                    "Can you summarize the main points?"
                ])
            
            # Add context-aware suggestions
            if context and context.previous_queries:
                suggestions.append("Can you compare this with my previous query?")
                suggestions.append("How has this changed over time?")
            
            # Limit to top 5 suggestions
            return suggestions[:5]
            
        except Exception as e:
            logger.error(f"Failed to generate follow-up suggestions: {e}")
            return ["What other data would you like to explore?"]
    
    def _classify_query(self, question: str, context: QueryContext) -> QueryType:
        """Classify the type of natural language query."""
        question_lower = question.lower()
        
        # Check for structured data patterns
        structured_score = sum(1 for pattern in self._structured_patterns 
                             if re.search(pattern, question_lower, re.IGNORECASE))
        
        # Check for unstructured data patterns
        unstructured_score = sum(1 for pattern in self._unstructured_patterns 
                               if re.search(pattern, question_lower, re.IGNORECASE))
        
        # Check for analytical patterns
        analytical_score = sum(1 for pattern in self._analytical_patterns 
                             if re.search(pattern, question_lower, re.IGNORECASE))
        
        # Check for metadata queries
        if any(word in question_lower for word in ['list', 'show me', 'what data', 'available']):
            return QueryType.METADATA_QUERY
        
        # Determine primary type
        if analytical_score > 0 and (structured_score > 0 or unstructured_score > 0):
            return QueryType.ANALYTICAL
        elif structured_score > unstructured_score:
            return QueryType.STRUCTURED_DATA
        elif unstructured_score > structured_score:
            return QueryType.UNSTRUCTURED_DATA
        elif structured_score > 0 and unstructured_score > 0:
            return QueryType.MIXED_DATA
        else:
            # Default to structured for ambiguous queries
            return QueryType.STRUCTURED_DATA
    
    def _get_relevant_schemas(self, question: str, client_id: str, user_id: str,
                            access_level: AccessLevel) -> List[SchemaContext]:
        """Get relevant schema contexts for the question."""
        try:
            # Get accessible resources
            resources = self.metadata_registry.list_resources(client_id, user_id if access_level == AccessLevel.USER else None)
            
            # Filter to structured resources only
            structured_resources = [r for r in resources if r.resource_type == ResourceType.STRUCTURED]
            
            schema_contexts = []
            for resource in structured_resources[:5]:  # Limit to top 5 resources
                try:
                    schema_context = self._build_schema_context(resource)
                    if schema_context:
                        schema_contexts.append(schema_context)
                except Exception as e:
                    logger.warning(f"Failed to build schema context for {resource.resource_id}: {e}")
                    continue
            
            return schema_contexts
            
        except Exception as e:
            logger.error(f"Failed to get relevant schemas: {e}")
            return []
    
    def _build_schema_context(self, resource: ResourceMetadata) -> Optional[SchemaContext]:
        """Build schema context for a resource."""
        try:
            # Get schema information
            schema_info = self.metadata_registry.get_schema_info(resource.resource_id)
            if not schema_info:
                return None
            
            schema_data = json.loads(schema_info.schema_json)
            statistics_data = json.loads(schema_info.statistics_json)
            
            # Build column information
            columns = []
            for col_name, col_info in schema_data.get('columns', {}).items():
                columns.append({
                    'name': col_name,
                    'type': col_info.get('type', 'unknown'),
                    'description': col_info.get('description', '')
                })
            
            # Get sample data
            sample_data = self._get_sample_data(resource)
            
            # Build table name
            table_name = f"structured_data.resource_{resource.resource_id.replace('-', '_')}_enhanced"
            
            return SchemaContext(
                resource_id=resource.resource_id,
                resource_type=resource.resource_type,
                table_name=table_name,
                columns=columns,
                sample_data=sample_data,
                statistics=statistics_data
            )
            
        except Exception as e:
            logger.error(f"Failed to build schema context for {resource.resource_id}: {e}")
            return None
    
    def _get_sample_data(self, resource: ResourceMetadata, limit: int = 3) -> List[Dict[str, Any]]:
        """Get sample data from a resource."""
        try:
            table_name = f"structured_data.resource_{resource.resource_id.replace('-', '_')}_enhanced"
            sql = f"SELECT * FROM {table_name} LIMIT {limit}"
            
            with self.storage_router.db_managers.duckdb.get_connection() as conn:
                cursor = conn.execute(sql)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            logger.warning(f"Failed to get sample data for {resource.resource_id}: {e}")
            return []
    
    def _process_structured_query(self, question: str, schema_contexts: List[SchemaContext],
                                client_id: str, user_id: str, access_level: AccessLevel,
                                context: QueryContext) -> NLQueryResult:
        """Process a structured data query using text-to-SQL generation."""
        try:
            # Generate SQL from natural language
            sql_result = self._generate_sql_from_question(question, schema_contexts, context)
            
            if not sql_result['sql']:
                return NLQueryResult(
                    original_question=question,
                    query_type=QueryType.STRUCTURED_DATA,
                    explanation="Could not generate SQL query from the question.",
                    suggestions=self._generate_sql_suggestions(question, schema_contexts)
                )
            
            # Execute the generated SQL
            query_result = self.sql_engine.execute_query(
                sql_result['sql'], client_id, user_id, access_level=access_level
            )
            
            # Build result
            result = NLQueryResult(
                original_question=question,
                query_type=QueryType.STRUCTURED_DATA,
                generated_sql=sql_result['sql'],
                explanation=sql_result['explanation'],
                data=query_result.data,
                columns=query_result.columns,
                row_count=query_result.row_count,
                confidence_score=sql_result['confidence'],
                resources_used=[ctx.resource_id for ctx in schema_contexts]
            )
            
            # Generate follow-up suggestions
            result.follow_up_suggestions = self.generate_follow_up_suggestions(result, context)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process structured query: {e}")
            return NLQueryResult(
                original_question=question,
                query_type=QueryType.STRUCTURED_DATA,
                explanation=f"Failed to process structured query: {str(e)}",
                suggestions=self._generate_error_suggestions(question, str(e))
            )
    
    def _generate_sql_from_question(self, question: str, schema_contexts: List[SchemaContext],
                                  context: QueryContext) -> Dict[str, Any]:
        """Generate SQL query from natural language question using OpenRouter LLM."""
        try:
            # Build comprehensive prompt
            prompt = self._build_sql_generation_prompt(question, schema_contexts, context)
            
            # Call OpenRouter LLM
            response = self.openai_client.chat.completions.create(
                model=self.config.openrouter.default_model,
                messages=[
                    {"role": "system", "content": "You are an expert SQL generator. Generate accurate SQL queries based on natural language questions and provided schema information. Always include explanations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1  # Low temperature for consistent SQL generation
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse the response to extract SQL and explanation
            return self._parse_sql_response(response_text)
            
        except Exception as e:
            logger.error(f"Failed to generate SQL from question: {e}")
            return {
                'sql': None,
                'explanation': f"Failed to generate SQL: {str(e)}",
                'confidence': 0.0
            }
    
    def _build_sql_generation_prompt(self, question: str, schema_contexts: List[SchemaContext],
                                   context: QueryContext) -> str:
        """Build a comprehensive prompt for SQL generation."""
        prompt_parts = [
            f"Question: {question}",
            "",
            "Available Tables and Schemas:"
        ]
        
        # Add schema information
        for schema_ctx in schema_contexts:
            prompt_parts.append(f"\nTable: {schema_ctx.table_name}")
            prompt_parts.append("Columns:")
            for col in schema_ctx.columns:
                prompt_parts.append(f"  - {col['name']} ({col['type']}): {col.get('description', 'No description')}")
            
            # Add sample data if available
            if schema_ctx.sample_data:
                prompt_parts.append("Sample data:")
                for i, sample in enumerate(schema_ctx.sample_data[:2]):
                    sample_str = ", ".join([f"{k}={v}" for k, v in sample.items() if k not in ['client_id', 'user_id']])
                    prompt_parts.append(f"  Row {i+1}: {sample_str}")
        
        # Add context from previous queries
        if context.previous_queries:
            prompt_parts.append("\nPrevious questions in this conversation:")
            for prev_q in context.previous_queries[-3:]:  # Last 3 questions
                prompt_parts.append(f"  - {prev_q}")
        
        prompt_parts.extend([
            "",
            "Instructions:",
            "1. Generate a SQL query that answers the question",
            "2. Use only the tables and columns provided above",
            "3. Include proper WHERE clauses for filtering",
            "4. Use appropriate JOINs if multiple tables are needed",
            "5. Add LIMIT clauses for large result sets",
            "6. Provide a clear explanation of what the query does",
            "",
            "Response format:",
            "SQL: [your SQL query here]",
            "EXPLANATION: [explanation of what the query does and why]",
            "CONFIDENCE: [confidence score from 0.0 to 1.0]"
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_sql_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the LLM response to extract SQL, explanation, and confidence."""
        result = {
            'sql': None,
            'explanation': 'No explanation provided',
            'confidence': 0.5
        }
        
        try:
            lines = response_text.split('\n')
            current_section = None
            sql_lines = []
            explanation_lines = []
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('SQL:'):
                    current_section = 'sql'
                    sql_content = line[4:].strip()
                    if sql_content:
                        sql_lines.append(sql_content)
                elif line.startswith('EXPLANATION:'):
                    current_section = 'explanation'
                    explanation_content = line[12:].strip()
                    if explanation_content:
                        explanation_lines.append(explanation_content)
                elif line.startswith('CONFIDENCE:'):
                    confidence_str = line[11:].strip()
                    try:
                        result['confidence'] = float(confidence_str)
                    except ValueError:
                        pass
                elif current_section == 'sql' and line:
                    sql_lines.append(line)
                elif current_section == 'explanation' and line:
                    explanation_lines.append(line)
            
            # Combine SQL lines
            if sql_lines:
                result['sql'] = ' '.join(sql_lines)
            
            # Combine explanation lines
            if explanation_lines:
                result['explanation'] = ' '.join(explanation_lines)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse SQL response: {e}")
            return result
    
    def _process_unstructured_query(self, question: str, client_id: str, user_id: str,
                                  access_level: AccessLevel, context: QueryContext) -> NLQueryResult:
        """Process an unstructured data query using semantic search."""
        # This would integrate with the semantic search engine (to be implemented)
        # For now, return a placeholder result
        return NLQueryResult(
            original_question=question,
            query_type=QueryType.UNSTRUCTURED_DATA,
            explanation="Unstructured data search not yet implemented",
            suggestions=["Try asking about structured data instead"]
        )
    
    def _process_mixed_query(self, question: str, schema_contexts: List[SchemaContext],
                           client_id: str, user_id: str, access_level: AccessLevel,
                           context: QueryContext) -> NLQueryResult:
        """Process a query that spans both structured and unstructured data."""
        # This would combine structured and unstructured processing
        # For now, default to structured processing
        return self._process_structured_query(question, schema_contexts, client_id, user_id, access_level, context)
    
    def _process_metadata_query(self, question: str, client_id: str, user_id: str,
                              access_level: AccessLevel, context: QueryContext) -> NLQueryResult:
        """Process a metadata query about available resources."""
        try:
            resources = self.metadata_registry.list_resources(
                client_id, user_id if access_level == AccessLevel.USER else None
            )
            
            # Build metadata response
            data = []
            for resource in resources:
                data.append({
                    'resource_id': resource.resource_id,
                    'filename': resource.original_filename,
                    'type': resource.resource_type.value,
                    'data_type': resource.data_type.value,
                    'size_mb': round(resource.file_size_bytes / (1024 * 1024), 2),
                    'created_at': resource.created_at.isoformat(),
                    'row_count': resource.row_count,
                    'column_count': resource.column_count
                })
            
            columns = ['resource_id', 'filename', 'type', 'data_type', 'size_mb', 'created_at', 'row_count', 'column_count']
            
            return NLQueryResult(
                original_question=question,
                query_type=QueryType.METADATA_QUERY,
                explanation=f"Found {len(data)} resources available to you",
                data=data,
                columns=columns,
                row_count=len(data),
                confidence_score=1.0
            )
            
        except Exception as e:
            logger.error(f"Failed to process metadata query: {e}")
            return NLQueryResult(
                original_question=question,
                query_type=QueryType.METADATA_QUERY,
                explanation=f"Failed to retrieve metadata: {str(e)}",
                suggestions=["Try asking 'What data do I have available?'"]
            )
    
    def _process_analytical_query(self, question: str, schema_contexts: List[SchemaContext],
                                client_id: str, user_id: str, access_level: AccessLevel,
                                context: QueryContext) -> NLQueryResult:
        """Process an analytical query that requires deeper insights."""
        # For now, process as structured query with enhanced explanation
        result = self._process_structured_query(question, schema_contexts, client_id, user_id, access_level, context)
        
        # Enhance explanation for analytical queries
        if result.data:
            enhanced_explanation = self.explain_query_result(result, context)
            result.explanation = f"{result.explanation}\n\nAnalytical Insights: {enhanced_explanation}"
        
        return result
    
    def _get_or_create_context(self, session_id: Optional[str], user_id: str, client_id: str) -> QueryContext:
        """Get existing query context or create a new one."""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        if session_id in self._query_contexts:
            context = self._query_contexts[session_id]
            # Check if context is still valid
            if (datetime.utcnow() - context.updated_at).total_seconds() < self._context_ttl:
                return context
            else:
                # Remove expired context
                del self._query_contexts[session_id]
        
        # Create new context
        context = QueryContext(
            session_id=session_id,
            user_id=user_id,
            client_id=client_id
        )
        self._query_contexts[session_id] = context
        return context
    
    def _update_context(self, context: QueryContext, question: str, result: NLQueryResult) -> None:
        """Update query context with new question and result."""
        context.previous_queries.append(question)
        context.previous_results.append({
            'question': question,
            'row_count': result.row_count,
            'query_type': result.query_type.value,
            'resources_used': result.resources_used
        })
        
        # Keep only last 10 queries
        if len(context.previous_queries) > 10:
            context.previous_queries = context.previous_queries[-10:]
            context.previous_results = context.previous_results[-10:]
        
        # Update referenced resources
        context.referenced_resources.extend(result.resources_used)
        context.referenced_resources = list(set(context.referenced_resources))  # Remove duplicates
        
        context.updated_at = datetime.utcnow()
    
    def _generate_error_suggestions(self, question: str, error_message: str) -> List[str]:
        """Generate helpful suggestions when query processing fails."""
        suggestions = []
        
        error_lower = error_message.lower()
        question_lower = question.lower()
        
        if 'table' in error_lower or 'column' in error_lower:
            suggestions.extend([
                "Try asking 'What data do I have available?' to see your resources",
                "Check if you're using the correct column names",
                "Make sure you have access to the data you're asking about"
            ])
        
        if 'sql' in error_lower or 'syntax' in error_lower:
            suggestions.extend([
                "Try rephrasing your question in simpler terms",
                "Ask for specific data rather than complex calculations",
                "Break down complex questions into smaller parts"
            ])
        
        if 'access' in error_lower or 'permission' in error_lower:
            suggestions.extend([
                "Check if you have permission to access this data",
                "Try asking about data you've uploaded yourself",
                "Contact your administrator for access to shared data"
            ])
        
        # Generic suggestions
        if not suggestions:
            suggestions.extend([
                "Try rephrasing your question",
                "Ask about specific data you know exists",
                "Use simpler terms and avoid technical jargon"
            ])
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def _generate_sql_suggestions(self, question: str, schema_contexts: List[SchemaContext]) -> List[str]:
        """Generate suggestions when SQL generation fails."""
        suggestions = []
        
        if schema_contexts:
            # Suggest questions based on available data
            for schema_ctx in schema_contexts[:2]:  # Top 2 schemas
                filename = schema_ctx.resource_id  # Could be enhanced with actual filename
                suggestions.append(f"Show me data from {filename}")
                
                if schema_ctx.columns:
                    col_names = [col['name'] for col in schema_ctx.columns[:3]]
                    suggestions.append(f"What are the values in {', '.join(col_names)}?")
        
        # Generic SQL-friendly suggestions
        suggestions.extend([
            "Show me the first 10 rows of my data",
            "Count the total number of records",
            "What columns are available in my data?"
        ])
        
        return suggestions[:5]
    
    def _build_explanation_prompt(self, result: NLQueryResult, context: Optional[QueryContext]) -> str:
        """Build prompt for generating query result explanations."""
        prompt_parts = [
            f"Original question: {result.original_question}",
            f"Query returned {result.row_count} rows",
            ""
        ]
        
        if result.data and len(result.data) > 0:
            prompt_parts.append("Sample results:")
            for i, row in enumerate(result.data[:3]):
                row_str = ", ".join([f"{k}: {v}" for k, v in row.items() if k not in ['client_id', 'user_id']])
                prompt_parts.append(f"  Row {i+1}: {row_str}")
        
        if result.generated_sql:
            prompt_parts.extend([
                "",
                f"SQL query used: {result.generated_sql}"
            ])
        
        prompt_parts.extend([
            "",
            "Please provide a clear, business-friendly explanation of these results.",
            "Focus on insights and what the data tells us.",
            "Keep it concise and avoid technical jargon."
        ])
        
        return "\n".join(prompt_parts)
    
    def clear_context(self, session_id: str) -> bool:
        """Clear query context for a session."""
        if session_id in self._query_contexts:
            del self._query_contexts[session_id]
            logger.debug(f"Cleared context for session {session_id}")
            return True
        return False
    
    def get_context_stats(self) -> Dict[str, Any]:
        """Get statistics about active query contexts."""
        return {
            "active_contexts": len(self._query_contexts),
            "context_ttl_seconds": self._context_ttl
        }
    
    def close(self) -> None:
        """Close the natural language processor and clean up resources."""
        self._query_contexts.clear()
        self.sql_engine.close()
        self.storage_router.close()
        logger.info("Natural Language Processor closed")
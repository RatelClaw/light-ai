"""
Unit tests for Natural Language Processor.

Tests specific functionality and integration with other components.
"""

import pytest
import uuid
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from light_ai.sub_layer_2.natural_language_processor import (
    NaturalLanguageProcessor, 
    NLQueryResult, 
    QueryType,
    QueryContext
)
from light_ai.core.models import AccessLevel
from light_ai.config import Config


class TestNaturalLanguageProcessor:
    """Unit tests for Natural Language Processor functionality."""
    
    def setup_method(self):
        """Set up test environment for each test method."""
        # Create temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        self.test_config = Config()
        
        # Configure test paths
        self.test_config.storage.base_directory = self.temp_dir
        self.test_config.database.duckdb_path = f"{self.temp_dir}/test.db"
        self.test_config.database.sqlite_path = f"{self.temp_dir}/test_metadata.db"
        self.test_config.database.chromadb_path = f"{self.temp_dir}/test_chroma"
        
        # Set a dummy API key for tests
        self.test_config.openrouter.api_key = "test-key-for-unit-tests"
        
        # Create necessary directories
        self.test_config.create_directories()
        
        # Initialize processor
        self.processor = NaturalLanguageProcessor(self.test_config)
    
    def teardown_method(self):
        """Clean up test environment after each test method."""
        if hasattr(self, 'processor'):
            self.processor.close()
        if hasattr(self, 'temp_dir') and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_processor_initialization(self):
        """Test that the processor initializes correctly."""
        assert self.processor is not None
        assert self.processor.config == self.test_config
        assert hasattr(self.processor, 'metadata_registry')
        assert hasattr(self.processor, 'storage_router')
        assert hasattr(self.processor, 'sql_engine')
        assert hasattr(self.processor, 'openai_client')
    
    def test_query_type_classification(self):
        """Test query type classification logic."""
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        context = QueryContext(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            client_id=client_id
        )
        
        # Test structured data queries
        structured_queries = [
            "Show me all customers",
            "Count the total orders",
            "What is the average sales amount?",
            "Group customers by region"
        ]
        
        for query in structured_queries:
            query_type = self.processor._classify_query(query, context)
            assert query_type == QueryType.STRUCTURED_DATA, f"'{query}' should be classified as structured"
        
        # Test unstructured data queries
        unstructured_queries = [
            "Find documents about sales",
            "Search for contract terms",
            "Look for similar content",
            "Extract information from reports"
        ]
        
        for query in unstructured_queries:
            query_type = self.processor._classify_query(query, context)
            assert query_type == QueryType.UNSTRUCTURED_DATA, f"'{query}' should be classified as unstructured"
        
        # Test metadata queries
        metadata_queries = [
            "What data do I have available?",
            "List my resources",
            "Show available data"
        ]
        
        for query in metadata_queries:
            query_type = self.processor._classify_query(query, context)
            assert query_type == QueryType.METADATA_QUERY, f"'{query}' should be classified as metadata"
    
    def test_context_management(self):
        """Test query context creation and management."""
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        # Test context creation
        context = self.processor._get_or_create_context(session_id, user_id, client_id)
        assert context.session_id == session_id
        assert context.user_id == user_id
        assert context.client_id == client_id
        assert len(context.previous_queries) == 0
        
        # Test context reuse
        same_context = self.processor._get_or_create_context(session_id, user_id, client_id)
        assert same_context.session_id == context.session_id
        
        # Test context update
        question = "Test question"
        result = NLQueryResult(
            original_question=question,
            query_type=QueryType.STRUCTURED_DATA,
            resources_used=["resource1", "resource2"]
        )
        
        self.processor._update_context(context, question, result)
        assert question in context.previous_queries
        assert len(context.previous_results) == 1
        assert "resource1" in context.referenced_resources
        assert "resource2" in context.referenced_resources
    
    def test_error_suggestion_generation(self):
        """Test error suggestion generation."""
        # Test empty question
        suggestions = self.processor._generate_error_suggestions("", "Empty question")
        assert len(suggestions) > 0
        assert any("specific" in suggestion.lower() for suggestion in suggestions)
        
        # Test SQL error
        suggestions = self.processor._generate_error_suggestions("test query", "SQL syntax error")
        assert len(suggestions) > 0
        assert any("simpler" in suggestion.lower() or "rephras" in suggestion.lower() for suggestion in suggestions)
        
        # Test access error
        suggestions = self.processor._generate_error_suggestions("test query", "Access denied")
        assert len(suggestions) > 0
        assert any("permission" in suggestion.lower() or "access" in suggestion.lower() for suggestion in suggestions)
        
        # Test API error
        suggestions = self.processor._generate_error_suggestions("test query", "OpenRouter API error 401")
        assert len(suggestions) > 0
        assert any("service" in suggestion.lower() or "try again" in suggestion.lower() for suggestion in suggestions)
    
    def test_sql_generation_prompt_building(self):
        """Test SQL generation prompt building."""
        from light_ai.core.models import ResourceMetadata, ResourceType, DataType
        from light_ai.sub_layer_2.natural_language_processor import SchemaContext
        
        # Create mock schema context
        schema_context = SchemaContext(
            resource_id="test-resource",
            resource_type=ResourceType.STRUCTURED,
            table_name="test_table",
            columns=[
                {"name": "id", "type": "integer", "description": "Primary key"},
                {"name": "name", "type": "varchar", "description": "Customer name"}
            ],
            sample_data=[
                {"id": 1, "name": "John Doe"},
                {"id": 2, "name": "Jane Smith"}
            ],
            statistics={}
        )
        
        context = QueryContext(
            session_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            client_id=str(uuid.uuid4())
        )
        
        question = "Show me all customers"
        prompt = self.processor._build_sql_generation_prompt(question, [schema_context], context)
        
        assert question in prompt
        assert "test_table" in prompt
        assert "id" in prompt
        assert "name" in prompt
        assert "John Doe" in prompt
        assert "SQL:" in prompt
        assert "EXPLANATION:" in prompt
    
    def test_sql_response_parsing(self):
        """Test parsing of LLM SQL responses."""
        # Test well-formatted response
        response = """
        SQL: SELECT * FROM customers WHERE age > 25
        EXPLANATION: This query selects all customers older than 25 years
        CONFIDENCE: 0.9
        """
        
        result = self.processor._parse_sql_response(response)
        assert result['sql'] == "SELECT * FROM customers WHERE age > 25"
        assert "customers older than 25" in result['explanation']
        assert result['confidence'] == 0.9
        
        # Test malformed response
        response = "Just some random text without proper format"
        result = self.processor._parse_sql_response(response)
        assert result['sql'] is None
        assert result['confidence'] == 0.5  # Default confidence
    
    def test_follow_up_suggestions(self):
        """Test follow-up suggestion generation."""
        # Test structured data result
        result = NLQueryResult(
            original_question="Show me customers",
            query_type=QueryType.STRUCTURED_DATA,
            row_count=10
        )
        
        suggestions = self.processor.generate_follow_up_suggestions(result)
        assert len(suggestions) > 0
        assert any("trend" in suggestion.lower() or "top" in suggestion.lower() for suggestion in suggestions)
        
        # Test empty result
        result.row_count = 0
        suggestions = self.processor.generate_follow_up_suggestions(result)
        assert len(suggestions) > 0
        assert any("similar" in suggestion.lower() or "broaden" in suggestion.lower() for suggestion in suggestions)
        
        # Test unstructured data result
        result.query_type = QueryType.UNSTRUCTURED_DATA
        result.row_count = 5
        suggestions = self.processor.generate_follow_up_suggestions(result)
        assert len(suggestions) > 0
        assert any("document" in suggestion.lower() or "theme" in suggestion.lower() for suggestion in suggestions)
    
    def test_cache_and_stats(self):
        """Test context cache management and statistics."""
        # Test initial stats
        stats = self.processor.get_context_stats()
        assert "active_contexts" in stats
        assert "context_ttl_seconds" in stats
        assert stats["active_contexts"] == 0
        
        # Create some contexts
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        context1 = self.processor._get_or_create_context(str(uuid.uuid4()), user_id, client_id)
        context2 = self.processor._get_or_create_context(str(uuid.uuid4()), user_id, client_id)
        
        stats = self.processor.get_context_stats()
        assert stats["active_contexts"] == 2
        
        # Test context clearing
        cleared = self.processor.clear_context(context1.session_id)
        assert cleared is True
        
        stats = self.processor.get_context_stats()
        assert stats["active_contexts"] == 1
        
        # Test clearing non-existent context
        cleared = self.processor.clear_context("non-existent-session")
        assert cleared is False
    
    @patch('light_ai.sub_layer_2.natural_language_processor.OpenAI')
    def test_explanation_generation(self, mock_openai):
        """Test query result explanation generation."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This query shows customer data with 10 results."
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Override the client
        self.processor.openai_client = mock_client
        
        result = NLQueryResult(
            original_question="Show me customers",
            query_type=QueryType.STRUCTURED_DATA,
            data=[{"id": 1, "name": "John"}],
            row_count=1
        )
        
        explanation = self.processor.explain_query_result(result)
        assert "customer data" in explanation.lower()
        assert mock_client.chat.completions.create.called
    
    def test_processor_close(self):
        """Test processor cleanup."""
        # Add some contexts
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        self.processor._get_or_create_context(str(uuid.uuid4()), user_id, client_id)
        
        stats_before = self.processor.get_context_stats()
        assert stats_before["active_contexts"] > 0
        
        # Close processor
        self.processor.close()
        
        # Contexts should be cleared
        stats_after = self.processor.get_context_stats()
        assert stats_after["active_contexts"] == 0
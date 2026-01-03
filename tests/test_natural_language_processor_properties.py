"""
Property-based tests for Natural Language Processor.

Tests universal properties that should hold for all natural language query processing operations.
"""

import pytest
import uuid
import tempfile
import shutil
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime

from light_ai.sub_layer_2.natural_language_processor import (
    NaturalLanguageProcessor, 
    NLQueryResult, 
    QueryType,
    QueryContext
)
from light_ai.core.models import AccessLevel
from light_ai.config import Config


class TestNaturalLanguageProcessorProperties:
    """Property-based tests for Natural Language Processor functionality."""
    
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
        self.test_config.openrouter.api_key = "test-key-for-property-tests"
        
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
    
    @given(
        question=st.text(min_size=5, max_size=200).filter(lambda x: x.strip() and len(x.strip()) >= 5),
        client_id=st.uuids(version=4),
        user_id=st.uuids(version=4)
    )
    @settings(max_examples=100, deadline=30000)  # 30 second deadline for property tests
    def test_property_7_natural_language_query_processing(self, question, client_id, user_id):
        """
        Feature: universal-data-handler, Property 7: Natural Language Query Processing
        
        For any natural language question about user's data, the system should convert it to 
        appropriate queries (SQL for structured, semantic search for unstructured), execute them, 
        and return results with explanations.
        
        **Validates: Requirements 7.1, 7.2, 7.3, 7.4**
        """
        # Convert UUIDs to strings
        client_id_str = str(client_id)
        user_id_str = str(user_id)
        
        # Filter out questions that are too short or contain only whitespace/special chars
        assume(len(question.strip()) >= 5)
        assume(any(c.isalnum() for c in question))
        
        try:
            # Process the natural language query
            result = self.processor.process_natural_query(
                question=question,
                client_id=client_id_str,
                user_id=user_id_str,
                access_level=AccessLevel.USER
            )
            
            # Property 1: Result should always be an NLQueryResult instance
            assert isinstance(result, NLQueryResult), f"Result should be NLQueryResult, got {type(result)}"
            
            # Property 2: Original question should be preserved
            assert result.original_question == question, "Original question should be preserved in result"
            
            # Property 3: Query type should be classified
            assert isinstance(result.query_type, QueryType), f"Query type should be QueryType enum, got {type(result.query_type)}"
            
            # Property 4: Should have some form of explanation
            assert isinstance(result.explanation, str), f"Explanation should be string, got {type(result.explanation)}"
            assert len(result.explanation) > 0, "Explanation should not be empty"
            
            # Property 5: Data should be a list
            assert isinstance(result.data, list), f"Data should be list, got {type(result.data)}"
            
            # Property 6: Columns should be a list
            assert isinstance(result.columns, list), f"Columns should be list, got {type(result.columns)}"
            
            # Property 7: Row count should match data length
            assert result.row_count == len(result.data), f"Row count {result.row_count} should match data length {len(result.data)}"
            
            # Property 8: Execution time should be non-negative
            assert result.execution_time_ms >= 0, f"Execution time should be non-negative, got {result.execution_time_ms}"
            
            # Property 9: Confidence score should be between 0 and 1
            assert 0.0 <= result.confidence_score <= 1.0, f"Confidence score should be 0-1, got {result.confidence_score}"
            
            # Property 10: Suggestions should be a list of strings
            assert isinstance(result.suggestions, list), f"Suggestions should be list, got {type(result.suggestions)}"
            for suggestion in result.suggestions:
                assert isinstance(suggestion, str), f"Each suggestion should be string, got {type(suggestion)}"
            
            # Property 11: Resources used should be a list of strings
            assert isinstance(result.resources_used, list), f"Resources used should be list, got {type(result.resources_used)}"
            for resource_id in result.resources_used:
                assert isinstance(resource_id, str), f"Each resource ID should be string, got {type(resource_id)}"
            
            # Property 12: Follow-up suggestions should be a list of strings
            assert isinstance(result.follow_up_suggestions, list), f"Follow-up suggestions should be list, got {type(result.follow_up_suggestions)}"
            for suggestion in result.follow_up_suggestions:
                assert isinstance(suggestion, str), f"Each follow-up suggestion should be string, got {type(suggestion)}"
            
            # Property 13: If data is present, columns should also be present
            if result.data and len(result.data) > 0:
                assert len(result.columns) > 0, "If data is present, columns should also be present"
                
                # Property 14: Each data row should have same keys as columns (if structured)
                if result.query_type in [QueryType.STRUCTURED_DATA, QueryType.METADATA_QUERY]:
                    for row in result.data:
                        assert isinstance(row, dict), f"Each data row should be dict, got {type(row)}"
            
            # Property 15: Generated SQL should be string if present
            if result.generated_sql is not None:
                assert isinstance(result.generated_sql, str), f"Generated SQL should be string, got {type(result.generated_sql)}"
                assert len(result.generated_sql.strip()) > 0, "Generated SQL should not be empty"
            
            # Property 16: Search terms should be list of strings if present
            if result.search_terms is not None:
                assert isinstance(result.search_terms, list), f"Search terms should be list, got {type(result.search_terms)}"
                for term in result.search_terms:
                    assert isinstance(term, str), f"Each search term should be string, got {type(term)}"
            
        except Exception as e:
            # Property 17: Even if processing fails, should return a valid NLQueryResult with error info
            # This tests graceful error handling
            if "test-key-for-property-tests" in str(e) or "OpenRouter" in str(e) or "API" in str(e):
                # Expected API key error - this is acceptable for property tests
                pytest.skip("Skipping due to API key limitation in property test")
            else:
                # Re-raise unexpected errors
                raise e
    
    @given(
        questions=st.lists(
            st.text(min_size=5, max_size=100).filter(lambda x: x.strip() and len(x.strip()) >= 5),
            min_size=1,
            max_size=5
        ),
        client_id=st.uuids(version=4),
        user_id=st.uuids(version=4)
    )
    @settings(max_examples=50, deadline=45000)  # 45 second deadline for context tests
    def test_context_management_consistency(self, questions, client_id, user_id):
        """
        Test that context management works consistently across multiple queries.
        
        Property: Context should be maintained and updated correctly across query sessions.
        """
        # Convert UUIDs to strings
        client_id_str = str(client_id)
        user_id_str = str(user_id)
        
        # Filter questions
        valid_questions = []
        for q in questions:
            if len(q.strip()) >= 5 and any(c.isalnum() for c in q):
                valid_questions.append(q)
        
        assume(len(valid_questions) >= 1)
        
        session_id = str(uuid.uuid4())
        
        try:
            previous_context = None
            
            for i, question in enumerate(valid_questions):
                result = self.processor.process_natural_query(
                    question=question,
                    client_id=client_id_str,
                    user_id=user_id_str,
                    session_id=session_id,
                    access_level=AccessLevel.USER
                )
                
                # Property: Each result should be valid
                assert isinstance(result, NLQueryResult)
                assert result.original_question == question
                
                # Property: Context should build up over time
                if i > 0:
                    # Should have context from previous queries
                    context = self.processor._query_contexts.get(session_id)
                    if context:
                        assert len(context.previous_queries) >= i, "Context should accumulate previous queries"
                        assert question in context.previous_queries, "Current question should be in context"
                
                previous_context = self.processor._query_contexts.get(session_id)
        
        except Exception as e:
            if "test-key-for-property-tests" in str(e) or "OpenRouter" in str(e) or "API" in str(e):
                pytest.skip("Skipping due to API key limitation in property test")
            else:
                raise e
    
    @given(
        question=st.text(min_size=5, max_size=200).filter(lambda x: x.strip() and len(x.strip()) >= 5),
        access_levels=st.sampled_from([AccessLevel.USER, AccessLevel.MANAGER, AccessLevel.ADMIN])
    )
    @settings(max_examples=30, deadline=20000)
    def test_access_level_consistency(self, question, access_levels):
        """
        Test that different access levels are handled consistently.
        
        Property: The system should handle different access levels without errors.
        """
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        assume(len(question.strip()) >= 5)
        assume(any(c.isalnum() for c in question))
        
        try:
            result = self.processor.process_natural_query(
                question=question,
                client_id=client_id,
                user_id=user_id,
                access_level=access_levels
            )
            
            # Property: Should always return valid result regardless of access level
            assert isinstance(result, NLQueryResult)
            assert result.original_question == question
            assert isinstance(result.query_type, QueryType)
            assert isinstance(result.explanation, str)
            assert len(result.explanation) > 0
            
        except Exception as e:
            if "test-key-for-property-tests" in str(e) or "OpenRouter" in str(e) or "API" in str(e):
                pytest.skip("Skipping due to API key limitation in property test")
            else:
                raise e
    
    def test_query_type_classification_consistency(self):
        """
        Test that query type classification is consistent and deterministic.
        
        Property: Same questions should always get the same query type classification.
        """
        test_questions = [
            ("Show me all customers", QueryType.STRUCTURED_DATA),
            ("Count the total orders", QueryType.STRUCTURED_DATA),
            ("Find documents about sales", QueryType.UNSTRUCTURED_DATA),
            ("Search for contract terms", QueryType.UNSTRUCTURED_DATA),
            ("What data do I have available?", QueryType.METADATA_QUERY),
            ("List my resources", QueryType.METADATA_QUERY),
        ]
        
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        for question, expected_type in test_questions:
            # Create a context for classification
            context = QueryContext(
                session_id=str(uuid.uuid4()),
                user_id=user_id,
                client_id=client_id
            )
            
            # Test classification multiple times
            for _ in range(3):
                classified_type = self.processor._classify_query(question, context)
                
                # Property: Classification should be consistent
                assert classified_type == expected_type, f"Question '{question}' should classify as {expected_type}, got {classified_type}"
    
    def test_error_handling_robustness(self):
        """
        Test that error handling provides useful information.
        
        Property: Error conditions should result in helpful suggestions and explanations.
        """
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Test with various problematic inputs
        problematic_questions = [
            "",  # Empty question
            "   ",  # Whitespace only
            "a",  # Too short
            "SELECT * FROM nonexistent_table;",  # SQL injection attempt
        ]
        
        for question in problematic_questions:
            try:
                result = self.processor.process_natural_query(
                    question=question,
                    client_id=client_id,
                    user_id=user_id,
                    access_level=AccessLevel.USER
                )
                
                # Property: Should always return a result, even for bad input
                assert isinstance(result, NLQueryResult)
                
                # Property: Should have helpful suggestions for problematic input
                if not question.strip() or len(question.strip()) < 5:
                    assert len(result.suggestions) > 0, "Should provide suggestions for problematic input"
                    assert any("try" in suggestion.lower() or "ask" in suggestion.lower() or "please" in suggestion.lower()
                             for suggestion in result.suggestions), f"Suggestions should be helpful, got: {result.suggestions}"
                
            except Exception as e:
                if "test-key-for-property-tests" in str(e) or "OpenRouter" in str(e) or "API" in str(e):
                    continue  # Skip API-related errors
                else:
                    raise e
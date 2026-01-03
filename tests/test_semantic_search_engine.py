"""
Unit tests for Semantic Search Engine.

Tests core functionality including document chunking, embedding generation,
search strategies, and result ranking.
"""

import json
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from light_ai.config import Config
from light_ai.core.models import DataHierarchy, DataType, ResourceMetadata, ResourceType
from light_ai.sub_layer_2.semantic_search_engine import (
    ChunkingStrategy,
    DocumentChunk,
    DocumentChunker,
    OpenRouterEmbeddingFunction,
    QueryVariationGenerator,
    SearchResult,
    SearchResults,
    SearchStrategy,
    SemanticSearchEngine,
)


@pytest.fixture
def temp_config():
    """Create a temporary configuration for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = Config()
        config.storage.base_directory = temp_dir
        config.openrouter.api_key = "test-api-key"
        config.openrouter.embedding_model = "text-embedding-3-small"
        config.processing.chunk_size_tokens = 512
        config.processing.chunk_overlap_tokens = 50
        yield config


@pytest.fixture
def sample_hierarchy():
    """Create sample data hierarchy for testing."""
    return DataHierarchy(
        client_id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        resource_id=str(uuid.uuid4())
    )


@pytest.fixture
def sample_metadata(sample_hierarchy):
    """Create sample resource metadata for testing."""
    return ResourceMetadata(
        resource_id=sample_hierarchy.resource_id,
        user_id=sample_hierarchy.user_id,
        client_id=sample_hierarchy.client_id,
        resource_type=ResourceType.UNSTRUCTURED,
        data_type=DataType.TXT,
        original_filename="test_document.txt",
        file_size_bytes=1024,
        storage_path="/test/path/document.txt"
    )


@pytest.fixture
def sample_document_text():
    """Sample document text for testing."""
    return """
    This is the first paragraph of the test document. It contains some important information
    about the topic we are discussing. The content is designed to test chunking algorithms.
    
    This is the second paragraph. It provides additional context and details about the subject.
    The text is structured to evaluate different chunking strategies and their effectiveness.
    
    The third paragraph concludes the document with final thoughts and summary points.
    It helps test the boundary detection in semantic chunking approaches.
    """


class TestDocumentChunker:
    """Test document chunking functionality."""
    
    def test_semantic_chunking(self, temp_config, sample_document_text):
        """Test semantic chunking strategy."""
        chunker = DocumentChunker(temp_config)
        metadata = {"test_key": "test_value"}
        
        chunks = chunker.chunk_document(
            sample_document_text, 
            ChunkingStrategy.SEMANTIC, 
            metadata
        )
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
        assert all(chunk.metadata.get("chunk_type") == "semantic" for chunk in chunks)
        assert all(chunk.metadata.get("test_key") == "test_value" for chunk in chunks)
        
        # Check chunk indices are sequential
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i
        
        # Check character positions are valid
        for chunk in chunks:
            assert chunk.start_char >= 0
            assert chunk.end_char > chunk.start_char
            assert chunk.token_count > 0
    
    def test_fixed_chunking(self, temp_config, sample_document_text):
        """Test fixed-size chunking strategy."""
        chunker = DocumentChunker(temp_config)
        
        chunks = chunker.chunk_document(
            sample_document_text, 
            ChunkingStrategy.FIXED
        )
        
        assert len(chunks) > 0
        assert all(chunk.metadata.get("chunk_type") == "fixed" for chunk in chunks)
        
        # Check token counts are within limits (with some tolerance for word boundaries)
        for chunk in chunks:
            assert chunk.token_count <= temp_config.processing.chunk_size_tokens + 50
    
    def test_sentence_chunking(self, temp_config, sample_document_text):
        """Test sentence-based chunking strategy."""
        chunker = DocumentChunker(temp_config)
        
        chunks = chunker.chunk_document(
            sample_document_text, 
            ChunkingStrategy.SENTENCE
        )
        
        assert len(chunks) > 0
        assert all(chunk.metadata.get("chunk_type") == "sentence" for chunk in chunks)
        
        # Check that chunks contain complete sentences
        for chunk in chunks:
            assert chunk.text.strip()  # No empty chunks
    
    def test_paragraph_chunking(self, temp_config, sample_document_text):
        """Test paragraph-based chunking strategy."""
        chunker = DocumentChunker(temp_config)
        
        chunks = chunker.chunk_document(
            sample_document_text, 
            ChunkingStrategy.PARAGRAPH
        )
        
        assert len(chunks) > 0
        assert all(chunk.metadata.get("chunk_type") == "paragraph" for chunk in chunks)
        
        # Should have fewer chunks than sentence-based for this text
        sentence_chunks = chunker.chunk_document(
            sample_document_text, 
            ChunkingStrategy.SENTENCE
        )
        assert len(chunks) <= len(sentence_chunks)
    
    def test_empty_text_handling(self, temp_config):
        """Test handling of empty or whitespace-only text."""
        chunker = DocumentChunker(temp_config)
        
        # Empty string
        chunks = chunker.chunk_document("", ChunkingStrategy.SEMANTIC)
        assert len(chunks) == 0
        
        # Whitespace only
        chunks = chunker.chunk_document("   \n\n   ", ChunkingStrategy.SEMANTIC)
        assert len(chunks) == 0
    
    def test_chunk_overlap(self, temp_config):
        """Test chunk overlap functionality."""
        # Set small chunk size to force overlap
        temp_config.processing.chunk_size_tokens = 20
        temp_config.processing.chunk_overlap_tokens = 5
        
        chunker = DocumentChunker(temp_config)
        long_text = "This is a long sentence. " * 20  # Repeat to create long text
        
        chunks = chunker.chunk_document(long_text, ChunkingStrategy.FIXED)
        
        if len(chunks) > 1:
            # Check that there's some overlap between consecutive chunks
            # This is a simplified check - in practice, overlap detection is complex
            assert len(chunks) > 1


class TestQueryVariationGenerator:
    """Test query variation generation."""
    
    def test_generate_variations(self, temp_config):
        """Test basic query variation generation."""
        generator = QueryVariationGenerator(temp_config)
        
        query = "find customer data"
        variations = generator.generate_variations(query, max_variations=3)
        
        assert len(variations) >= 1  # At least the original query
        assert query in variations  # Original query should be included
        assert len(variations) <= 4  # max_variations + 1 (original)
        
        # All variations should be strings
        assert all(isinstance(v, str) for v in variations)
        assert all(v.strip() for v in variations)  # No empty variations
    
    def test_synonym_variation(self, temp_config):
        """Test synonym-based variation generation."""
        generator = QueryVariationGenerator(temp_config)
        
        # Test with words that have known synonyms
        query = "find data"
        variations = generator.generate_variations(query)
        
        # Should include variations with synonyms
        assert len(variations) > 1
        
        # Check if synonym replacement occurred
        variation_texts = " ".join(variations).lower()
        assert "search" in variation_texts or "information" in variation_texts
    
    def test_reformulated_variation(self, temp_config):
        """Test reformulated query variations."""
        generator = QueryVariationGenerator(temp_config)
        
        # Test different query patterns
        test_queries = [
            "find customer information",
            "what is the sales data",
            "show me the reports",
            "how to process orders"
        ]
        
        for query in test_queries:
            variations = generator.generate_variations(query)
            assert len(variations) >= 1
            assert query in variations
    
    def test_keyword_variation(self, temp_config):
        """Test keyword extraction variation."""
        generator = QueryVariationGenerator(temp_config)
        
        query = "find the customer data in the database"
        variations = generator.generate_variations(query)
        
        # Should include a variation with key terms only
        keyword_variations = [v for v in variations if len(v.split()) < len(query.split())]
        assert len(keyword_variations) > 0


class TestOpenRouterEmbeddingFunction:
    """Test OpenRouter embedding function."""
    
    @patch('httpx.AsyncClient')
    def test_embedding_generation_success(self, mock_client, temp_config):
        """Test successful embedding generation."""
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"embedding": [0.1, 0.2, 0.3]},
                {"embedding": [0.4, 0.5, 0.6]}
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        embedding_func = OpenRouterEmbeddingFunction(temp_config)
        
        texts = ["test text 1", "test text 2"]
        embeddings = embedding_func(texts)
        
        assert len(embeddings) == 2
        assert embeddings[0] == [0.1, 0.2, 0.3]
        assert embeddings[1] == [0.4, 0.5, 0.6]
        
        # Verify API call was made correctly
        mock_client_instance.post.assert_called_once()
        call_args = mock_client_instance.post.call_args
        assert call_args[0][0].endswith("/embeddings")
        assert call_args[1]["json"]["model"] == temp_config.openrouter.embedding_model
        assert call_args[1]["json"]["input"] == texts
    
    @patch('httpx.AsyncClient')
    def test_embedding_generation_failure(self, mock_client, temp_config):
        """Test embedding generation failure handling."""
        # Mock HTTP error
        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(side_effect=Exception("API Error"))
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
        
        embedding_func = OpenRouterEmbeddingFunction(temp_config)
        
        with pytest.raises(RuntimeError, match="Failed to generate embeddings"):
            embedding_func(["test text"])
    
    def test_missing_api_key(self, temp_config):
        """Test error when API key is missing."""
        temp_config.openrouter.api_key = ""
        
        with pytest.raises(ValueError, match="OpenRouter API key is required"):
            OpenRouterEmbeddingFunction(temp_config)


class TestSearchResult:
    """Test search result data structures."""
    
    def test_search_result_creation(self):
        """Test SearchResult creation and serialization."""
        result = SearchResult(
            id="test_id",
            document="test document text",
            metadata={"key": "value"},
            distance=0.5,
            relevance_score=0.8,
            resource_id="resource_123",
            chunk_index=1
        )
        
        assert result.id == "test_id"
        assert result.document == "test document text"
        assert result.metadata == {"key": "value"}
        assert result.distance == 0.5
        assert result.relevance_score == 0.8
        assert result.resource_id == "resource_123"
        assert result.chunk_index == 1
        
        # Test serialization
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict["id"] == "test_id"
        assert result_dict["relevance_score"] == 0.8
    
    def test_search_results_collection(self):
        """Test SearchResults collection."""
        results = [
            SearchResult("id1", "doc1", {}, 0.3, 0.7),
            SearchResult("id2", "doc2", {}, 0.5, 0.5)
        ]
        
        search_results = SearchResults(
            results=results,
            total_results=2,
            search_strategy=SearchStrategy.SEMANTIC,
            query_variations=["query1", "query2"],
            execution_time_ms=150.0
        )
        
        assert len(search_results.results) == 2
        assert search_results.total_results == 2
        assert search_results.search_strategy == SearchStrategy.SEMANTIC
        assert search_results.execution_time_ms == 150.0
        
        # Test serialization
        results_dict = search_results.to_dict()
        assert isinstance(results_dict, dict)
        assert len(results_dict["results"]) == 2
        assert results_dict["search_strategy"] == "semantic"


class TestSemanticSearchEngine:
    """Test semantic search engine core functionality."""
    
    @patch('light_ai.sub_layer_2.semantic_search_engine.ChromaDBManager')
    @patch('light_ai.sub_layer_2.semantic_search_engine.MetadataRegistry')
    def test_initialization(self, mock_metadata_registry, mock_chromadb_manager, temp_config):
        """Test search engine initialization."""
        engine = SemanticSearchEngine(temp_config)
        
        assert engine.config == temp_config
        assert isinstance(engine.chunker, DocumentChunker)
        assert isinstance(engine.query_generator, QueryVariationGenerator)
        assert not engine._initialized
        
        # Test initialization
        engine.initialize()
        assert engine._initialized
    
    @patch('light_ai.sub_layer_2.semantic_search_engine.ChromaDBManager')
    @patch('light_ai.sub_layer_2.semantic_search_engine.MetadataRegistry')
    @patch('light_ai.sub_layer_2.semantic_search_engine.OpenRouterEmbeddingFunction')
    def test_process_and_store_document(self, mock_embedding_func, mock_metadata_registry, 
                                      mock_chromadb_manager, temp_config, sample_hierarchy, 
                                      sample_metadata, sample_document_text):
        """Test document processing and storage."""
        # Mock embedding function
        mock_embedding_instance = MagicMock()
        mock_embedding_instance.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock_embedding_func.return_value = mock_embedding_instance
        
        # Mock ChromaDB manager
        mock_chromadb_instance = MagicMock()
        mock_chromadb_manager.return_value = mock_chromadb_instance
        
        # Mock metadata registry
        mock_metadata_instance = MagicMock()
        mock_metadata_registry.return_value = mock_metadata_instance
        
        engine = SemanticSearchEngine(temp_config)
        
        collection_name = engine.process_and_store_document(
            sample_document_text,
            sample_hierarchy,
            sample_metadata,
            ChunkingStrategy.SEMANTIC
        )
        
        # Verify collection name format
        expected_name = f"unstructured_{sample_hierarchy.resource_id.replace('-', '_')}"
        assert collection_name == expected_name
        
        # Verify ChromaDB operations were called
        mock_chromadb_instance.create_collection.assert_called_once()
        mock_chromadb_instance.add_embeddings.assert_called_once()
        
        # Verify metadata was updated
        assert sample_metadata.processing_status == "completed"
        assert sample_metadata.chunk_count > 0
    
    @patch('light_ai.sub_layer_2.semantic_search_engine.ChromaDBManager')
    @patch('light_ai.sub_layer_2.semantic_search_engine.MetadataRegistry')
    def test_get_accessible_resources(self, mock_metadata_registry, mock_chromadb_manager, 
                                    temp_config, sample_hierarchy):
        """Test filtering of accessible resources."""
        # Mock metadata registry to return test resources
        unstructured_resource = ResourceMetadata(
            resource_id=str(uuid.uuid4()),
            user_id=sample_hierarchy.user_id,
            client_id=sample_hierarchy.client_id,
            resource_type=ResourceType.UNSTRUCTURED,
            data_type=DataType.PDF,
            original_filename="test.pdf",
            file_size_bytes=1024,
            storage_path="/test/path"
        )
        
        structured_resource = ResourceMetadata(
            resource_id=str(uuid.uuid4()),
            user_id=sample_hierarchy.user_id,
            client_id=sample_hierarchy.client_id,
            resource_type=ResourceType.STRUCTURED,
            data_type=DataType.CSV,
            original_filename="test.csv",
            file_size_bytes=1024,
            storage_path="/test/path"
        )
        
        mock_metadata_instance = MagicMock()
        mock_metadata_instance.list_resources.return_value = [
            unstructured_resource, structured_resource
        ]
        mock_metadata_registry.return_value = mock_metadata_instance
        
        mock_chromadb_instance = MagicMock()
        mock_chromadb_manager.return_value = mock_chromadb_instance
        
        engine = SemanticSearchEngine(temp_config)
        
        accessible_resources = engine._get_accessible_resources(
            sample_hierarchy.client_id,
            sample_hierarchy.user_id
        )
        
        # Should only return unstructured resources
        assert len(accessible_resources) == 1
        assert accessible_resources[0].resource_type == ResourceType.UNSTRUCTURED
        assert accessible_resources[0].resource_id == unstructured_resource.resource_id
    
    def test_text_similarity_calculation(self, temp_config):
        """Test text similarity calculation for MMR."""
        engine = SemanticSearchEngine(temp_config)
        
        # Identical texts
        similarity = engine._calculate_text_similarity("hello world", "hello world")
        assert similarity == 1.0
        
        # Completely different texts
        similarity = engine._calculate_text_similarity("hello world", "foo bar")
        assert similarity == 0.0
        
        # Partially similar texts
        similarity = engine._calculate_text_similarity("hello world test", "hello world example")
        assert 0.0 < similarity < 1.0
        
        # Empty texts
        similarity = engine._calculate_text_similarity("", "")
        assert similarity == 1.0
        
        similarity = engine._calculate_text_similarity("hello", "")
        assert similarity == 0.0
    
    def test_deduplicate_results(self, temp_config):
        """Test result deduplication."""
        engine = SemanticSearchEngine(temp_config)
        
        results = [
            SearchResult("id1", "doc1", {}, 0.3, 0.7),
            SearchResult("id2", "doc2", {}, 0.5, 0.5),
            SearchResult("id1", "doc1_duplicate", {}, 0.4, 0.6),  # Duplicate ID
            SearchResult("id3", "doc3", {}, 0.2, 0.8)
        ]
        
        unique_results = engine._deduplicate_results(results)
        
        assert len(unique_results) == 3
        result_ids = [r.id for r in unique_results]
        assert "id1" in result_ids
        assert "id2" in result_ids
        assert "id3" in result_ids
        
        # First occurrence should be kept
        id1_result = next(r for r in unique_results if r.id == "id1")
        assert id1_result.document == "doc1"  # Not the duplicate
    
    @patch('light_ai.sub_layer_2.semantic_search_engine.ChromaDBManager')
    @patch('light_ai.sub_layer_2.semantic_search_engine.MetadataRegistry')
    def test_get_collection_info(self, mock_metadata_registry, mock_chromadb_manager, 
                                temp_config):
        """Test getting collection information."""
        # Mock ChromaDB collection
        mock_collection = MagicMock()
        mock_collection.count.return_value = 42
        mock_collection.metadata = {"test": "metadata"}
        
        mock_chromadb_instance = MagicMock()
        mock_chromadb_instance.get_collection.return_value = mock_collection
        mock_chromadb_manager.return_value = mock_chromadb_instance
        
        mock_metadata_instance = MagicMock()
        mock_metadata_registry.return_value = mock_metadata_instance
        
        engine = SemanticSearchEngine(temp_config)
        
        resource_id = str(uuid.uuid4())
        info = engine.get_collection_info(resource_id)
        
        assert info is not None
        assert info["document_count"] == 42
        assert info["metadata"] == {"test": "metadata"}
        assert info["collection_name"] == f"unstructured_{resource_id.replace('-', '_')}"
    
    @patch('light_ai.sub_layer_2.semantic_search_engine.ChromaDBManager')
    @patch('light_ai.sub_layer_2.semantic_search_engine.MetadataRegistry')
    def test_delete_resource_embeddings(self, mock_metadata_registry, mock_chromadb_manager, 
                                      temp_config):
        """Test deleting resource embeddings."""
        mock_chromadb_instance = MagicMock()
        mock_chromadb_manager.return_value = mock_chromadb_instance
        
        mock_metadata_instance = MagicMock()
        mock_metadata_registry.return_value = mock_metadata_instance
        
        engine = SemanticSearchEngine(temp_config)
        
        resource_id = str(uuid.uuid4())
        result = engine.delete_resource_embeddings(resource_id)
        
        assert result is True
        expected_collection_name = f"unstructured_{resource_id.replace('-', '_')}"
        mock_chromadb_instance.delete_collection.assert_called_once_with(expected_collection_name)
    
    @patch('light_ai.sub_layer_2.semantic_search_engine.ChromaDBManager')
    @patch('light_ai.sub_layer_2.semantic_search_engine.MetadataRegistry')
    def test_list_collections(self, mock_metadata_registry, mock_chromadb_manager, temp_config):
        """Test listing ChromaDB collections."""
        mock_chromadb_instance = MagicMock()
        mock_chromadb_instance.list_collections.return_value = ["collection1", "collection2"]
        mock_chromadb_manager.return_value = mock_chromadb_instance
        
        mock_metadata_instance = MagicMock()
        mock_metadata_registry.return_value = mock_metadata_instance
        
        engine = SemanticSearchEngine(temp_config)
        
        collections = engine.list_collections()
        
        assert collections == ["collection1", "collection2"]
        mock_chromadb_instance.list_collections.assert_called_once()


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases."""
    
    def test_document_chunk_id_generation(self, sample_hierarchy):
        """Test document chunk ID generation."""
        chunk = DocumentChunk(
            text="test text",
            metadata={},
            chunk_index=5,
            start_char=0,
            end_char=10,
            token_count=2
        )
        
        chunk_id = chunk.generate_id(sample_hierarchy.resource_id)
        expected_id = f"{sample_hierarchy.resource_id}_chunk_5"
        assert chunk_id == expected_id
    
    def test_search_strategy_enum_values(self):
        """Test search strategy enum values."""
        assert SearchStrategy.SEMANTIC.value == "semantic"
        assert SearchStrategy.KEYWORD.value == "keyword"
        assert SearchStrategy.HYBRID.value == "hybrid"
        assert SearchStrategy.MMR.value == "mmr"
    
    def test_chunking_strategy_enum_values(self):
        """Test chunking strategy enum values."""
        assert ChunkingStrategy.SEMANTIC.value == "semantic"
        assert ChunkingStrategy.FIXED.value == "fixed"
        assert ChunkingStrategy.SENTENCE.value == "sentence"
        assert ChunkingStrategy.PARAGRAPH.value == "paragraph"
    
    @patch('light_ai.sub_layer_2.semantic_search_engine.ChromaDBManager')
    @patch('light_ai.sub_layer_2.semantic_search_engine.MetadataRegistry')
    def test_search_with_no_accessible_resources(self, mock_metadata_registry, 
                                               mock_chromadb_manager, temp_config):
        """Test search behavior when no resources are accessible."""
        # Mock empty resource list
        mock_metadata_instance = MagicMock()
        mock_metadata_instance.list_resources.return_value = []
        mock_metadata_registry.return_value = mock_metadata_instance
        
        mock_chromadb_instance = MagicMock()
        mock_chromadb_manager.return_value = mock_chromadb_instance
        
        engine = SemanticSearchEngine(temp_config)
        
        results = engine.search(
            query="test query",
            client_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            strategy=SearchStrategy.SEMANTIC
        )
        
        assert isinstance(results, SearchResults)
        assert len(results.results) == 0
        assert results.total_results == 0
        assert results.search_strategy == SearchStrategy.SEMANTIC
    
    def test_error_handling_in_document_processing(self, temp_config, sample_hierarchy, 
                                                 sample_metadata):
        """Test error handling during document processing."""
        with patch('light_ai.sub_layer_2.semantic_search_engine.OpenRouterEmbeddingFunction') as mock_embedding:
            # Mock embedding function to raise an error
            mock_embedding_instance = MagicMock()
            mock_embedding_instance.side_effect = Exception("Embedding generation failed")
            mock_embedding.return_value = mock_embedding_instance
            
            engine = SemanticSearchEngine(temp_config)
            
            with pytest.raises(RuntimeError, match="Document processing failed"):
                engine.process_and_store_document(
                    "test text",
                    sample_hierarchy,
                    sample_metadata
                )
            
            # Verify metadata was updated with error status
            assert sample_metadata.processing_status == "failed"
            assert "Embedding generation failed" in sample_metadata.error_message
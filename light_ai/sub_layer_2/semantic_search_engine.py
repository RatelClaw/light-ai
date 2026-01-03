"""
Semantic Search Engine for Universal Data Handler.

Provides AI-powered search capabilities for unstructured data using ChromaDB
with multiple search strategies, embedding generation via OpenRouter, and
advanced result ranking and relevance scoring.
"""

import asyncio
import hashlib
import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx
import numpy as np
from chromadb.utils import embedding_functions

from ..config import Config, get_config
from ..core.models import DataHierarchy, ResourceMetadata, ResourceType
from ..logger import get_logger
from ..storage.database_managers import ChromaDBManager
from ..storage.metadata_registry import MetadataRegistry

logger = get_logger(__name__)


class SearchStrategy(Enum):
    """Available search strategies for semantic search."""
    SEMANTIC = "semantic"           # Pure embedding-based similarity
    KEYWORD = "keyword"             # Traditional text matching
    HYBRID = "hybrid"               # Combination of semantic and keyword
    MMR = "mmr"                     # Maximal Marginal Relevance for diversity


class ChunkingStrategy(Enum):
    """Available chunking strategies for document processing."""
    SEMANTIC = "semantic"           # Semantic-aware chunking
    FIXED = "fixed"                 # Fixed token size chunking
    SENTENCE = "sentence"           # Sentence-based chunking
    PARAGRAPH = "paragraph"         # Paragraph-based chunking


@dataclass
class SearchResult:
    """Individual search result with metadata and scoring."""
    id: str
    document: str
    metadata: Dict[str, Any]
    distance: float
    relevance_score: float = 0.0
    resource_id: str = ""
    chunk_index: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "document": self.document,
            "metadata": self.metadata,
            "distance": self.distance,
            "relevance_score": self.relevance_score,
            "resource_id": self.resource_id,
            "chunk_index": self.chunk_index
        }


@dataclass
class SearchResults:
    """Collection of search results with aggregated metadata."""
    results: List[SearchResult] = field(default_factory=list)
    total_results: int = 0
    search_strategy: SearchStrategy = SearchStrategy.SEMANTIC
    query_variations: List[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "results": [r.to_dict() for r in self.results],
            "total_results": self.total_results,
            "search_strategy": self.search_strategy.value,
            "query_variations": self.query_variations,
            "execution_time_ms": self.execution_time_ms
        }


@dataclass
class DocumentChunk:
    """Document chunk with metadata for embedding storage."""
    text: str
    metadata: Dict[str, Any]
    chunk_index: int
    start_char: int
    end_char: int
    token_count: int
    
    def generate_id(self, resource_id: str) -> str:
        """Generate unique ID for the chunk."""
        return f"{resource_id}_chunk_{self.chunk_index}"


class OpenRouterEmbeddingFunction:
    """Custom embedding function for OpenRouter API integration."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize OpenRouter embedding function.
        
        Args:
            config: Optional configuration instance
        """
        self.config = config or get_config()
        self.api_key = self.config.openrouter.api_key
        self.base_url = self.config.openrouter.base_url
        self.embedding_model = self.config.openrouter.embedding_model
        self.timeout = self.config.openrouter.timeout_seconds
        
        if not self.api_key:
            raise ValueError("OpenRouter API key is required for embedding generation")
    
    async def _generate_embeddings_async(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings asynchronously via OpenRouter API."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # OpenRouter uses OpenAI-compatible embedding endpoint
            payload = {
                "model": self.embedding_model,
                "input": texts
            }
            
            try:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                embeddings = [item["embedding"] for item in data["data"]]
                
                logger.debug(f"Generated {len(embeddings)} embeddings via OpenRouter")
                return embeddings
                
            except httpx.HTTPError as e:
                logger.error(f"OpenRouter API error: {e}")
                raise RuntimeError(f"Failed to generate embeddings: {e}")
    
    def __call__(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        return asyncio.run(self._generate_embeddings_async(texts))


class DocumentChunker:
    """Advanced document chunking with multiple strategies."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize document chunker.
        
        Args:
            config: Optional configuration instance
        """
        self.config = config or get_config()
        self.chunk_size = self.config.processing.chunk_size_tokens
        self.chunk_overlap = self.config.processing.chunk_overlap_tokens
    
    def chunk_document(self, text: str, strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC,
                      metadata: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        """
        Chunk a document using the specified strategy.
        
        Args:
            text: Document text to chunk
            strategy: Chunking strategy to use
            metadata: Optional metadata to include with each chunk
            
        Returns:
            List[DocumentChunk]: List of document chunks
        """
        metadata = metadata or {}
        
        if strategy == ChunkingStrategy.SEMANTIC:
            return self._semantic_chunking(text, metadata)
        elif strategy == ChunkingStrategy.FIXED:
            return self._fixed_chunking(text, metadata)
        elif strategy == ChunkingStrategy.SENTENCE:
            return self._sentence_chunking(text, metadata)
        elif strategy == ChunkingStrategy.PARAGRAPH:
            return self._paragraph_chunking(text, metadata)
        else:
            raise ValueError(f"Unsupported chunking strategy: {strategy}")
    
    def _semantic_chunking(self, text: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """
        Semantic-aware chunking that preserves meaning boundaries.
        
        This implementation uses a combination of sentence boundaries and
        semantic coherence to create meaningful chunks.
        """
        # Split into sentences first
        sentences = self._split_into_sentences(text)
        chunks = []
        current_chunk = ""
        current_start = 0
        chunk_index = 0
        
        for sentence in sentences:
            # Estimate token count (rough approximation: 1 token ≈ 4 characters)
            potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
            estimated_tokens = len(potential_chunk) // 4
            
            if estimated_tokens <= self.chunk_size:
                current_chunk = potential_chunk
            else:
                # Create chunk from current content
                if current_chunk:
                    chunk_end = current_start + len(current_chunk)
                    chunks.append(DocumentChunk(
                        text=current_chunk.strip(),
                        metadata={**metadata, "chunk_type": "semantic"},
                        chunk_index=chunk_index,
                        start_char=current_start,
                        end_char=chunk_end,
                        token_count=len(current_chunk) // 4
                    ))
                    chunk_index += 1
                
                # Start new chunk with overlap
                if chunks and self.chunk_overlap > 0:
                    # Include last part of previous chunk for overlap
                    overlap_text = current_chunk[-self.chunk_overlap * 4:] if current_chunk else ""
                    current_chunk = overlap_text + " " + sentence if overlap_text else sentence
                    current_start = chunk_end - len(overlap_text)
                else:
                    current_chunk = sentence
                    current_start = chunk_end if chunks else 0
        
        # Add final chunk
        if current_chunk:
            chunk_end = current_start + len(current_chunk)
            chunks.append(DocumentChunk(
                text=current_chunk.strip(),
                metadata={**metadata, "chunk_type": "semantic"},
                chunk_index=chunk_index,
                start_char=current_start,
                end_char=chunk_end,
                token_count=len(current_chunk) // 4
            ))
        
        return chunks
    
    def _fixed_chunking(self, text: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Fixed-size chunking with token-based splitting."""
        chunks = []
        chunk_size_chars = self.chunk_size * 4  # Rough token-to-char conversion
        overlap_chars = self.chunk_overlap * 4
        
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = min(start + chunk_size_chars, len(text))
            
            # Try to break at word boundary
            if end < len(text):
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(DocumentChunk(
                    text=chunk_text,
                    metadata={**metadata, "chunk_type": "fixed"},
                    chunk_index=chunk_index,
                    start_char=start,
                    end_char=end,
                    token_count=len(chunk_text) // 4
                ))
                chunk_index += 1
            
            # Move start position with overlap
            start = max(start + chunk_size_chars - overlap_chars, end)
        
        return chunks
    
    def _sentence_chunking(self, text: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Sentence-based chunking that keeps sentences intact."""
        sentences = self._split_into_sentences(text)
        chunks = []
        current_chunk = ""
        current_start = 0
        chunk_index = 0
        
        for sentence in sentences:
            potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
            estimated_tokens = len(potential_chunk) // 4
            
            if estimated_tokens <= self.chunk_size:
                current_chunk = potential_chunk
            else:
                # Create chunk from current sentences
                if current_chunk:
                    chunk_end = current_start + len(current_chunk)
                    chunks.append(DocumentChunk(
                        text=current_chunk.strip(),
                        metadata={**metadata, "chunk_type": "sentence"},
                        chunk_index=chunk_index,
                        start_char=current_start,
                        end_char=chunk_end,
                        token_count=len(current_chunk) // 4
                    ))
                    chunk_index += 1
                    current_start = chunk_end
                
                current_chunk = sentence
        
        # Add final chunk
        if current_chunk:
            chunk_end = current_start + len(current_chunk)
            chunks.append(DocumentChunk(
                text=current_chunk.strip(),
                metadata={**metadata, "chunk_type": "sentence"},
                chunk_index=chunk_index,
                start_char=current_start,
                end_char=chunk_end,
                token_count=len(current_chunk) // 4
            ))
        
        return chunks
    
    def _paragraph_chunking(self, text: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Paragraph-based chunking that preserves paragraph boundaries."""
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        current_start = 0
        chunk_index = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            potential_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
            estimated_tokens = len(potential_chunk) // 4
            
            if estimated_tokens <= self.chunk_size:
                current_chunk = potential_chunk
            else:
                # Create chunk from current paragraphs
                if current_chunk:
                    chunk_end = current_start + len(current_chunk)
                    chunks.append(DocumentChunk(
                        text=current_chunk.strip(),
                        metadata={**metadata, "chunk_type": "paragraph"},
                        chunk_index=chunk_index,
                        start_char=current_start,
                        end_char=chunk_end,
                        token_count=len(current_chunk) // 4
                    ))
                    chunk_index += 1
                    current_start = chunk_end
                
                current_chunk = paragraph
        
        # Add final chunk
        if current_chunk:
            chunk_end = current_start + len(current_chunk)
            chunks.append(DocumentChunk(
                text=current_chunk.strip(),
                metadata={**metadata, "chunk_type": "paragraph"},
                chunk_index=chunk_index,
                start_char=current_start,
                end_char=chunk_end,
                token_count=len(current_chunk) // 4
            ))
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using simple regex patterns."""
        # Simple sentence splitting - in production, consider using spaCy or NLTK
        sentence_endings = r'[.!?]+\s+'
        sentences = re.split(sentence_endings, text)
        return [s.strip() for s in sentences if s.strip()]


class QueryVariationGenerator:
    """Generates query variations for improved search coverage."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize query variation generator.
        
        Args:
            config: Optional configuration instance
        """
        self.config = config or get_config()
    
    def generate_variations(self, query: str, max_variations: int = 3) -> List[str]:
        """
        Generate query variations for multi-query retrieval.
        
        Args:
            query: Original search query
            max_variations: Maximum number of variations to generate
            
        Returns:
            List[str]: List of query variations including the original
        """
        variations = [query]  # Always include original query
        
        # Generate synonym-based variations
        synonym_variation = self._generate_synonym_variation(query)
        if synonym_variation and synonym_variation != query:
            variations.append(synonym_variation)
        
        # Generate reformulated variations
        reformulated = self._generate_reformulated_variation(query)
        if reformulated and reformulated != query:
            variations.append(reformulated)
        
        # Generate keyword extraction variation
        keyword_variation = self._generate_keyword_variation(query)
        if keyword_variation and keyword_variation != query:
            variations.append(keyword_variation)
        
        return variations[:max_variations + 1]  # +1 to include original
    
    def _generate_synonym_variation(self, query: str) -> str:
        """Generate variation with common synonyms."""
        # Simple synonym replacement - in production, use a proper thesaurus
        synonyms = {
            'find': 'search',
            'search': 'find',
            'show': 'display',
            'display': 'show',
            'get': 'retrieve',
            'retrieve': 'get',
            'data': 'information',
            'information': 'data',
            'document': 'file',
            'file': 'document'
        }
        
        words = query.lower().split()
        for i, word in enumerate(words):
            if word in synonyms:
                words[i] = synonyms[word]
                break  # Only replace one word to avoid over-modification
        
        return ' '.join(words)
    
    def _generate_reformulated_variation(self, query: str) -> str:
        """Generate reformulated variation of the query."""
        # Simple reformulation patterns
        if query.startswith('find'):
            return query.replace('find', 'what is', 1)
        elif query.startswith('what'):
            return query.replace('what is', 'find', 1)
        elif query.startswith('show'):
            return query.replace('show', 'list', 1)
        elif query.startswith('how'):
            return query.replace('how', 'what is the process for', 1)
        
        return query
    
    def _generate_keyword_variation(self, query: str) -> str:
        """Generate variation focusing on key terms."""
        # Extract key terms (simple approach - remove common words)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must'}
        
        words = [word.lower() for word in query.split() if word.lower() not in stop_words]
        return ' '.join(words) if words else query


class SemanticSearchEngine:
    """
    Advanced semantic search engine with multiple strategies and optimization.
    
    Provides comprehensive search capabilities including semantic similarity,
    keyword matching, hybrid search, and MMR for diverse results.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize semantic search engine.
        
        Args:
            config: Optional configuration instance
        """
        self.config = config or get_config()
        self.chromadb_manager = ChromaDBManager(self.config)
        self.metadata_registry = MetadataRegistry(self.config)
        self.embedding_function = OpenRouterEmbeddingFunction(self.config)
        self.chunker = DocumentChunker(self.config)
        self.query_generator = QueryVariationGenerator(self.config)
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize the semantic search engine."""
        if not self._initialized:
            logger.info("Initializing semantic search engine...")
            self.chromadb_manager.initialize()
            self.metadata_registry.initialize()
            self._initialized = True
            logger.info("Semantic search engine initialized successfully")
    
    def process_and_store_document(self, text: str, hierarchy: DataHierarchy,
                                 metadata: ResourceMetadata,
                                 chunking_strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC) -> str:
        """
        Process a document, chunk it, generate embeddings, and store in ChromaDB.
        
        Args:
            text: Document text to process
            hierarchy: Data hierarchy for the document
            metadata: Resource metadata
            chunking_strategy: Strategy to use for chunking
            
        Returns:
            str: Collection name where the document was stored
            
        Raises:
            RuntimeError: If processing or storage fails
        """
        self.initialize()
        
        try:
            start_time = datetime.utcnow()
            
            # Chunk the document
            chunk_metadata = {
                "resource_id": hierarchy.resource_id,
                "user_id": hierarchy.user_id,
                "client_id": hierarchy.client_id,
                "original_filename": metadata.original_filename,
                "data_type": metadata.data_type.value,
                "created_at": metadata.created_at.isoformat()
            }
            
            chunks = self.chunker.chunk_document(text, chunking_strategy, chunk_metadata)
            
            if not chunks:
                raise ValueError("No chunks generated from document")
            
            # Generate embeddings for all chunks
            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = self.embedding_function(chunk_texts)
            
            # Prepare data for ChromaDB storage
            collection_name = f"unstructured_{hierarchy.resource_id.replace('-', '_')}"
            
            # Create collection with metadata
            collection_metadata = {
                "client_id": hierarchy.client_id,
                "user_id": hierarchy.user_id,
                "resource_id": hierarchy.resource_id,
                "resource_type": "unstructured",
                "chunking_strategy": chunking_strategy.value,
                "chunk_count": len(chunks),
                "created_at": datetime.utcnow().isoformat()
            }
            
            self.chromadb_manager.create_collection(collection_name, collection_metadata)
            
            # Prepare chunk data
            chunk_ids = [chunk.generate_id(hierarchy.resource_id) for chunk in chunks]
            chunk_metadatas = [
                {
                    **chunk.metadata,
                    "chunk_index": chunk.chunk_index,
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                    "token_count": chunk.token_count
                }
                for chunk in chunks
            ]
            
            # Store embeddings in ChromaDB
            self.chromadb_manager.add_embeddings(
                collection_name, embeddings, chunk_texts, chunk_metadatas, chunk_ids
            )
            
            # Update metadata with chunk count
            metadata.chunk_count = len(chunks)
            metadata.processing_status = "completed"
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Processed document into {len(chunks)} chunks in {processing_time:.2f}s")
            
            return collection_name
            
        except Exception as e:
            logger.error(f"Failed to process and store document: {e}")
            metadata.processing_status = "failed"
            metadata.error_message = str(e)
            raise RuntimeError(f"Document processing failed: {e}")
    
    def search(self, query: str, client_id: str, user_id: str,
              strategy: SearchStrategy = SearchStrategy.SEMANTIC,
              n_results: int = 5, use_multi_query: bool = True,
              resource_ids: Optional[List[str]] = None) -> SearchResults:
        """
        Perform semantic search across accessible unstructured data.
        
        Args:
            query: Search query
            client_id: Client ID for access control
            user_id: User ID for access control
            strategy: Search strategy to use
            n_results: Number of results to return
            use_multi_query: Whether to use query variations
            resource_ids: Optional list of specific resource IDs to search
            
        Returns:
            SearchResults: Search results with metadata
        """
        self.initialize()
        
        start_time = datetime.utcnow()
        
        try:
            # Get accessible resources
            accessible_resources = self._get_accessible_resources(
                client_id, user_id, resource_ids
            )
            
            if not accessible_resources:
                return SearchResults(
                    results=[],
                    total_results=0,
                    search_strategy=strategy,
                    execution_time_ms=0.0
                )
            
            # Generate query variations if requested
            queries = [query]
            if use_multi_query:
                queries = self.query_generator.generate_variations(query)
            
            # Perform search based on strategy
            if strategy == SearchStrategy.SEMANTIC:
                results = self._semantic_search(queries, accessible_resources, n_results)
            elif strategy == SearchStrategy.KEYWORD:
                results = self._keyword_search(queries, accessible_resources, n_results)
            elif strategy == SearchStrategy.HYBRID:
                results = self._hybrid_search(queries, accessible_resources, n_results)
            elif strategy == SearchStrategy.MMR:
                results = self._mmr_search(queries, accessible_resources, n_results)
            else:
                raise ValueError(f"Unsupported search strategy: {strategy}")
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return SearchResults(
                results=results,
                total_results=len(results),
                search_strategy=strategy,
                query_variations=queries,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return SearchResults(
                results=[],
                total_results=0,
                search_strategy=strategy,
                query_variations=[query],
                execution_time_ms=execution_time
            )
    
    def _get_accessible_resources(self, client_id: str, user_id: str,
                                resource_ids: Optional[List[str]] = None) -> List[ResourceMetadata]:
        """Get accessible unstructured resources for the user."""
        # Get all accessible resources
        all_resources = self.metadata_registry.list_resources(
            client_id, user_id, include_deleted=False
        )
        
        # Filter to unstructured resources only
        unstructured_resources = [
            r for r in all_resources 
            if r.resource_type == ResourceType.UNSTRUCTURED
        ]
        
        # Filter by specific resource IDs if provided
        if resource_ids:
            unstructured_resources = [
                r for r in unstructured_resources 
                if r.resource_id in resource_ids
            ]
        
        return unstructured_resources
    
    def _semantic_search(self, queries: List[str], resources: List[ResourceMetadata],
                        n_results: int) -> List[SearchResult]:
        """Perform pure semantic search using embeddings."""
        all_results = []
        
        for query in queries:
            # Generate query embedding
            query_embeddings = self.embedding_function([query])
            
            # Search each accessible collection
            for resource in resources:
                collection_name = f"unstructured_{resource.resource_id.replace('-', '_')}"
                
                try:
                    # Query ChromaDB collection
                    results = self.chromadb_manager.query_collection(
                        collection_name, query_embeddings, n_results
                    )
                    
                    # Convert to SearchResult objects
                    if results.get("ids") and results["ids"][0]:
                        for i, result_id in enumerate(results["ids"][0]):
                            search_result = SearchResult(
                                id=result_id,
                                document=results["documents"][0][i] if results.get("documents") else "",
                                metadata=results["metadatas"][0][i] if results.get("metadatas") else {},
                                distance=results["distances"][0][i] if results.get("distances") else 0.0,
                                resource_id=resource.resource_id,
                                chunk_index=results["metadatas"][0][i].get("chunk_index", 0) if results.get("metadatas") else 0
                            )
                            
                            # Calculate relevance score (inverse of distance)
                            search_result.relevance_score = max(0.0, 1.0 - search_result.distance)
                            
                            all_results.append(search_result)
                
                except Exception as e:
                    logger.warning(f"Failed to search collection {collection_name}: {e}")
                    continue
        
        # Remove duplicates and sort by relevance
        unique_results = self._deduplicate_results(all_results)
        unique_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return unique_results[:n_results]
    
    def _keyword_search(self, queries: List[str], resources: List[ResourceMetadata],
                       n_results: int) -> List[SearchResult]:
        """Perform keyword-based search using text matching."""
        all_results = []
        
        for query in queries:
            query_terms = query.lower().split()
            
            # Search each accessible collection
            for resource in resources:
                collection_name = f"unstructured_{resource.resource_id.replace('-', '_')}"
                
                try:
                    # Get all documents from collection for keyword matching
                    # Note: This is a simplified implementation - in production,
                    # you'd want to use a proper full-text search index
                    collection = self.chromadb_manager.get_collection(collection_name)
                    
                    # Get all documents (limit to reasonable number)
                    all_docs = collection.get(limit=1000)
                    
                    if all_docs.get("documents"):
                        for i, document in enumerate(all_docs["documents"]):
                            # Calculate keyword match score
                            doc_lower = document.lower()
                            matches = sum(1 for term in query_terms if term in doc_lower)
                            
                            if matches > 0:
                                relevance_score = matches / len(query_terms)
                                
                                search_result = SearchResult(
                                    id=all_docs["ids"][i],
                                    document=document,
                                    metadata=all_docs["metadatas"][i] if all_docs.get("metadatas") else {},
                                    distance=1.0 - relevance_score,  # Convert to distance
                                    relevance_score=relevance_score,
                                    resource_id=resource.resource_id,
                                    chunk_index=all_docs["metadatas"][i].get("chunk_index", 0) if all_docs.get("metadatas") else 0
                                )
                                
                                all_results.append(search_result)
                
                except Exception as e:
                    logger.warning(f"Failed to keyword search collection {collection_name}: {e}")
                    continue
        
        # Remove duplicates and sort by relevance
        unique_results = self._deduplicate_results(all_results)
        unique_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return unique_results[:n_results]
    
    def _hybrid_search(self, queries: List[str], resources: List[ResourceMetadata],
                      n_results: int) -> List[SearchResult]:
        """Perform hybrid search combining semantic and keyword approaches."""
        # Get results from both approaches
        semantic_results = self._semantic_search(queries, resources, n_results * 2)
        keyword_results = self._keyword_search(queries, resources, n_results * 2)
        
        # Combine and rerank results
        all_results = semantic_results + keyword_results
        
        # Calculate hybrid scores (weighted combination)
        semantic_weight = 0.7
        keyword_weight = 0.3
        
        result_map = {}
        for result in all_results:
            if result.id in result_map:
                # Combine scores for duplicate results
                existing = result_map[result.id]
                if result in semantic_results and existing in keyword_results:
                    # This result appeared in both - boost its score
                    combined_score = (semantic_weight * existing.relevance_score + 
                                    keyword_weight * result.relevance_score)
                    existing.relevance_score = min(1.0, combined_score * 1.2)  # Boost factor
                elif result in keyword_results and existing in semantic_results:
                    combined_score = (semantic_weight * result.relevance_score + 
                                    keyword_weight * existing.relevance_score)
                    existing.relevance_score = min(1.0, combined_score * 1.2)
            else:
                result_map[result.id] = result
        
        # Sort by hybrid score
        final_results = list(result_map.values())
        final_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return final_results[:n_results]
    
    def _mmr_search(self, queries: List[str], resources: List[ResourceMetadata],
                   n_results: int) -> List[SearchResult]:
        """Perform MMR (Maximal Marginal Relevance) search for diverse results."""
        # Start with semantic search to get candidate results
        candidates = self._semantic_search(queries, resources, n_results * 3)
        
        if not candidates:
            return []
        
        # MMR algorithm parameters
        lambda_param = 0.7  # Balance between relevance and diversity
        
        # Initialize with the most relevant result
        selected_results = [candidates[0]]
        remaining_candidates = candidates[1:]
        
        # Select remaining results using MMR
        while len(selected_results) < n_results and remaining_candidates:
            best_score = -1
            best_candidate = None
            best_index = -1
            
            for i, candidate in enumerate(remaining_candidates):
                # Calculate relevance score
                relevance = candidate.relevance_score
                
                # Calculate maximum similarity to already selected results
                max_similarity = 0
                for selected in selected_results:
                    # Simple similarity based on text overlap (in production, use embeddings)
                    similarity = self._calculate_text_similarity(candidate.document, selected.document)
                    max_similarity = max(max_similarity, similarity)
                
                # MMR score: balance relevance and diversity
                mmr_score = lambda_param * relevance - (1 - lambda_param) * max_similarity
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_candidate = candidate
                    best_index = i
            
            if best_candidate:
                selected_results.append(best_candidate)
                remaining_candidates.pop(best_index)
            else:
                break
        
        return selected_results
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity for MMR algorithm."""
        # Simple Jaccard similarity based on word sets
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on ID."""
        seen_ids = set()
        unique_results = []
        
        for result in results:
            if result.id not in seen_ids:
                seen_ids.add(result.id)
                unique_results.append(result)
        
        return unique_results
    
    def get_collection_info(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a ChromaDB collection for a resource.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            Optional[Dict[str, Any]]: Collection information or None if not found
        """
        self.initialize()
        
        collection_name = f"unstructured_{resource_id.replace('-', '_')}"
        
        try:
            collection = self.chromadb_manager.get_collection(collection_name)
            count = collection.count()
            metadata = collection.metadata
            
            return {
                "collection_name": collection_name,
                "document_count": count,
                "metadata": metadata
            }
        except Exception as e:
            logger.warning(f"Failed to get collection info for {resource_id}: {e}")
            return None
    
    def delete_resource_embeddings(self, resource_id: str) -> bool:
        """
        Delete all embeddings for a resource.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            bool: True if deletion was successful
        """
        self.initialize()
        
        collection_name = f"unstructured_{resource_id.replace('-', '_')}"
        
        try:
            self.chromadb_manager.delete_collection(collection_name)
            logger.info(f"Deleted embeddings for resource: {resource_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete embeddings for resource {resource_id}: {e}")
            return False
    
    def list_collections(self) -> List[str]:
        """
        List all ChromaDB collections.
        
        Returns:
            List[str]: List of collection names
        """
        self.initialize()
        return self.chromadb_manager.list_collections()
    
    def get_search_statistics(self, client_id: str) -> Dict[str, Any]:
        """
        Get search statistics for a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Dict[str, Any]: Search statistics
        """
        self.initialize()
        
        try:
            # Get unstructured resources for the client
            all_resources = self.metadata_registry.list_resources(client_id, None)
            unstructured_resources = [
                r for r in all_resources 
                if r.resource_type == ResourceType.UNSTRUCTURED
            ]
            
            total_chunks = sum(r.chunk_count or 0 for r in unstructured_resources)
            collections = self.list_collections()
            
            return {
                "total_unstructured_resources": len(unstructured_resources),
                "total_document_chunks": total_chunks,
                "total_collections": len(collections),
                "embedding_model": self.config.openrouter.embedding_model,
                "chunk_size_tokens": self.config.processing.chunk_size_tokens,
                "chunk_overlap_tokens": self.config.processing.chunk_overlap_tokens
            }
            
        except Exception as e:
            logger.error(f"Failed to get search statistics: {e}")
            return {"error": str(e)}
    
    def clear_cache(self) -> int:
        """Clear any internal caches."""
        # SemanticSearchEngine doesn't currently implement caching
        # This is a placeholder for future caching implementation
        logger.info("Semantic search cache cleared (no cache currently implemented)")
        return 0
    
    def get_cache_size(self) -> int:
        """Get the current cache size."""
        # SemanticSearchEngine doesn't currently implement caching
        # This is a placeholder for future caching implementation
        return 0
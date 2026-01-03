#!/usr/bin/env python3
"""
Semantic Search Engine Demo

Demonstrates the capabilities of the semantic search engine including:
- Document chunking with different strategies
- Embedding generation and storage
- Multiple search strategies (semantic, keyword, hybrid, MMR)
- Query variation generation
- Result ranking and relevance scoring
"""

import asyncio
import os
import tempfile
import uuid
from pathlib import Path

from light_ai.config import Config
from light_ai.core.models import DataHierarchy, DataType, ResourceMetadata, ResourceType
from light_ai.sub_layer_2.semantic_search_engine import (
    ChunkingStrategy,
    SearchStrategy,
    SemanticSearchEngine,
)


def setup_demo_config():
    """Set up configuration for the demo."""
    config = Config()
    
    # Use temporary directory for demo
    temp_dir = tempfile.mkdtemp(prefix="semantic_search_demo_")
    config.storage.base_directory = temp_dir
    
    # Set OpenRouter API key (you'll need to set this environment variable)
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Warning: OPENROUTER_API_KEY environment variable not set.")
        print("Using mock API key for demo purposes.")
        api_key = "demo-api-key"
    
    config.openrouter.api_key = api_key
    config.openrouter.embedding_model = "text-embedding-3-small"
    
    # Configure processing settings
    config.processing.chunk_size_tokens = 256  # Smaller chunks for demo
    config.processing.chunk_overlap_tokens = 25
    
    print(f"Demo data directory: {temp_dir}")
    return config


def create_sample_documents():
    """Create sample documents for the demo."""
    documents = {
        "company_overview.txt": """
        TechCorp is a leading technology company specializing in artificial intelligence 
        and machine learning solutions. Founded in 2015, we have grown to serve over 
        1000 clients worldwide with our innovative data processing platforms.
        
        Our mission is to democratize AI technology and make it accessible to businesses 
        of all sizes. We believe that every organization should have the power to harness 
        their data for better decision-making and improved operational efficiency.
        
        Our flagship product, DataMaster Pro, combines advanced analytics with intuitive 
        user interfaces to deliver actionable insights from complex datasets. The platform 
        supports multiple data formats and provides real-time processing capabilities.
        """,
        
        "product_features.txt": """
        DataMaster Pro Features:
        
        1. Universal Data Ingestion
        - Support for CSV, Excel, JSON, PDF, and text files
        - Automatic data cleaning and standardization
        - Bulk upload capabilities with progress tracking
        
        2. Intelligent Analytics
        - Natural language query interface
        - Advanced statistical analysis
        - Machine learning model integration
        - Predictive analytics and forecasting
        
        3. Visualization and Reporting
        - Interactive dashboards and charts
        - Automated report generation
        - Export capabilities in multiple formats
        - Real-time data monitoring
        
        4. Security and Compliance
        - Enterprise-grade security features
        - Role-based access control
        - Audit trails and compliance reporting
        - Data encryption at rest and in transit
        """,
        
        "customer_success.txt": """
        Customer Success Stories:
        
        RetailMax increased their sales by 25% after implementing DataMaster Pro's 
        predictive analytics for inventory management. The system helped them identify 
        optimal stock levels and reduce waste by 40%.
        
        HealthSystem Solutions improved patient outcomes by using our platform to 
        analyze treatment patterns and identify best practices. They reduced average 
        treatment time by 15% while maintaining high quality care standards.
        
        Manufacturing Giant Corp optimized their supply chain operations using our 
        real-time analytics dashboard. They achieved 20% cost savings and improved 
        delivery times by 30% through better demand forecasting.
        
        Financial Services Inc enhanced their risk assessment capabilities with our 
        machine learning models. They reduced loan default rates by 18% while 
        increasing approval rates for qualified applicants.
        """
    }
    
    return documents


def demonstrate_chunking_strategies(engine, sample_text):
    """Demonstrate different chunking strategies."""
    print("\n" + "="*60)
    print("CHUNKING STRATEGIES DEMONSTRATION")
    print("="*60)
    
    strategies = [
        ChunkingStrategy.SEMANTIC,
        ChunkingStrategy.FIXED,
        ChunkingStrategy.SENTENCE,
        ChunkingStrategy.PARAGRAPH
    ]
    
    for strategy in strategies:
        print(f"\n{strategy.value.upper()} Chunking:")
        print("-" * 40)
        
        chunks = engine.chunker.chunk_document(sample_text, strategy)
        print(f"Number of chunks: {len(chunks)}")
        
        for i, chunk in enumerate(chunks[:2]):  # Show first 2 chunks
            print(f"\nChunk {i+1} ({chunk.token_count} tokens):")
            print(f"Text: {chunk.text[:100]}...")
            print(f"Start: {chunk.start_char}, End: {chunk.end_char}")


def demonstrate_query_variations(engine):
    """Demonstrate query variation generation."""
    print("\n" + "="*60)
    print("QUERY VARIATION DEMONSTRATION")
    print("="*60)
    
    test_queries = [
        "find customer data",
        "what are the product features",
        "show me sales information",
        "how to improve performance"
    ]
    
    for query in test_queries:
        print(f"\nOriginal query: '{query}'")
        variations = engine.query_generator.generate_variations(query, max_variations=3)
        print("Variations:")
        for i, variation in enumerate(variations, 1):
            print(f"  {i}. {variation}")


def demonstrate_search_strategies(engine, client_id, user_id):
    """Demonstrate different search strategies."""
    print("\n" + "="*60)
    print("SEARCH STRATEGIES DEMONSTRATION")
    print("="*60)
    
    # Note: This is a mock demonstration since we don't have real embeddings
    # In a real scenario, you would have processed documents first
    
    test_query = "artificial intelligence and machine learning"
    strategies = [
        SearchStrategy.SEMANTIC,
        SearchStrategy.KEYWORD,
        SearchStrategy.HYBRID,
        SearchStrategy.MMR
    ]
    
    print(f"Search query: '{test_query}'")
    
    for strategy in strategies:
        print(f"\n{strategy.value.upper()} Search Strategy:")
        print("-" * 40)
        
        try:
            # This will return empty results since we don't have real data
            # but demonstrates the API
            results = engine.search(
                query=test_query,
                client_id=client_id,
                user_id=user_id,
                strategy=strategy,
                n_results=5,
                use_multi_query=True
            )
            
            print(f"Results found: {results.total_results}")
            print(f"Execution time: {results.execution_time_ms:.2f}ms")
            print(f"Query variations used: {len(results.query_variations)}")
            
            if results.results:
                for i, result in enumerate(results.results[:3], 1):
                    print(f"\nResult {i}:")
                    print(f"  Relevance: {result.relevance_score:.3f}")
                    print(f"  Text: {result.document[:100]}...")
            else:
                print("  (No results - demo data not processed)")
                
        except Exception as e:
            print(f"  Error: {e}")


def demonstrate_text_similarity(engine):
    """Demonstrate text similarity calculation for MMR."""
    print("\n" + "="*60)
    print("TEXT SIMILARITY DEMONSTRATION")
    print("="*60)
    
    text_pairs = [
        ("artificial intelligence", "machine learning"),
        ("data processing", "information analysis"),
        ("customer service", "technical support"),
        ("hello world", "goodbye universe"),
        ("identical text", "identical text")
    ]
    
    for text1, text2 in text_pairs:
        similarity = engine._calculate_text_similarity(text1, text2)
        print(f"'{text1}' vs '{text2}': {similarity:.3f}")


def main():
    """Run the semantic search engine demonstration."""
    print("Semantic Search Engine Demo")
    print("="*60)
    
    # Setup
    config = setup_demo_config()
    engine = SemanticSearchEngine(config)
    
    # Create sample data
    documents = create_sample_documents()
    sample_text = documents["company_overview.txt"]
    
    # Create sample hierarchy
    client_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    # Demonstrate chunking strategies
    demonstrate_chunking_strategies(engine, sample_text)
    
    # Demonstrate query variations
    demonstrate_query_variations(engine)
    
    # Demonstrate text similarity
    demonstrate_text_similarity(engine)
    
    # Demonstrate search strategies (mock)
    demonstrate_search_strategies(engine, client_id, user_id)
    
    # Show configuration
    print("\n" + "="*60)
    print("CONFIGURATION")
    print("="*60)
    print(f"Chunk size: {config.processing.chunk_size_tokens} tokens")
    print(f"Chunk overlap: {config.processing.chunk_overlap_tokens} tokens")
    print(f"Embedding model: {config.openrouter.embedding_model}")
    print(f"Base directory: {config.storage.base_directory}")
    
    print("\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60)
    print("Note: This demo shows the API and basic functionality.")
    print("For full functionality, set OPENROUTER_API_KEY environment variable")
    print("and process real documents through the system.")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Natural Language Processing Demo for Universal Data Handler.

This demo shows how to use the Natural Language Processor to convert
natural language questions into structured queries and get explanations.
"""

import os
import uuid
from pathlib import Path

from light_ai.sub_layer_2 import NaturalLanguageProcessor, QueryType
from light_ai.core.models import AccessLevel
from light_ai.config import Config


def main():
    """Demonstrate natural language processing capabilities."""
    print("🤖 Universal Data Handler - Natural Language Processing Demo")
    print("=" * 60)
    
    # Set up configuration
    config = Config()
    
    # For demo purposes, use a test API key
    # In real usage, set OPENROUTER_API_KEY environment variable
    if not config.openrouter.api_key:
        config.openrouter.api_key = "demo-key-replace-with-real-key"
        print("⚠️  Using demo API key - set OPENROUTER_API_KEY for real usage")
    
    # Initialize the natural language processor
    processor = NaturalLanguageProcessor(config)
    
    # Demo client and user IDs
    client_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    
    print(f"\n📋 Demo Setup:")
    print(f"   Client ID: {client_id}")
    print(f"   User ID: {user_id}")
    print(f"   Session ID: {session_id}")
    
    # Demo questions to test different query types
    demo_questions = [
        "Show me all customers",
        "Count the total number of orders",
        "Find documents about sales contracts",
        "What data do I have available?",
        "Search for product information",
        "Group customers by region and show totals",
        "What are the trends in my sales data?",
        "",  # Test error handling
        "a",  # Test short query
    ]
    
    print(f"\n🔍 Testing Natural Language Query Processing:")
    print("-" * 50)
    
    for i, question in enumerate(demo_questions, 1):
        print(f"\n{i}. Question: '{question}'")
        
        if not question.strip():
            print("   → Empty question")
        elif len(question.strip()) < 5:
            print("   → Very short question")
        
        try:
            # Process the natural language query
            result = processor.process_natural_query(
                question=question,
                client_id=client_id,
                user_id=user_id,
                session_id=session_id,
                access_level=AccessLevel.USER
            )
            
            # Display results
            print(f"   ✓ Query Type: {result.query_type.value}")
            print(f"   ✓ Explanation: {result.explanation}")
            print(f"   ✓ Row Count: {result.row_count}")
            print(f"   ✓ Execution Time: {result.execution_time_ms:.2f}ms")
            print(f"   ✓ Confidence: {result.confidence_score:.2f}")
            
            if result.generated_sql:
                print(f"   ✓ Generated SQL: {result.generated_sql}")
            
            if result.suggestions:
                print(f"   ✓ Suggestions: {', '.join(result.suggestions[:2])}...")
            
            if result.follow_up_suggestions:
                print(f"   ✓ Follow-ups: {', '.join(result.follow_up_suggestions[:2])}...")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            if "demo-key" in str(e) or "API" in str(e):
                print("   ℹ️  This is expected with demo API key")
    
    # Test query classification directly
    print(f"\n🏷️  Testing Query Classification:")
    print("-" * 40)
    
    from light_ai.sub_layer_2.natural_language_processor import QueryContext
    
    context = QueryContext(
        session_id=session_id,
        user_id=user_id,
        client_id=client_id
    )
    
    classification_tests = [
        ("Show me all customers", "Should be STRUCTURED_DATA"),
        ("Find sales documents", "Should be UNSTRUCTURED_DATA"),
        ("What data is available?", "Should be METADATA_QUERY"),
        ("Analyze trends over time", "Should be ANALYTICAL"),
    ]
    
    for question, expected in classification_tests:
        query_type = processor._classify_query(question, context)
        print(f"   '{question}' → {query_type.value} ({expected})")
    
    # Test context management
    print(f"\n💭 Testing Context Management:")
    print("-" * 35)
    
    stats = processor.get_context_stats()
    print(f"   Active contexts: {stats['active_contexts']}")
    print(f"   Context TTL: {stats['context_ttl_seconds']} seconds")
    
    # Test error suggestions
    print(f"\n🔧 Testing Error Handling:")
    print("-" * 30)
    
    error_suggestions = processor._generate_error_suggestions("", "Empty question")
    print(f"   Empty question suggestions: {error_suggestions[:2]}")
    
    sql_suggestions = processor._generate_error_suggestions("bad query", "SQL syntax error")
    print(f"   SQL error suggestions: {sql_suggestions[:2]}")
    
    # Clean up
    processor.close()
    
    print(f"\n✅ Demo completed successfully!")
    print(f"\n📚 Key Features Demonstrated:")
    print("   • Natural language query processing")
    print("   • Query type classification")
    print("   • Context management across sessions")
    print("   • Error handling with helpful suggestions")
    print("   • Follow-up question generation")
    print("   • Integration with OpenRouter LLM API")
    
    print(f"\n🚀 Next Steps:")
    print("   • Set OPENROUTER_API_KEY environment variable")
    print("   • Upload some data files to test with real queries")
    print("   • Try asking questions about your actual data")


if __name__ == "__main__":
    main()
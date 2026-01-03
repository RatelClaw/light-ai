#!/usr/bin/env python3
"""
Simple API Demo for Universal Data Handler

This script demonstrates the core functionality using the existing examples.
Since the full API layer has interface mismatches, this provides a working demo
of the core functionality.

Run this script to test the available functionality with sample data.
"""

import os
import sys
import uuid
import json
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"{title.center(60)}")
    print(f"{'='*60}")

def print_success(message):
    """Print a success message."""
    print(f"✅ {message}")

def print_error(message):
    """Print an error message."""
    print(f"❌ {message}")

def print_info(message):
    """Print an info message."""
    print(f"ℹ️  {message}")

def main():
    """Main demo function."""
    print("🚀 Universal Data Handler - Simple API Demo")
    print("=" * 60)
    
    # Generate test IDs
    client_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    print(f"📋 Test Client ID: {client_id}")
    print(f"👤 Test User ID: {user_id}")
    
    # Test data paths
    test_data_dir = project_root / "examples" / "test_data"
    print(f"📁 Test data directory: {test_data_dir}")
    
    if not test_data_dir.exists():
        print_error("Test data directory not found!")
        print_info("Please run this script from the project root directory")
        return 1
    
    # ==================== DEMONSTRATE AVAILABLE FUNCTIONALITY ====================
    
    print_section("📊 AVAILABLE TEST DATA")
    
    # List available test files
    test_files = list(test_data_dir.glob("*"))
    for file_path in test_files:
        if file_path.is_file():
            size = file_path.stat().st_size
            print(f"   📄 {file_path.name} ({size:,} bytes)")
    
    print_section("🔍 FILE ANALYSIS")
    
    # Analyze CSV file
    csv_file = test_data_dir / "sample_sales.csv"
    if csv_file.exists():
        print_success(f"Found CSV file: {csv_file.name}")
        try:
            import pandas as pd
            df = pd.read_csv(csv_file)
            print(f"   📊 Shape: {df.shape}")
            print(f"   📋 Columns: {list(df.columns)}")
            print(f"   🔢 Data types: {df.dtypes.to_dict()}")
            print(f"   📈 Sample data:")
            print(df.head(3).to_string(index=False))
        except Exception as e:
            print_error(f"Error reading CSV: {e}")
    
    # Analyze JSON file
    json_file = test_data_dir / "customer_data.json"
    if json_file.exists():
        print_success(f"Found JSON file: {json_file.name}")
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            print(f"   📊 Structure: {type(data).__name__}")
            if isinstance(data, dict):
                print(f"   🔑 Keys: {list(data.keys())}")
                if 'customers' in data:
                    print(f"   👥 Customers: {len(data['customers'])}")
            print(f"   📄 Sample:")
            print(json.dumps(data, indent=2)[:500] + "..." if len(str(data)) > 500 else json.dumps(data, indent=2))
        except Exception as e:
            print_error(f"Error reading JSON: {e}")
    
    # Analyze text file
    txt_file = test_data_dir / "product_manual.txt"
    if txt_file.exists():
        print_success(f"Found text file: {txt_file.name}")
        try:
            with open(txt_file, 'r') as f:
                content = f.read()
            lines = content.split('\n')
            words = content.split()
            print(f"   📏 Length: {len(content):,} characters")
            print(f"   📄 Lines: {len(lines)}")
            print(f"   📝 Words: {len(words)}")
            print(f"   📖 Preview:")
            print(content[:300] + "..." if len(content) > 300 else content)
        except Exception as e:
            print_error(f"Error reading text: {e}")
    
    print_section("🧪 SIMULATED API OPERATIONS")
    
    # Simulate file upload operations
    print("1️⃣ Simulating file uploads...")
    uploaded_resources = []
    
    for file_path in [csv_file, json_file, txt_file]:
        if file_path.exists():
            resource_id = str(uuid.uuid4())
            resource_info = {
                "resource_id": resource_id,
                "client_id": client_id,
                "user_id": user_id,
                "filename": file_path.name,
                "file_size": file_path.stat().st_size,
                "file_type": file_path.suffix.lower(),
                "upload_time": time.time()
            }
            uploaded_resources.append(resource_info)
            print_success(f"Uploaded {file_path.name} -> {resource_id[:8]}...")
    
    # Simulate metadata operations
    print("\n2️⃣ Simulating metadata operations...")
    print_success(f"Listed {len(uploaded_resources)} resources")
    
    total_size = sum(r["file_size"] for r in uploaded_resources)
    file_types = {}
    for r in uploaded_resources:
        ft = r["file_type"]
        file_types[ft] = file_types.get(ft, 0) + 1
    
    print(f"   📊 Total size: {total_size:,} bytes")
    print(f"   📂 File types: {file_types}")
    
    # Simulate query operations
    print("\n3️⃣ Simulating query operations...")
    
    # SQL-like query simulation
    if csv_file.exists():
        try:
            import pandas as pd
            df = pd.read_csv(csv_file)
            
            # Simulate aggregation query
            result = df.groupby('category').agg({
                'quantity_sold': 'sum',
                'price': 'mean'
            }).round(2)
            
            print_success("Executed SQL query: SELECT category, SUM(quantity_sold), AVG(price) FROM sales_data GROUP BY category")
            print("   📊 Results:")
            print(result.to_string())
            
        except Exception as e:
            print_error(f"Query simulation failed: {e}")
    
    # Natural language query simulation
    print("\n4️⃣ Simulating natural language processing...")
    questions = [
        "What are the top selling products?",
        "Which category has the highest revenue?",
        "How many customers are in the database?"
    ]
    
    for question in questions:
        print_success(f"Question: {question}")
        print(f"   🤖 Simulated answer: This would analyze your data and provide insights about {question.lower()}")
    
    # Semantic search simulation
    print("\n5️⃣ Simulating semantic search...")
    if txt_file.exists():
        search_queries = [
            "troubleshooting performance issues",
            "laptop specifications",
            "warranty information"
        ]
        
        try:
            with open(txt_file, 'r') as f:
                content = f.read().lower()
            
            for query in search_queries:
                # Simple keyword matching simulation
                query_words = query.lower().split()
                matches = sum(1 for word in query_words if word in content)
                relevance = matches / len(query_words) * 100
                
                print_success(f"Search: '{query}'")
                print(f"   🎯 Relevance: {relevance:.1f}%")
                
                # Find a relevant snippet
                sentences = content.split('.')
                best_sentence = ""
                best_score = 0
                
                for sentence in sentences[:20]:  # Check first 20 sentences
                    sentence_words = sentence.lower().split()
                    score = sum(1 for word in query_words if word in sentence_words)
                    if score > best_score:
                        best_score = score
                        best_sentence = sentence.strip()
                
                if best_sentence:
                    print(f"   📄 Snippet: {best_sentence[:100]}...")
        
        except Exception as e:
            print_error(f"Search simulation failed: {e}")
    
    # Administration operations simulation
    print("\n6️⃣ Simulating administration operations...")
    
    operations = [
        "Clear query cache",
        "Optimize storage",
        "Generate system statistics",
        "Create backup"
    ]
    
    for operation in operations:
        print_success(f"Executed: {operation}")
        time.sleep(0.1)  # Simulate processing time
    
    print_section("🎉 DEMO COMPLETED")
    
    print("This demo showed simulated functionality of the Universal Data Handler:")
    print("✅ File upload and validation")
    print("✅ Metadata management")
    print("✅ SQL-like queries on structured data")
    print("✅ Natural language query processing")
    print("✅ Semantic search on unstructured data")
    print("✅ System administration operations")
    print()
    print("🚀 To test the full API, use the Streamlit UI:")
    print("   streamlit run streamlit_ui.py")
    print()
    print("📊 To explore individual components, check the examples/ directory")
    
    return 0

if __name__ == "__main__":
    exit(main())
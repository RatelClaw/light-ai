#!/usr/bin/env python3
"""
Complete API Demo for Universal Data Handler

This script demonstrates all API functionality including:
- Sub-Layer 1: Data Ingestion & Storage
- Sub-Layer 2: Data Retrieval  
- Metadata APIs
- Administration APIs

Run this script to test all API endpoints with sample data.
"""

import os
import sys
import uuid
import json
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from light_ai.api import create_api
from light_ai.config import Config


def print_response(response, title="API Response"):
    """Pretty print API response."""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    print(f"Success: {response.success}")
    if response.success:
        print("Data:", json.dumps(response.data, indent=2, default=str))
    else:
        print(f"Error: {response.error}")
    print(f"Metadata: {response.metadata}")
    print(f"Timestamp: {response.timestamp}")


def main():
    """Main demo function."""
    print("🚀 Universal Data Handler - Complete API Demo")
    print("=" * 60)
    
    # Initialize API
    try:
        config = Config.load()
        api = create_api(config=config)
        print("✅ API initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize API: {e}")
        return
    
    # Generate test IDs
    client_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    print(f"📋 Test Client ID: {client_id}")
    print(f"👤 Test User ID: {user_id}")
    
    # Test data paths
    test_data_dir = project_root / "examples" / "test_data"
    csv_file = test_data_dir / "sample_sales.csv"
    json_file = test_data_dir / "customer_data.json"
    txt_file = test_data_dir / "product_manual.txt"
    
    print(f"\n📁 Test data directory: {test_data_dir}")
    
    # ==================== SUB-LAYER 1: DATA INGESTION & STORAGE ====================
    print("\n" + "🔄 SUB-LAYER 1: DATA INGESTION & STORAGE".center(60, "="))
    
    # 1. Upload CSV file
    print("\n1️⃣ Testing upload_file() with CSV...")
    response = api.upload_file(
        client_id=client_id,
        user_id=user_id,
        file_path=str(csv_file),
        resource_name="sales_data"
    )
    print_response(response, "Upload CSV File")
    csv_resource_id = response.data.get('resource_id') if response.success else None
    
    # 2. Upload JSON file
    print("\n2️⃣ Testing upload_file() with JSON...")
    response = api.upload_file(
        client_id=client_id,
        user_id=user_id,
        file_path=str(json_file),
        resource_name="customer_data"
    )
    print_response(response, "Upload JSON File")
    json_resource_id = response.data.get('resource_id') if response.success else None
    
    # 3. Upload raw JSON data
    print("\n3️⃣ Testing upload_json() with raw JSON...")
    raw_json_data = {
        "products": [
            {"id": 1, "name": "Test Product", "price": 99.99},
            {"id": 2, "name": "Another Product", "price": 149.99}
        ],
        "metadata": {"source": "api_demo", "version": "1.0"}
    }
    response = api.upload_json(
        client_id=client_id,
        user_id=user_id,
        json_data=raw_json_data,
        resource_name="raw_product_data",
        flatten=False
    )
    print_response(response, "Upload Raw JSON")
    raw_json_resource_id = response.data.get('resource_id') if response.success else None
    
    # 4. Upload text file
    print("\n4️⃣ Testing upload_file() with text...")
    response = api.upload_file(
        client_id=client_id,
        user_id=user_id,
        file_path=str(txt_file),
        resource_name="product_manual"
    )
    print_response(response, "Upload Text File")
    txt_resource_id = response.data.get('resource_id') if response.success else None
    
    # 5. Bulk upload
    print("\n5️⃣ Testing upload_bulk()...")
    response = api.upload_bulk(
        client_id=client_id,
        user_id=user_id,
        files=[str(csv_file), str(json_file)],
        parallel=False
    )
    print_response(response, "Bulk Upload")
    
    # Wait a moment for processing
    time.sleep(2)
    
    # ==================== SUB-LAYER 2: DATA RETRIEVAL ====================
    print("\n" + "🔍 SUB-LAYER 2: DATA RETRIEVAL".center(60, "="))
    
    # 6. Get resource data
    if csv_resource_id:
        print("\n6️⃣ Testing get_resource()...")
        response = api.get_resource(
            resource_id=csv_resource_id,
            output_format="json",
            client_id=client_id,
            user_id=user_id
        )
        print_response(response, "Get Resource Data")
    
    # 7. SQL query on structured data
    print("\n7️⃣ Testing query_structured()...")
    response = api.query_structured(
        client_id=client_id,
        user_id=user_id,
        sql_query="SELECT category, COUNT(*) as product_count, SUM(quantity_sold) as total_sold FROM sales_data GROUP BY category ORDER BY total_sold DESC"
    )
    print_response(response, "SQL Query")
    
    # 8. Natural language query
    print("\n8️⃣ Testing query_natural()...")
    response = api.query_natural(
        client_id=client_id,
        user_id=user_id,
        question="What are the top 3 best selling products by quantity?"
    )
    print_response(response, "Natural Language Query")
    
    # 9. Semantic search on unstructured data
    if txt_resource_id:
        print("\n9️⃣ Testing search_unstructured()...")
        response = api.search_unstructured(
            client_id=client_id,
            user_id=user_id,
            query="laptop performance troubleshooting",
            strategy="hybrid",
            limit=3
        )
        print_response(response, "Semantic Search")
    
    # 10. AI Data Analyst
    print("\n🔟 Testing ask_data_analyst()...")
    response = api.ask_data_analyst(
        client_id=client_id,
        user_id=user_id,
        question="Analyze my sales data and provide insights about product performance and customer behavior",
        include_visualizations=False
    )
    print_response(response, "AI Data Analyst")
    
    # ==================== METADATA APIs ====================
    print("\n" + "📊 METADATA APIs".center(60, "="))
    
    # 11. List resources
    print("\n1️⃣1️⃣ Testing list_resources()...")
    response = api.list_resources(
        client_id=client_id,
        user_id=user_id,
        access_level="user"
    )
    print_response(response, "List Resources")
    
    # 12. Get resource metadata
    if csv_resource_id:
        print("\n1️⃣2️⃣ Testing get_resource_metadata()...")
        response = api.get_resource_metadata(
            resource_id=csv_resource_id,
            client_id=client_id,
            user_id=user_id
        )
        print_response(response, "Get Resource Metadata")
    
    # 13. Get schema
    if csv_resource_id:
        print("\n1️⃣3️⃣ Testing get_schema()...")
        response = api.get_schema(
            resource_id=csv_resource_id,
            client_id=client_id,
            user_id=user_id
        )
        print_response(response, "Get Schema")
    
    # 14. Get statistics
    print("\n1️⃣4️⃣ Testing get_statistics()...")
    response = api.get_statistics(
        client_id=client_id,
        user_id=user_id,
        access_level="user"
    )
    print_response(response, "Get Statistics")
    
    # ==================== ADMINISTRATION APIs ====================
    print("\n" + "⚙️ ADMINISTRATION APIs".center(60, "="))
    
    # 15. Get system stats
    print("\n1️⃣5️⃣ Testing get_system_stats()...")
    response = api.get_system_stats()
    print_response(response, "Get System Stats")
    
    # 16. Clear cache
    print("\n1️⃣6️⃣ Testing clear_cache()...")
    response = api.clear_cache(scope="query")
    print_response(response, "Clear Cache")
    
    # 17. Export resource
    if csv_resource_id:
        print("\n1️⃣7️⃣ Testing export_resource()...")
        response = api.export_resource(
            resource_id=csv_resource_id,
            export_format="json",
            client_id=client_id,
            user_id=user_id
        )
        print_response(response, "Export Resource")
    
    # 18. Update resource
    if csv_resource_id:
        print("\n1️⃣8️⃣ Testing update_resource()...")
        response = api.update_resource(
            resource_id=csv_resource_id,
            new_data=str(json_file),  # Update with JSON file
            create_version=True,
            client_id=client_id,
            user_id=user_id
        )
        print_response(response, "Update Resource")
    
    # 19. Optimize storage
    print("\n1️⃣9️⃣ Testing optimize_storage()...")
    response = api.optimize_storage()
    print_response(response, "Optimize Storage")
    
    # 20. Backup data
    print("\n2️⃣0️⃣ Testing backup_data()...")
    response = api.backup_data(
        backup_path="demo_backup",
        include_raw_files=False
    )
    print_response(response, "Backup Data")
    
    # 21. Delete resource (soft delete)
    if raw_json_resource_id:
        print("\n2️⃣1️⃣ Testing delete_resource() - Soft Delete...")
        response = api.delete_resource(
            resource_id=raw_json_resource_id,
            hard_delete=False,
            client_id=client_id,
            user_id=user_id
        )
        print_response(response, "Soft Delete Resource")
    
    print("\n" + "🎉 DEMO COMPLETED SUCCESSFULLY!".center(60, "="))
    print("All API endpoints have been tested.")
    print("Check the responses above for detailed results.")


if __name__ == "__main__":
    main()
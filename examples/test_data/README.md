# Test Data Files

This directory contains sample data files for testing the Universal Data Handler API.

## Files Included

### 1. sample_sales.csv
- **Type**: Structured data (CSV)
- **Content**: Sales transaction data with product information, prices, quantities, and customer details
- **Use Case**: Test structured data upload, SQL queries, and data analysis

### 2. customer_data.json
- **Type**: JSON data (nested structure)
- **Content**: Customer profiles with nested location and preference data
- **Use Case**: Test JSON upload, flattening, and complex data queries

### 3. product_manual.txt
- **Type**: Unstructured text data
- **Content**: Product manual with setup instructions, specifications, and troubleshooting
- **Use Case**: Test unstructured data upload, text extraction, and semantic search

### 4. inventory.xlsx
- **Type**: Structured data (Excel format)
- **Content**: Warehouse inventory data with stock levels and supplier information
- **Use Case**: Test Excel file processing and cross-resource analysis

## Usage Examples

### Upload Files
```python
from light_ai.api import create_api
import uuid

# Initialize API
api = create_api()
client_id = str(uuid.uuid4())
user_id = str(uuid.uuid4())

# Upload CSV file
response = api.upload_file(
    client_id=client_id,
    user_id=user_id,
    file_path="examples/test_data/sample_sales.csv",
    resource_name="sales_data"
)

# Upload JSON data
response = api.upload_file(
    client_id=client_id,
    user_id=user_id,
    file_path="examples/test_data/customer_data.json",
    resource_name="customer_profiles"
)
```

### Query Data
```python
# SQL query on sales data
response = api.query_structured(
    client_id=client_id,
    user_id=user_id,
    sql_query="SELECT category, SUM(quantity_sold) as total_sold FROM sales_data GROUP BY category"
)

# Natural language query
response = api.query_natural(
    client_id=client_id,
    user_id=user_id,
    question="What are the top selling products by quantity?"
)

# Semantic search on manual
response = api.search_unstructured(
    client_id=client_id,
    user_id=user_id,
    query="troubleshooting laptop performance issues"
)
```

## Data Relationships

The test data is designed with relationships:
- Sales data references customers (customer_id)
- Inventory data references products (product_id)
- Customer data provides detailed profiles for sales analysis

This allows testing of cross-resource queries and comprehensive data analysis scenarios.
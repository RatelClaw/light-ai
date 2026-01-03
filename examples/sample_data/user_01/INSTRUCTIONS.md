# USER 01 - E-COMMERCE BUSINESS DATA
## Sample Data Overview
This folder contains e-commerce business data including sales transactions, customer feedback, and product documentation.

### Files:
- `sales_data.csv` - Daily sales transactions with product, region, and customer data
- `customer_feedback.json` - Customer reviews and ratings for products
- `product_manual.txt` - Technical documentation for Laptop Pro product

## API Testing Instructions

### 1. FILE UPLOAD (Sub-Layer 1)
Upload each file to test different data types:

```python
# Upload CSV file
api.upload_file(client_id, user_id, "sales_data.csv", "Sales Transactions")

# Upload JSON file  
api.upload_json(client_id, user_id, feedback_data, "Customer Feedback")

# Upload text file
api.upload_file(client_id, user_id, "product_manual.txt", "Product Manual")
```

### 2. SQL QUERIES (Sub-Layer 2)
Test structured data queries on the uploaded CSV:

```sql
-- Basic sales analysis
SELECT product, SUM(sales_amount) as total_sales, COUNT(*) as transactions
FROM structured_data.resource_[RESOURCE_ID] 
GROUP BY product 
ORDER BY total_sales DESC;

-- Regional performance
SELECT region, AVG(sales_amount) as avg_sale, SUM(quantity) as total_quantity
FROM structured_data.resource_[RESOURCE_ID]
GROUP BY region;

-- Customer type analysis
SELECT customer_type, COUNT(*) as transactions, AVG(sales_amount) as avg_amount
FROM structured_data.resource_[RESOURCE_ID]
GROUP BY customer_type;

-- Top selling categories
SELECT category, SUM(sales_amount) as revenue, COUNT(*) as sales_count
FROM structured_data.resource_[RESOURCE_ID]
GROUP BY category
ORDER BY revenue DESC;
```

### 3. NATURAL LANGUAGE QUERIES
Test conversational queries:

```
"What are the top selling products by revenue?"
"Show me sales performance by region"
"Which customer type generates more revenue - business or consumer?"
"What's the average sale amount for electronics?"
"How many transactions were there in North America?"
"Which products have the highest quantity sold?"
"Compare sales between different regions"
"What's the total revenue for January 2024?"
```

### 4. SEMANTIC SEARCH (Unstructured Data)
Search through product manual and customer feedback:

```
"laptop specifications and performance"
"battery life and power management"
"customer complaints about connectivity"
"setup and installation instructions"
"warranty and support information"
"positive customer reviews"
"technical troubleshooting steps"
"product features and capabilities"
```

### 5. AI DATA ANALYST QUERIES
Ask complex analytical questions:

```
"Analyze the sales performance and identify trends in customer behavior"
"What insights can you provide about regional sales patterns?"
"Compare product performance across different categories"
"Identify opportunities for revenue growth based on the data"
"What are the key factors driving customer satisfaction?"
"Analyze the relationship between product price and sales volume"
"Provide recommendations for inventory management"
"What seasonal patterns do you see in the sales data?"
```

### 6. EXPECTED RESULTS
- **CSV Upload**: Should create structured data table with 15 sales records
- **JSON Upload**: Should store customer feedback with nested structure
- **Text Upload**: Should create searchable chunks of product manual
- **SQL Queries**: Should return aggregated sales metrics
- **Natural Language**: Should convert to SQL and return relevant data
- **Semantic Search**: Should find relevant sections from product manual
- **AI Analysis**: Should provide business insights and recommendations

### 7. CLIENT/USER IDs FOR TESTING
```
client_id = "client-ecommerce-001"
user_id = "user-sales-manager-001"
```

Use these IDs consistently across all API calls to maintain data isolation and access control.
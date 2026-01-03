"""
Tests for SQL Query Engine functionality.

Tests the core SQL query execution, cross-resource joins, derived fields,
query optimization, and streaming capabilities.
"""

import pytest
import uuid
import tempfile
import pandas as pd
from pathlib import Path
from datetime import datetime

from light_ai.sub_layer_2.sql_query_engine import (
    SQLQueryEngine, QueryResult, QueryPlan, 
    build_select_query, build_aggregation_query, validate_sql_injection
)
from light_ai.core.models import (
    DataHierarchy, ResourceMetadata, ResourceType, DataType, AccessLevel
)
from light_ai.storage.storage_router import StorageRouter
from light_ai.config import Config


class TestSQLQueryEngine:
    """Test SQL Query Engine functionality."""
    
    @pytest.fixture
    def temp_config(self):
        """Create temporary configuration for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config()
            config.data_dir = Path(temp_dir) / "data"
            config.database.sqlite_path = Path(temp_dir) / "metadata" / "registry.db"
            config.database.duckdb_path = Path(temp_dir) / "metadata" / "duckdb.db"
            config.database.chromadb_path = Path(temp_dir) / "metadata" / "chromadb"
            yield config
    
    @pytest.fixture
    def query_engine(self, temp_config):
        """Create SQL query engine with test configuration."""
        engine = SQLQueryEngine(temp_config)
        engine.initialize()
        return engine
    
    @pytest.fixture
    def sample_data_setup(self, temp_config):
        """Set up sample data for testing."""
        # Create sample CSV data
        customers_data = pd.DataFrame({
            'customer_id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
            'email': ['alice@test.com', 'bob@test.com', 'charlie@test.com', 'diana@test.com', 'eve@test.com'],
            'city': ['New York', 'London', 'Tokyo', 'Paris', 'Berlin']
        })
        
        orders_data = pd.DataFrame({
            'order_id': [101, 102, 103, 104, 105, 106],
            'customer_id': [1, 2, 1, 3, 2, 4],
            'product': ['Laptop', 'Phone', 'Tablet', 'Monitor', 'Keyboard', 'Mouse'],
            'amount': [1200.00, 800.00, 500.00, 300.00, 100.00, 50.00],
            'order_date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05', '2024-01-06']
        })
        
        # Save to temporary files
        temp_dir = temp_config.data_dir
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        customers_file = temp_dir / "customers.csv"
        orders_file = temp_dir / "orders.csv"
        
        customers_data.to_csv(customers_file, index=False)
        orders_data.to_csv(orders_file, index=False)
        
        # Create storage router and store the data
        storage_router = StorageRouter(temp_config)
        storage_router.initialize()
        
        # Create test hierarchy
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        customers_resource_id = str(uuid.uuid4())
        orders_resource_id = str(uuid.uuid4())
        
        customers_hierarchy = DataHierarchy(client_id, user_id, customers_resource_id)
        orders_hierarchy = DataHierarchy(client_id, user_id, orders_resource_id)
        
        # Create metadata
        customers_metadata = ResourceMetadata(
            resource_id=customers_resource_id,
            user_id=user_id,
            client_id=client_id,
            resource_type=ResourceType.STRUCTURED,
            data_type=DataType.CSV,
            original_filename="customers.csv",
            file_size_bytes=customers_file.stat().st_size,
            storage_path=str(customers_file),
            row_count=len(customers_data),
            column_count=len(customers_data.columns)
        )
        
        orders_metadata = ResourceMetadata(
            resource_id=orders_resource_id,
            user_id=user_id,
            client_id=client_id,
            resource_type=ResourceType.STRUCTURED,
            data_type=DataType.CSV,
            original_filename="orders.csv",
            file_size_bytes=orders_file.stat().st_size,
            storage_path=str(orders_file),
            row_count=len(orders_data),
            column_count=len(orders_data.columns)
        )
        
        # Store in storage router
        customers_table = storage_router.store_structured_data(
            customers_file, customers_hierarchy, customers_metadata
        )
        orders_table = storage_router.store_structured_data(
            orders_file, orders_hierarchy, orders_metadata
        )
        
        return {
            'client_id': client_id,
            'user_id': user_id,
            'customers_resource_id': customers_resource_id,
            'orders_resource_id': orders_resource_id,
            'customers_table': customers_table,
            'orders_table': orders_table,
            'storage_router': storage_router
        }
    
    def test_basic_query_execution(self, query_engine, sample_data_setup):
        """Test basic SQL query execution."""
        setup = sample_data_setup
        
        # Simple SELECT query
        sql = f"SELECT * FROM structured_data.{setup['customers_table']}_enhanced"
        
        result = query_engine.execute_query(
            sql, setup['client_id'], setup['user_id']
        )
        
        assert isinstance(result, QueryResult)
        assert result.row_count == 5  # 5 customers
        assert len(result.columns) >= 4  # customer_id, name, email, city + metadata columns
        assert not result.is_streaming
        assert result.execution_time_ms > 0
    
    def test_query_with_where_clause(self, query_engine, sample_data_setup):
        """Test SQL query with WHERE clause."""
        setup = sample_data_setup
        
        sql = f"""
        SELECT name, email 
        FROM structured_data.{setup['customers_table']}_enhanced 
        WHERE city = 'New York'
        """
        
        result = query_engine.execute_query(
            sql, setup['client_id'], setup['user_id']
        )
        
        assert result.row_count == 1
        assert result.data[0]['name'] == 'Alice'
        assert result.data[0]['email'] == 'alice@test.com'
    
    def test_cross_resource_join(self, query_engine, sample_data_setup):
        """Test cross-resource JOIN query."""
        setup = sample_data_setup
        
        resources = [setup['customers_resource_id'], setup['orders_resource_id']]
        join_conditions = ["a.customer_id = b.customer_id"]  # Use correct aliases a, b
        select_fields = ["a.name", "a.email", "b.product", "b.amount"]
        
        result = query_engine.execute_cross_resource_join(
            resources, join_conditions, select_fields,
            setup['client_id'], setup['user_id']
        )
        
        assert result.row_count == 6  # 6 orders with customer info
        assert 'name' in result.columns
        assert 'product' in result.columns
        assert 'amount' in result.columns
    
    def test_derived_field_calculation(self, query_engine, sample_data_setup):
        """Test derived field creation with calculations."""
        setup = sample_data_setup
        
        result = query_engine.create_derived_field(
            setup['orders_resource_id'],
            'amount_with_tax',
            'amount * 1.1',  # 10% tax
            setup['client_id'],
            setup['user_id']
        )
        
        assert result.row_count == 6  # 6 orders
        assert 'amount_with_tax' in result.columns
        
        # Verify calculation
        for row in result.data:
            expected_tax_amount = row['amount'] * 1.1
            assert abs(row['amount_with_tax'] - expected_tax_amount) < 0.01
    
    def test_query_plan_generation(self, query_engine, sample_data_setup):
        """Test query plan generation and optimization."""
        setup = sample_data_setup
        
        sql = f"SELECT * FROM structured_data.{setup['customers_table']}_enhanced WHERE city = 'London'"
        
        plan = query_engine.get_query_plan(
            sql, setup['client_id'], setup['user_id']
        )
        
        assert isinstance(plan, QueryPlan)
        assert plan.original_query == sql
        assert len(plan.tables_accessed) > 0
        assert plan.estimated_rows > 0
        assert plan.execution_strategy in ['in-memory', 'streaming']
        assert isinstance(plan.optimization_notes, list)
    
    def test_access_control_user_level(self, query_engine, sample_data_setup):
        """Test access control at user level."""
        setup = sample_data_setup
        
        # Create another user in the same client
        other_user_id = str(uuid.uuid4())
        
        sql = f"SELECT * FROM structured_data.{setup['customers_table']}_enhanced"
        
        # Original user should have access
        result1 = query_engine.execute_query(
            sql, setup['client_id'], setup['user_id']
        )
        assert result1.row_count == 5
        
        # Other user should not have access (no data)
        result2 = query_engine.execute_query(
            sql, setup['client_id'], other_user_id
        )
        assert result2.row_count == 0
    
    def test_access_control_manager_level(self, query_engine, sample_data_setup):
        """Test access control at manager level."""
        setup = sample_data_setup
        
        # Create another user in the same client
        manager_user_id = str(uuid.uuid4())
        
        sql = f"SELECT * FROM structured_data.{setup['customers_table']}_enhanced"
        
        # Manager should have access to all data in the client
        result = query_engine.execute_query(
            sql, setup['client_id'], manager_user_id,
            access_level=AccessLevel.MANAGER
        )
        assert result.row_count == 5
    
    def test_streaming_query_simulation(self, query_engine, sample_data_setup):
        """Test streaming query behavior (simulated with small threshold)."""
        setup = sample_data_setup
        
        # Temporarily lower streaming threshold for testing
        original_threshold = query_engine._streaming_threshold
        query_engine._streaming_threshold = 3  # Very low threshold
        
        try:
            sql = f"SELECT * FROM structured_data.{setup['customers_table']}_enhanced"
            
            result = query_engine.execute_query(
                sql, setup['client_id'], setup['user_id']
            )
            
            # Should trigger streaming mode
            assert result.is_streaming
            assert result.total_rows is not None
            assert result.total_rows >= result.row_count  # Preview is smaller than total
            
        finally:
            # Restore original threshold
            query_engine._streaming_threshold = original_threshold
    
    def test_query_caching(self, query_engine, sample_data_setup):
        """Test query result caching."""
        setup = sample_data_setup
        
        sql = f"SELECT * FROM structured_data.{setup['customers_table']}_enhanced"
        
        # First execution
        result1 = query_engine.execute_query(
            sql, setup['client_id'], setup['user_id']
        )
        
        # Second execution should use cache
        result2 = query_engine.execute_query(
            sql, setup['client_id'], setup['user_id']
        )
        
        assert result1.row_count == result2.row_count
        assert result1.columns == result2.columns
        
        # Check cache stats
        stats = query_engine.get_cache_stats()
        assert stats['cache_size'] >= 1
    
    def test_cache_clearing(self, query_engine, sample_data_setup):
        """Test cache clearing functionality."""
        setup = sample_data_setup
        
        sql = f"SELECT * FROM structured_data.{setup['customers_table']}_enhanced"
        
        # Execute query to populate cache
        query_engine.execute_query(sql, setup['client_id'], setup['user_id'])
        
        # Clear cache
        cleared_count = query_engine.clear_cache()
        assert cleared_count >= 1
        
        # Check cache is empty
        stats = query_engine.get_cache_stats()
        assert stats['cache_size'] == 0


class TestQueryBuilders:
    """Test query building utility functions."""
    
    def test_build_select_query_basic(self):
        """Test basic SELECT query building."""
        query = build_select_query("test_table")
        assert query == "SELECT * FROM test_table"
    
    def test_build_select_query_with_columns(self):
        """Test SELECT query with specific columns."""
        query = build_select_query("test_table", ["id", "name", "email"])
        assert query == "SELECT id, name, email FROM test_table"
    
    def test_build_select_query_with_where(self):
        """Test SELECT query with WHERE conditions."""
        query = build_select_query(
            "test_table", 
            where_conditions=["status = 'active'", "age > 18"]
        )
        assert query == "SELECT * FROM test_table WHERE status = 'active' AND age > 18"
    
    def test_build_select_query_complete(self):
        """Test complete SELECT query with all clauses."""
        query = build_select_query(
            "test_table",
            columns=["id", "name"],
            where_conditions=["status = 'active'"],
            order_by=["name ASC"],
            limit=10
        )
        expected = "SELECT id, name FROM test_table WHERE status = 'active' ORDER BY name ASC LIMIT 10"
        assert query == expected
    
    def test_build_aggregation_query(self):
        """Test aggregation query building."""
        query = build_aggregation_query(
            "sales_table",
            group_by_columns=["region", "product"],
            aggregations={
                "total_sales": "SUM(amount)",
                "avg_price": "AVG(price)",
                "order_count": "COUNT(*)"
            }
        )
        
        assert "SELECT region, product" in query
        assert "SUM(amount) AS total_sales" in query
        assert "AVG(price) AS avg_price" in query
        assert "COUNT(*) AS order_count" in query
        assert "GROUP BY region, product" in query
    
    def test_build_aggregation_query_with_conditions(self):
        """Test aggregation query with WHERE and HAVING."""
        query = build_aggregation_query(
            "sales_table",
            group_by_columns=["region"],
            aggregations={"total_sales": "SUM(amount)"},
            where_conditions=["date >= '2024-01-01'"],
            having_conditions=["SUM(amount) > 1000"]
        )
        
        assert "WHERE date >= '2024-01-01'" in query
        assert "HAVING SUM(amount) > 1000" in query


class TestSQLValidation:
    """Test SQL injection validation."""
    
    def test_safe_queries(self):
        """Test that safe queries pass validation."""
        safe_queries = [
            "SELECT * FROM table",
            "SELECT id, name FROM users WHERE age > 18",
            "SELECT COUNT(*) FROM orders GROUP BY region",
            "SELECT * FROM products ORDER BY price DESC LIMIT 10"
        ]
        
        for query in safe_queries:
            assert validate_sql_injection(query), f"Safe query failed validation: {query}"
    
    def test_dangerous_queries(self):
        """Test that dangerous queries fail validation."""
        dangerous_queries = [
            "DROP TABLE users",
            "DELETE FROM orders",
            "INSERT INTO users VALUES (1, 'hacker')",
            "UPDATE users SET password = 'hacked'",
            "SELECT * FROM users; DROP TABLE users;",
            "SELECT * FROM users -- comment",
            "SELECT * FROM users /* comment */",
            "EXEC sp_executesql 'malicious code'"
        ]
        
        for query in dangerous_queries:
            assert not validate_sql_injection(query), f"Dangerous query passed validation: {query}"


if __name__ == "__main__":
    pytest.main([__file__])
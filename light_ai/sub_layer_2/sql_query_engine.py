"""
SQL Query Engine for Universal Data Handler Sub-Layer 2.

Provides comprehensive SQL query execution with virtual table support,
cross-resource joins, derived field calculations, query optimization,
and streaming support for large result sets.
"""

import re
import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Iterator, Tuple
from dataclasses import dataclass
from datetime import datetime
from contextlib import contextmanager

from ..core.models import DataHierarchy, ResourceMetadata, ResourceType, AccessLevel
from ..storage.storage_router import StorageRouter
from ..storage.metadata_registry import MetadataRegistry
from ..config import Config, get_config
from ..logger import get_logger

logger = get_logger(__name__)


@dataclass
class QueryResult:
    """Result of a SQL query execution."""
    data: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    execution_time_ms: float
    query_plan: Optional[str] = None
    is_streaming: bool = False
    total_rows: Optional[int] = None  # For streaming queries


@dataclass
class QueryPlan:
    """Query execution plan with optimization information."""
    original_query: str
    optimized_query: str
    tables_accessed: List[str]
    estimated_rows: int
    execution_strategy: str
    optimization_notes: List[str]


class SQLQueryEngine:
    """
    Advanced SQL query engine with cross-resource joins and optimization.
    
    Features:
    - Virtual table support for CSV/Excel files
    - Cross-resource SQL joins
    - Derived field calculations
    - Query optimization and planning
    - Streaming support for large result sets
    - Access control integration
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize SQL query engine.
        
        Args:
            config: Optional configuration instance
        """
        self.config = config or get_config()
        self.storage_router = StorageRouter(config)
        self.metadata_registry = MetadataRegistry(config)
        self._streaming_threshold = 10000  # Switch to streaming for >10k rows
        self._query_cache = {}  # Simple query result cache
        self._cache_ttl = 300  # 5 minutes cache TTL
        
    def initialize(self) -> None:
        """Initialize the query engine and storage systems."""
        self.storage_router.initialize()
        self.metadata_registry.initialize()
        logger.info("SQL Query Engine initialized")
    
    def execute_query(self, sql: str, client_id: str, user_id: str,
                     parameters: Optional[List] = None,
                     access_level: AccessLevel = AccessLevel.USER,
                     enable_streaming: bool = True) -> QueryResult:
        """
        Execute a SQL query with access control and optimization.
        
        Args:
            sql: SQL query string
            client_id: Client ID for access control
            user_id: User ID for access control
            parameters: Optional query parameters
            access_level: Access level for the user
            enable_streaming: Whether to enable streaming for large results
            
        Returns:
            QueryResult: Query execution result
            
        Raises:
            ValueError: If query is invalid or access is denied
            RuntimeError: If query execution fails
        """
        self.initialize()
        
        start_time = datetime.utcnow()
        
        try:
            # Validate and optimize query
            query_plan = self._create_query_plan(sql, client_id, user_id, access_level)
            
            # Check cache first
            cache_key = self._generate_cache_key(query_plan.optimized_query, parameters)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                logger.debug(f"Returning cached query result for user {user_id}")
                return cached_result
            
            # Execute query with access control
            filtered_sql = self._add_access_control_filter(
                query_plan.optimized_query, client_id, user_id, access_level
            )
            
            # Determine if streaming is needed
            estimated_rows = query_plan.estimated_rows
            use_streaming = enable_streaming and estimated_rows > self._streaming_threshold
            
            if use_streaming:
                # Execute with streaming
                result = self._execute_streaming_query(
                    filtered_sql, parameters, query_plan, start_time
                )
            else:
                # Execute normal query
                result = self._execute_normal_query(
                    filtered_sql, parameters, query_plan, start_time
                )
            
            # Cache result if not streaming
            if not result.is_streaming:
                self._cache_result(cache_key, result)
            
            logger.info(f"Executed SQL query for user {user_id}, returned {result.row_count} rows")
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute SQL query: {e}")
            raise RuntimeError(f"Query execution failed: {e}")
    
    def execute_cross_resource_join(self, resources: List[str], join_conditions: List[str],
                                  select_fields: List[str], client_id: str, user_id: str,
                                  where_clause: Optional[str] = None,
                                  access_level: AccessLevel = AccessLevel.USER) -> QueryResult:
        """
        Execute a cross-resource join query across multiple data sources.
        
        Args:
            resources: List of resource IDs to join
            join_conditions: List of JOIN conditions (e.g., ["a.id = b.user_id"])
            select_fields: List of fields to select (e.g., ["a.name", "b.value"])
            client_id: Client ID for access control
            user_id: User ID for access control
            where_clause: Optional WHERE clause
            access_level: Access level for the user
            
        Returns:
            QueryResult: Join query result
        """
        self.initialize()
        
        # Validate access to all resources
        accessible_resources = []
        table_aliases = {}
        
        for i, resource_id in enumerate(resources):
            resource_metadata = self.metadata_registry.get_resource_metadata(resource_id)
            if not resource_metadata:
                raise ValueError(f"Resource not found: {resource_id}")
            
            # Check access
            hierarchy = DataHierarchy(
                client_id=resource_metadata.client_id,
                user_id=resource_metadata.user_id,
                resource_id=resource_id
            )
            
            if not self._validate_access(client_id, user_id, hierarchy, access_level):
                raise ValueError(f"Access denied to resource: {resource_id}")
            
            accessible_resources.append(resource_metadata)
            table_aliases[resource_id] = chr(ord('a') + i)  # a, b, c, etc.
        
        # Build JOIN query
        sql = self._build_join_query(
            accessible_resources, table_aliases, join_conditions,
            select_fields, where_clause
        )
        
        return self.execute_query(sql, client_id, user_id, access_level=access_level)
    
    def create_derived_field(self, base_resource_id: str, field_name: str,
                           calculation: str, client_id: str, user_id: str,
                           access_level: AccessLevel = AccessLevel.USER) -> QueryResult:
        """
        Create a derived field with custom calculations.
        
        Args:
            base_resource_id: Base resource ID
            field_name: Name for the derived field
            calculation: SQL expression for the calculation
            client_id: Client ID for access control
            user_id: User ID for access control
            access_level: Access level for the user
            
        Returns:
            QueryResult: Result with derived field
        """
        self.initialize()
        
        # Validate access to base resource
        resource_metadata = self.metadata_registry.get_resource_metadata(base_resource_id)
        if not resource_metadata:
            raise ValueError(f"Resource not found: {base_resource_id}")
        
        hierarchy = DataHierarchy(
            client_id=resource_metadata.client_id,
            user_id=resource_metadata.user_id,
            resource_id=base_resource_id
        )
        
        if not self._validate_access(client_id, user_id, hierarchy, access_level):
            raise ValueError(f"Access denied to resource: {base_resource_id}")
        
        # Build query with derived field
        table_name = self._get_table_name(resource_metadata)
        sql = f"""
        SELECT *, 
               {calculation} AS {field_name}
        FROM {table_name}
        """
        
        return self.execute_query(sql, client_id, user_id, access_level=access_level)
    
    def get_query_plan(self, sql: str, client_id: str, user_id: str,
                      access_level: AccessLevel = AccessLevel.USER) -> QueryPlan:
        """
        Get query execution plan without executing the query.
        
        Args:
            sql: SQL query string
            client_id: Client ID for access control
            user_id: User ID for access control
            access_level: Access level for the user
            
        Returns:
            QueryPlan: Query execution plan
        """
        self.initialize()
        return self._create_query_plan(sql, client_id, user_id, access_level)
    
    def stream_query_results(self, sql: str, client_id: str, user_id: str,
                           parameters: Optional[List] = None,
                           batch_size: int = 1000,
                           access_level: AccessLevel = AccessLevel.USER) -> Iterator[List[Dict[str, Any]]]:
        """
        Stream query results in batches for large datasets.
        
        Args:
            sql: SQL query string
            client_id: Client ID for access control
            user_id: User ID for access control
            parameters: Optional query parameters
            batch_size: Number of rows per batch
            access_level: Access level for the user
            
        Yields:
            List[Dict[str, Any]]: Batches of query results
        """
        self.initialize()
        
        # Create query plan
        query_plan = self._create_query_plan(sql, client_id, user_id, access_level)
        
        # Add access control
        filtered_sql = self._add_access_control_filter(
            query_plan.optimized_query, client_id, user_id, access_level
        )
        
        # Stream results
        with self.storage_router.db_managers.duckdb.get_connection() as conn:
            if parameters:
                cursor = conn.execute(filtered_sql, parameters)
            else:
                cursor = conn.execute(filtered_sql)
            
            columns = [desc[0] for desc in cursor.description]
            
            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break
                
                batch = [dict(zip(columns, row)) for row in rows]
                yield batch
    
    def _create_query_plan(self, sql: str, client_id: str, user_id: str,
                          access_level: AccessLevel) -> QueryPlan:
        """Create an optimized query execution plan."""
        optimization_notes = []
        
        # Parse query to identify tables
        tables_accessed = self._extract_table_references(sql)
        
        # Validate access to all referenced tables
        for table_ref in tables_accessed:
            if not self._validate_table_access(table_ref, client_id, user_id, access_level):
                raise ValueError(f"Access denied to table: {table_ref}")
        
        # Optimize query
        optimized_query = self._optimize_query(sql, optimization_notes)
        
        # Estimate result size
        estimated_rows = self._estimate_result_size(optimized_query, tables_accessed)
        
        # Determine execution strategy
        if estimated_rows > self._streaming_threshold:
            execution_strategy = "streaming"
            optimization_notes.append(f"Using streaming for {estimated_rows} estimated rows")
        else:
            execution_strategy = "in-memory"
        
        return QueryPlan(
            original_query=sql,
            optimized_query=optimized_query,
            tables_accessed=tables_accessed,
            estimated_rows=estimated_rows,
            execution_strategy=execution_strategy,
            optimization_notes=optimization_notes
        )
    
    def _optimize_query(self, sql: str, optimization_notes: List[str]) -> str:
        """Apply query optimizations."""
        optimized_sql = sql
        
        # Add LIMIT if not present and query looks like it might return many rows
        if "LIMIT" not in sql.upper() and "SELECT *" in sql.upper():
            # Don't auto-limit, but note the potential issue
            optimization_notes.append("Consider adding LIMIT clause for large result sets")
        
        # Suggest indexes for WHERE clauses
        where_match = re.search(r'WHERE\s+(\w+)', sql, re.IGNORECASE)
        if where_match:
            field = where_match.group(1)
            optimization_notes.append(f"Query filters on '{field}' - index recommended")
        
        # Check for cross joins (missing JOIN conditions)
        if "," in sql and "JOIN" not in sql.upper():
            optimization_notes.append("Potential cross join detected - verify JOIN conditions")
        
        return optimized_sql
    
    def _extract_table_references(self, sql: str) -> List[str]:
        """Extract table references from SQL query."""
        tables = []
        
        # Look for structured_data.table_name patterns
        structured_pattern = r'structured_data\.(\w+)'
        structured_matches = re.findall(structured_pattern, sql, re.IGNORECASE)
        tables.extend([f"structured_data.{match}" for match in structured_matches])
        
        # Look for json_data.table_name patterns
        json_pattern = r'json_data\.(\w+)'
        json_matches = re.findall(json_pattern, sql, re.IGNORECASE)
        tables.extend([f"json_data.{match}" for match in json_matches])
        
        # Look for FROM and JOIN clauses
        from_pattern = r'FROM\s+(\w+(?:\.\w+)?)'
        from_matches = re.findall(from_pattern, sql, re.IGNORECASE)
        tables.extend(from_matches)
        
        join_pattern = r'JOIN\s+(\w+(?:\.\w+)?)'
        join_matches = re.findall(join_pattern, sql, re.IGNORECASE)
        tables.extend(join_matches)
        
        return list(set(tables))  # Remove duplicates
    
    def _validate_table_access(self, table_ref: str, client_id: str, user_id: str,
                              access_level: AccessLevel) -> bool:
        """Validate access to a table reference."""
        # Extract resource ID from table name
        if "structured_data." in table_ref:
            table_name = table_ref.split(".")[-1]
            if table_name.startswith("resource_"):
                # Remove "resource_" prefix and "_enhanced" suffix if present
                resource_part = table_name.replace("resource_", "")
                if resource_part.endswith("_enhanced"):
                    resource_part = resource_part.replace("_enhanced", "")
                # Convert underscores back to hyphens for UUID format
                resource_id = resource_part.replace("_", "-")
            else:
                return False
        elif "json_data." in table_ref:
            table_name = table_ref.split(".")[-1]
            if table_name.startswith("json_"):
                # Remove "json_" prefix and convert underscores to hyphens
                resource_id = table_name.replace("json_", "").replace("_", "-")
            else:
                return False
        else:
            # Unknown table format
            return False
        
        # Get resource metadata
        resource_metadata = self.metadata_registry.get_resource_metadata(resource_id)
        if not resource_metadata:
            return False
        
        # Check access
        hierarchy = DataHierarchy(
            client_id=resource_metadata.client_id,
            user_id=resource_metadata.user_id,
            resource_id=resource_id
        )
        
        return self._validate_access(client_id, user_id, hierarchy, access_level)
    
    def _validate_access(self, requesting_client_id: str, requesting_user_id: str,
                        target_hierarchy: DataHierarchy, access_level: AccessLevel) -> bool:
        """Validate access to a resource based on hierarchy and access level."""
        # Must be same client
        if requesting_client_id != target_hierarchy.client_id:
            return False
        
        # Check access based on level
        if access_level == AccessLevel.USER:
            return requesting_user_id == target_hierarchy.user_id
        elif access_level in [AccessLevel.MANAGER, AccessLevel.ADMIN]:
            return True  # Same client access
        
        return False
    
    def _estimate_result_size(self, sql: str, tables_accessed: List[str]) -> int:
        """Estimate the number of rows the query will return."""
        # Simple estimation based on table sizes
        total_estimated = 0
        
        for table_ref in tables_accessed:
            try:
                # Get table row count
                count_sql = f"SELECT COUNT(*) as count FROM {table_ref}"
                with self.storage_router.db_managers.duckdb.get_connection() as conn:
                    result = conn.execute(count_sql).fetchone()
                    if result:
                        total_estimated += result[0]
            except Exception:
                # If we can't get count, assume moderate size
                total_estimated += 1000
        
        # Adjust for JOINs (typically reduce result size)
        if "JOIN" in sql.upper():
            total_estimated = int(total_estimated * 0.7)  # Assume 30% reduction
        
        # Adjust for WHERE clauses (typically reduce result size)
        if "WHERE" in sql.upper():
            total_estimated = int(total_estimated * 0.5)  # Assume 50% reduction
        
        return max(1, total_estimated)
    
    def _add_access_control_filter(self, sql: str, client_id: str, user_id: str,
                                  access_level: AccessLevel) -> str:
        """Add access control filtering to SQL queries."""
        # For user-level access, filter by exact user_id
        if access_level == AccessLevel.USER:
            user_filter = f"user_id = '{user_id}'"
        else:
            # For manager/admin, allow any user in the same client
            user_filter = "1=1"  # No user restriction
        
        # Replace table references with enhanced views that have access control columns
        # Only add _enhanced if it's not already there
        enhanced_sql = re.sub(
            r'structured_data\.(resource_[a-f0-9_]+)(?<!_enhanced)\b',
            r'structured_data.\1_enhanced',
            sql
        )
        
        # Add access control WHERE clause
        if "WHERE" in enhanced_sql.upper():
            # Add to existing WHERE clause
            enhanced_sql = re.sub(
                r'\bWHERE\b',
                f"WHERE client_id = '{client_id}' AND {user_filter} AND (",
                enhanced_sql,
                flags=re.IGNORECASE
            ) + ")"
        else:
            # Find the position to insert WHERE clause (before ORDER BY, LIMIT, etc.)
            # Split the query to find the right position
            order_by_match = re.search(r'\b(ORDER\s+BY|LIMIT|OFFSET)\b', enhanced_sql, re.IGNORECASE)
            if order_by_match:
                # Insert WHERE clause before ORDER BY/LIMIT/OFFSET
                insert_pos = order_by_match.start()
                enhanced_sql = (
                    enhanced_sql[:insert_pos] + 
                    f" WHERE client_id = '{client_id}' AND {user_filter} " +
                    enhanced_sql[insert_pos:]
                )
            else:
                # Add WHERE clause at the end
                enhanced_sql += f" WHERE client_id = '{client_id}' AND {user_filter}"
        
        return enhanced_sql
    
    def _execute_normal_query(self, sql: str, parameters: Optional[List],
                             query_plan: QueryPlan, start_time: datetime) -> QueryResult:
        """Execute a normal (non-streaming) query."""
        with self.storage_router.db_managers.duckdb.get_connection() as conn:
            if parameters:
                cursor = conn.execute(sql, parameters)
            else:
                cursor = conn.execute(sql)
            
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            data = [dict(zip(columns, row)) for row in rows]
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return QueryResult(
                data=data,
                columns=columns,
                row_count=len(data),
                execution_time_ms=execution_time,
                query_plan=query_plan.execution_strategy,
                is_streaming=False
            )
    
    def _execute_streaming_query(self, sql: str, parameters: Optional[List],
                                query_plan: QueryPlan, start_time: datetime) -> QueryResult:
        """Execute a streaming query for large result sets."""
        # For streaming, we return a limited preview and indicate streaming is available
        preview_sql = f"SELECT * FROM ({sql}) LIMIT 100"
        
        with self.storage_router.db_managers.duckdb.get_connection() as conn:
            # Get total count
            count_sql = f"SELECT COUNT(*) as total FROM ({sql})"
            if parameters:
                total_result = conn.execute(count_sql, parameters).fetchone()
            else:
                total_result = conn.execute(count_sql).fetchone()
            
            total_rows = total_result[0] if total_result else 0
            
            # Get preview data
            if parameters:
                cursor = conn.execute(preview_sql, parameters)
            else:
                cursor = conn.execute(preview_sql)
            
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            data = [dict(zip(columns, row)) for row in rows]
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return QueryResult(
                data=data,
                columns=columns,
                row_count=len(data),
                execution_time_ms=execution_time,
                query_plan=f"streaming (preview of {len(data)} rows)",
                is_streaming=True,
                total_rows=total_rows
            )
    
    def _build_join_query(self, resources: List[ResourceMetadata], table_aliases: Dict[str, str],
                         join_conditions: List[str], select_fields: List[str],
                         where_clause: Optional[str]) -> str:
        """Build a JOIN query across multiple resources."""
        # Build FROM clause with first table
        first_resource = resources[0]
        first_table = self._get_table_name(first_resource)
        first_alias = table_aliases[first_resource.resource_id]
        
        sql = f"SELECT {', '.join(select_fields)} FROM {first_table} {first_alias}"
        
        # Add JOIN clauses
        for i, resource in enumerate(resources[1:], 1):
            table_name = self._get_table_name(resource)
            alias = table_aliases[resource.resource_id]
            join_condition = join_conditions[i-1] if i-1 < len(join_conditions) else "1=1"
            
            sql += f" JOIN {table_name} {alias} ON {join_condition}"
        
        # Add WHERE clause
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        return sql
    
    def _get_table_name(self, resource_metadata: ResourceMetadata) -> str:
        """Get the appropriate table name for a resource."""
        if resource_metadata.resource_type == ResourceType.STRUCTURED:
            return f"structured_data.resource_{resource_metadata.resource_id.replace('-', '_')}_enhanced"
        elif resource_metadata.resource_type == ResourceType.JSON:
            return f"json_data.json_{resource_metadata.resource_id.replace('-', '_')}"
        else:
            raise ValueError(f"Unsupported resource type for SQL queries: {resource_metadata.resource_type}")
    
    def _generate_cache_key(self, sql: str, parameters: Optional[List]) -> str:
        """Generate a cache key for query results."""
        key_data = {"sql": sql, "parameters": parameters or []}
        return str(hash(json.dumps(key_data, sort_keys=True)))
    
    def _get_cached_result(self, cache_key: str) -> Optional[QueryResult]:
        """Get cached query result if still valid."""
        if cache_key in self._query_cache:
            cached_data, timestamp = self._query_cache[cache_key]
            if (datetime.utcnow() - timestamp).total_seconds() < self._cache_ttl:
                return cached_data
            else:
                # Remove expired cache entry
                del self._query_cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: QueryResult) -> None:
        """Cache query result with timestamp."""
        self._query_cache[cache_key] = (result, datetime.utcnow())
        
        # Simple cache size management - keep only last 100 entries
        if len(self._query_cache) > 100:
            oldest_key = min(self._query_cache.keys(), 
                           key=lambda k: self._query_cache[k][1])
            del self._query_cache[oldest_key]
    
    def clear_cache(self) -> int:
        """Clear query result cache."""
        cache_size = len(self._query_cache)
        self._query_cache.clear()
        logger.info(f"Cleared query cache ({cache_size} entries)")
        return cache_size
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get query cache statistics."""
        return {
            "cache_size": len(self._query_cache),
            "cache_ttl_seconds": self._cache_ttl,
            "streaming_threshold": self._streaming_threshold
        }
    
    def close(self) -> None:
        """Close the query engine and clean up resources."""
        self.clear_cache()
        self.storage_router.close()
        logger.info("SQL Query Engine closed")


# Utility functions for query building and optimization

def build_select_query(table_name: str, columns: List[str] = None,
                      where_conditions: List[str] = None,
                      order_by: List[str] = None,
                      limit: Optional[int] = None) -> str:
    """
    Build a SELECT query with common clauses.
    
    Args:
        table_name: Name of the table to query
        columns: List of columns to select (default: all)
        where_conditions: List of WHERE conditions
        order_by: List of ORDER BY clauses
        limit: Optional LIMIT value
        
    Returns:
        str: Complete SELECT query
    """
    # SELECT clause
    if columns:
        select_clause = f"SELECT {', '.join(columns)}"
    else:
        select_clause = "SELECT *"
    
    # FROM clause
    query = f"{select_clause} FROM {table_name}"
    
    # WHERE clause
    if where_conditions:
        query += f" WHERE {' AND '.join(where_conditions)}"
    
    # ORDER BY clause
    if order_by:
        query += f" ORDER BY {', '.join(order_by)}"
    
    # LIMIT clause
    if limit:
        query += f" LIMIT {limit}"
    
    return query


def build_aggregation_query(table_name: str, group_by_columns: List[str],
                           aggregations: Dict[str, str],
                           where_conditions: List[str] = None,
                           having_conditions: List[str] = None) -> str:
    """
    Build an aggregation query with GROUP BY.
    
    Args:
        table_name: Name of the table to query
        group_by_columns: Columns to group by
        aggregations: Dict of {alias: aggregation_expression}
        where_conditions: Optional WHERE conditions
        having_conditions: Optional HAVING conditions
        
    Returns:
        str: Complete aggregation query
    """
    # SELECT clause with grouping columns and aggregations
    select_items = group_by_columns.copy()
    for alias, expr in aggregations.items():
        select_items.append(f"{expr} AS {alias}")
    
    query = f"SELECT {', '.join(select_items)} FROM {table_name}"
    
    # WHERE clause
    if where_conditions:
        query += f" WHERE {' AND '.join(where_conditions)}"
    
    # GROUP BY clause
    query += f" GROUP BY {', '.join(group_by_columns)}"
    
    # HAVING clause
    if having_conditions:
        query += f" HAVING {' AND '.join(having_conditions)}"
    
    return query


def validate_sql_injection(sql: str) -> bool:
    """
    Basic SQL injection validation.
    
    Args:
        sql: SQL query to validate
        
    Returns:
        bool: True if query appears safe, False otherwise
    """
    # List of dangerous SQL keywords/patterns
    dangerous_patterns = [
        r'\bDROP\b',
        r'\bDELETE\b',
        r'\bINSERT\b',
        r'\bUPDATE\b',
        r'\bALTER\b',
        r'\bCREATE\b',
        r'\bTRUNCATE\b',
        r'\bEXEC\b',
        r'\bEXECUTE\b',
        r'--',  # SQL comments
        r'/\*',  # SQL block comments
        r';\s*\w',  # Multiple statements
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, sql, re.IGNORECASE):
            return False
    
    return True
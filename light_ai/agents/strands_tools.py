"""
AI Agent Tools for Data Operations using Strands Framework.

Provides specialized tools for the Master AI Agent to perform data operations
including resource discovery, field extraction, query execution, data synthesis,
cross-resource synthesis, and visualization generation.
"""

import json
import time
import uuid
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime

from ..core.models import ResourceMetadata, ResourceType, AccessLevel
from ..storage.storage_router import StorageRouter
from ..storage.metadata_registry import MetadataRegistry
from ..sub_layer_2.sql_query_engine import SQLQueryEngine
from ..sub_layer_2.semantic_search_engine import SemanticSearchEngine, SearchStrategy
from ..config import Config, get_config
from ..logger import get_logger
from .logging import get_activity_logger
# Import the new data retrieval engine
from ..data_retrieval_engine import get_retrieval_engine

logger = get_logger(__name__)
activity_logger = get_activity_logger()


@dataclass
class ToolResult:
    """Standard result format for all agent tools."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


class ResourceDiscoveryTool:
    """
    Tool for automatic data source cataloging and resource discovery.
    
    Helps the AI agent identify relevant data sources for queries and
    understand the available data landscape.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize resource discovery tool."""
        self.config = config or get_config()
        # Use the new data retrieval engine that works with Universal Data Handler
        self.retrieval_engine = get_retrieval_engine()
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize the tool and dependencies."""
        if not self._initialized:
            # The retrieval engine handles its own initialization
            self._initialized = True
    
    def discover_resources(self, user_id: str, client_id: str, 
                          query_context: Optional[str] = None,
                          resource_type: Optional[ResourceType] = None) -> ToolResult:
        """
        Discover and catalog available data sources for a user.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            query_context: Optional context about what kind of data is needed
            resource_type: Optional filter by resource type
            
        Returns:
            ToolResult with discovered resources
        """
        start_time = time.time()
        
        try:
            self.initialize()
            
            # Log tool usage
            activity_logger.log_tool_usage(
                "master_data_analyst", user_id, client_id,
                "resource_discovery", 
                {"query_context": query_context, "resource_type": resource_type.value if resource_type else None},
                None, 0.0
            )
            
            # Get all accessible resources using the new data retrieval engine
            user_resources = self.retrieval_engine.get_user_resources(client_id, user_id)
            
            if not user_resources:
                return ToolResult(
                    success=False,
                    error="No resources found for this user",
                    execution_time_ms=(time.time() - start_time) * 1000
                )
            
            # Convert ResourceInfo objects to dictionaries for compatibility
            resources_data = []
            for resource_info in user_resources:
                resource_dict = {
                    "resource_id": resource_info.resource_id,
                    "filename": resource_info.original_filename,
                    "resource_type": resource_info.data_type,
                    "type": resource_info.data_type,
                    "size_bytes": resource_info.file_size_bytes,
                    "created_at": resource_info.created_at,
                    "row_count": resource_info.row_count,
                    "column_count": resource_info.column_count
                }
                resources_data.append(resource_dict)
            
            # Filter by type if specified
            if resource_type:
                resources_data = [r for r in resources_data if r.get("resource_type") == resource_type.value]
            
            # Score resources based on query context if provided
            if query_context:
                scored_resources = self._score_resources_by_context(resources_data, query_context)
            else:
                scored_resources = [(r, 1.0) for r in resources_data]
            
            # Build comprehensive resource information
            resource_info_list = []
            for resource_dict, relevance_score in scored_resources:
                resource_info = {
                    "resource_id": resource_dict.get("resource_id"),
                    "filename": resource_dict.get("filename"),
                    "resource_type": resource_dict.get("type"),
                    "data_type": resource_dict.get("type"),
                    "file_size_mb": round(resource_dict.get("size_bytes", 0) / (1024 * 1024), 2),
                    "created_at": resource_dict.get("created_at"),
                    "relevance_score": relevance_score,
                    "processing_status": "completed"
                }
                
                resource_info_list.append(resource_info)
            
            execution_time = (time.time() - start_time) * 1000
            
            # Update tool usage log
            activity_logger.log_tool_usage(
                "master_data_analyst", user_id, client_id,
                "resource_discovery", 
                {"query_context": query_context, "resource_type": resource_type.value if resource_type else None},
                f"Found {len(resource_info_list)} resources", execution_time
            )
            
            return ToolResult(
                success=True,
                data={
                    "resources": resource_info_list,
                    "total_count": len(resource_info_list),
                    "resource_types": list(set(r["resource_type"] for r in resource_info_list if r["resource_type"]))
                },
                execution_time_ms=execution_time,
                metadata={"query_context": query_context}
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Resource discovery failed: {str(e)}"
            logger.error(error_msg)
            
            activity_logger.log_tool_usage(
                "master_data_analyst", user_id, client_id,
                "resource_discovery", 
                {"query_context": query_context},
                error_msg, execution_time
            )
            
            return ToolResult(
                success=False,
                error=error_msg,
                execution_time_ms=execution_time
            )
    
    def _score_resources_by_context(self, resources: List[Dict[str, Any]], 
                                   query_context: str) -> List[tuple]:
        """Score resources based on relevance to query context."""
        import re
        
        scored_resources = []
        query_words = set(re.findall(r'\w+', query_context.lower()))
        
        for resource in resources:
            score = 0.0
            
            # Check filename relevance
            filename = resource.get("original_filename", resource.get("filename", ""))
            filename_words = set(re.findall(r'\w+', filename.lower()))
            common_words = query_words & filename_words
            if filename_words:
                score += len(common_words) / len(filename_words) * 0.5
            
            # Boost recent files
            created_at_str = resource.get("created_at", "")
            if created_at_str:
                try:
                    from datetime import datetime
                    if isinstance(created_at_str, str):
                        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    else:
                        created_at = created_at_str
                    days_old = (datetime.utcnow() - created_at.replace(tzinfo=None)).days
                    if days_old < 7:
                        score += 0.2
                    elif days_old < 30:
                        score += 0.1
                except:
                    pass
            
            # Boost larger datasets
            row_count = resource.get("row_count", 0)
            chunk_count = resource.get("chunk_count", 0)
            if row_count and row_count > 100:
                score += 0.1
            elif chunk_count and chunk_count > 10:
                score += 0.1
            
            # Ensure minimum score
            score = max(score, 0.1)
            scored_resources.append((resource, score))
        
        # Sort by score descending
        scored_resources.sort(key=lambda x: x[1], reverse=True)
        return scored_resources


class FieldExtractionTool:
    """
    Tool for intelligent field mapping and extraction.
    
    Analyzes desired fields against available data and suggests
    field mappings and derivations.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize field extraction tool."""
        self.config = config or get_config()
        # Use the new data retrieval engine
        self.retrieval_engine = get_retrieval_engine()
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize the tool and dependencies."""
        if not self._initialized:
            # The retrieval engine handles its own initialization
            self._initialized = True
    
    def extract_and_map_fields(self, user_id: str, client_id: str,
                              desired_fields: Dict[str, str],
                              resource_ids: Optional[List[str]] = None) -> ToolResult:
        """
        Extract and map fields from available data sources.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            desired_fields: Dict of {field_name: description} for desired fields
            resource_ids: Optional list of specific resources to analyze
            
        Returns:
            ToolResult with field mapping information
        """
        start_time = time.time()
        
        try:
            self.initialize()
            
            # Log tool usage
            activity_logger.log_tool_usage(
                "master_data_analyst", user_id, client_id,
                "field_extraction", 
                {"desired_fields": desired_fields, "resource_ids": resource_ids},
                None, 0.0
            )
            
            # Get resources to analyze using the data retrieval engine
            if resource_ids:
                # Get specific resources
                resources = []
                for resource_id in resource_ids:
                    resource_result = self.retrieval_engine.get_resource_by_id(resource_id)
                    if resource_result.success and resource_result.data:
                        resources.append({
                            "resource_id": resource_id,
                            "data": resource_result.data
                        })
            else:
                # Get all user resources
                user_resources = self.retrieval_engine.get_user_resources(client_id, user_id)
                resources = [{"resource_id": r["resource_id"], "data": None} for r in user_resources]
            
            # Analyze fields in each resource
            field_mappings = {}
            available_fields = {}
            
            for resource in resources:
                resource_id = resource["resource_id"]
                
                # Get the actual data if not already loaded
                if resource["data"] is None:
                    resource_result = self.retrieval_engine.get_resource_by_id(resource_id)
                    resource_data = resource_result.data if resource_result.success else None
                else:
                    resource_data = resource["data"]
                
                if resource_data and isinstance(resource_data, dict):
                    # Extract field names from the data structure
                    resource_fields = self._extract_fields_from_data(resource_data)
                    available_fields[resource_id] = resource_fields
                    
                    # Map desired fields to available fields
                    mappings = self._map_fields(desired_fields, resource_fields)
                    if mappings:
                        field_mappings[resource_id] = mappings
            
            # Generate field derivation suggestions
            derivation_suggestions = self._suggest_field_derivations(
                desired_fields, available_fields
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            # Update tool usage log
            activity_logger.log_tool_usage(
                "master_data_analyst", user_id, client_id,
                "field_extraction", 
                {"desired_fields": desired_fields},
                f"Mapped {len(field_mappings)} resources", execution_time
            )
            
            return ToolResult(
                success=True,
                data={
                    "field_mappings": field_mappings,
                    "available_fields": available_fields,
                    "derivation_suggestions": derivation_suggestions,
                    "resources_analyzed": len(resources)
                },
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Field extraction failed: {str(e)}"
            logger.error(error_msg)
            
            activity_logger.log_tool_usage(
                "master_data_analyst", user_id, client_id,
                "field_extraction", 
                {"desired_fields": desired_fields},
                error_msg, execution_time
            )
            
            return ToolResult(
                success=False,
                error=error_msg,
                execution_time_ms=execution_time
            )
    
    def _extract_fields_from_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract field information from actual data structure."""
        fields = {}
        
        def extract_from_dict(d: Dict[str, Any], prefix: str = ""):
            for key, value in d.items():
                field_name = f"{prefix}.{key}" if prefix else key
                
                if isinstance(value, dict):
                    # Nested dictionary - recurse
                    extract_from_dict(value, field_name)
                elif isinstance(value, list) and value and isinstance(value[0], dict):
                    # List of dictionaries - analyze first item
                    extract_from_dict(value[0], field_name)
                else:
                    # Simple field
                    field_type = type(value).__name__
                    fields[field_name] = {
                        "type": field_type,
                        "description": f"Field of type {field_type}",
                        "nullable": True,
                        "sample_value": str(value)[:100] if value is not None else None
                    }
        
        extract_from_dict(data)
        return fields
    
    def _analyze_structured_fields(self, resource: ResourceMetadata) -> Dict[str, Any]:
        """Analyze fields in a structured resource."""
        fields = {}
        
        try:
            # Get schema information
            schema_info = self.metadata_registry.get_schema_info(resource.resource_id)
            if schema_info:
                schema_data = json.loads(schema_info.schema_json)
                
                for col_name, col_info in schema_data.get("columns", {}).items():
                    fields[col_name] = {
                        "type": col_info.get("type", "unknown"),
                        "description": col_info.get("description", ""),
                        "nullable": col_info.get("nullable", True),
                        "unique_values": col_info.get("unique_values", 0)
                    }
        
        except Exception as e:
            logger.warning(f"Failed to analyze fields for {resource.resource_id}: {e}")
        
        return fields
    
    def _map_fields(self, desired_fields: Dict[str, str], 
                   available_fields: Dict[str, Any]) -> Dict[str, Any]:
        """Map desired fields to available fields."""
        mappings = {}
        
        for desired_name, desired_desc in desired_fields.items():
            best_match = None
            best_score = 0.0
            
            for available_name, available_info in available_fields.items():
                score = self._calculate_field_similarity(
                    desired_name, desired_desc, available_name, available_info
                )
                
                if score > best_score and score > 0.3:  # Minimum similarity threshold
                    best_score = score
                    best_match = {
                        "available_field": available_name,
                        "similarity_score": score,
                        "field_info": available_info,
                        "mapping_type": "direct" if score > 0.8 else "similar"
                    }
            
            if best_match:
                mappings[desired_name] = best_match
        
        return mappings
    
    def _calculate_field_similarity(self, desired_name: str, desired_desc: str,
                                   available_name: str, available_info: Dict[str, Any]) -> float:
        """Calculate similarity between desired and available fields."""
        import re
        
        score = 0.0
        
        # Name similarity
        desired_words = set(re.findall(r'\w+', desired_name.lower()))
        available_words = set(re.findall(r'\w+', available_name.lower()))
        
        if desired_words and available_words:
            common_words = desired_words & available_words
            score += len(common_words) / max(len(desired_words), len(available_words)) * 0.6
        
        # Description similarity
        if desired_desc and available_info.get("description"):
            desc_desired = set(re.findall(r'\w+', desired_desc.lower()))
            desc_available = set(re.findall(r'\w+', available_info["description"].lower()))
            
            if desc_desired and desc_available:
                common_desc = desc_desired & desc_available
                score += len(common_desc) / max(len(desc_desired), len(desc_available)) * 0.4
        
        return min(score, 1.0)
    
    def _suggest_field_derivations(self, desired_fields: Dict[str, str],
                                  available_fields: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Suggest how to derive missing fields from available data."""
        suggestions = []
        
        # This is a simplified implementation - in practice, this would use
        # more sophisticated AI reasoning to suggest derivations
        for desired_name, desired_desc in desired_fields.items():
            # Check if any resource has fields that could be combined
            for resource_id, fields in available_fields.items():
                if len(fields) >= 2:  # Need at least 2 fields to derive something
                    suggestions.append({
                        "desired_field": desired_name,
                        "resource_id": resource_id,
                        "derivation_type": "calculation",
                        "suggestion": f"Could potentially derive '{desired_name}' from available fields in {resource_id}",
                        "confidence": 0.5,
                        "available_fields": list(fields.keys())
                    })
        
        return suggestions[:5]  # Limit suggestions


class QueryExecutionTool:
    """
    Tool for safe query execution with validation.
    
    Executes queries against user data with proper access control
    and safety validation.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize query execution tool."""
        self.config = config or get_config()
        # Use the new data retrieval engine
        self.retrieval_engine = get_retrieval_engine()
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize the tool and dependencies."""
        if not self._initialized:
            # The retrieval engine handles its own initialization
            self._initialized = True
    
    def execute_query(self, user_id: str, client_id: str,
                     query: str, query_type: str = "sql",
                     parameters: Optional[List] = None,
                     access_level: AccessLevel = AccessLevel.USER) -> ToolResult:
        """
        Execute a query with safety validation.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            query: Query to execute
            query_type: Type of query ("sql", "search", etc.)
            parameters: Optional query parameters
            access_level: User access level
            
        Returns:
            ToolResult with query results
        """
        start_time = time.time()
        
        try:
            self.initialize()
            
            # Log tool usage
            activity_logger.log_tool_usage(
                "master_data_analyst", user_id, client_id,
                "query_execution", 
                {"query_type": query_type, "query_length": len(query)},
                None, 0.0
            )
            
            # Validate query safety
            if not self._validate_query_safety(query, query_type):
                return ToolResult(
                    success=False,
                    error="Query failed safety validation",
                    execution_time_ms=(time.time() - start_time) * 1000
                )
            
            # Execute based on query type
            if query_type == "sql":
                # For now, return a simple message since SQL queries need the full system
                data = {
                    "results": [],
                    "message": "SQL queries not yet supported in simplified mode. Use data retrieval instead.",
                    "query_type": "sql"
                }
            
            elif query_type == "search":
                # Use the retrieval engine to search user data
                search_results = self.retrieval_engine.search_user_data(client_id, user_id, query)
                
                data = {
                    "results": search_results.get("matches", []),
                    "total_results": search_results.get("total_searched", 0),
                    "search_time_ms": 0,
                    "query_type": "search"
                }
            
            elif query_type == "data":
                # Get all user data
                all_data = self.retrieval_engine.get_all_user_data(client_id, user_id)
                
                data = {
                    "results": all_data.get("data_by_source", {}).get("json_files", []),
                    "total_results": all_data.get("total_resources", 0),
                    "query_type": "data"
                }
            
            else:
                return ToolResult(
                    success=False,
                    error=f"Unsupported query type: {query_type}",
                    execution_time_ms=(time.time() - start_time) * 1000
                )
            
            execution_time = (time.time() - start_time) * 1000
            
            # Update tool usage log
            activity_logger.log_tool_usage(
                "master_data_analyst", user_id, client_id,
                "query_execution", 
                {"query_type": query_type},
                f"Returned {data.get('row_count', 0)} rows", execution_time
            )
            
            return ToolResult(
                success=True,
                data=data,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Query execution failed: {str(e)}"
            logger.error(error_msg)
            
            activity_logger.log_tool_usage(
                "master_data_analyst", user_id, client_id,
                "query_execution", 
                {"query_type": query_type},
                error_msg, execution_time
            )
            
            return ToolResult(
                success=False,
                error=error_msg,
                execution_time_ms=execution_time
            )
    
    def _validate_query_safety(self, query: str, query_type: str) -> bool:
        """Validate query for safety (prevent dangerous operations)."""
        if query_type == "sql":
            query_upper = query.upper()
            
            # Block dangerous SQL operations
            dangerous_keywords = [
                "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE",
                "TRUNCATE", "EXEC", "EXECUTE", "GRANT", "REVOKE"
            ]
            
            for keyword in dangerous_keywords:
                if keyword in query_upper:
                    logger.warning(f"Blocked dangerous SQL keyword: {keyword}")
                    return False
        
        return True


class DataSynthesisTool:
    """
    Tool for data synthesis and analysis across multiple sources.
    
    Combines data from multiple sources and generates insights.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize data synthesis tool."""
        self.config = config or get_config()
        # Use the new data retrieval engine
        self.retrieval_engine = get_retrieval_engine()
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize the tool and dependencies."""
        if not self._initialized:
            # The retrieval engine handles its own initialization
            self._initialized = True
    
    def synthesize_data(self, user_id: str, client_id: str,
                       resource_ids: List[str],
                       synthesis_type: str = "summary") -> ToolResult:
        """
        Synthesize data from multiple sources.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            resource_ids: List of resource IDs to synthesize
            synthesis_type: Type of synthesis ("summary", "correlation", etc.)
            
        Returns:
            ToolResult with synthesis results
        """
        start_time = time.time()
        
        try:
            self.initialize()
            
            # Log tool usage
            activity_logger.log_tool_usage(
                "master_data_analyst", user_id, client_id,
                "data_synthesis", 
                {"resource_ids": resource_ids, "synthesis_type": synthesis_type},
                None, 0.0
            )
            
            # Get resource information using the data retrieval engine
            resources = []
            for resource_id in resource_ids:
                resource_result = self.retrieval_engine.get_resource_by_id(resource_id)
                if resource_result.success and resource_result.data:
                    resources.append({
                        "resource_id": resource_id,
                        "data": resource_result.data
                    })
            
            if not resources:
                return ToolResult(
                    success=False,
                    error="No accessible resources found for synthesis",
                    execution_time_ms=(time.time() - start_time) * 1000
                )
            
            # Perform synthesis based on type
            if synthesis_type == "summary":
                synthesis_result = self._generate_summary_synthesis(resources)
            elif synthesis_type == "correlation":
                synthesis_result = self._generate_correlation_synthesis(resources)
            else:
                synthesis_result = {
                    "message": f"Synthesis type '{synthesis_type}' not yet implemented",
                    "resources_analyzed": len(resources)
                }
            
            execution_time = (time.time() - start_time) * 1000
            
            # Update tool usage log
            activity_logger.log_tool_usage(
                "master_data_analyst", user_id, client_id,
                "data_synthesis", 
                {"synthesis_type": synthesis_type},
                f"Synthesized {len(resources)} resources", execution_time
            )
            
            return ToolResult(
                success=True,
                data=synthesis_result,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Data synthesis failed: {str(e)}"
            logger.error(error_msg)
            
            activity_logger.log_tool_usage(
                "master_data_analyst", user_id, client_id,
                "data_synthesis", 
                {"synthesis_type": synthesis_type},
                error_msg, execution_time
            )
            
            return ToolResult(
                success=False,
                error=error_msg,
                execution_time_ms=execution_time
            )
    
    def _generate_summary_synthesis(self, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary synthesis of resources."""
        structured_count = len([r for r in resources if r.get("resource_type") == "structured"])
        unstructured_count = len([r for r in resources if r.get("resource_type") == "unstructured"])
        json_count = len([r for r in resources if r.get("resource_type") == "json"])
        
        total_rows = sum(r.get("row_count", 0) or 0 for r in resources)
        total_size_mb = sum(r.get("file_size_bytes", 0) for r in resources) / (1024 * 1024)
        
        # Get date range
        created_dates = []
        for r in resources:
            created_at = r.get("created_at")
            if created_at:
                try:
                    if isinstance(created_at, str):
                        from datetime import datetime
                        created_dates.append(datetime.fromisoformat(created_at.replace('Z', '+00:00')))
                    else:
                        created_dates.append(created_at)
                except:
                    pass
        
        date_range = {}
        if created_dates:
            date_range = {
                "earliest": min(created_dates).isoformat(),
                "latest": max(created_dates).isoformat()
            }
        
        return {
            "synthesis_type": "summary",
            "total_resources": len(resources),
            "resource_breakdown": {
                "structured": structured_count,
                "unstructured": unstructured_count,
                "json": json_count
            },
            "total_data_rows": total_rows,
            "total_size_mb": round(total_size_mb, 2),
            "date_range": date_range,
            "resources": [
                {
                    "filename": r.get("original_filename", r.get("filename", "unknown")),
                    "type": r.get("resource_type", "unknown"),
                    "rows": r.get("row_count"),
                    "size_mb": round(r.get("file_size_bytes", 0) / (1024 * 1024), 2)
                }
                for r in resources
            ]
        }
    
    def _generate_correlation_synthesis(self, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate correlation synthesis (placeholder implementation)."""
        return {
            "synthesis_type": "correlation",
            "message": "Correlation analysis not yet implemented",
            "resources_analyzed": len(resources),
            "suggestion": "Use summary synthesis for now"
        }


class CrossResourceSynthesisTool:
    """
    Tool for cross-resource data synthesis and combination.
    
    Combines data from multiple sources using intelligent strategies
    and resolves schema conflicts automatically.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize cross-resource synthesis tool."""
        self.config = config or get_config()
        # Use the new data retrieval engine
        self.retrieval_engine = get_retrieval_engine()
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize the tool and dependencies."""
        if not self._initialized:
            # The retrieval engine handles its own initialization
            self._initialized = True
    
    def synthesize_resources(self, user_id: str, client_id: str,
                           resource_ids: List[str],
                           synthesis_goal: str,
                           desired_fields: Optional[Dict[str, str]] = None) -> ToolResult:
        """
        Synthesize data from multiple resources into a unified view.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            resource_ids: List of resource IDs to synthesize
            synthesis_goal: Description of synthesis objective
            desired_fields: Optional target schema specification
            
        Returns:
            ToolResult with synthesis specification and execution plan
        """
        start_time = time.time()
        
        try:
            self.initialize()
            
            # Log tool usage
            activity_logger.log_tool_usage(
                "master_data_analyst", user_id, client_id,
                "cross_resource_synthesis", 
                {"resource_ids": resource_ids, "synthesis_goal": synthesis_goal},
                None, 0.0
            )
            
            # Import here to avoid circular imports
            from .cross_resource_synthesis_agent import CrossResourceSynthesisAgent
            
            # Create synthesis agent
            synthesis_agent = CrossResourceSynthesisAgent(self.config)
            
            # This would be async in a real implementation
            # For now, create a simplified synchronous version
            synthesis_result = self._create_synthesis_plan(
                user_id, client_id, resource_ids, synthesis_goal, desired_fields
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            # Update tool usage log
            activity_logger.log_tool_usage(
                "master_data_analyst", user_id, client_id,
                "cross_resource_synthesis", 
                {"synthesis_goal": synthesis_goal},
                f"Created synthesis plan for {len(resource_ids)} resources", execution_time
            )
            
            return ToolResult(
                success=True,
                data=synthesis_result,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Cross-resource synthesis failed: {str(e)}"
            logger.error(error_msg)
            
            activity_logger.log_tool_usage(
                "master_data_analyst", user_id, client_id,
                "cross_resource_synthesis", 
                {"synthesis_goal": synthesis_goal},
                error_msg, execution_time
            )
            
            return ToolResult(
                success=False,
                error=error_msg,
                execution_time_ms=execution_time
            )
    
    def _create_synthesis_plan(self, user_id: str, client_id: str,
                             resource_ids: List[str], synthesis_goal: str,
                             desired_fields: Optional[Dict[str, str]]) -> Dict[str, Any]:
        """Create a synthesis plan (simplified implementation)."""
        # Get resource information using Universal Data Handler
        resources = []
        for resource_id in resource_ids:
            resource_response = self.data_handler.get_resource_metadata(
                resource_id=resource_id,
                client_id=client_id,
                user_id=user_id
            )
            if resource_response.success:
                resource_data = resource_response.data
                if resource_data.get("user_id") == user_id and resource_data.get("client_id") == client_id:
                    resources.append({
                        "resource_id": resource_id,
                        "filename": resource_data.get("original_filename", "unknown"),
                        "resource_type": resource_data.get("resource_type", "unknown"),
                        "row_count": resource_data.get("row_count", 0),
                        "column_count": resource_data.get("column_count", 0)
                    })
        
        # Determine synthesis strategy
        if len(resources) == 2 and "join" in synthesis_goal.lower():
            strategy = "join_based"
            execution_plan = [
                "1. Analyze schemas for join compatibility",
                "2. Identify optimal join keys",
                "3. Execute inner join operation",
                "4. Generate unified view"
            ]
        elif "combine" in synthesis_goal.lower() or "merge" in synthesis_goal.lower():
            strategy = "union_based"
            execution_plan = [
                "1. Align schemas across resources",
                "2. Resolve field name conflicts",
                "3. Stack data vertically",
                "4. Generate unified view"
            ]
        else:
            strategy = "transformation_based"
            execution_plan = [
                "1. Analyze data relationships",
                "2. Design transformation pipeline",
                "3. Apply data transformations",
                "4. Generate unified view"
            ]
        
        return {
            "synthesis_id": str(uuid.uuid4()),
            "synthesis_strategy": strategy,
            "resources_analyzed": len(resources),
            "resource_details": resources,
            "execution_plan": execution_plan,
            "estimated_complexity": "medium" if len(resources) <= 3 else "high",
            "recommendations": [
                f"Synthesis strategy: {strategy}",
                f"Resources to combine: {len(resources)}",
                "Review execution plan before proceeding"
            ],
            "warnings": [
                "Ensure data quality before synthesis",
                "Large datasets may impact performance"
            ] if sum(r.get("row_count", 0) for r in resources) > 10000 else []
        }


class VisualizationTool:
    """
    Tool for generating visualization suggestions and specifications.
    
    Analyzes data and suggests appropriate visualizations.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize visualization tool."""
        self.config = config or get_config()
    
    def generate_visualizations(self, user_id: str, client_id: str,
                               data: List[Dict[str, Any]],
                               data_context: Optional[Dict[str, Any]] = None) -> ToolResult:
        """
        Generate visualization suggestions for data.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            data: Data to visualize
            data_context: Optional context about the data
            
        Returns:
            ToolResult with visualization suggestions
        """
        start_time = time.time()
        
        try:
            # Log tool usage
            activity_logger.log_tool_usage(
                "master_data_analyst", user_id, client_id,
                "visualization_generation", 
                {"data_rows": len(data), "has_context": data_context is not None},
                None, 0.0
            )
            
            if not data:
                return ToolResult(
                    success=False,
                    error="No data provided for visualization",
                    execution_time_ms=(time.time() - start_time) * 1000
                )
            
            # Analyze data structure
            columns = list(data[0].keys()) if data else []
            numeric_columns = self._identify_numeric_columns(data, columns)
            categorical_columns = self._identify_categorical_columns(data, columns)
            date_columns = self._identify_date_columns(data, columns)
            
            # Generate visualization suggestions
            suggestions = []
            
            # Summary statistics visualization
            if numeric_columns:
                suggestions.append({
                    "type": "summary_table",
                    "title": "Summary Statistics",
                    "description": "Table showing key statistics for numeric columns",
                    "columns": numeric_columns,
                    "priority": "high"
                })
            
            # Bar chart for categorical data
            if categorical_columns and len(data) > 1:
                suggestions.append({
                    "type": "bar_chart",
                    "title": "Category Distribution",
                    "description": f"Bar chart showing distribution of {categorical_columns[0]}",
                    "x_axis": categorical_columns[0],
                    "y_axis": "count",
                    "priority": "medium"
                })
            
            # Time series for date data
            if date_columns and numeric_columns:
                suggestions.append({
                    "type": "line_chart",
                    "title": "Trend Over Time",
                    "description": f"Line chart showing {numeric_columns[0]} over {date_columns[0]}",
                    "x_axis": date_columns[0],
                    "y_axis": numeric_columns[0],
                    "priority": "high"
                })
            
            # Scatter plot for numeric correlations
            if len(numeric_columns) >= 2:
                suggestions.append({
                    "type": "scatter_plot",
                    "title": "Correlation Analysis",
                    "description": f"Scatter plot showing relationship between {numeric_columns[0]} and {numeric_columns[1]}",
                    "x_axis": numeric_columns[0],
                    "y_axis": numeric_columns[1],
                    "priority": "medium"
                })
            
            # Data table as fallback
            suggestions.append({
                "type": "data_table",
                "title": "Data Table",
                "description": "Interactive table showing all data",
                "columns": columns,
                "priority": "low"
            })
            
            execution_time = (time.time() - start_time) * 1000
            
            # Update tool usage log
            activity_logger.log_tool_usage(
                "master_data_analyst", user_id, client_id,
                "visualization_generation", 
                {"data_rows": len(data)},
                f"Generated {len(suggestions)} visualization suggestions", execution_time
            )
            
            return ToolResult(
                success=True,
                data={
                    "suggestions": suggestions,
                    "data_analysis": {
                        "total_rows": len(data),
                        "total_columns": len(columns),
                        "numeric_columns": numeric_columns,
                        "categorical_columns": categorical_columns,
                        "date_columns": date_columns
                    }
                },
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Visualization generation failed: {str(e)}"
            logger.error(error_msg)
            
            activity_logger.log_tool_usage(
                "master_data_analyst", user_id, client_id,
                "visualization_generation", 
                {"data_rows": len(data) if data else 0},
                error_msg, execution_time
            )
            
            return ToolResult(
                success=False,
                error=error_msg,
                execution_time_ms=execution_time
            )
    
    def _identify_numeric_columns(self, data: List[Dict[str, Any]], columns: List[str]) -> List[str]:
        """Identify numeric columns in the data."""
        numeric_columns = []
        
        for col in columns:
            if col in ['client_id', 'user_id']:  # Skip system columns
                continue
                
            # Check first few non-null values
            sample_values = [row.get(col) for row in data[:10] if row.get(col) is not None]
            
            if sample_values:
                numeric_count = sum(1 for val in sample_values 
                                  if isinstance(val, (int, float)) or 
                                  (isinstance(val, str) and val.replace('.', '').replace('-', '').isdigit()))
                
                if numeric_count / len(sample_values) > 0.7:  # 70% numeric
                    numeric_columns.append(col)
        
        return numeric_columns
    
    def _identify_categorical_columns(self, data: List[Dict[str, Any]], columns: List[str]) -> List[str]:
        """Identify categorical columns in the data."""
        categorical_columns = []
        
        for col in columns:
            if col in ['client_id', 'user_id']:  # Skip system columns
                continue
                
            # Check unique values ratio
            values = [row.get(col) for row in data if row.get(col) is not None]
            if values:
                unique_ratio = len(set(values)) / len(values)
                
                # If less than 50% unique and not numeric, likely categorical
                if unique_ratio < 0.5 and col not in self._identify_numeric_columns(data, [col]):
                    categorical_columns.append(col)
        
        return categorical_columns
    
    def _identify_date_columns(self, data: List[Dict[str, Any]], columns: List[str]) -> List[str]:
        """Identify date/time columns in the data."""
        date_columns = []
        
        for col in columns:
            if any(keyword in col.lower() for keyword in ['date', 'time', 'created', 'updated']):
                date_columns.append(col)
        
        return date_columns
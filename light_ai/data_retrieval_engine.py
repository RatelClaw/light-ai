#!/usr/bin/env python3
"""
Comprehensive Data Retrieval Engine for Universal Data Handler

This module provides robust data retrieval from all storage layers:
- JSON files (structured by client_id/user_id/resource_id)
- DuckDB (structured data)
- ChromaDB (unstructured/vector data)
- Metadata Registry (resource information)
"""

import json
import sqlite3
import duckdb
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class ResourceInfo:
    """Information about a stored resource"""
    resource_id: str
    user_id: str
    client_id: str
    resource_type: str
    data_type: str
    original_filename: str
    storage_path: str
    created_at: str
    file_size_bytes: int
    row_count: Optional[int] = None
    column_count: Optional[int] = None

@dataclass
class RetrievalResult:
    """Result of data retrieval operation"""
    success: bool
    data: Any = None
    metadata: Dict[str, Any] = None
    error: Optional[str] = None
    source: str = "unknown"

class DataRetrievalEngine:
    """Comprehensive data retrieval engine for all storage layers"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.metadata_db_path = self.base_path / "metadata" / "registry.db"
        self.duckdb_path = self.base_path / "data" / "duckdb" / "main.db"
        self.json_data_path = self.base_path / "data" / "json"
        self.chroma_db_path = self.base_path / "data" / "unstructured" / "chroma_db"
        
        logger.info("Data Retrieval Engine initialized")
    
    def get_user_resources(self, client_id: str, user_id: str) -> List[ResourceInfo]:
        """Get all resources for a specific user"""
        try:
            with sqlite3.connect(self.metadata_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT resource_id, user_id, client_id, resource_type, data_type,
                           original_filename, storage_path, created_at, file_size_bytes,
                           row_count, column_count
                    FROM resource_metadata 
                    WHERE client_id = ? AND user_id = ? AND is_deleted = 0
                    ORDER BY created_at DESC
                """, (client_id, user_id))
                
                resources = []
                for row in cursor.fetchall():
                    resources.append(ResourceInfo(
                        resource_id=row[0],
                        user_id=row[1],
                        client_id=row[2],
                        resource_type=row[3],
                        data_type=row[4],
                        original_filename=row[5],
                        storage_path=row[6],
                        created_at=row[7],
                        file_size_bytes=row[8],
                        row_count=row[9],
                        column_count=row[10]
                    ))
                
                logger.info(f"Found {len(resources)} resources for user {user_id}")
                return resources
                
        except Exception as e:
            logger.error(f"Failed to get user resources: {e}")
            return []
    
    def get_json_data(self, resource_info: ResourceInfo) -> RetrievalResult:
        """Retrieve JSON data from file storage"""
        try:
            json_file_path = self.base_path / resource_info.storage_path
            
            if not json_file_path.exists():
                return RetrievalResult(
                    success=False,
                    error=f"JSON file not found: {json_file_path}",
                    source="json_file"
                )
            
            with open(json_file_path, 'r') as f:
                data = json.load(f)
            
            return RetrievalResult(
                success=True,
                data=data,
                metadata={
                    "resource_id": resource_info.resource_id,
                    "file_path": str(json_file_path),
                    "file_size": resource_info.file_size_bytes,
                    "original_filename": resource_info.original_filename
                },
                source="json_file"
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve JSON data: {e}")
            return RetrievalResult(
                success=False,
                error=str(e),
                source="json_file"
            )
    
    def get_duckdb_data(self, resource_info: ResourceInfo) -> RetrievalResult:
        """Retrieve data from DuckDB"""
        try:
            # Generate table name based on resource info
            table_name = f"json_data.json_{resource_info.resource_id.replace('-', '_')}"
            
            conn = duckdb.connect(str(self.duckdb_path))
            
            # Check if table exists
            tables_query = "SELECT table_name FROM information_schema.tables WHERE table_name = ?"
            table_exists = conn.execute(tables_query, [table_name.split('.')[-1]]).fetchone()
            
            if not table_exists:
                conn.close()
                return RetrievalResult(
                    success=False,
                    error=f"Table not found in DuckDB: {table_name}",
                    source="duckdb"
                )
            
            # Retrieve data
            query = f"SELECT * FROM {table_name}"
            result = conn.execute(query).fetchdf()
            conn.close()
            
            return RetrievalResult(
                success=True,
                data=result.to_dict('records'),
                metadata={
                    "resource_id": resource_info.resource_id,
                    "table_name": table_name,
                    "row_count": len(result),
                    "columns": list(result.columns)
                },
                source="duckdb"
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve DuckDB data: {e}")
            return RetrievalResult(
                success=False,
                error=str(e),
                source="duckdb"
            )
    
    def get_all_user_data(self, client_id: str, user_id: str) -> Dict[str, Any]:
        """Get all data for a user from all sources"""
        result = {
            "client_id": client_id,
            "user_id": user_id,
            "resources": [],
            "total_resources": 0,
            "data_by_source": {
                "json_files": [],
                "duckdb_tables": [],
                "errors": []
            }
        }
        
        # Get all resources for the user
        resources = self.get_user_resources(client_id, user_id)
        result["total_resources"] = len(resources)
        
        for resource in resources:
            resource_data = {
                "resource_info": {
                    "resource_id": resource.resource_id,
                    "resource_type": resource.resource_type,
                    "data_type": resource.data_type,
                    "original_filename": resource.original_filename,
                    "created_at": resource.created_at,
                    "file_size_bytes": resource.file_size_bytes
                },
                "json_data": None,
                "duckdb_data": None
            }
            
            # Try to get JSON data
            if resource.data_type == "json":
                json_result = self.get_json_data(resource)
                if json_result.success:
                    resource_data["json_data"] = json_result.data
                    result["data_by_source"]["json_files"].append({
                        "resource_id": resource.resource_id,
                        "data": json_result.data,
                        "metadata": json_result.metadata
                    })
                else:
                    result["data_by_source"]["errors"].append({
                        "resource_id": resource.resource_id,
                        "source": "json",
                        "error": json_result.error
                    })
            
            # Try to get DuckDB data
            duckdb_result = self.get_duckdb_data(resource)
            if duckdb_result.success:
                resource_data["duckdb_data"] = duckdb_result.data
                result["data_by_source"]["duckdb_tables"].append({
                    "resource_id": resource.resource_id,
                    "data": duckdb_result.data,
                    "metadata": duckdb_result.metadata
                })
            else:
                result["data_by_source"]["errors"].append({
                    "resource_id": resource.resource_id,
                    "source": "duckdb",
                    "error": duckdb_result.error
                })
            
            result["resources"].append(resource_data)
        
        return result
    
    def search_user_data(self, client_id: str, user_id: str, query: str) -> Dict[str, Any]:
        """Search through all user data for relevant information"""
        all_data = self.get_all_user_data(client_id, user_id)
        
        search_results = {
            "query": query,
            "matches": [],
            "summary": "",
            "total_resources_searched": all_data["total_resources"]
        }
        
        query_lower = query.lower()
        
        # Search through JSON data
        for json_item in all_data["data_by_source"]["json_files"]:
            resource_id = json_item["resource_id"]
            data = json_item["data"]
            
            # Convert data to searchable text
            data_text = json.dumps(data, indent=2).lower()
            
            # Simple keyword matching
            matches = []
            for word in query_lower.split():
                if word in data_text:
                    matches.append(word)
            
            if matches:
                search_results["matches"].append({
                    "resource_id": resource_id,
                    "source": "json",
                    "data": data,
                    "matched_keywords": matches,
                    "relevance_score": len(matches) / len(query_lower.split())
                })
        
        # Generate summary
        if search_results["matches"]:
            search_results["summary"] = f"Found {len(search_results['matches'])} resources matching your query."
        else:
            search_results["summary"] = "No matching resources found."
        
        return search_results
    
    def get_resource_by_id(self, resource_id: str) -> RetrievalResult:
        """Get a specific resource by ID"""
        try:
            with sqlite3.connect(self.metadata_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT resource_id, user_id, client_id, resource_type, data_type,
                           original_filename, storage_path, created_at, file_size_bytes,
                           row_count, column_count
                    FROM resource_metadata 
                    WHERE resource_id = ? AND is_deleted = 0
                """, (resource_id,))
                
                row = cursor.fetchone()
                if not row:
                    return RetrievalResult(
                        success=False,
                        error=f"Resource not found: {resource_id}",
                        source="metadata"
                    )
                
                resource_info = ResourceInfo(
                    resource_id=row[0],
                    user_id=row[1],
                    client_id=row[2],
                    resource_type=row[3],
                    data_type=row[4],
                    original_filename=row[5],
                    storage_path=row[6],
                    created_at=row[7],
                    file_size_bytes=row[8],
                    row_count=row[9],
                    column_count=row[10]
                )
                
                # Get the actual data
                if resource_info.data_type == "json":
                    return self.get_json_data(resource_info)
                else:
                    return self.get_duckdb_data(resource_info)
                    
        except Exception as e:
            logger.error(f"Failed to get resource by ID: {e}")
            return RetrievalResult(
                success=False,
                error=str(e),
                source="metadata"
            )


# Global instance
_retrieval_engine: Optional[DataRetrievalEngine] = None

def get_retrieval_engine() -> DataRetrievalEngine:
    """Get the global retrieval engine instance"""
    global _retrieval_engine
    if _retrieval_engine is None:
        _retrieval_engine = DataRetrievalEngine()
    return _retrieval_engine
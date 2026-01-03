"""
Storage routing and database operations for Universal Data Handler.

Provides unified interface for routing data to appropriate storage systems
(DuckDB for structured/JSON, ChromaDB for unstructured, SQLite for metadata)
with automatic indexing and cross-database operations.
"""

import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from ..core.models import (
    DataHierarchy, ResourceMetadata, SchemaInfo, ResourceType, DataType
)
from .database_managers import DatabaseManagers
from .metadata_registry import MetadataRegistry
from .storage_utils import StoragePathUtils, FileManager
from .version_manager import VersionManager, OperationType
from ..config import Config, get_config
from ..logger import get_logger

logger = get_logger(__name__)


class StorageRouter:
    """
    Unified storage router that coordinates data storage across multiple databases.
    
    Routes data to appropriate storage systems based on type:
    - Structured data (CSV, Excel, Parquet) → DuckDB virtual tables
    - JSON data → DuckDB JSONB storage with indexing
    - Unstructured data (PDF, TXT, etc.) → ChromaDB embeddings
    - Metadata → SQLite registry
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize storage router.
        
        Args:
            config: Optional configuration instance
        """
        self.config = config or get_config()
        self.db_managers = DatabaseManagers(config)
        self.metadata_registry = MetadataRegistry(config)
        self.path_utils = StoragePathUtils(config)
        self.file_manager = FileManager(config)
        self.version_manager = VersionManager(config)
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize all storage systems."""
        if not self._initialized:
            logger.info("Initializing storage router...")
            self.db_managers.initialize_all()
            self.metadata_registry.initialize()
            self._initialized = True
            logger.info("Storage router initialized successfully")
    
    def store_structured_data(self, file_path: Union[str, Path], 
                            hierarchy: DataHierarchy, metadata: ResourceMetadata,
                            schema_info: Optional[SchemaInfo] = None) -> str:
        """
        Store structured data (CSV, Excel, Parquet) using DuckDB virtual tables.
        
        Args:
            file_path: Path to the structured data file
            hierarchy: Data hierarchy for the resource
            metadata: Resource metadata
            schema_info: Optional schema information
            
        Returns:
            str: Table name created in DuckDB
            
        Raises:
            ValueError: If file type is not supported for structured data
            RuntimeError: If storage operation fails
        """
        self.initialize()
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Validate file type for structured data
        supported_extensions = {'.csv', '.xlsx', '.xls', '.parquet', '.tsv'}
        if file_path.suffix.lower() not in supported_extensions:
            raise ValueError(f"Unsupported structured data file type: {file_path.suffix}")
        
        try:
            # Set processing status to completed before version creation
            metadata.processing_status = "completed"
            
            # Use version manager to create new version
            new_version = self.version_manager.create_version(
                metadata, file_path, hierarchy.user_id, OperationType.UPLOAD,
                f"Uploaded structured data file: {metadata.original_filename}"
            )
            
            # Generate table name based on resource_id
            table_name = f"resource_{hierarchy.resource_id.replace('-', '_')}"
            
            # Create virtual table in DuckDB using the stored file
            stored_path = metadata.storage_path
            self.db_managers.duckdb.create_virtual_table(
                table_name, stored_path, "structured_data",
                hierarchy.client_id, hierarchy.user_id, hierarchy.resource_id
            )
            
            # Create indexes for fast filtering
            self._create_structured_data_indexes(table_name, hierarchy)
            
            # Store schema information if provided
            if schema_info:
                self.metadata_registry.create_schema_info(schema_info)
            
            logger.info(f"Stored structured data: {table_name}")
            return table_name
            
        except Exception as e:
            logger.error(f"Failed to store structured data: {e}")
            raise RuntimeError(f"Failed to store structured data: {e}")
    
    def store_json_data(self, json_data: Union[Dict[str, Any], List[Dict[str, Any]]], 
                       hierarchy: DataHierarchy, metadata: ResourceMetadata) -> str:
        """
        Store JSON data using DuckDB JSONB storage with indexing.
        
        Args:
            json_data: JSON data to store (dict or list of dicts)
            hierarchy: Data hierarchy for the resource
            metadata: Resource metadata
            
        Returns:
            str: Table name created in DuckDB
            
        Raises:
            RuntimeError: If storage operation fails
        """
        self.initialize()
        
        try:
            # Set processing status to completed before version creation
            metadata.processing_status = "completed"
            
            # Use version manager to create new version
            new_version = self.version_manager.create_version(
                metadata, None, hierarchy.user_id, OperationType.UPLOAD,
                f"Uploaded JSON data"
            )
            
            # Generate table name based on resource_id
            table_name = f"json_{hierarchy.resource_id.replace('-', '_')}"
            
            # Store JSON data in DuckDB
            self.db_managers.duckdb.store_json_data(
                table_name, json_data, hierarchy.resource_id, metadata.version
            )
            
            # Create indexes for fast filtering on metadata
            self._create_json_data_indexes(table_name, hierarchy)
            
            logger.info(f"Stored JSON data: {table_name}")
            return table_name
            
        except Exception as e:
            logger.error(f"Failed to store JSON data: {e}")
            raise RuntimeError(f"Failed to store JSON data: {e}")
    
    def store_unstructured_data(self, embeddings: List[List[float]], 
                              documents: List[str], metadatas: List[Dict[str, Any]],
                              hierarchy: DataHierarchy, metadata: ResourceMetadata) -> str:
        """
        Store unstructured data using ChromaDB embeddings.
        
        Args:
            embeddings: List of embedding vectors
            documents: List of document text chunks
            metadatas: List of metadata for each chunk
            hierarchy: Data hierarchy for the resource
            metadata: Resource metadata
            
        Returns:
            str: Collection name created in ChromaDB
            
        Raises:
            RuntimeError: If storage operation fails
        """
        self.initialize()
        
        try:
            # Set processing status to completed before version creation
            metadata.processing_status = "completed"
            
            # Use version manager to create new version
            new_version = self.version_manager.create_version(
                metadata, None, hierarchy.user_id, OperationType.UPLOAD,
                f"Uploaded unstructured data with {len(documents)} chunks"
            )
            
            # Generate collection name based on resource_id
            collection_name = f"unstructured_{hierarchy.resource_id.replace('-', '_')}"
            
            # Create collection with metadata
            collection_metadata = {
                "client_id": hierarchy.client_id,
                "user_id": hierarchy.user_id,
                "resource_id": hierarchy.resource_id,
                "resource_type": "unstructured",
                "created_at": datetime.utcnow().isoformat()
            }
            
            self.db_managers.chromadb.create_collection(
                collection_name, collection_metadata
            )
            
            # Generate unique IDs for each chunk
            chunk_ids = [
                f"{hierarchy.resource_id}_chunk_{i}" 
                for i in range(len(documents))
            ]
            
            # Add embeddings to collection
            self.db_managers.chromadb.add_embeddings(
                collection_name, embeddings, documents, metadatas, chunk_ids
            )
            
            logger.info(f"Stored unstructured data: {collection_name}")
            return collection_name
            
        except Exception as e:
            logger.error(f"Failed to store unstructured data: {e}")
            # Update metadata with error status
            metadata.processing_status = "failed"
            metadata.error_message = str(e)
            try:
                self.metadata_registry.create_resource_metadata(metadata)
            except:
                pass
            raise RuntimeError(f"Failed to store unstructured data: {e}")
    
    def _create_structured_data_indexes(self, table_name: str, hierarchy: DataHierarchy) -> None:
        """Create indexes on structured data for fast filtering."""
        # Enhanced view is now created in DuckDB manager
        logger.debug(f"Enhanced view created for structured data: {table_name}_enhanced")
    
    def _create_json_data_indexes(self, table_name: str, hierarchy: DataHierarchy) -> None:
        """Create indexes on JSON data for fast filtering."""
        try:
            with self.db_managers.duckdb.get_connection() as conn:
                # Create indexes on resource_id for fast lookups
                index_sql = f"""
                CREATE INDEX IF NOT EXISTS idx_{table_name}_resource_id 
                ON json_data.{table_name} (resource_id)
                """
                conn.execute(index_sql)
                logger.debug(f"Created index on JSON table: {table_name}")
        except Exception as e:
            logger.warning(f"Failed to create JSON data indexes: {e}")
    
    def query_structured_data(self, sql: str, client_id: str, user_id: str,
                            parameters: Optional[List] = None) -> List[Dict[str, Any]]:
        """
        Query structured data with automatic access control filtering.
        
        Args:
            sql: SQL query string
            client_id: Client ID for access control
            user_id: User ID for access control
            parameters: Optional query parameters
            
        Returns:
            List[Dict[str, Any]]: Query results
            
        Raises:
            ValueError: If access control validation fails
            RuntimeError: If query execution fails
        """
        self.initialize()
        
        try:
            # Add access control filtering to the query
            filtered_sql = self._add_access_control_filter(sql, client_id, user_id)
            
            # Execute query
            results = self.db_managers.duckdb.execute_query(filtered_sql, parameters)
            
            logger.debug(f"Executed structured data query for user {user_id}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to query structured data: {e}")
            raise RuntimeError(f"Query execution failed: {e}")
    
    def query_json_data(self, table_name: str, client_id: str, user_id: str,
                       where_clause: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Query JSON data with access control filtering.
        
        Args:
            table_name: JSON table name
            client_id: Client ID for access control
            user_id: User ID for access control
            where_clause: Optional WHERE clause for filtering
            
        Returns:
            List[Dict[str, Any]]: Query results
        """
        self.initialize()
        
        try:
            # Build query with access control
            sql = f"""
            SELECT * FROM json_data.{table_name} 
            WHERE resource_id IN (
                SELECT resource_id FROM resource_metadata 
                WHERE client_id = ? AND user_id = ? AND is_deleted = 0
            )
            """
            
            parameters = [client_id, user_id]
            
            if where_clause:
                sql += f" AND ({where_clause})"
            
            # Execute through DuckDB
            results = self.db_managers.duckdb.execute_query(sql, parameters)
            
            logger.debug(f"Executed JSON data query for user {user_id}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to query JSON data: {e}")
            raise RuntimeError(f"JSON query execution failed: {e}")
    
    def search_unstructured_data(self, query_embeddings: List[List[float]], 
                               client_id: str, user_id: str, n_results: int = 5) -> Dict[str, Any]:
        """
        Search unstructured data with access control filtering.
        
        Args:
            query_embeddings: Query embedding vectors
            client_id: Client ID for access control
            user_id: User ID for access control
            n_results: Number of results to return
            
        Returns:
            Dict[str, Any]: Search results
        """
        self.initialize()
        
        try:
            # Get accessible resources for the user
            accessible_resources = self.metadata_registry.list_resources(
                client_id, user_id, include_deleted=False
            )
            
            # Filter to unstructured resources only
            unstructured_resources = [
                r for r in accessible_resources 
                if r.resource_type == ResourceType.UNSTRUCTURED
            ]
            
            if not unstructured_resources:
                return {"ids": [], "documents": [], "metadatas": [], "distances": []}
            
            # Build metadata filter for ChromaDB
            resource_ids = [r.resource_id for r in unstructured_resources]
            
            # Search across all accessible collections
            all_results = {"ids": [], "documents": [], "metadatas": [], "distances": []}
            
            for resource in unstructured_resources:
                collection_name = f"unstructured_{resource.resource_id.replace('-', '_')}"
                
                try:
                    # Query the specific collection
                    results = self.db_managers.chromadb.query_collection(
                        collection_name, query_embeddings, n_results
                    )
                    
                    # Merge results
                    if results.get("ids"):
                        for i, ids_list in enumerate(results["ids"]):
                            if i < len(all_results.get("ids", [])):
                                all_results["ids"][i].extend(ids_list)
                            else:
                                all_results["ids"].append(ids_list)
                        
                        for key in ["documents", "metadatas", "distances"]:
                            if key in results:
                                for i, values_list in enumerate(results[key]):
                                    if i < len(all_results.get(key, [])):
                                        all_results[key][i].extend(values_list)
                                    else:
                                        all_results[key].append(values_list)
                
                except Exception as e:
                    logger.warning(f"Failed to search collection {collection_name}: {e}")
                    continue
            
            # Sort by distance and limit results
            if all_results["ids"]:
                # Flatten and sort by distance
                flattened_results = []
                for i in range(len(all_results["ids"])):
                    for j in range(len(all_results["ids"][i])):
                        flattened_results.append({
                            "id": all_results["ids"][i][j],
                            "document": all_results["documents"][i][j] if "documents" in all_results else "",
                            "metadata": all_results["metadatas"][i][j] if "metadatas" in all_results else {},
                            "distance": all_results["distances"][i][j] if "distances" in all_results else 0.0
                        })
                
                # Sort by distance and limit
                flattened_results.sort(key=lambda x: x["distance"])
                flattened_results = flattened_results[:n_results]
                
                # Reconstruct result format
                all_results = {
                    "ids": [[r["id"] for r in flattened_results]],
                    "documents": [[r["document"] for r in flattened_results]],
                    "metadatas": [[r["metadata"] for r in flattened_results]],
                    "distances": [[r["distance"] for r in flattened_results]]
                }
            
            logger.debug(f"Executed unstructured data search for user {user_id}")
            return all_results
            
        except Exception as e:
            logger.error(f"Failed to search unstructured data: {e}")
            raise RuntimeError(f"Unstructured search failed: {e}")
    
    def _add_access_control_filter(self, sql: str, client_id: str, user_id: str) -> str:
        """Add access control filtering to SQL queries."""
        # Replace table references with enhanced views that have access control columns
        # This is a simplified implementation - in production, you'd want more sophisticated SQL parsing
        
        # Replace structured_data.table_name with structured_data.table_name_enhanced
        import re
        pattern = r'structured_data\.(\w+)(?!_enhanced)'
        sql = re.sub(pattern, r'structured_data.\1_enhanced', sql)
        
        if "WHERE" in sql.upper():
            # Add to existing WHERE clause
            sql = sql.replace(" WHERE ", f" WHERE client_id = '{client_id}' AND user_id = '{user_id}' AND (") + ")"
        else:
            # Add new WHERE clause
            sql += f" WHERE client_id = '{client_id}' AND user_id = '{user_id}'"
        
        return sql
    
    def get_resource_info(self, resource_id: str) -> Optional[ResourceMetadata]:
        """
        Get resource information from metadata registry.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            Optional[ResourceMetadata]: Resource metadata or None if not found
        """
        self.initialize()
        return self.metadata_registry.get_resource_metadata(resource_id)
    
    def list_user_resources(self, client_id: str, user_id: str, 
                          resource_type: Optional[ResourceType] = None) -> List[ResourceMetadata]:
        """
        List resources for a user, optionally filtered by type.
        
        Args:
            client_id: Client identifier
            user_id: User identifier
            resource_type: Optional resource type filter
            
        Returns:
            List[ResourceMetadata]: List of accessible resources
        """
        self.initialize()
        
        resources = self.metadata_registry.list_resources(client_id, user_id)
        
        if resource_type:
            resources = [r for r in resources if r.resource_type == resource_type]
        
        return resources
    
    def delete_resource(self, resource_id: str, user_id: str, hard_delete: bool = False) -> bool:
        """
        Delete a resource from all storage systems using version manager.
        
        Args:
            resource_id: Resource identifier
            user_id: User performing the deletion
            hard_delete: If True, permanently delete; if False, soft delete
            
        Returns:
            bool: True if deletion was successful
        """
        self.initialize()
        
        try:
            if hard_delete:
                return self.version_manager.hard_delete_resource(resource_id, user_id)
            else:
                return self.version_manager.soft_delete_resource(resource_id, user_id)
            
        except Exception as e:
            logger.error(f"Failed to delete resource {resource_id}: {e}")
            return False
    
    def get_storage_statistics(self, client_id: str) -> Dict[str, Any]:
        """
        Get comprehensive storage statistics for a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Dict[str, Any]: Storage statistics
        """
        self.initialize()
        
        try:
            # Get basic statistics from metadata registry
            stats = self.metadata_registry.get_storage_statistics(client_id)
            
            # Add database health information
            health = self.db_managers.health_check()
            stats["database_health"] = health
            
            # Add storage system specific stats
            stats["storage_systems"] = {
                "duckdb_initialized": health.get("duckdb", False),
                "chromadb_initialized": health.get("chromadb", False),
                "sqlite_initialized": health.get("sqlite", False)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get storage statistics: {e}")
            return {"error": str(e)}
    
    def optimize_storage(self) -> Dict[str, Any]:
        """
        Optimize storage systems (vacuum, rebuild indexes, etc.).
        
        Returns:
            Dict[str, Any]: Optimization results
        """
        self.initialize()
        
        results = {}
        
        try:
            # Optimize SQLite
            with self.db_managers.sqlite.get_connection() as conn:
                conn.execute("VACUUM")
                conn.execute("ANALYZE")
            results["sqlite"] = "optimized"
        except Exception as e:
            results["sqlite"] = f"failed: {e}"
        
        try:
            # Optimize DuckDB
            with self.db_managers.duckdb.get_connection() as conn:
                conn.execute("CHECKPOINT")
            results["duckdb"] = "optimized"
        except Exception as e:
            results["duckdb"] = f"failed: {e}"
        
        # ChromaDB doesn't need explicit optimization
        results["chromadb"] = "no optimization needed"
        
        logger.info("Storage optimization completed")
        return results
    
    def close(self) -> None:
        """Close all database connections."""
        self.db_managers.close_all()
        logger.info("Storage router closed")
    
    # Version Management Methods
    
    def update_resource(self, resource_id: str, source_file_path: Optional[Union[str, Path]] = None,
                       user_id: Optional[str] = None, operation_details: Optional[str] = None) -> int:
        """
        Update a resource to a new version.
        
        Args:
            resource_id: Resource identifier
            source_file_path: Optional path to new file version
            user_id: User performing the update
            operation_details: Optional details about the update
            
        Returns:
            int: New version number
        """
        self.initialize()
        
        # Get current metadata
        current_metadata = self.metadata_registry.get_resource_metadata(resource_id)
        if not current_metadata:
            raise ValueError(f"Resource not found: {resource_id}")
        
        # Create new metadata for the version
        new_metadata = ResourceMetadata(
            resource_id=current_metadata.resource_id,
            user_id=current_metadata.user_id,
            client_id=current_metadata.client_id,
            resource_type=current_metadata.resource_type,
            data_type=current_metadata.data_type,
            original_filename=current_metadata.original_filename,
            file_size_bytes=current_metadata.file_size_bytes,
            storage_path=current_metadata.storage_path,
            version=current_metadata.version + 1,
            row_count=current_metadata.row_count,
            column_count=current_metadata.column_count,
            chunk_count=current_metadata.chunk_count,
            file_hash=current_metadata.file_hash,
            content_preview=current_metadata.content_preview,
            processing_status="completed"
        )
        
        # Use version manager to create new version
        return self.version_manager.create_version(
            new_metadata, source_file_path, user_id or current_metadata.user_id,
            OperationType.UPDATE, operation_details or "Resource updated"
        )
    
    def rollback_resource(self, resource_id: str, target_version: int, user_id: str,
                         operation_details: Optional[str] = None) -> int:
        """
        Rollback a resource to a specific version.
        
        Args:
            resource_id: Resource identifier
            target_version: Version to rollback to
            user_id: User performing the rollback
            operation_details: Optional details about the rollback
            
        Returns:
            int: New version number after rollback
        """
        self.initialize()
        return self.version_manager.rollback_to_version(resource_id, target_version, user_id, operation_details)
    
    def get_version_history(self, resource_id: str) -> List[Dict[str, Any]]:
        """
        Get version history for a resource.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            List[Dict[str, Any]]: Version history
        """
        self.initialize()
        versions = self.version_manager.list_versions(resource_id)
        return [
            {
                "version": v.version,
                "created_at": v.created_at.isoformat(),
                "created_by": v.created_by,
                "operation": v.operation.value,
                "file_path": v.file_path,
                "file_size_bytes": v.file_size_bytes,
                "operation_details": v.operation_details
            }
            for v in versions
        ]
    
    def get_audit_trail(self, resource_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get audit trail for a resource.
        
        Args:
            resource_id: Resource identifier
            limit: Maximum number of records to return
            
        Returns:
            List[Dict[str, Any]]: Audit trail records
        """
        self.initialize()
        return self.version_manager.get_audit_trail(resource_id, limit)
    
    def restore_resource(self, resource_id: str, user_id: str, 
                        operation_details: Optional[str] = None) -> bool:
        """
        Restore a soft-deleted resource.
        
        Args:
            resource_id: Resource identifier
            user_id: User performing the restoration
            operation_details: Optional details about the restoration
            
        Returns:
            bool: True if resource was restored
        """
        self.initialize()
        return self.version_manager.restore_resource(resource_id, user_id, operation_details)
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> Dict[str, int]:
        """
        Clean up old soft-deleted resources and audit records.
        
        Args:
            days_to_keep: Number of days to keep soft-deleted resources
            
        Returns:
            Dict[str, int]: Cleanup statistics
        """
        self.initialize()
        
        resources_deleted = self.version_manager.cleanup_old_soft_deleted(days_to_keep)
        audit_records_deleted = self.version_manager.cleanup_old_audit_records()
        
        return {
            'soft_deleted_resources_cleaned': resources_deleted,
            'audit_records_cleaned': audit_records_deleted
        }
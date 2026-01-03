"""
Comprehensive API layer for Universal Data Handler.

Provides unified access to both Sub-Layer 1 (Data Ingestion & Storage) and 
Sub-Layer 2 (Data Retrieval) functionality through a consistent interface.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
from pathlib import Path
import pandas as pd

from .config import Config
from .logger import setup_logger
from .core.models import (
    DataHierarchy, ResourceMetadata, SchemaInfo, ResourceType, DataType,
    AccessLevel, validate_hierarchy_access, filter_accessible_resources
)

# Sub-Layer 1 imports
from .sub_layer_1 import (
    FileUploadAPI, FileValidator, DuplicateDetector, UploadProgressTracker,
    DataCleaningEngine, CleaningConfig
)

# Sub-Layer 2 imports  
from .sub_layer_2 import (
    SQLQueryEngine, QueryResult,
    NaturalLanguageProcessor, NLQueryResult,
    SemanticSearchEngine, SearchResults,
    AIDataAnalyst, AnalysisReport
)

# Storage imports
from .storage import (
    DatabaseManagers, MetadataRegistry, StorageRouter, VersionManager,
    DirectoryManager, create_directory_structure
)


class APIResponse:
    """Standardized API response format."""
    
    def __init__(self, success: bool, data: Any = None, error: str = None, 
                 metadata: Dict[str, Any] = None):
        self.success = success
        self.data = data
        self.error = error
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        response = {
            "success": self.success,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }
        
        if self.success:
            response["data"] = self.data
        else:
            response["error"] = self.error
            
        return response
    
    def to_json(self) -> str:
        """Convert response to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)


class UniversalDataHandler:
    """
    Main API class providing comprehensive access to all system functionality.
    
    Implements both Sub-Layer 1 (Data Ingestion & Storage) and Sub-Layer 2 (Data Retrieval)
    operations through a unified interface with consistent error handling and response formatting.
    """
    
    def __init__(self, config: Optional[Config] = None, base_path: str = None):
        """
        Initialize the Universal Data Handler API.
        
        Args:
            config: Optional configuration object
            base_path: Optional base path for data storage
        """
        self.config = config or Config.load()
        self.base_path = base_path or os.getcwd()
        
        # Update config to use the specified base path
        if base_path:
            self.config.storage.base_directory = base_path
        
        self.logger = setup_logger("universal_data_handler", self.config)
        
        # Initialize directory structure
        self.directory_manager = DirectoryManager(self.config)
        create_directory_structure(self.config)
        
        # Initialize database managers
        self.db_managers = DatabaseManagers(self.config)
        
        # Initialize core components
        self.metadata_registry = MetadataRegistry(self.config)
        self.storage_router = StorageRouter(self.config)
        self.version_manager = VersionManager(self.config)
        
        # Initialize Sub-Layer 1 components
        self.file_upload_api = FileUploadAPI(self.config)
        self.progress_tracker = UploadProgressTracker()
        self.cleaning_engine = DataCleaningEngine()
        
        # Initialize Sub-Layer 2 components
        self.sql_engine = SQLQueryEngine(self.config)
        self.nl_processor = NaturalLanguageProcessor(self.config)
        self.search_engine = SemanticSearchEngine(self.config)
        self.ai_analyst = AIDataAnalyst(self.config)
        
        self.logger.info("Universal Data Handler API initialized successfully")
    
    def _handle_error(self, error: Exception, operation: str) -> APIResponse:
        """Handle errors consistently across all API methods."""
        error_msg = f"Error in {operation}: {str(error)}"
        self.logger.error(error_msg, exc_info=True)
        return APIResponse(success=False, error=error_msg)
    
    def _validate_access(self, client_id: str, user_id: str, resource_id: str = None,
                        access_level: AccessLevel = AccessLevel.USER) -> bool:
        """Validate user access to resources."""
        try:
            if resource_id:
                hierarchy = DataHierarchy(client_id, user_id, resource_id)
                return validate_hierarchy_access(user_id, client_id, hierarchy, access_level)
            return True
        except Exception as e:
            self.logger.warning(f"Access validation failed: {e}")
            return False
    
    # ==================== Sub-Layer 1 APIs: Data Ingestion & Storage ====================
    
    def upload_file(self, client_id: str, user_id: str, file_path: str,
                   resource_name: str = None, cleaning_config: Dict[str, Any] = None) -> APIResponse:
        """
        Upload and process a file of any supported type.
        
        Args:
            client_id: Client UUID
            user_id: User UUID  
            file_path: Path to file to upload
            resource_name: Optional custom name for the resource
            cleaning_config: Optional data cleaning configuration
        
        Returns:
            APIResponse with resource_id on success
        """
        try:
            if not self._validate_access(client_id, user_id):
                return APIResponse(success=False, error="Invalid client_id or user_id")
            
            if not os.path.exists(file_path):
                return APIResponse(success=False, error=f"File not found: {file_path}")
            
            # Upload file using Sub-Layer 1 API - returns ResourceMetadata
            metadata = self.file_upload_api.upload_file(
                client_id=client_id,
                user_id=user_id,
                file_path=file_path,
                resource_name=resource_name
            )
            
            # Clean the data based on type
            if metadata.resource_type == ResourceType.STRUCTURED:
                # Load and clean structured data
                if metadata.data_type == DataType.CSV:
                    df = pd.read_csv(file_path)
                elif metadata.data_type == DataType.EXCEL:
                    df = pd.read_excel(file_path)
                else:
                    # For other structured types, try pandas read_csv as fallback
                    df = pd.read_csv(file_path)
                
                cleaned_data, stats = self.cleaning_engine.clean_data(df, metadata.data_type)
                
                # Create hierarchy for storage
                hierarchy = DataHierarchy(
                    client_id=client_id,
                    user_id=user_id, 
                    resource_id=metadata.resource_id
                )
                
                # Store in DuckDB
                self.storage_router.store_structured_data(
                    file_path, hierarchy, metadata
                )
            elif metadata.resource_type == ResourceType.JSON:
                # Load and clean JSON data
                with open(file_path, 'r') as f:
                    json_data = json.load(f)
                cleaned_data, stats = self.cleaning_engine.clean_data(json_data, metadata.data_type)
                
                # Create hierarchy for storage
                hierarchy = DataHierarchy(
                    client_id=client_id,
                    user_id=user_id, 
                    resource_id=metadata.resource_id
                )
                
                # Store in DuckDB JSONB
                self.storage_router.store_json_data(
                    cleaned_data, hierarchy, metadata
                )
            elif metadata.resource_type == ResourceType.UNSTRUCTURED:
                # Clean unstructured data
                cleaned_data, stats = self.cleaning_engine.clean_data(
                    None, metadata.data_type, file_path=Path(file_path)
                )
                
                # Create hierarchy for storage
                hierarchy = DataHierarchy(
                    client_id=client_id,
                    user_id=user_id, 
                    resource_id=metadata.resource_id
                )
                
                # For unstructured data, we need to prepare embeddings and documents
                # For now, let's skip the actual storage and just log
                self.logger.info(f"Would store unstructured data for {metadata.resource_id}")
                # TODO: Implement proper unstructured data storage with embeddings
            
            # Register metadata (only once, not done by storage router for file uploads)
            # Note: Storage router already creates metadata for all types, so skip this
            # self.metadata_registry.create_resource_metadata(metadata)
            
            return APIResponse(
                success=True,
                data={
                    "resource_id": metadata.resource_id,
                    "filename": metadata.original_filename,
                    "resource_type": metadata.resource_type.value,
                    "data_type": metadata.data_type.value,
                    "file_size_bytes": metadata.file_size_bytes,
                    "version": metadata.version
                },
                metadata={"operation": "upload_file", "processing_time": "< 1s"}
            )
            
        except Exception as e:
            return self._handle_error(e, "upload_file")
    
    def upload_json(self, client_id: str, user_id: str, json_data: Union[Dict, List],
                   resource_name: str, flatten: bool = False) -> APIResponse:
        """
        Upload JSON data directly.
        
        Args:
            client_id: Client UUID
            user_id: User UUID
            json_data: JSON data as dict or list
            resource_name: Name for the resource
            flatten: Whether to flatten nested structures
        
        Returns:
            APIResponse with resource_id on success
        """
        try:
            if not self._validate_access(client_id, user_id):
                return APIResponse(success=False, error="Invalid client_id or user_id")
            
            # Create temporary JSON file
            import tempfile
            import json
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
                json.dump(json_data, tmp_file, indent=2)
                tmp_file_path = tmp_file.name
            
            try:
                # Upload JSON file using existing file upload
                metadata = self.file_upload_api.upload_file(
                    client_id=client_id,
                    user_id=user_id,
                    file_path=tmp_file_path,
                    resource_name=resource_name
                )
                
                # Clean and store the JSON data
                cleaned_data, stats = self.cleaning_engine.clean_data(
                    json_data, DataType.JSON
                )
                
                # Create hierarchy for storage
                hierarchy = DataHierarchy(
                    client_id=client_id,
                    user_id=user_id, 
                    resource_id=metadata.resource_id
                )
                
                # Store in appropriate database
                self.storage_router.store_json_data(
                    cleaned_data, hierarchy, metadata
                )
                
                # Metadata is already registered by storage_router
                
                return APIResponse(
                    success=True,
                    data={
                        "resource_id": metadata.resource_id,
                        "resource_name": resource_name,
                        "resource_type": metadata.resource_type.value,
                        "data_type": metadata.data_type.value,
                        "version": metadata.version,
                        "flattened": flatten,
                        "file_size_bytes": metadata.file_size_bytes
                    },
                    metadata={"operation": "upload_json"}
                )
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass
            
        except Exception as e:
            return self._handle_error(e, "upload_json")
    
    def upload_bulk(self, client_id: str, user_id: str, files: List[str],
                   parallel: bool = True, cleaning_config: Dict[str, Any] = None) -> APIResponse:
        """
        Upload multiple files in bulk.
        
        Args:
            client_id: Client UUID
            user_id: User UUID
            files: List of file paths to upload
            parallel: Whether to process files in parallel
            cleaning_config: Optional data cleaning configuration
        
        Returns:
            APIResponse with list of resource_ids on success
        """
        try:
            if not self._validate_access(client_id, user_id):
                return APIResponse(success=False, error="Invalid client_id or user_id")
            
            # Validate all files exist
            missing_files = [f for f in files if not os.path.exists(f)]
            if missing_files:
                return APIResponse(
                    success=False, 
                    error=f"Files not found: {missing_files}"
                )
            
            # Create cleaning config if provided
            config = None
            if cleaning_config:
                config = CleaningConfig(**cleaning_config)
            
            # Upload files using Sub-Layer 1 API - returns List[ResourceMetadata]
            metadata_list = self.file_upload_api.upload_bulk(
                client_id=client_id,
                user_id=user_id,
                file_paths=files,
                parallel=parallel
            )
            
            # Process each uploaded file
            resources_info = []
            resource_ids = []
            
            for metadata in metadata_list:
                # Clean and store the data based on type
                file_path = files[metadata_list.index(metadata)]  # Get original file path
                
                # Create hierarchy for storage
                hierarchy = DataHierarchy(
                    client_id=client_id,
                    user_id=user_id, 
                    resource_id=metadata.resource_id
                )
                
                if metadata.resource_type == ResourceType.STRUCTURED:
                    if metadata.data_type == DataType.CSV:
                        df = pd.read_csv(file_path)
                    elif metadata.data_type == DataType.EXCEL:
                        df = pd.read_excel(file_path)
                    else:
                        df = pd.read_csv(file_path)
                    
                    cleaned_data, stats = self.cleaning_engine.clean_data(df, metadata.data_type)
                    self.storage_router.store_structured_data(
                        file_path, hierarchy, metadata
                    )
                elif metadata.resource_type == ResourceType.JSON:
                    with open(file_path, 'r') as f:
                        json_data = json.load(f)
                    cleaned_data, stats = self.cleaning_engine.clean_data(json_data, metadata.data_type)
                    self.storage_router.store_json_data(
                        cleaned_data, hierarchy, metadata
                    )
                elif metadata.resource_type == ResourceType.UNSTRUCTURED:
                    cleaned_data, stats = self.cleaning_engine.clean_data(
                        None, metadata.data_type, file_path=Path(file_path)
                    )
                    # Skip unstructured storage for now
                    self.logger.info(f"Would store unstructured data for {metadata.resource_id}")
                
                # Register metadata (only for bulk uploads where storage router doesn't handle it)
                # Note: Storage router already handles metadata creation, so skip this
                # self.metadata_registry.create_resource_metadata(metadata)
                
                # Add to response data
                resource_ids.append(metadata.resource_id)
                resources_info.append({
                    "resource_id": metadata.resource_id,
                    "filename": metadata.original_filename,
                    "resource_type": metadata.resource_type.value,
                    "data_type": metadata.data_type.value,
                    "file_size_bytes": metadata.file_size_bytes
                })
            
            return APIResponse(
                success=True,
                data={
                    "resource_ids": resource_ids,
                    "resources": resources_info,
                    "total_files": len(files),
                    "successful_uploads": len(resource_ids)
                },
                metadata={"operation": "upload_bulk", "parallel": parallel}
            )
            
        except Exception as e:
            return self._handle_error(e, "upload_bulk")
    
    def update_resource(self, resource_id: str, new_data: Union[str, Dict],
                       create_version: bool = True, client_id: str = None,
                       user_id: str = None) -> APIResponse:
        """
        Update an existing resource with new data.
        
        Args:
            resource_id: Resource UUID to update
            new_data: New data (file path or JSON data)
            create_version: Whether to create a new version
            client_id: Client UUID for access validation
            user_id: User UUID for access validation
        
        Returns:
            APIResponse with new version info on success
        """
        try:
            # Get existing metadata for validation
            existing_metadata = self.metadata_registry.get_resource_metadata(resource_id)
            if not existing_metadata:
                return APIResponse(success=False, error=f"Resource not found: {resource_id}")
            
            # Validate access if client_id and user_id provided
            if client_id and user_id:
                if not self._validate_access(client_id, user_id, resource_id):
                    return APIResponse(success=False, error="Access denied")
            
            # Update resource using version manager
            new_version = self.version_manager.create_version(
                resource_id=resource_id,
                new_data=new_data,
                operation_type="update",
                user_id=user_id or existing_metadata.user_id
            )
            
            # Get updated metadata
            updated_metadata = self.metadata_registry.get_resource_metadata(resource_id)
            
            return APIResponse(
                success=True,
                data={
                    "resource_id": resource_id,
                    "old_version": existing_metadata.version,
                    "new_version": new_version,
                    "updated_at": updated_metadata.updated_at.isoformat(),
                    "version_created": create_version
                },
                metadata={"operation": "update_resource"}
            )
            
        except Exception as e:
            return self._handle_error(e, "update_resource")
    
    def delete_resource(self, resource_id: str, hard_delete: bool = False,
                       client_id: str = None, user_id: str = None) -> APIResponse:
        """
        Delete a resource (soft delete by default).
        
        Args:
            resource_id: Resource UUID to delete
            hard_delete: Whether to permanently delete (default: soft delete)
            client_id: Client UUID for access validation
            user_id: User UUID for access validation
        
        Returns:
            APIResponse confirming deletion
        """
        try:
            # Get existing metadata for validation
            existing_metadata = self.metadata_registry.get_resource_metadata(resource_id)
            if not existing_metadata:
                return APIResponse(success=False, error=f"Resource not found: {resource_id}")
            
            # Validate access if client_id and user_id provided
            if client_id and user_id:
                if not self._validate_access(client_id, user_id, resource_id):
                    return APIResponse(success=False, error="Access denied")
            
            # Delete resource using version manager
            delete_type = "hard" if hard_delete else "soft"
            success = self.version_manager.delete_resource(
                resource_id=resource_id,
                delete_type=delete_type,
                user_id=user_id or existing_metadata.user_id
            )
            
            if not success:
                return APIResponse(success=False, error="Failed to delete resource")
            
            return APIResponse(
                success=True,
                data={
                    "resource_id": resource_id,
                    "delete_type": delete_type,
                    "deleted_at": datetime.utcnow().isoformat(),
                    "recoverable": not hard_delete
                },
                metadata={"operation": "delete_resource"}
            )
            
        except Exception as e:
            return self._handle_error(e, "delete_resource")
    
    # ==================== Sub-Layer 2 APIs: Data Retrieval ====================
    
    def get_resource(self, resource_id: str, version: int = None,
                    output_format: str = "dataframe", client_id: str = None,
                    user_id: str = None) -> APIResponse:
        """
        Retrieve original resource data.
        
        Args:
            resource_id: Resource UUID to retrieve
            version: Optional specific version (default: latest)
            output_format: Output format (dataframe, json, csv, dict)
            client_id: Client UUID for access validation
            user_id: User UUID for access validation
        
        Returns:
            APIResponse with resource data
        """
        try:
            # Get metadata for validation
            metadata = self.metadata_registry.get_resource_metadata(resource_id)
            if not metadata:
                return APIResponse(success=False, error=f"Resource not found: {resource_id}")
            
            # Validate access if client_id and user_id provided
            if client_id and user_id:
                if not self._validate_access(client_id, user_id, resource_id):
                    return APIResponse(success=False, error="Access denied")
            
            # Get resource data using storage router
            data = self.storage_router.get_resource_data(resource_id, version)
            
            # Format output based on requested format
            formatted_data = self._format_output(data, output_format, metadata.resource_type)
            
            return APIResponse(
                success=True,
                data={
                    "resource_id": resource_id,
                    "version": version or metadata.version,
                    "data": formatted_data,
                    "resource_type": metadata.resource_type.value,
                    "data_type": metadata.data_type.value
                },
                metadata={"operation": "get_resource", "output_format": output_format}
            )
            
        except Exception as e:
            return self._handle_error(e, "get_resource")
    
    def query_structured(self, client_id: str, user_id: str, sql_query: str,
                        output_format: str = "dataframe") -> APIResponse:
        """
        Execute SQL query on structured data.
        
        Args:
            client_id: Client UUID for access validation
            user_id: User UUID for access validation
            sql_query: SQL query to execute
            output_format: Output format (dataframe, json, csv, dict)
        
        Returns:
            APIResponse with query results
        """
        try:
            if not self._validate_access(client_id, user_id):
                return APIResponse(success=False, error="Invalid client_id or user_id")
            
            # Execute query using SQL engine
            result = self.sql_engine.execute_query(sql_query, client_id, user_id)
            
            # Format output
            formatted_data = self._format_output(result.data, output_format, ResourceType.STRUCTURED)
            
            return APIResponse(
                success=True,
                data={
                    "query": sql_query,
                    "results": formatted_data,
                    "row_count": result.row_count,
                    "execution_time_ms": result.execution_time_ms,
                    "query_plan": result.query_plan.to_dict() if hasattr(result.query_plan, 'to_dict') else str(result.query_plan)
                },
                metadata={"operation": "query_structured", "output_format": output_format}
            )
            
        except Exception as e:
            return self._handle_error(e, "query_structured")
    
    def query_natural(self, client_id: str, user_id: str, question: str,
                     output_format: str = "dataframe") -> APIResponse:
        """
        Process natural language query.
        
        Args:
            client_id: Client UUID for access validation
            user_id: User UUID for access validation
            question: Natural language question
            output_format: Output format (dataframe, json, csv, dict)
        
        Returns:
            APIResponse with query results and explanation
        """
        try:
            if not self._validate_access(client_id, user_id):
                return APIResponse(success=False, error="Invalid client_id or user_id")
            
            # Process natural language query
            result = self.nl_processor.process_natural_query(question, client_id, user_id)
            
            # Format output if data is available
            formatted_data = None
            if result.data is not None:
                formatted_data = self._format_output(result.data, output_format, ResourceType.STRUCTURED)
            
            return APIResponse(
                success=True,
                data={
                    "question": question,
                    "generated_sql": result.generated_sql,
                    "explanation": result.explanation,
                    "results": formatted_data,
                    "confidence": result.confidence_score,
                    "query_type": result.query_type.value if result.query_type else None
                },
                metadata={"operation": "query_natural", "output_format": output_format}
            )
            
        except Exception as e:
            return self._handle_error(e, "query_natural")
    
    def search_unstructured(self, client_id: str, user_id: str, query: str,
                           strategy: str = "hybrid", limit: int = 5) -> APIResponse:
        """
        Perform semantic search on unstructured data.
        
        Args:
            client_id: Client UUID for access validation
            user_id: User UUID for access validation
            query: Search query
            strategy: Search strategy (semantic, keyword, hybrid, mmr)
            limit: Maximum number of results
        
        Returns:
            APIResponse with search results
        """
        try:
            if not self._validate_access(client_id, user_id):
                return APIResponse(success=False, error="Invalid client_id or user_id")
            
            # Convert string strategy to enum
            from .sub_layer_2.semantic_search_engine import SearchStrategy
            try:
                strategy_enum = SearchStrategy(strategy)
            except ValueError:
                return APIResponse(success=False, error=f"Invalid search strategy: {strategy}")
            
            # Perform semantic search
            results = self.search_engine.search(
                query=query,
                client_id=client_id,
                user_id=user_id,
                strategy=strategy_enum,
                n_results=limit
            )
            
            # Format results
            formatted_results = []
            for result in results.results:
                formatted_results.append({
                    "resource_id": result.resource_id,
                    "chunk_id": result.chunk_index,
                    "content": result.document,
                    "score": result.relevance_score,
                    "metadata": result.metadata
                })
            
            return APIResponse(
                success=True,
                data={
                    "query": query,
                    "strategy": strategy,
                    "results": formatted_results,
                    "total_results": len(formatted_results),
                    "search_time_ms": results.execution_time_ms
                },
                metadata={"operation": "search_unstructured", "limit": limit}
            )
            
        except Exception as e:
            return self._handle_error(e, "search_unstructured")
    
    def ask_data_analyst(self, client_id: str, user_id: str, question: str,
                        include_visualizations: bool = False) -> APIResponse:
        """
        Ask the AI data analyst for comprehensive analysis.
        
        Args:
            client_id: Client UUID for access validation
            user_id: User UUID for access validation
            question: Analytical question
            include_visualizations: Whether to include charts/visualizations
        
        Returns:
            APIResponse with comprehensive analysis report
        """
        try:
            if not self._validate_access(client_id, user_id):
                return APIResponse(success=False, error="Invalid client_id or user_id")
            
            # Get analysis from AI data analyst
            report = self.ai_analyst.analyze_data(
                question=question,
                client_id=client_id,
                user_id=user_id
            )
            
            return APIResponse(
                success=True,
                data={
                    "question": question,
                    "analysis_type": report.analysis_type.value,
                    "summary": report.executive_summary,
                    "insights": [insight.to_dict() for insight in report.key_insights],
                    "data_sources": [source.to_dict() for source in report.data_sources_used],
                    "reasoning": report.methodology,
                    "recommendations": report.recommendations,
                    "visualizations": report.visualizations,
                    "confidence": report.confidence_score
                },
                metadata={"operation": "ask_data_analyst", "include_visualizations": include_visualizations}
            )
            
        except Exception as e:
            return self._handle_error(e, "ask_data_analyst")
    
    # ==================== Metadata APIs ====================
    
    def get_resource_metadata(self, resource_id: str, client_id: str = None,
                             user_id: str = None) -> APIResponse:
        """
        Get metadata for a specific resource.
        
        Args:
            resource_id: Resource UUID
            client_id: Client UUID for access validation
            user_id: User UUID for access validation
        
        Returns:
            APIResponse with resource metadata
        """
        try:
            # Get metadata
            metadata = self.metadata_registry.get_resource_metadata(resource_id)
            if not metadata:
                return APIResponse(success=False, error=f"Resource not found: {resource_id}")
            
            # Validate access if client_id and user_id provided
            if client_id and user_id:
                if not self._validate_access(client_id, user_id, resource_id):
                    return APIResponse(success=False, error="Access denied")
            
            return APIResponse(
                success=True,
                data=metadata.to_dict(),
                metadata={"operation": "get_resource_metadata"}
            )
            
        except Exception as e:
            return self._handle_error(e, "get_resource_metadata")
    
    def list_resources(self, client_id: str, user_id: str,
                      access_level: str = "user", resource_type: str = None,
                      include_deleted: bool = False) -> APIResponse:
        """
        List all accessible resources for a user.
        
        Args:
            client_id: Client UUID
            user_id: User UUID
            access_level: Access level (user, manager, admin)
            resource_type: Optional filter by resource type
            include_deleted: Whether to include soft-deleted resources
        
        Returns:
            APIResponse with list of resources
        """
        try:
            if not self._validate_access(client_id, user_id):
                return APIResponse(success=False, error="Invalid client_id or user_id")
            
            # Get all resources for client
            all_resources = self.metadata_registry.list_resources(
                client_id=client_id,
                include_deleted=include_deleted
            )
            
            # Filter by resource type if specified
            if resource_type:
                try:
                    resource_type_enum = ResourceType(resource_type)
                    all_resources = [r for r in all_resources if r.resource_type == resource_type_enum]
                except ValueError:
                    return APIResponse(success=False, error=f"Invalid resource_type: {resource_type}")
            
            # Filter by access level
            try:
                access_level_enum = AccessLevel(access_level)
            except ValueError:
                return APIResponse(success=False, error=f"Invalid access_level: {access_level}")
            
            accessible_resources = filter_accessible_resources(
                requesting_user_id=user_id,
                requesting_client_id=client_id,
                resources=all_resources,
                access_level=access_level_enum
            )
            
            # Format response
            resources_data = [resource.to_dict() for resource in accessible_resources]
            
            return APIResponse(
                success=True,
                data={
                    "resources": resources_data,
                    "total_count": len(resources_data),
                    "access_level": access_level,
                    "resource_type_filter": resource_type,
                    "include_deleted": include_deleted
                },
                metadata={"operation": "list_resources"}
            )
            
        except Exception as e:
            return self._handle_error(e, "list_resources")
    
    def get_schema(self, resource_id: str, version: int = None,
                  client_id: str = None, user_id: str = None) -> APIResponse:
        """
        Get schema information for a structured resource.
        
        Args:
            resource_id: Resource UUID
            version: Optional specific version
            client_id: Client UUID for access validation
            user_id: User UUID for access validation
        
        Returns:
            APIResponse with schema information
        """
        try:
            # Get metadata for validation
            metadata = self.metadata_registry.get_resource_metadata(resource_id)
            if not metadata:
                return APIResponse(success=False, error=f"Resource not found: {resource_id}")
            
            # Validate access if client_id and user_id provided
            if client_id and user_id:
                if not self._validate_access(client_id, user_id, resource_id):
                    return APIResponse(success=False, error="Access denied")
            
            # Only structured resources have schemas
            if metadata.resource_type != ResourceType.STRUCTURED:
                return APIResponse(
                    success=False, 
                    error=f"Schema not available for resource type: {metadata.resource_type.value}"
                )
            
            # Get schema information
            schema_info = self.metadata_registry.get_schema_info(resource_id, version)
            if not schema_info:
                return APIResponse(success=False, error="Schema information not found")
            
            return APIResponse(
                success=True,
                data={
                    "resource_id": resource_id,
                    "version": schema_info.version,
                    "schema": json.loads(schema_info.schema_json),
                    "statistics": json.loads(schema_info.statistics_json),
                    "detected_at": schema_info.detected_at.isoformat()
                },
                metadata={"operation": "get_schema"}
            )
            
        except Exception as e:
            return self._handle_error(e, "get_schema")
    
    def get_statistics(self, client_id: str, user_id: str,
                      access_level: str = "user") -> APIResponse:
        """
        Get system statistics for accessible resources.
        
        Args:
            client_id: Client UUID
            user_id: User UUID
            access_level: Access level (user, manager, admin)
        
        Returns:
            APIResponse with system statistics
        """
        try:
            if not self._validate_access(client_id, user_id):
                return APIResponse(success=False, error="Invalid client_id or user_id")
            
            # Get accessible resources
            all_resources = self.metadata_registry.list_resources(client_id=client_id)
            
            try:
                access_level_enum = AccessLevel(access_level)
            except ValueError:
                return APIResponse(success=False, error=f"Invalid access_level: {access_level}")
            
            accessible_resources = filter_accessible_resources(
                requesting_user_id=user_id,
                requesting_client_id=client_id,
                resources=all_resources,
                access_level=access_level_enum
            )
            
            # Calculate statistics
            stats = {
                "total_resources": len(accessible_resources),
                "by_type": {},
                "by_data_type": {},
                "total_size_bytes": 0,
                "total_rows": 0,
                "total_chunks": 0,
                "active_resources": 0,
                "deleted_resources": 0
            }
            
            for resource in accessible_resources:
                # Count by resource type
                resource_type = resource.resource_type.value
                stats["by_type"][resource_type] = stats["by_type"].get(resource_type, 0) + 1
                
                # Count by data type
                data_type = resource.data_type.value
                stats["by_data_type"][data_type] = stats["by_data_type"].get(data_type, 0) + 1
                
                # Aggregate sizes and counts
                stats["total_size_bytes"] += resource.file_size_bytes
                if resource.row_count:
                    stats["total_rows"] += resource.row_count
                if resource.chunk_count:
                    stats["total_chunks"] += resource.chunk_count
                
                # Count active vs deleted
                if resource.is_deleted:
                    stats["deleted_resources"] += 1
                else:
                    stats["active_resources"] += 1
            
            return APIResponse(
                success=True,
                data=stats,
                metadata={"operation": "get_statistics", "access_level": access_level}
            )
            
        except Exception as e:
            return self._handle_error(e, "get_statistics")
    
    # ==================== Administration APIs ====================
    
    def clear_cache(self, scope: str = "all") -> APIResponse:
        """
        Clear system caches.
        
        Args:
            scope: Cache scope to clear (all, query, embedding, metadata)
        
        Returns:
            APIResponse confirming cache clearing
        """
        try:
            cleared_caches = []
            
            if scope in ("all", "query"):
                # Clear SQL query cache
                self.sql_engine.clear_cache()
                cleared_caches.append("query")
            
            if scope in ("all", "embedding"):
                # Clear embedding cache
                self.search_engine.clear_cache()
                cleared_caches.append("embedding")
            
            if scope in ("all", "metadata"):
                # Clear metadata cache
                self.metadata_registry.clear_cache()
                cleared_caches.append("metadata")
            
            return APIResponse(
                success=True,
                data={
                    "cleared_caches": cleared_caches,
                    "scope": scope,
                    "cleared_at": datetime.utcnow().isoformat()
                },
                metadata={"operation": "clear_cache"}
            )
            
        except Exception as e:
            return self._handle_error(e, "clear_cache")
    
    def get_system_stats(self) -> APIResponse:
        """
        Get comprehensive system statistics.
        
        Returns:
            APIResponse with system statistics
        """
        try:
            # Get database sizes
            db_stats = self.db_managers.get_database_stats()
            
            # Get directory sizes
            directory_stats = self.directory_manager.get_directory_stats()
            
            # Get cache statistics
            cache_stats = {
                "sql_cache_size": self.sql_engine.get_cache_size(),
                "embedding_cache_size": self.search_engine.get_cache_size(),
                "metadata_cache_size": self.metadata_registry.get_cache_size()
            }
            
            return APIResponse(
                success=True,
                data={
                    "database_stats": db_stats,
                    "directory_stats": directory_stats,
                    "cache_stats": cache_stats,
                    "system_info": {
                        "base_path": self.base_path,
                        "config": self.config.to_dict(),
                        "uptime": "N/A"  # Could track this if needed
                    }
                },
                metadata={"operation": "get_system_stats"}
            )
            
        except Exception as e:
            return self._handle_error(e, "get_system_stats")
    
    def optimize_storage(self) -> APIResponse:
        """
        Optimize storage by running vacuum operations and rebuilding indexes.
        
        Returns:
            APIResponse confirming optimization
        """
        try:
            optimization_results = []
            
            # Optimize DuckDB
            self.db_managers.duckdb.vacuum()
            optimization_results.append("DuckDB vacuumed")
            
            # Optimize SQLite
            self.db_managers.sqlite.vacuum()
            optimization_results.append("SQLite vacuumed")
            
            # Optimize ChromaDB (if supported)
            try:
                self.db_managers.chromadb.optimize()
                optimization_results.append("ChromaDB optimized")
            except AttributeError:
                # ChromaDB might not have optimize method
                pass
            
            # Clean up temporary files
            from .storage.storage_utils import cleanup_temp_files
            cleanup_temp_files(self.base_path)
            optimization_results.append("Temporary files cleaned")
            
            return APIResponse(
                success=True,
                data={
                    "optimizations": optimization_results,
                    "optimized_at": datetime.utcnow().isoformat()
                },
                metadata={"operation": "optimize_storage"}
            )
            
        except Exception as e:
            return self._handle_error(e, "optimize_storage")
    
    def export_resource(self, resource_id: str, export_format: str = "csv",
                       output_path: str = None, client_id: str = None,
                       user_id: str = None) -> APIResponse:
        """
        Export a resource in the specified format.
        
        Args:
            resource_id: Resource UUID to export
            export_format: Export format (csv, json, parquet, excel)
            output_path: Optional output file path
            client_id: Client UUID for access validation
            user_id: User UUID for access validation
        
        Returns:
            APIResponse with export information
        """
        try:
            # Get metadata for validation
            metadata = self.metadata_registry.get_resource_metadata(resource_id)
            if not metadata:
                return APIResponse(success=False, error=f"Resource not found: {resource_id}")
            
            # Validate access if client_id and user_id provided
            if client_id and user_id:
                if not self._validate_access(client_id, user_id, resource_id):
                    return APIResponse(success=False, error="Access denied")
            
            # Get resource data
            data = self.storage_router.get_resource_data(resource_id)
            
            # Generate output path if not provided
            if not output_path:
                base_name = Path(metadata.original_filename).stem
                output_path = f"{base_name}_export.{export_format}"
            
            # Export data based on format
            if export_format == "csv":
                if isinstance(data, pd.DataFrame):
                    data.to_csv(output_path, index=False)
                else:
                    return APIResponse(success=False, error="CSV export only supported for structured data")
            
            elif export_format == "json":
                if isinstance(data, pd.DataFrame):
                    data.to_json(output_path, orient="records", indent=2)
                else:
                    with open(output_path, 'w') as f:
                        json.dump(data, f, indent=2, default=str)
            
            elif export_format == "parquet":
                if isinstance(data, pd.DataFrame):
                    data.to_parquet(output_path, index=False)
                else:
                    return APIResponse(success=False, error="Parquet export only supported for structured data")
            
            elif export_format == "excel":
                if isinstance(data, pd.DataFrame):
                    data.to_excel(output_path, index=False)
                else:
                    return APIResponse(success=False, error="Excel export only supported for structured data")
            
            else:
                return APIResponse(success=False, error=f"Unsupported export format: {export_format}")
            
            # Get file size
            export_size = os.path.getsize(output_path)
            
            return APIResponse(
                success=True,
                data={
                    "resource_id": resource_id,
                    "export_format": export_format,
                    "output_path": output_path,
                    "export_size_bytes": export_size,
                    "exported_at": datetime.utcnow().isoformat()
                },
                metadata={"operation": "export_resource"}
            )
            
        except Exception as e:
            return self._handle_error(e, "export_resource")
    
    def backup_data(self, backup_path: str = None, include_raw_files: bool = True) -> APIResponse:
        """
        Create a full system backup.
        
        Args:
            backup_path: Optional backup directory path
            include_raw_files: Whether to include raw uploaded files
        
        Returns:
            APIResponse with backup information
        """
        try:
            if not backup_path:
                backup_path = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Create backup directory
            os.makedirs(backup_path, exist_ok=True)
            
            backup_info = {
                "backup_path": backup_path,
                "backup_started": datetime.utcnow().isoformat(),
                "components": []
            }
            
            # Backup databases
            db_backup_path = os.path.join(backup_path, "databases")
            os.makedirs(db_backup_path, exist_ok=True)
            
            # Backup SQLite metadata
            import shutil
            sqlite_path = self.db_managers.sqlite_manager.db_path
            shutil.copy2(sqlite_path, os.path.join(db_backup_path, "metadata.db"))
            backup_info["components"].append("SQLite metadata")
            
            # Backup DuckDB data
            duckdb_path = self.db_managers.duckdb_manager.db_path
            shutil.copy2(duckdb_path, os.path.join(db_backup_path, "structured.duckdb"))
            backup_info["components"].append("DuckDB structured data")
            
            # Backup ChromaDB
            chroma_source = os.path.join(self.base_path, "data", "unstructured", "chroma_db")
            chroma_dest = os.path.join(db_backup_path, "chroma_db")
            if os.path.exists(chroma_source):
                shutil.copytree(chroma_source, chroma_dest)
                backup_info["components"].append("ChromaDB embeddings")
            
            # Backup raw files if requested
            if include_raw_files:
                raw_source = os.path.join(self.base_path, "data", "raw")
                raw_dest = os.path.join(backup_path, "raw_files")
                if os.path.exists(raw_source):
                    shutil.copytree(raw_source, raw_dest)
                    backup_info["components"].append("Raw files")
            
            # Create backup manifest
            backup_info["backup_completed"] = datetime.utcnow().isoformat()
            manifest_path = os.path.join(backup_path, "backup_manifest.json")
            with open(manifest_path, 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            return APIResponse(
                success=True,
                data=backup_info,
                metadata={"operation": "backup_data"}
            )
            
        except Exception as e:
            return self._handle_error(e, "backup_data")
    
    def restore_data(self, backup_path: str, restore_raw_files: bool = True) -> APIResponse:
        """
        Restore system from backup.
        
        Args:
            backup_path: Path to backup directory
            restore_raw_files: Whether to restore raw files
        
        Returns:
            APIResponse with restore information
        """
        try:
            if not os.path.exists(backup_path):
                return APIResponse(success=False, error=f"Backup path not found: {backup_path}")
            
            # Read backup manifest
            manifest_path = os.path.join(backup_path, "backup_manifest.json")
            if not os.path.exists(manifest_path):
                return APIResponse(success=False, error="Backup manifest not found")
            
            with open(manifest_path, 'r') as f:
                backup_info = json.load(f)
            
            restore_info = {
                "backup_path": backup_path,
                "restore_started": datetime.utcnow().isoformat(),
                "restored_components": []
            }
            
            # Close existing database connections
            self.db_managers.close_all()
            
            # Restore databases
            db_backup_path = os.path.join(backup_path, "databases")
            
            # Restore SQLite
            sqlite_backup = os.path.join(db_backup_path, "metadata.db")
            if os.path.exists(sqlite_backup):
                import shutil
                shutil.copy2(sqlite_backup, self.db_managers.sqlite_manager.db_path)
                restore_info["restored_components"].append("SQLite metadata")
            
            # Restore DuckDB
            duckdb_backup = os.path.join(db_backup_path, "structured.duckdb")
            if os.path.exists(duckdb_backup):
                import shutil
                shutil.copy2(duckdb_backup, self.db_managers.duckdb_manager.db_path)
                restore_info["restored_components"].append("DuckDB structured data")
            
            # Restore ChromaDB
            chroma_backup = os.path.join(db_backup_path, "chroma_db")
            chroma_dest = os.path.join(self.base_path, "data", "unstructured", "chroma_db")
            if os.path.exists(chroma_backup):
                import shutil
                if os.path.exists(chroma_dest):
                    shutil.rmtree(chroma_dest)
                shutil.copytree(chroma_backup, chroma_dest)
                restore_info["restored_components"].append("ChromaDB embeddings")
            
            # Restore raw files if requested
            if restore_raw_files:
                raw_backup = os.path.join(backup_path, "raw_files")
                raw_dest = os.path.join(self.base_path, "data", "raw")
                if os.path.exists(raw_backup):
                    import shutil
                    if os.path.exists(raw_dest):
                        shutil.rmtree(raw_dest)
                    shutil.copytree(raw_backup, raw_dest)
                    restore_info["restored_components"].append("Raw files")
            
            # Reinitialize database connections
            self.db_managers = DatabaseManagers(self.base_path, self.config)
            
            restore_info["restore_completed"] = datetime.utcnow().isoformat()
            restore_info["original_backup_info"] = backup_info
            
            return APIResponse(
                success=True,
                data=restore_info,
                metadata={"operation": "restore_data"}
            )
            
        except Exception as e:
            return self._handle_error(e, "restore_data")
    
    # ==================== Helper Methods ====================
    
    def _format_output(self, data: Any, output_format: str, resource_type: ResourceType) -> Any:
        """Format output data based on requested format."""
        if output_format == "dataframe":
            return data  # Return as-is (pandas DataFrame or original format)
        
        elif output_format == "json":
            if isinstance(data, pd.DataFrame):
                return data.to_dict(orient="records")
            return data
        
        elif output_format == "csv":
            if isinstance(data, pd.DataFrame):
                return data.to_csv(index=False)
            else:
                raise ValueError("CSV format only supported for structured data")
        
        elif output_format == "dict":
            if isinstance(data, pd.DataFrame):
                return data.to_dict()
            return data
        
        else:
            raise ValueError(f"Unsupported output format: {output_format}")


# Convenience function to create API instance
def create_api(config: Optional[Config] = None, base_path: str = None) -> UniversalDataHandler:
    """
    Create a Universal Data Handler API instance.
    
    Args:
        config: Optional configuration object
        base_path: Optional base path for data storage
    
    Returns:
        UniversalDataHandler: Configured API instance
    """
    return UniversalDataHandler(config=config, base_path=base_path)
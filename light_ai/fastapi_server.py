#!/usr/bin/env python3
"""
FastAPI server for Universal Data Handler with Swagger documentation.

This provides a REST API interface with automatic OpenAPI/Swagger documentation
for all the Universal Data Handler functionality.
"""

import os
import uuid
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from .api import create_api, APIResponse
from .config import Config


# Pydantic models for request/response validation
class UploadFileRequest(BaseModel):
    client_id: str = Field(..., description="Client UUID")
    user_id: str = Field(..., description="User UUID")
    resource_name: Optional[str] = Field(None, description="Optional resource name")


class UploadJSONRequest(BaseModel):
    client_id: str = Field(..., description="Client UUID")
    user_id: str = Field(..., description="User UUID")
    json_data: Union[Dict, List] = Field(..., description="JSON data to upload")
    resource_name: str = Field(..., description="Resource name")
    flatten: bool = Field(False, description="Whether to flatten nested structures")


class QueryStructuredRequest(BaseModel):
    client_id: str = Field(..., description="Client UUID")
    user_id: str = Field(..., description="User UUID")
    sql_query: str = Field(..., description="SQL query to execute")
    output_format: str = Field("json", description="Output format (json, csv, dataframe)")


class QueryNaturalRequest(BaseModel):
    client_id: str = Field(..., description="Client UUID")
    user_id: str = Field(..., description="User UUID")
    question: str = Field(..., description="Natural language question")
    output_format: str = Field("json", description="Output format (json, csv, dataframe)")


class SearchUnstructuredRequest(BaseModel):
    client_id: str = Field(..., description="Client UUID")
    user_id: str = Field(..., description="User UUID")
    query: str = Field(..., description="Search query")
    strategy: str = Field("hybrid", description="Search strategy (semantic, keyword, hybrid, mmr)")
    limit: int = Field(5, description="Maximum number of results")


class AnalystRequest(BaseModel):
    client_id: str = Field(..., description="Client UUID")
    user_id: str = Field(..., description="User UUID")
    question: str = Field(..., description="Analytical question")
    include_visualizations: bool = Field(False, description="Whether to include visualizations")


# Initialize FastAPI app
app = FastAPI(
    title="Universal Data Handler API",
    description="A comprehensive on-premises data management system with AI-powered querying",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the Universal Data Handler API
try:
    config = Config.load()
    api = create_api(config=config)
    print("✅ Universal Data Handler API initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize API: {e}")
    api = None


def handle_api_response(response: APIResponse):
    """Convert APIResponse to FastAPI response."""
    if response.success:
        return response.to_dict()
    else:
        raise HTTPException(status_code=400, detail=response.error)


# ==================== Sub-Layer 1: Data Ingestion & Storage ====================

@app.post("/api/v1/upload/file", 
          summary="Upload a file",
          description="Upload and process a file of any supported type (CSV, Excel, JSON, PDF, TXT, etc.)")
async def upload_file(
    file: UploadFile = File(..., description="File to upload"),
    client_id: str = Form(..., description="Client UUID"),
    user_id: str = Form(..., description="User UUID"),
    resource_name: Optional[str] = Form(None, description="Optional resource name")
):
    """Upload and process a file of any supported type."""
    if not api:
        raise HTTPException(status_code=500, detail="API not initialized")
    
    # Save uploaded file temporarily
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        response = api.upload_file(
            client_id=client_id,
            user_id=user_id,
            file_path=tmp_file_path,
            resource_name=resource_name or file.filename
        )
        return handle_api_response(response)
    finally:
        # Clean up temporary file
        try:
            os.unlink(tmp_file_path)
        except:
            pass


@app.post("/api/v1/upload/json",
          summary="Upload JSON data",
          description="Upload JSON data directly without a file")
async def upload_json(request: UploadJSONRequest):
    """Upload JSON data directly."""
    if not api:
        raise HTTPException(status_code=500, detail="API not initialized")
    
    response = api.upload_json(
        client_id=request.client_id,
        user_id=request.user_id,
        json_data=request.json_data,
        resource_name=request.resource_name,
        flatten=request.flatten
    )
    return handle_api_response(response)


@app.post("/api/v1/upload/bulk",
          summary="Upload multiple files",
          description="Upload multiple files in bulk with parallel processing")
async def upload_bulk(
    files: List[UploadFile] = File(..., description="Files to upload"),
    client_id: str = Form(..., description="Client UUID"),
    user_id: str = Form(..., description="User UUID"),
    parallel: bool = Form(True, description="Whether to process files in parallel")
):
    """Upload multiple files in bulk."""
    if not api:
        raise HTTPException(status_code=500, detail="API not initialized")
    
    # Save all uploaded files temporarily
    import tempfile
    temp_files = []
    
    try:
        for file in files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                temp_files.append(tmp_file.name)
        
        response = api.upload_bulk(
            client_id=client_id,
            user_id=user_id,
            files=temp_files,
            parallel=parallel
        )
        return handle_api_response(response)
    
    finally:
        # Clean up temporary files
        for tmp_file_path in temp_files:
            try:
                os.unlink(tmp_file_path)
            except:
                pass


# ==================== Sub-Layer 2: Data Retrieval ====================

@app.get("/api/v1/resource/{resource_id}",
         summary="Get resource data",
         description="Retrieve original resource data by ID")
async def get_resource(
    resource_id: str,
    version: Optional[int] = Query(None, description="Optional specific version"),
    output_format: str = Query("json", description="Output format (json, csv, dataframe)"),
    client_id: Optional[str] = Query(None, description="Client UUID for access validation"),
    user_id: Optional[str] = Query(None, description="User UUID for access validation")
):
    """Retrieve original resource data."""
    if not api:
        raise HTTPException(status_code=500, detail="API not initialized")
    
    response = api.get_resource(
        resource_id=resource_id,
        version=version,
        output_format=output_format,
        client_id=client_id,
        user_id=user_id
    )
    return handle_api_response(response)


@app.get("/api/v1/tables",
         summary="Get available tables",
         description="Get all available tables and their schemas for a user")
async def get_available_tables(
    client_id: str = Query(..., description="Client UUID"),
    user_id: str = Query(..., description="User UUID")
):
    """Get all available tables and their schemas for a user."""
    if not api:
        raise HTTPException(status_code=500, detail="API not initialized")
    
    try:
        tables_info = api.sql_engine.get_available_tables(client_id, user_id)
        return {"success": True, "data": tables_info}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/query/smart",
          summary="Smart SQL query",
          description="Build and execute smart SQL queries based on natural language")
async def smart_query(
    client_id: str = Query(..., description="Client UUID"),
    user_id: str = Query(..., description="User UUID"),
    question: str = Query(..., description="Natural language question"),
    output_format: str = Query("json", description="Output format (json, csv, dataframe)")
):
    """Build and execute smart SQL queries based on natural language."""
    if not api:
        raise HTTPException(status_code=500, detail="API not initialized")
    
    try:
        # Build smart query
        smart_sql = api.sql_engine.build_smart_query(question, client_id, user_id)
        
        # Execute the query
        response = api.query_structured(
            client_id=client_id,
            user_id=user_id,
            sql_query=smart_sql,
            output_format=output_format
        )
        
        # Add the generated SQL to the response
        if response.success:
            response.data["generated_sql"] = smart_sql
            response.data["question"] = question
        
        return handle_api_response(response)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/query/structured",
          summary="Execute SQL query",
          description="Execute SQL query on structured data")
async def query_structured(request: QueryStructuredRequest):
    """Execute SQL query on structured data."""
    if not api:
        raise HTTPException(status_code=500, detail="API not initialized")
    
    response = api.query_structured(
        client_id=request.client_id,
        user_id=request.user_id,
        sql_query=request.sql_query,
        output_format=request.output_format
    )
    return handle_api_response(response)


@app.post("/api/v1/query/natural",
          summary="Natural language query",
          description="Process natural language questions about your data")
async def query_natural(request: QueryNaturalRequest):
    """Process natural language query."""
    if not api:
        raise HTTPException(status_code=500, detail="API not initialized")
    
    response = api.query_natural(
        client_id=request.client_id,
        user_id=request.user_id,
        question=request.question,
        output_format=request.output_format
    )
    return handle_api_response(response)


@app.post("/api/v1/search/unstructured",
          summary="Semantic search",
          description="Perform AI-powered semantic search on unstructured data")
async def search_unstructured(request: SearchUnstructuredRequest):
    """Perform semantic search on unstructured data."""
    if not api:
        raise HTTPException(status_code=500, detail="API not initialized")
    
    response = api.search_unstructured(
        client_id=request.client_id,
        user_id=request.user_id,
        query=request.query,
        strategy=request.strategy,
        limit=request.limit
    )
    return handle_api_response(response)


@app.post("/api/v1/analyst",
          summary="AI Data Analyst",
          description="Ask the AI data analyst for comprehensive analysis and insights")
async def ask_data_analyst(request: AnalystRequest):
    """Ask the AI data analyst for comprehensive analysis."""
    if not api:
        raise HTTPException(status_code=500, detail="API not initialized")
    
    response = api.ask_data_analyst(
        client_id=request.client_id,
        user_id=request.user_id,
        question=request.question,
        include_visualizations=request.include_visualizations
    )
    return handle_api_response(response)


# ==================== Metadata APIs ====================

@app.get("/api/v1/resources",
         summary="List resources",
         description="List all accessible resources for a user")
async def list_resources(
    client_id: str = Query(..., description="Client UUID"),
    user_id: str = Query(..., description="User UUID"),
    access_level: str = Query("user", description="Access level (user, manager, admin)"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    include_deleted: bool = Query(False, description="Include soft-deleted resources")
):
    """List all accessible resources for a user."""
    if not api:
        raise HTTPException(status_code=500, detail="API not initialized")
    
    response = api.list_resources(
        client_id=client_id,
        user_id=user_id,
        access_level=access_level,
        resource_type=resource_type,
        include_deleted=include_deleted
    )
    return handle_api_response(response)


@app.get("/api/v1/resource/{resource_id}/metadata",
         summary="Get resource metadata",
         description="Get detailed metadata for a specific resource")
async def get_resource_metadata(
    resource_id: str,
    client_id: Optional[str] = Query(None, description="Client UUID for access validation"),
    user_id: Optional[str] = Query(None, description="User UUID for access validation")
):
    """Get metadata for a specific resource."""
    if not api:
        raise HTTPException(status_code=500, detail="API not initialized")
    
    response = api.get_resource_metadata(
        resource_id=resource_id,
        client_id=client_id,
        user_id=user_id
    )
    return handle_api_response(response)


@app.get("/api/v1/resource/{resource_id}/schema",
         summary="Get resource schema",
         description="Get schema information for structured resources")
async def get_schema(
    resource_id: str,
    version: Optional[int] = Query(None, description="Optional specific version"),
    client_id: Optional[str] = Query(None, description="Client UUID for access validation"),
    user_id: Optional[str] = Query(None, description="User UUID for access validation")
):
    """Get schema information for a structured resource."""
    if not api:
        raise HTTPException(status_code=500, detail="API not initialized")
    
    response = api.get_schema(
        resource_id=resource_id,
        version=version,
        client_id=client_id,
        user_id=user_id
    )
    return handle_api_response(response)


@app.get("/api/v1/statistics",
         summary="Get system statistics",
         description="Get comprehensive statistics for accessible resources")
async def get_statistics(
    client_id: str = Query(..., description="Client UUID"),
    user_id: str = Query(..., description="User UUID"),
    access_level: str = Query("user", description="Access level (user, manager, admin)")
):
    """Get system statistics for accessible resources."""
    if not api:
        raise HTTPException(status_code=500, detail="API not initialized")
    
    response = api.get_statistics(
        client_id=client_id,
        user_id=user_id,
        access_level=access_level
    )
    return handle_api_response(response)


# ==================== Administration APIs ====================

@app.post("/api/v1/admin/cache/clear",
          summary="Clear cache",
          description="Clear system caches")
async def clear_cache(
    scope: str = Query("all", description="Cache scope (all, query, embedding, metadata)")
):
    """Clear system caches."""
    if not api:
        raise HTTPException(status_code=500, detail="API not initialized")
    
    response = api.clear_cache(scope=scope)
    return handle_api_response(response)


@app.get("/api/v1/admin/stats",
         summary="Get system stats",
         description="Get comprehensive system statistics")
async def get_system_stats():
    """Get comprehensive system statistics."""
    if not api:
        raise HTTPException(status_code=500, detail="API not initialized")
    
    response = api.get_system_stats()
    return handle_api_response(response)


@app.post("/api/v1/admin/optimize",
          summary="Optimize storage",
          description="Optimize storage by running vacuum operations")
async def optimize_storage():
    """Optimize storage by running vacuum operations."""
    if not api:
        raise HTTPException(status_code=500, detail="API not initialized")
    
    response = api.optimize_storage()
    return handle_api_response(response)


@app.get("/api/v1/health",
         summary="Health check",
         description="Check system health")
async def health_check():
    """Check system health."""
    if not api:
        return {"status": "error", "message": "API not initialized"}
    
    try:
        # Test basic functionality
        stats_response = api.get_system_stats()
        if stats_response.success:
            return {"status": "healthy", "timestamp": stats_response.timestamp}
        else:
            return {"status": "degraded", "error": stats_response.error}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ==================== Utility endpoints ====================

@app.get("/api/v1/demo/ids",
         summary="Generate demo IDs",
         description="Generate sample client and user IDs for testing")
async def generate_demo_ids():
    """Generate sample client and user IDs for testing."""
    return {
        "client_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "note": "Use these IDs for testing the API endpoints"
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Universal Data Handler FastAPI Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    print(f"🚀 Starting Universal Data Handler API server...")
    print(f"📖 Swagger docs will be available at: http://{args.host}:{args.port}/docs")
    print(f"📚 ReDoc docs will be available at: http://{args.host}:{args.port}/redoc")
    
    uvicorn.run(
        "light_ai.fastapi_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )
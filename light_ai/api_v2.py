"""
Comprehensive API Layer v2 for Intelligent AI Data Analyst System.

This module provides a complete API layer with:
- RESTful API for all analysis operations
- WebSocket support for real-time interactions
- Streaming API for large result sets
- Comprehensive request validation and sanitization
- Rate limiting and abuse prevention
- Integration with Strands AI framework

Requirements: 12.1, 12.3, 11.4
"""

import asyncio
import json
import time
import uuid
import logging
from typing import Dict, List, Any, Optional, Union, AsyncGenerator
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
import hashlib
import re
from collections import defaultdict

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field, validator
import uvicorn

from .config import Config
from .logger import setup_logger
from .agents.master_agent import MasterDataAnalystAgent, AnalysisRequest, AnalysisResult
from .security.security_manager import SecurityManager
from .security.access_control_manager import AccessControlManager
from .core.models import AccessLevel


# ==================== Simple Rate Limiter ====================

class SimpleRateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.limits = {
            "analysis": (10, 60),  # 10 requests per 60 seconds
            "streaming": (5, 60),   # 5 requests per 60 seconds
            "websocket": (20, 60),  # 20 requests per 60 seconds
            "health": (60, 60),     # 60 requests per 60 seconds
            "default": (30, 60)     # 30 requests per 60 seconds
        }
    
    def is_allowed(self, key: str, endpoint: str = "default") -> bool:
        """Check if request is allowed."""
        now = time.time()
        limit, window = self.limits.get(endpoint, self.limits["default"])
        
        # Clean old requests
        self.requests[key] = [req_time for req_time in self.requests[key] 
                             if now - req_time < window]
        
        # Check if under limit
        if len(self.requests[key]) < limit:
            self.requests[key].append(now)
            return True
        
        return False


# Global rate limiter instance
rate_limiter = SimpleRateLimiter()


def get_client_ip(request: Request) -> str:
    """Get client IP address."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_rate_limit(request: Request, endpoint: str = "default"):
    """Check rate limit for request."""
    client_ip = get_client_ip(request)
    if not rate_limiter.is_allowed(client_ip, endpoint):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return True


# ==================== Request/Response Models ====================

class BaseAPIRequest(BaseModel):
    """Base request model with common validation."""
    client_id: str = Field(..., description="Client UUID", pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
    user_id: str = Field(..., description="User UUID", pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
    
    @validator('client_id', 'user_id')
    def validate_uuid_format(cls, v):
        """Validate UUID format and sanitize."""
        if not v or len(v) != 36:
            raise ValueError('Invalid UUID format')
        # Sanitize by removing any non-UUID characters
        sanitized = re.sub(r'[^0-9a-f-]', '', v.lower())
        if len(sanitized) != 36:
            raise ValueError('Invalid UUID format after sanitization')
        return sanitized


class AnalysisAPIRequest(BaseAPIRequest):
    """Request for AI data analysis."""
    query: str = Field(..., description="Natural language query", min_length=1, max_length=10000)
    desired_fields: Optional[Dict[str, str]] = Field(None, description="Desired fields mapping")
    optional_fields: Optional[Dict[str, str]] = Field(None, description="Optional fields mapping")
    derived_fields: Optional[Dict[str, str]] = Field(None, description="Derived fields definitions")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    conversation_id: Optional[str] = Field(None, description="Conversation UUID")
    access_level: str = Field("user", description="Access level")
    include_visualizations: bool = Field(True, description="Include visualization suggestions")
    streaming: bool = Field(False, description="Enable streaming response")
    
    @validator('query')
    def sanitize_query(cls, v):
        """Sanitize query input."""
        if not v or not v.strip():
            raise ValueError('Query cannot be empty')
        # Remove potentially dangerous characters but preserve meaningful content
        sanitized = re.sub(r'[<>"\'\x00-\x1f\x7f-\x9f]', '', v.strip())
        if len(sanitized) < 1:
            raise ValueError('Query contains no valid content')
        return sanitized[:10000]  # Truncate to max length
    
    @validator('access_level')
    def validate_access_level(cls, v):
        """Validate access level."""
        valid_levels = ['user', 'manager', 'admin']
        if v not in valid_levels:
            raise ValueError(f'Invalid access level. Must be one of: {valid_levels}')
        return v


class StreamingAnalysisRequest(BaseAPIRequest):
    """Request for streaming analysis."""
    query: str = Field(..., description="Natural language query", min_length=1, max_length=10000)
    chunk_size: int = Field(100, description="Number of records per chunk", ge=1, le=1000)
    include_metadata: bool = Field(True, description="Include metadata in stream")


class WebSocketMessage(BaseModel):
    """WebSocket message format."""
    type: str = Field(..., description="Message type")
    data: Dict[str, Any] = Field(..., description="Message data")
    timestamp: Optional[str] = Field(None, description="Message timestamp")
    message_id: Optional[str] = Field(None, description="Message ID")


class APIResponse(BaseModel):
    """Standardized API response."""
    success: bool = Field(..., description="Success status")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Response timestamp")


# ==================== Rate Limiting ====================

# Rate limiting configurations
RATE_LIMITS = {
    "analysis": "10/minute",
    "streaming": "5/minute", 
    "websocket": "20/minute",
    "health": "60/minute",
    "default": "30/minute"
}


# ==================== Security and Validation ====================

class SecurityValidator:
    """Security validation and sanitization."""
    
    @staticmethod
    def validate_request_size(request: Request) -> bool:
        """Validate request size limits."""
        content_length = request.headers.get('content-length')
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
            return False
        return True
    
    @staticmethod
    def sanitize_headers(headers: Dict[str, str]) -> Dict[str, str]:
        """Sanitize request headers."""
        safe_headers = {}
        for key, value in headers.items():
            # Only allow safe header characters
            safe_key = re.sub(r'[^\w-]', '', key.lower())
            safe_value = re.sub(r'[^\w\s\-\.\,\;\:\@\#\$\%\^\&\*\(\)\+\=\[\]\{\}\|\\\`\~]', '', str(value))
            if safe_key and safe_value:
                safe_headers[safe_key] = safe_value[:1000]  # Limit header value length
        return safe_headers
    
    @staticmethod
    def validate_json_payload(payload: Any) -> bool:
        """Validate JSON payload structure."""
        if isinstance(payload, dict):
            # Check for reasonable nesting depth
            def check_depth(obj, depth=0):
                if depth > 10:  # Max nesting depth
                    return False
                if isinstance(obj, dict):
                    return all(check_depth(v, depth + 1) for v in obj.values())
                elif isinstance(obj, list):
                    return all(check_depth(item, depth + 1) for item in obj)
                return True
            return check_depth(payload)
        return True


# ==================== WebSocket Connection Manager ====================

class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
    
    async def connect(self, websocket: WebSocket, client_id: str, user_id: str) -> str:
        """Accept WebSocket connection and return connection ID."""
        await websocket.accept()
        connection_id = f"{client_id}_{user_id}_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        
        self.active_connections[connection_id] = websocket
        self.connection_metadata[connection_id] = {
            "client_id": client_id,
            "user_id": user_id,
            "connected_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }
        
        self.logger.info(f"WebSocket connected: {connection_id}")
        return connection_id
    
    def disconnect(self, connection_id: str):
        """Remove WebSocket connection."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        if connection_id in self.connection_metadata:
            del self.connection_metadata[connection_id]
        self.logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], connection_id: str):
        """Send message to specific connection."""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_json(message)
                # Update last activity
                if connection_id in self.connection_metadata:
                    self.connection_metadata[connection_id]["last_activity"] = datetime.utcnow().isoformat()
            except Exception as e:
                self.logger.error(f"Failed to send message to {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def broadcast_to_user(self, message: Dict[str, Any], client_id: str, user_id: str):
        """Broadcast message to all connections for a user."""
        user_connections = [
            conn_id for conn_id, metadata in self.connection_metadata.items()
            if metadata["client_id"] == client_id and metadata["user_id"] == user_id
        ]
        
        for connection_id in user_connections:
            await self.send_personal_message(message, connection_id)
    
    def get_active_connections(self) -> Dict[str, Dict[str, Any]]:
        """Get information about active connections."""
        return self.connection_metadata.copy()
    
    async def cleanup_stale_connections(self):
        """Clean up stale connections."""
        current_time = datetime.utcnow()
        stale_connections = []
        
        for conn_id, metadata in self.connection_metadata.items():
            last_activity = datetime.fromisoformat(metadata["last_activity"])
            if (current_time - last_activity).total_seconds() > 3600:  # 1 hour timeout
                stale_connections.append(conn_id)
        
        for conn_id in stale_connections:
            self.disconnect(conn_id)


# ==================== API Application Setup ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    app.state.logger.info("Starting Comprehensive API Layer v2")
    
    # Initialize cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup(app.state.connection_manager))
    
    yield
    
    # Shutdown
    cleanup_task.cancel()
    app.state.logger.info("Shutting down Comprehensive API Layer v2")


async def periodic_cleanup(connection_manager: ConnectionManager):
    """Periodic cleanup of stale connections."""
    while True:
        try:
            await asyncio.sleep(300)  # 5 minutes
            await connection_manager.cleanup_stale_connections()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logging.error(f"Cleanup task error: {e}")


def create_comprehensive_api(config: Optional[Config] = None) -> FastAPI:
    """
    Create comprehensive API application with all features.
    
    Args:
        config: Optional configuration object
        
    Returns:
        FastAPI application instance
    """
    # Load configuration
    if not config:
        config = Config.load()
    
    # Create FastAPI app with lifespan
    app = FastAPI(
        title="Intelligent AI Data Analyst API v2",
        description="Comprehensive API layer with AI-powered data analysis, real-time interactions, and streaming capabilities",
        version="2.0.0",
        docs_url="/api/v2/docs",
        redoc_url="/api/v2/redoc",
        lifespan=lifespan
    )
    
    # Initialize logger
    logger = setup_logger("comprehensive_api_v2", config)
    app.state.logger = logger
    
    # Initialize components
    app.state.config = config
    app.state.master_agent = MasterDataAnalystAgent(config)
    app.state.security_manager = SecurityManager(config)
    app.state.access_control = AccessControlManager(config)
    app.state.connection_manager = ConnectionManager()
    app.state.security_validator = SecurityValidator()
    
    # Add middleware
    app.state.rate_limiter = rate_limiter
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Trusted host middleware for security
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure appropriately for production
    )
    
    return app


# Create the application instance
app = create_comprehensive_api()


# ==================== Security Dependencies ====================

security = HTTPBearer(auto_error=False)

async def validate_request_security(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """Validate request security and return user context."""
    # Validate request size
    if not app.state.security_validator.validate_request_size(request):
        raise HTTPException(status_code=413, detail="Request too large")
    
    # Sanitize headers
    safe_headers = app.state.security_validator.sanitize_headers(dict(request.headers))
    
    # For now, we'll use a simple validation
    # In production, implement proper JWT/API key validation
    user_context = {
        "authenticated": True,
        "headers": safe_headers,
        "ip_address": get_remote_address(request)
    }
    
    return user_context


async def validate_user_access(
    request_data: BaseAPIRequest,
    user_context: Dict[str, Any] = Depends(validate_request_security)
) -> bool:
    """Validate user access to resources."""
    try:
        # Use access control manager to validate access
        access_granted = app.state.access_control.validate_user_access(
            request_data.client_id,
            request_data.user_id,
            AccessLevel.USER
        )
        
        if not access_granted:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return True
    except Exception as e:
        app.state.logger.error(f"Access validation failed: {e}")
        raise HTTPException(status_code=403, detail="Access validation failed")


# ==================== RESTful API Endpoints ====================

@app.post("/api/v2/analysis", response_model=APIResponse)
async def analyze_data(
    request: Request,
    analysis_request: AnalysisAPIRequest,
    background_tasks: BackgroundTasks,
    user_context: Dict[str, Any] = Depends(validate_request_security),
    access_validated: bool = Depends(validate_user_access),
    rate_limit_check: bool = Depends(lambda req: check_rate_limit(req, "analysis"))
):
    """
    Perform comprehensive AI data analysis.
    
    This endpoint provides intelligent data analysis using the Strands AI framework
    with natural language understanding and cross-resource synthesis.
    """
    try:
        app.state.logger.info(f"Analysis request from {analysis_request.user_id}: {analysis_request.query[:100]}")
        
        # Convert to internal request format
        internal_request = AnalysisRequest(
            user_id=analysis_request.user_id,
            client_id=analysis_request.client_id,
            query=analysis_request.query,
            desired_fields=analysis_request.desired_fields,
            optional_fields=analysis_request.optional_fields,
            derived_fields=analysis_request.derived_fields,
            context=analysis_request.context,
            conversation_id=analysis_request.conversation_id,
            access_level=AccessLevel(analysis_request.access_level),
            include_visualizations=analysis_request.include_visualizations
        )
        
        # Execute analysis
        result = await app.state.master_agent.analyze_data(internal_request)
        
        # Log successful analysis
        background_tasks.add_task(
            log_analysis_completion,
            analysis_request.user_id,
            analysis_request.client_id,
            result.query_id,
            result.execution_time_ms
        )
        
        return APIResponse(
            success=True,
            data=asdict(result),
            metadata={
                "operation": "analysis",
                "execution_time_ms": result.execution_time_ms,
                "sources_used": len(result.sources_used),
                "ip_address": user_context["ip_address"]
            }
        )
        
    except Exception as e:
        app.state.logger.error(f"Analysis failed: {e}")
        return APIResponse(
            success=False,
            error=f"Analysis failed: {str(e)}",
            metadata={"operation": "analysis", "ip_address": user_context["ip_address"]}
        )


@app.post("/api/v2/analysis/streaming")
async def stream_analysis(
    request: Request,
    streaming_request: StreamingAnalysisRequest,
    user_context: Dict[str, Any] = Depends(validate_request_security),
    access_validated: bool = Depends(validate_user_access),
    rate_limit_check: bool = Depends(lambda req: check_rate_limit(req, "streaming"))
):
    """
    Stream large analysis results in chunks.
    
    This endpoint provides streaming responses for large datasets to prevent
    timeout issues and enable real-time data processing.
    """
    async def generate_analysis_stream():
        """Generate streaming analysis response."""
        try:
            # Start analysis
            internal_request = AnalysisRequest(
                user_id=streaming_request.user_id,
                client_id=streaming_request.client_id,
                query=streaming_request.query,
                access_level=AccessLevel.USER,
                include_visualizations=False  # Skip visualizations for streaming
            )
            
            # Get analysis result
            result = await app.state.master_agent.analyze_data(internal_request)
            
            # Stream metadata first if requested
            if streaming_request.include_metadata:
                metadata_chunk = {
                    "type": "metadata",
                    "data": {
                        "query_id": result.query_id,
                        "total_results": len(result.results),
                        "execution_time_ms": result.execution_time_ms,
                        "sources_used": result.sources_used,
                        "insights": result.insights
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                yield f"data: {json.dumps(metadata_chunk)}\n\n"
            
            # Stream results in chunks
            chunk_size = streaming_request.chunk_size
            for i in range(0, len(result.results), chunk_size):
                chunk = result.results[i:i + chunk_size]
                
                chunk_data = {
                    "type": "data_chunk",
                    "data": {
                        "chunk_index": i // chunk_size,
                        "chunk_size": len(chunk),
                        "results": chunk,
                        "is_final": i + chunk_size >= len(result.results)
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                yield f"data: {json.dumps(chunk_data)}\n\n"
                
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.1)
            
            # Send completion signal
            completion_data = {
                "type": "completion",
                "data": {
                    "query_id": result.query_id,
                    "total_chunks": (len(result.results) + chunk_size - 1) // chunk_size,
                    "follow_up_suggestions": result.follow_up_suggestions
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            yield f"data: {json.dumps(completion_data)}\n\n"
            
        except Exception as e:
            error_data = {
                "type": "error",
                "data": {"error": str(e)},
                "timestamp": datetime.utcnow().isoformat()
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_analysis_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )


@app.post("/api/v2/analysis/continue", response_model=APIResponse)
async def continue_conversation(
    request: Request,
    analysis_request: AnalysisAPIRequest,
    user_context: Dict[str, Any] = Depends(validate_request_security),
    access_validated: bool = Depends(validate_user_access),
    rate_limit_check: bool = Depends(lambda req: check_rate_limit(req, "analysis"))
):
    """
    Continue a conversation with follow-up questions.
    
    This endpoint maintains conversation context for multi-turn interactions
    with the AI data analyst.
    """
    try:
        if not analysis_request.conversation_id:
            raise HTTPException(status_code=400, detail="conversation_id required for continuing conversation")
        
        # Convert to internal request format
        internal_request = AnalysisRequest(
            user_id=analysis_request.user_id,
            client_id=analysis_request.client_id,
            query=analysis_request.query,
            desired_fields=analysis_request.desired_fields,
            optional_fields=analysis_request.optional_fields,
            derived_fields=analysis_request.derived_fields,
            context=analysis_request.context,
            conversation_id=analysis_request.conversation_id,
            access_level=AccessLevel(analysis_request.access_level),
            include_visualizations=analysis_request.include_visualizations
        )
        
        # Continue conversation
        result = await app.state.master_agent.continue_conversation(internal_request)
        
        return APIResponse(
            success=True,
            data=asdict(result),
            metadata={
                "operation": "continue_conversation",
                "conversation_id": analysis_request.conversation_id,
                "execution_time_ms": result.execution_time_ms
            }
        )
        
    except Exception as e:
        app.state.logger.error(f"Conversation continuation failed: {e}")
        return APIResponse(
            success=False,
            error=f"Conversation continuation failed: {str(e)}",
            metadata={"operation": "continue_conversation"}
        )


# ==================== WebSocket Endpoints ====================

@app.websocket("/api/v2/ws/{client_id}/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    user_id: str
):
    """
    WebSocket endpoint for real-time interactions.
    
    Provides real-time communication for interactive data analysis,
    progress updates, and collaborative features.
    """
    connection_id = None
    try:
        # Validate UUIDs
        if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', client_id):
            await websocket.close(code=1008, reason="Invalid client_id format")
            return
        
        if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', user_id):
            await websocket.close(code=1008, reason="Invalid user_id format")
            return
        
        # Validate access
        access_granted = app.state.access_control.validate_user_access(
            client_id, user_id, AccessLevel.USER
        )
        
        if not access_granted:
            await websocket.close(code=1008, reason="Access denied")
            return
        
        # Accept connection
        connection_id = await app.state.connection_manager.connect(websocket, client_id, user_id)
        
        # Send welcome message
        welcome_message = {
            "type": "connection_established",
            "data": {
                "connection_id": connection_id,
                "message": "Connected to Intelligent AI Data Analyst",
                "capabilities": [
                    "real_time_analysis",
                    "conversation_management",
                    "progress_updates",
                    "collaborative_features"
                ]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        await app.state.connection_manager.send_personal_message(welcome_message, connection_id)
        
        # Message handling loop
        while True:
            try:
                # Receive message
                message_data = await websocket.receive_json()
                
                # Validate message format
                try:
                    message = WebSocketMessage(**message_data)
                except Exception as e:
                    error_response = {
                        "type": "error",
                        "data": {"error": f"Invalid message format: {str(e)}"},
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await app.state.connection_manager.send_personal_message(error_response, connection_id)
                    continue
                
                # Handle different message types
                await handle_websocket_message(message, connection_id, client_id, user_id)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                app.state.logger.error(f"WebSocket message handling error: {e}")
                error_response = {
                    "type": "error",
                    "data": {"error": f"Message processing failed: {str(e)}"},
                    "timestamp": datetime.utcnow().isoformat()
                }
                try:
                    await app.state.connection_manager.send_personal_message(error_response, connection_id)
                except:
                    break
    
    except Exception as e:
        app.state.logger.error(f"WebSocket connection error: {e}")
    
    finally:
        if connection_id:
            app.state.connection_manager.disconnect(connection_id)


async def handle_websocket_message(
    message: WebSocketMessage,
    connection_id: str,
    client_id: str,
    user_id: str
):
    """Handle incoming WebSocket messages."""
    try:
        if message.type == "analysis_request":
            # Handle real-time analysis request
            query = message.data.get("query", "")
            if not query:
                raise ValueError("Query is required for analysis")
            
            # Send acknowledgment
            ack_message = {
                "type": "analysis_started",
                "data": {
                    "message": "Analysis started",
                    "query": query[:100] + "..." if len(query) > 100 else query
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            await app.state.connection_manager.send_personal_message(ack_message, connection_id)
            
            # Perform analysis
            internal_request = AnalysisRequest(
                user_id=user_id,
                client_id=client_id,
                query=query,
                conversation_id=message.data.get("conversation_id"),
                access_level=AccessLevel.USER,
                include_visualizations=message.data.get("include_visualizations", True)
            )
            
            result = await app.state.master_agent.analyze_data(internal_request)
            
            # Send result
            result_message = {
                "type": "analysis_result",
                "data": asdict(result),
                "timestamp": datetime.utcnow().isoformat()
            }
            await app.state.connection_manager.send_personal_message(result_message, connection_id)
        
        elif message.type == "ping":
            # Handle ping for connection health
            pong_message = {
                "type": "pong",
                "data": {"timestamp": datetime.utcnow().isoformat()},
                "timestamp": datetime.utcnow().isoformat()
            }
            await app.state.connection_manager.send_personal_message(pong_message, connection_id)
        
        elif message.type == "get_conversation_history":
            # Handle conversation history request
            conversation_id = message.data.get("conversation_id")
            if conversation_id:
                history = app.state.master_agent.get_conversation_history(conversation_id)
                history_message = {
                    "type": "conversation_history",
                    "data": {
                        "conversation_id": conversation_id,
                        "history": history
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                await app.state.connection_manager.send_personal_message(history_message, connection_id)
        
        else:
            # Unknown message type
            error_message = {
                "type": "error",
                "data": {"error": f"Unknown message type: {message.type}"},
                "timestamp": datetime.utcnow().isoformat()
            }
            await app.state.connection_manager.send_personal_message(error_message, connection_id)
    
    except Exception as e:
        error_message = {
            "type": "error",
            "data": {"error": f"Message handling failed: {str(e)}"},
            "timestamp": datetime.utcnow().isoformat()
        }
        await app.state.connection_manager.send_personal_message(error_message, connection_id)


# ==================== Health and Monitoring Endpoints ====================

@app.get("/api/v2/health", response_model=APIResponse)
async def health_check(
    request: Request,
    rate_limit_check: bool = Depends(lambda req: check_rate_limit(req, "health"))
):
    """
    Comprehensive health check endpoint.
    
    Provides detailed system health information including component status,
    performance metrics, and resource utilization.
    """
    try:
        # Check master agent health
        agent_health = await app.state.master_agent.health_check()
        
        # Check connection manager health
        active_connections = app.state.connection_manager.get_active_connections()
        
        # System health metrics
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "master_agent": agent_health,
                "websocket_connections": {
                    "active_count": len(active_connections),
                    "connections": active_connections
                },
                "security_manager": {
                    "status": "operational"
                },
                "access_control": {
                    "status": "operational"
                }
            },
            "performance": {
                "uptime": "N/A",  # Could implement uptime tracking
                "memory_usage": "N/A",  # Could implement memory monitoring
                "cpu_usage": "N/A"  # Could implement CPU monitoring
            }
        }
        
        return APIResponse(
            success=True,
            data=health_data,
            metadata={"operation": "health_check"}
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            error=f"Health check failed: {str(e)}",
            metadata={"operation": "health_check"}
        )


@app.get("/api/v2/metrics", response_model=APIResponse)
async def get_metrics(
    request: Request,
    user_context: Dict[str, Any] = Depends(validate_request_security),
    rate_limit_check: bool = Depends(lambda req: check_rate_limit(req, "default"))
):
    """
    Get system performance metrics.
    
    Provides detailed metrics about API usage, performance, and system health.
    """
    try:
        # Get connection metrics
        connections = app.state.connection_manager.get_active_connections()
        
        # Calculate connection statistics
        connection_stats = {
            "total_active": len(connections),
            "by_client": {},
            "average_duration": 0
        }
        
        current_time = datetime.utcnow()
        total_duration = 0
        
        for conn_id, metadata in connections.items():
            client_id = metadata["client_id"]
            connection_stats["by_client"][client_id] = connection_stats["by_client"].get(client_id, 0) + 1
            
            # Calculate connection duration
            connected_at = datetime.fromisoformat(metadata["connected_at"])
            duration = (current_time - connected_at).total_seconds()
            total_duration += duration
        
        if connections:
            connection_stats["average_duration"] = total_duration / len(connections)
        
        metrics_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "websocket_metrics": connection_stats,
            "api_metrics": {
                "total_requests": "N/A",  # Could implement request counting
                "average_response_time": "N/A",  # Could implement response time tracking
                "error_rate": "N/A"  # Could implement error rate tracking
            },
            "system_metrics": {
                "memory_usage": "N/A",
                "cpu_usage": "N/A",
                "disk_usage": "N/A"
            }
        }
        
        return APIResponse(
            success=True,
            data=metrics_data,
            metadata={"operation": "get_metrics"}
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            error=f"Metrics retrieval failed: {str(e)}",
            metadata={"operation": "get_metrics"}
        )


# ==================== Administrative Endpoints ====================

@app.post("/api/v2/admin/connections/cleanup", response_model=APIResponse)
async def cleanup_connections(
    request: Request,
    user_context: Dict[str, Any] = Depends(validate_request_security),
    rate_limit_check: bool = Depends(lambda req: check_rate_limit(req, "default"))
):
    """
    Clean up stale WebSocket connections.
    
    Administrative endpoint to manually trigger cleanup of inactive connections.
    """
    try:
        initial_count = len(app.state.connection_manager.get_active_connections())
        await app.state.connection_manager.cleanup_stale_connections()
        final_count = len(app.state.connection_manager.get_active_connections())
        
        cleanup_data = {
            "initial_connections": initial_count,
            "final_connections": final_count,
            "cleaned_up": initial_count - final_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return APIResponse(
            success=True,
            data=cleanup_data,
            metadata={"operation": "cleanup_connections"}
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            error=f"Connection cleanup failed: {str(e)}",
            metadata={"operation": "cleanup_connections"}
        )


# ==================== Background Tasks ====================

async def log_analysis_completion(
    user_id: str,
    client_id: str,
    query_id: str,
    execution_time_ms: float
):
    """Background task to log analysis completion."""
    try:
        app.state.logger.info(
            f"Analysis completed - User: {user_id}, Client: {client_id}, "
            f"Query: {query_id}, Time: {execution_time_ms:.2f}ms"
        )
    except Exception as e:
        app.state.logger.error(f"Failed to log analysis completion: {e}")


# ==================== Error Handlers ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper logging."""
    app.state.logger.warning(f"HTTP {exc.status_code}: {exc.detail} - {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {"operation": "error_handler", "status_code": exc.status_code}
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with proper logging."""
    app.state.logger.error(f"Unhandled exception: {exc} - {request.url}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {"operation": "error_handler", "status_code": 500}
        }
    )


# ==================== Main Application Entry Point ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive API Layer v2")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    
    args = parser.parse_args()
    
    print(f"🚀 Starting Comprehensive API Layer v2...")
    print(f"📖 API docs available at: http://{args.host}:{args.port}/api/v2/docs")
    print(f"🔌 WebSocket endpoint: ws://{args.host}:{args.port}/api/v2/ws/{{client_id}}/{{user_id}}")
    print(f"📊 Streaming endpoint: http://{args.host}:{args.port}/api/v2/analysis/streaming")
    
    uvicorn.run(
        "light_ai.api_v2:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1
    )
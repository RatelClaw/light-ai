#!/usr/bin/env python3
"""
Demo script for Comprehensive API Layer v2.

Demonstrates the key features of the new API layer including:
- RESTful endpoints
- Request validation
- Rate limiting
- Security features
- WebSocket capabilities (conceptual)
"""

import asyncio
import json
import uuid
from datetime import datetime

from light_ai.api_v2 import (
    create_comprehensive_api, 
    APIResponse, 
    AnalysisAPIRequest,
    SecurityValidator,
    SimpleRateLimiter,
    ConnectionManager
)
from light_ai.config import Config


def demo_api_creation():
    """Demonstrate API creation and basic setup."""
    print("🚀 Creating Comprehensive API Layer v2...")
    
    config = Config.load()
    app = create_comprehensive_api(config)
    
    print(f"✅ API created successfully!")
    print(f"   Title: {app.title}")
    print(f"   Version: {app.version}")
    print(f"   Docs URL: {app.docs_url}")
    print()
    
    return app


def demo_request_validation():
    """Demonstrate request validation and sanitization."""
    print("🔍 Testing Request Validation...")
    
    # Valid request
    valid_data = {
        "client_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "query": "What are the sales trends for Q4?",
        "access_level": "user",
        "include_visualizations": True
    }
    
    try:
        request = AnalysisAPIRequest(**valid_data)
        print(f"✅ Valid request created:")
        print(f"   Client ID: {request.client_id}")
        print(f"   Query: {request.query}")
        print(f"   Access Level: {request.access_level}")
    except Exception as e:
        print(f"❌ Request validation failed: {e}")
    
    # Invalid request (bad UUID)
    try:
        invalid_data = valid_data.copy()
        invalid_data["client_id"] = "invalid-uuid"
        request = AnalysisAPIRequest(**invalid_data)
        print("❌ Should have failed validation!")
    except Exception as e:
        print(f"✅ Invalid request properly rejected: {type(e).__name__}")
    
    print()


def demo_security_validator():
    """Demonstrate security validation features."""
    print("🔒 Testing Security Validation...")
    
    validator = SecurityValidator()
    
    # Test JSON payload validation
    valid_payload = {
        "user_query": "Show me sales data",
        "filters": {"region": "US", "year": 2024}
    }
    
    deep_payload = {"level1": {"level2": {"level3": {"level4": {"level5": {
        "level6": {"level7": {"level8": {"level9": {"level10": {
            "level11": "too deep"
        }}}}}}}}}}}
    
    print(f"✅ Valid payload validation: {validator.validate_json_payload(valid_payload)}")
    print(f"✅ Deep payload validation: {validator.validate_json_payload(deep_payload)}")
    
    # Test header sanitization
    headers = {
        "Content-Type": "application/json",
        "X-Custom-Header": "safe_value",
        "Dangerous<Script>": "alert('xss')",
        "": "empty_key"
    }
    
    sanitized = validator.sanitize_headers(headers)
    print(f"✅ Headers sanitized: {len(sanitized)} safe headers from {len(headers)} original")
    print(f"   Safe headers: {list(sanitized.keys())}")
    print()


def demo_rate_limiter():
    """Demonstrate rate limiting functionality."""
    print("⏱️  Testing Rate Limiting...")
    
    limiter = SimpleRateLimiter()
    
    # Test normal usage
    client_key = "demo_client_123"
    
    print("Testing analysis endpoint limits (10/minute):")
    for i in range(12):
        allowed = limiter.is_allowed(client_key, "analysis")
        status = "✅ Allowed" if allowed else "❌ Rate limited"
        print(f"   Request {i+1}: {status}")
        if i == 9:  # After 10 requests
            print("   --- Rate limit should kick in now ---")
    
    print()
    
    # Test different endpoint
    print("Testing health endpoint limits (60/minute):")
    health_allowed = limiter.is_allowed(client_key, "health")
    print(f"   Health check: {'✅ Allowed' if health_allowed else '❌ Rate limited'}")
    print()


def demo_connection_manager():
    """Demonstrate WebSocket connection management."""
    print("🔌 Testing WebSocket Connection Manager...")
    
    manager = ConnectionManager()
    
    # Simulate connection metadata
    client_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    # Add some mock connection metadata
    connection_id = f"{client_id}_{user_id}_{int(datetime.now().timestamp())}"
    manager.connection_metadata[connection_id] = {
        "client_id": client_id,
        "user_id": user_id,
        "connected_at": datetime.utcnow().isoformat(),
        "last_activity": datetime.utcnow().isoformat()
    }
    
    connections = manager.get_active_connections()
    print(f"✅ Connection manager initialized")
    print(f"   Active connections: {len(connections)}")
    
    if connections:
        conn_info = list(connections.values())[0]
        print(f"   Sample connection: Client {conn_info['client_id'][:8]}...")
    
    print()


def demo_api_response():
    """Demonstrate API response formatting."""
    print("📤 Testing API Response Formatting...")
    
    # Success response
    success_response = APIResponse(
        success=True,
        data={
            "query_id": "demo_query_123",
            "results": [
                {"product": "Widget A", "sales": 1500},
                {"product": "Widget B", "sales": 2300}
            ],
            "insights": [
                "Widget B outperformed Widget A by 53%",
                "Total sales increased compared to last quarter"
            ]
        },
        metadata={
            "operation": "analysis",
            "execution_time_ms": 245.7,
            "sources_used": 2
        }
    )
    
    print("✅ Success response created:")
    print(f"   Success: {success_response.success}")
    print(f"   Results count: {len(success_response.data['results'])}")
    print(f"   Insights: {len(success_response.data['insights'])}")
    print(f"   Execution time: {success_response.metadata['execution_time_ms']}ms")
    
    # Error response
    error_response = APIResponse(
        success=False,
        error="Invalid query: missing required parameters",
        metadata={
            "operation": "analysis",
            "error_code": "VALIDATION_ERROR"
        }
    )
    
    print("✅ Error response created:")
    print(f"   Success: {error_response.success}")
    print(f"   Error: {error_response.error}")
    print()


async def demo_async_features():
    """Demonstrate async features (conceptual)."""
    print("⚡ Testing Async Features...")
    
    # Simulate async analysis
    print("   Simulating async analysis request...")
    await asyncio.sleep(0.1)  # Simulate processing time
    
    print("✅ Async processing completed")
    print("   Real implementation would:")
    print("   - Process natural language queries")
    print("   - Execute AI agent analysis")
    print("   - Stream large result sets")
    print("   - Handle WebSocket real-time updates")
    print()


def main():
    """Run the comprehensive demo."""
    print("=" * 60)
    print("🎯 Comprehensive API Layer v2 Demo")
    print("=" * 60)
    print()
    
    # Demo each component
    app = demo_api_creation()
    demo_request_validation()
    demo_security_validator()
    demo_rate_limiter()
    demo_connection_manager()
    demo_api_response()
    
    # Run async demo
    asyncio.run(demo_async_features())
    
    print("=" * 60)
    print("🎉 Demo completed successfully!")
    print()
    print("Key Features Demonstrated:")
    print("✅ RESTful API creation with FastAPI")
    print("✅ Comprehensive request validation and sanitization")
    print("✅ Security validation and header sanitization")
    print("✅ Rate limiting and abuse prevention")
    print("✅ WebSocket connection management")
    print("✅ Standardized API response formatting")
    print("✅ Async processing capabilities")
    print()
    print("Next Steps:")
    print("🚀 Start the API server: python -m light_ai.api_v2")
    print("📖 View API docs: http://localhost:8001/api/v2/docs")
    print("🔌 WebSocket endpoint: ws://localhost:8001/api/v2/ws/{client_id}/{user_id}")
    print("📊 Streaming endpoint: http://localhost:8001/api/v2/analysis/streaming")
    print("=" * 60)


if __name__ == "__main__":
    main()
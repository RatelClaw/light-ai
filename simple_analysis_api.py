#!/usr/bin/env python3
"""
Simple Analysis API - A lightweight wrapper for external server calls.

This provides a simple REST API that calls the master agent directly,
just like the Streamlit UI does. No complex dependencies or validation.

Usage:
    python simple_analysis_api.py

Then call from any server:
    POST http://127.0.0.1:5000/analyze
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from light_ai.agents.master_agent import MasterDataAnalystAgent, AnalysisRequest
from light_ai.core.models import AccessLevel
from light_ai.config import get_config

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Initialize the master agent
config = get_config()
agent = MasterDataAnalystAgent(config)

print("✅ Simple Analysis API initialized")
print("📊 Master agent ready")


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "Simple Analysis API",
        "version": "1.0.0"
    })


@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Analyze user data and extract insights.
    
    Request body:
    {
        "client_id": "uuid",
        "user_id": "uuid",
        "query": "your analysis query",
        "desired_fields": {"field": "description"} (optional),
        "optional_fields": {"field": "description"} (optional)
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400
        
        client_id = data.get('client_id')
        user_id = data.get('user_id')
        query = data.get('query')
        
        if not client_id or not user_id or not query:
            return jsonify({
                "success": False,
                "error": "Missing required fields: client_id, user_id, query"
            }), 400
        
        # Create analysis request (same as Streamlit does)
        analysis_request = AnalysisRequest(
            user_id=user_id,
            client_id=client_id,
            query=query,
            desired_fields=data.get('desired_fields', {
                "persona": "Extract detailed persona characteristics, personality traits, demographics, interests, and behavioral patterns",
                "context": "Provide contextual information about the user's situation, environment, and circumstances"
            }),
            optional_fields=data.get('optional_fields', {
                "insights": "Generate insights about the user's patterns and preferences",
                "recommendations": "Provide personalized recommendations based on the analysis"
            }),
            access_level=AccessLevel.USER,
            include_visualizations=data.get('include_visualizations', True)
        )
        
        # Run the analysis using asyncio (same as Streamlit)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(agent.analyze_data(analysis_request))
        finally:
            loop.close()
        
        # Format response
        if result and (result.results or result.insights):
            response = {
                "success": True,
                "data": {
                    "persona": result.insights[0] if result.insights else "Persona analysis completed",
                    "context": result.methodology if result.methodology else "Context extracted",
                    "insights": "; ".join(result.insights) if result.insights else "Insights generated",
                    "recommendations": "; ".join(result.follow_up_suggestions) if result.follow_up_suggestions else "Recommendations provided",
                    "data_summary": {
                        "sources_used": len(result.sources_used) if result.sources_used else 0,
                        "confidence_score": result.confidence_score if hasattr(result, 'confidence_score') else 0.8,
                        "execution_time_ms": result.execution_time_ms if hasattr(result, 'execution_time_ms') else 0,
                        "field_mappings": result.field_mappings if hasattr(result, 'field_mappings') else None
                    },
                    "analysis_method": "AI Agent System with Intelligent Field Extraction"
                }
            }
            return jsonify(response), 200
        else:
            return jsonify({
                "success": False,
                "error": "AI agent analysis returned no results"
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Analysis failed: {str(e)}"
        }), 500


@app.route('/analyze/simple', methods=['POST'])
def analyze_simple():
    """
    Simplified analysis endpoint with minimal response.
    
    Request body:
    {
        "client_id": "uuid",
        "user_id": "uuid",
        "query": "your analysis query"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "No JSON data provided"}), 400
        
        client_id = data.get('client_id')
        user_id = data.get('user_id')
        query = data.get('query')
        
        if not client_id or not user_id or not query:
            return jsonify({
                "success": False,
                "error": "Missing required fields: client_id, user_id, query"
            }), 400
        
        # Create simple analysis request
        analysis_request = AnalysisRequest(
            user_id=user_id,
            client_id=client_id,
            query=query,
            access_level=AccessLevel.USER,
            include_visualizations=False
        )
        
        # Run analysis
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(agent.analyze_data(analysis_request))
        finally:
            loop.close()
        
        # Simple response
        if result:
            return jsonify({
                "success": True,
                "insights": result.insights if result.insights else [],
                "recommendations": result.follow_up_suggestions if result.follow_up_suggestions else [],
                "confidence": result.confidence_score if hasattr(result, 'confidence_score') else 0.8
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "No results"
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple Analysis API Server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    print(f"\n🚀 Starting Simple Analysis API on http://{args.host}:{args.port}")
    print(f"📖 Endpoints:")
    print(f"   • POST /analyze - Full analysis with persona extraction")
    print(f"   • POST /analyze/simple - Simple analysis with minimal response")
    print(f"   • GET /health - Health check")
    print(f"\n💡 Example curl command:")
    print(f'   curl -X POST "http://{args.host}:{args.port}/analyze" \\')
    print(f'     -H "Content-Type: application/json" \\')
    print(f'     -d \'{{"client_id": "your-uuid", "user_id": "your-uuid", "query": "analyze this user"}}\'')
    print(f"\n⏹️  Press Ctrl+C to stop\n")
    
    app.run(host=args.host, port=args.port, debug=args.debug)

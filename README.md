# Universal Data Handler

A comprehensive on-premises data management system with automated ingestion, cleaning, and intelligent retrieval capabilities.

## Features

- **Universal File Upload**: Support for CSV, Excel, JSON, PDF, TXT, and more
- **Automatic Data Cleaning**: Intelligent preprocessing and normalization
- **Multi-Database Storage**: DuckDB for structured data, ChromaDB for embeddings, SQLite for metadata
- **Natural Language Queries**: Ask questions about your data in plain English
- **Semantic Search**: Find relevant information across unstructured documents
- **AI Data Analyst**: Get insights and analysis from your data
- **Complete API**: RESTful interface for all functionality

## Quick Start

### 1. Install Dependencies
```bash
uv sync
```

If you want to use the Simple Analysis API, make sure Flask is installed:
```bash
pip install flask flask-cors
```

### 2. Set Up Environment
```bash
cp .env.example .env
# Add your OpenRouter API key to .env
```

### 3. Start the Servers
```bash
python start_servers.py
```

This starts:
- **API v1** (Data Upload): http://127.0.0.1:8000/docs
- **API v2** (Analysis): http://127.0.0.1:8001/api/v2/docs

### 4. Launch Streamlit UI (Optional)
In a separate terminal:
```bash
streamlit run streamlit_data_handler_ui.py
```

## Usage Workflows

### Option 1: Using Streamlit UI (Easiest)

1. Start servers: `python start_servers.py`
2. Start Streamlit: `streamlit run streamlit_data_handler_ui.py`
3. Open browser to http://localhost:8501
4. Enter Client ID and User ID (or generate new ones)
5. Upload JSON data in the "Upload Data" tab
6. Run analysis in the "Analysis" tab

### Option 2: Using Simple Analysis API (For External Servers)

This is a lightweight API that works exactly like the Streamlit UI - perfect for calling from other servers/applications.

**Start the Simple API:**
```bash
python simple_analysis_api.py
```

This starts a Flask server on http://127.0.0.1:5000

**Step 1: Upload data to API v1 (same as before)**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/upload/json" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "123e4567-e89b-12d3-a456-426614174007",
    "json_data": {
      "student_profile": {
        "name": "S Roy",
        "program": "Computer Science",
        "gpa": 3.75,
        "interests": ["AI", "Web Development"]
      }
    },
    "resource_name": "student_data",
    "flatten": false
  }'
```

**Step 2: Run analysis using Simple API**
```bash
curl -X POST "http://127.0.0.1:5000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "123e4567-e89b-12d3-a456-426614174007",
    "query": "Extract persona characteristics and provide insights about this student"
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "persona": "Computer Science student with strong academic performance...",
    "context": "Academic environment focused on technology...",
    "insights": "High GPA indicates strong performance; Interest in AI and Web Development...",
    "recommendations": "Consider advanced courses in AI; Explore web development projects...",
    "data_summary": {
      "sources_used": 1,
      "confidence_score": 0.85,
      "execution_time_ms": 1250
    }
  }
}
```

**For simpler response:**
```bash
curl -X POST "http://127.0.0.1:5000/analyze/simple" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "123e4567-e89b-12d3-a456-426614174007",
    "query": "What are the key insights about this student?"
  }'
```

### Option 3: Using API Endpoints Directly

#### Step 1: Upload JSON Data

**Endpoint:** `POST http://127.0.0.1:8000/api/v1/upload/json`

**Request Body:**
```json
{
  "client_id": "your-client-uuid",
  "user_id": "your-user-uuid",
  "json_data": {
    "user_profile": {
      "name": "John Doe",
      "age": 30,
      "interests": ["AI", "Data Science"]
    }
  },
  "resource_name": "user_data",
  "flatten": false
}
```

**Example with curl:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/upload/json" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "123e4567-e89b-12d3-a456-426614174007",
    "json_data": {
      "student_profile": {
        "name": "Alice Johnson",
        "program": "Computer Science",
        "gpa": 3.75,
        "interests": ["AI", "Web Development"]
      }
    },
    "resource_name": "student_data",
    "flatten": false
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "resource_id": "abc123...",
    "resource_name": "student_data",
    "resource_type": "json",
    "version": 1
  }
}
```

#### Step 2: Run Analysis

**Endpoint:** `POST http://127.0.0.1:8001/api/v2/analysis`

**Request Body:**
```json
{
  "client_id": "your-client-uuid",
  "user_id": "your-user-uuid",
  "query": "Analyze the user's profile and extract persona characteristics",
  "access_level": "user",
  "include_visualizations": true
}
```

**Example with curl:**
```bash
curl -X POST "http://127.0.0.1:8001/api/v2/analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "123e4567-e89b-12d3-a456-426614174007",
    "query": "Extract persona characteristics and provide insights about this student",
    "access_level": "user",
    "include_visualizations": true
  }'
```

**Note:** If you encounter validation errors with the API v2 endpoint, use the **Streamlit UI** instead (recommended method). The Streamlit UI at `streamlit_data_handler_ui.py` handles analysis internally using the master agent and provides a user-friendly interface.

Alternatively, you can use the master agent directly in Python:
```python
from light_ai.agents.master_agent import MasterDataAnalystAgent, AnalysisRequest
from light_ai.core.models import AccessLevel
from light_ai.config import get_config
import asyncio

config = get_config()
agent = MasterDataAnalystAgent(config)

request = AnalysisRequest(
    user_id="123e4567-e89b-12d3-a456-426614174007",
    client_id="123e4567-e89b-12d3-a456-426614174000",
    query="Extract persona characteristics and provide insights",
    access_level=AccessLevel.USER,
    include_visualizations=True
)

result = asyncio.run(agent.analyze_data(request))
print(result)
```

**Response:**
```json
{
  "success": true,
  "data": {
    "results": {
      "persona": "Student profile analysis...",
      "insights": ["High academic performance", "Interest in technology"],
      "recommendations": ["Consider advanced AI courses"]
    },
    "confidence_score": 0.85,
    "execution_time_ms": 1250
  }
}
```

#### Step 3: List User Resources

**Endpoint:** `GET http://127.0.0.1:8000/api/v1/resources`

**Query Parameters:**
- `client_id`: Your client UUID
- `user_id`: Your user UUID
- `access_level`: user/manager/admin

**Example with curl:**
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/resources?client_id=123e4567-e89b-12d3-a456-426614174000&user_id=123e4567-e89b-12d3-a456-426614174001&access_level=user"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "resources": [
      {
        "resource_id": "abc123...",
        "resource_name": "student_data",
        "resource_type": "json",
        "file_size_bytes": 1024,
        "created_at": "2026-01-15T10:30:00",
        "version": 1
      }
    ],
    "total_count": 1
  }
}
```

## API Documentation

- **API v1 (Data Management)**: http://127.0.0.1:8000/docs
  - Upload files and JSON data
  - Manage resources
  - Query structured data
  
- **API v2 (AI Analysis)**: http://127.0.0.1:8001/api/v2/docs
  - AI-powered data analysis (complex dependencies)
  - Persona extraction
  - Intelligent insights

- **Simple Analysis API**: http://127.0.0.1:5000
  - Lightweight Flask API for external servers
  - Direct master agent calls (same as Streamlit)
  - No complex dependencies
  - Perfect for integration with other applications

## Quick Reference

| Task | Recommended Method | Command |
|------|-------------------|---------|
| Upload Data | API v1 | `curl -X POST http://127.0.0.1:8000/api/v1/upload/json` |
| Run Analysis (UI) | Streamlit | `streamlit run streamlit_data_handler_ui.py` |
| Run Analysis (API) | Simple API | `curl -X POST http://127.0.0.1:5000/analyze` |
| List Resources | API v1 | `curl -X GET http://127.0.0.1:8000/api/v1/resources` |
| Health Check | Simple API | `curl http://127.0.0.1:5000/health` |

## Testing

Test the complete workflow:
```bash
# 1. Start all servers
python start_servers.py

# 2. In another terminal, start Simple API
python simple_analysis_api.py

# 3. In another terminal, run the test
./test_simple_api.sh
```

Or use the Python client example:
```bash
python example_simple_api_client.py
```

## Integration Example

To integrate with your own application:

```python
from example_simple_api_client import SimpleAnalysisClient

# Initialize client
client = SimpleAnalysisClient()

# Upload data
result, status = client.upload_json_data(
    client_id="your-client-id",
    user_id="your-user-id",
    json_data={"user_data": {...}},
    resource_name="my_data"
)

# Run analysis
analysis, status = client.analyze(
    client_id="your-client-id",
    user_id="your-user-id",
    query="Analyze this user's profile"
)

print(analysis["data"]["insights"])
```

## Architecture

The system is built with two main layers:
- **Sub-Layer 1**: Data Ingestion & Storage
- **Sub-Layer 2**: Data Retrieval & Analysis

See `.kiro/specs/universal-data-handler/` for detailed documentation.
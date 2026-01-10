# Universal Data Handler - Setup and Testing Guide

This guide provides step-by-step instructions to run the complete Universal Data Handler system with both APIs and Streamlit UI.

## 🚀 Quick Start

### Step 1: Start the Servers

```bash
# Activate virtual environment
source .venv/bin/activate

# Start both API servers (v1 and v2)
python start_servers.py
```

This will start:
- **API v1** on port 8000 (Basic functionality)
- **API v2** on port 8001 (Advanced analysis features)

### Step 2: Start Streamlit UI (in another terminal)

```bash
# Activate virtual environment
source .venv/bin/activate

# Start Streamlit UI
streamlit run streamlit_data_handler_ui.py
```

The UI will be available at: http://localhost:8501

### Step 3: Test the Complete Workflow

```bash
# In another terminal, run the automated test
python test_complete_workflow.py
```

## 📋 Detailed Instructions

### Prerequisites

1. **Virtual Environment**: Make sure your virtual environment is activated
   ```bash
   source .venv/bin/activate
   ```

2. **Dependencies**: Ensure all dependencies are installed
   ```bash
   pip install -r requirements.txt  # if you have one
   # or install manually:
   pip install fastapi uvicorn streamlit requests pandas
   ```

### Manual Server Startup (Alternative)

If you prefer to start servers manually:

```bash
# Terminal 1: API v1
source .venv/bin/activate
python -m light_ai.fastapi_server --port 8000

# Terminal 2: API v2  
source .venv/bin/activate
python -m light_ai.api_v2 --port 8001

# Terminal 3: Streamlit UI
source .venv/bin/activate
streamlit run streamlit_data_handler_ui.py
```

## 🧪 Testing Scenarios

### Scenario 1: Using the Streamlit UI

1. **Open the UI**: http://localhost:8501
2. **Generate IDs**: Click "Generate New IDs" in the sidebar
3. **Upload Data**: 
   - Go to "Upload Data" tab
   - Click "Student Data" for sample data
   - Click "Upload Data"
4. **Run Analysis**:
   - Go to "Analysis" tab
   - Click "Get User Persona" or enter custom query
   - Click "Run Analysis"
5. **View Results**: Check the "View Data" tab

### Scenario 2: Using the Test Script

```bash
python test_complete_workflow.py
```

This will:
- Test API connections
- Upload sample education data
- Retrieve the uploaded data
- Run persona analysis
- Display comprehensive results

### Scenario 3: Manual API Testing

#### Upload Data (API v1):
```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/upload/json' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "client_id": "your-client-id",
    "user_id": "your-user-id",
    "json_data": {
      "student_profile": {
        "student_id": "STU-001",
        "name": "Alice Johnson",
        "program": "Computer Science",
        "gpa": 3.75
      }
    },
    "resource_name": "test_student_data",
    "flatten": false
  }'
```

#### Run Analysis (API v2):
```bash
curl -X 'POST' \
  'http://localhost:8001/api/v2/analysis' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "client_id": "your-client-id",
    "user_id": "your-user-id",
    "query": "Get the persona and context of this student",
    "desired_fields": {
      "persona": "Extract persona characteristics",
      "context": "Provide contextual information"
    },
    "access_level": "user",
    "include_visualizations": true,
    "streaming": false
  }'
```

## 🔧 Troubleshooting

### Common Issues

1. **Import Error: attempted relative import with no known parent package**
   - **Solution**: Use `python -m light_ai.api_v2` instead of `python light_ai/api_v2.py`

2. **Port Already in Use**
   - **Solution**: Kill existing processes or use different ports
   ```bash
   lsof -ti:8000 | xargs kill -9
   lsof -ti:8001 | xargs kill -9
   ```

3. **Virtual Environment Not Activated**
   - **Solution**: Always activate before running
   ```bash
   source .venv/bin/activate
   ```

4. **API Connection Refused**
   - **Solution**: Ensure servers are running and ports are correct

### Checking Server Status

```bash
# Check if servers are running
curl http://localhost:8000/health
curl http://localhost:8001/api/v2/health

# Check processes
ps aux | grep python
```

## 📊 API Documentation

- **API v1 (Basic)**: http://localhost:8000/docs
- **API v2 (Advanced)**: http://localhost:8001/api/v2/docs

## 🎯 Sample Data for Testing

### Student Data
```json
{
  "student_profile": {
    "student_id": "STU-001",
    "name": "Alice Johnson",
    "program": "Computer Science",
    "year_level": "Junior",
    "age": 21,
    "gpa": 3.75,
    "interests": ["AI", "Web Development"],
    "career_goals": "Software Engineer"
  }
}
```

### Business User Data
```json
{
  "business_profile": {
    "user_id": "BUS-001",
    "name": "John Smith",
    "role": "Marketing Manager",
    "department": "Marketing",
    "experience_years": 8,
    "skills": ["Digital Marketing", "Analytics"]
  }
}
```

## 🔄 Complete Workflow

1. **Start Servers**: `python start_servers.py`
2. **Start UI**: `streamlit run streamlit_data_handler_ui.py`
3. **Upload Data**: Use UI or API to upload JSON data
4. **Run Analysis**: Use API v2 to get persona/context analysis
5. **View Results**: Check analysis results and data overview

## 📝 Notes

- The system uses UUID-based client and user IDs for data isolation
- Data is stored locally in SQLite databases
- Analysis uses AI agents for persona extraction and context analysis
- All APIs support CORS for web-based access

## 🆘 Support

If you encounter issues:
1. Check server logs in the terminal
2. Verify virtual environment is activated
3. Ensure all dependencies are installed
4. Check API documentation for correct request formats
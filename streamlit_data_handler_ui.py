#!/usr/bin/env python3
"""
Streamlit UI for Universal Data Handler
Provides a simple interface to upload data and get persona/context analysis
"""

import streamlit as st
import requests
import json
import uuid
from datetime import datetime
import pandas as pd

# Configuration
API_V1_BASE = "http://127.0.0.1:8000/api/v1"
API_V2_BASE = "http://127.0.0.1:8001/api/v2"

def generate_uuid():
    """Generate a new UUID"""
    return str(uuid.uuid4())

def upload_json_data(client_id, user_id, json_data, resource_name):
    """Upload JSON data to API v1"""
    url = f"{API_V1_BASE}/upload/json"
    payload = {
        "client_id": client_id,
        "user_id": user_id,
        "json_data": json_data,
        "resource_name": resource_name,
        "flatten": False
    }
    
    try:
        response = requests.post(url, json=payload)
        return response.json(), response.status_code
    except Exception as e:
        return {"error": str(e)}, 500

def get_persona_analysis(client_id, user_id, query):
    """Get persona and context analysis using the new enhanced analysis agent"""
    try:
        # Import the enhanced analysis agent
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent.parent))
        
        from light_ai.agents.enhanced_analysis_agent import get_analysis_agent, AnalysisRequest
        
        # Create analysis request
        request = AnalysisRequest(
            client_id=client_id,
            user_id=user_id,
            query=query,
            desired_fields={
                "persona": "Extract detailed persona characteristics",
                "context": "Provide contextual information"
            },
            optional_fields={
                "insights": "Generate insights from the data",
                "recommendations": "Provide recommendations"
            }
        )
        
        # Get the analysis agent and perform analysis
        agent = get_analysis_agent()
        result = agent.analyze_user_data(request)
        
        if result.success:
            formatted_result = {
                "success": True,
                "data": {
                    "persona": result.persona or "Persona analysis completed",
                    "context": result.context or "Context information extracted",
                    "insights": result.insights or "Insights generated from available data",
                    "recommendations": result.recommendations or "Recommendations provided",
                    "data_summary": result.data_summary,
                    "analysis_method": "Enhanced Analysis Agent with Direct Data Access"
                }
            }
            return formatted_result, 200
        else:
            return {"success": False, "error": result.error}, 400
            
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}, 500

def get_user_resources(client_id, user_id):
    """Get all resources for a user"""
    url = f"{API_V1_BASE}/resources"
    params = {
        "client_id": client_id,
        "user_id": user_id,
        "access_level": "user"
    }
    
    try:
        response = requests.get(url, params=params)
        result = response.json()
        
        # Handle the response properly
        if response.status_code == 200 and result.get("success"):
            resources = result.get("data", [])
            # Ensure resources is a list and handle string items
            if isinstance(resources, list):
                processed_resources = []
                for resource in resources:
                    if isinstance(resource, dict):
                        processed_resources.append(resource)
                    else:
                        # Handle string or other types
                        processed_resources.append({
                            "resource_id": str(resource),
                            "resource_name": "Unknown",
                            "resource_type": "Unknown",
                            "file_size_bytes": 0,
                            "created_at": "Unknown",
                            "version": 1
                        })
                return {"success": True, "data": processed_resources}, 200
            else:
                return {"success": True, "data": []}, 200
        else:
            return result, response.status_code
    except Exception as e:
        return {"error": str(e)}, 500

# Streamlit UI
st.set_page_config(
    page_title="Universal Data Handler",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Universal Data Handler")
st.markdown("Upload data and get AI-powered persona & context analysis")

# Sidebar for configuration
st.sidebar.header("Configuration")

# Generate or input IDs
if st.sidebar.button("Generate New IDs"):
    st.session_state.client_id = generate_uuid()
    st.session_state.user_id = generate_uuid()

if 'client_id' not in st.session_state:
    st.session_state.client_id = generate_uuid()
if 'user_id' not in st.session_state:
    st.session_state.user_id = generate_uuid()

client_id = st.sidebar.text_input("Client ID", value=st.session_state.client_id)
user_id = st.sidebar.text_input("User ID", value=st.session_state.user_id)

# Main interface
tab1, tab2, tab3 = st.tabs(["📤 Upload Data", "🔍 Analysis", "📋 View Data"])

# Tab 1: Upload Data
with tab1:
    st.header("Upload JSON Data")
    
    resource_name = st.text_input("Resource Name", value="user_data")
    
    # Sample data templates
    st.subheader("Sample Data Templates")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Student Data"):
            sample_data = {
                "student_profile": {
                    "student_id": "STU-001",
                    "name": "Alice Johnson",
                    "program": "Computer Science",
                    "year_level": "Junior",
                    "age": 21,
                    "gender": "Female",
                    "gpa": 3.75,
                    "interests": ["AI", "Web Development", "Data Science"],
                    "career_goals": "Software Engineer at tech company"
                }
            }
            st.session_state.json_input = json.dumps(sample_data, indent=2)
    
    with col2:
        if st.button("Business User"):
            sample_data = {
                "business_profile": {
                    "user_id": "BUS-001",
                    "name": "John Smith",
                    "role": "Marketing Manager",
                    "department": "Marketing",
                    "experience_years": 8,
                    "skills": ["Digital Marketing", "Analytics", "Strategy"],
                    "projects": ["Campaign Analysis", "Customer Segmentation"]
                }
            }
            st.session_state.json_input = json.dumps(sample_data, indent=2)
    
    with col3:
        if st.button("Healthcare Data"):
            sample_data = {
                "patient_profile": {
                    "patient_id": "PAT-001",
                    "age_group": "30-40",
                    "condition": "Diabetes Type 2",
                    "treatment_plan": "Medication + Diet",
                    "lifestyle": ["Regular Exercise", "Healthy Diet"],
                    "monitoring_frequency": "Weekly"
                }
            }
            st.session_state.json_input = json.dumps(sample_data, indent=2)
    
    # JSON input area
    if 'json_input' not in st.session_state:
        st.session_state.json_input = ""
    
    json_text = st.text_area(
        "JSON Data", 
        value=st.session_state.json_input,
        height=300,
        help="Enter your JSON data here"
    )
    
    if st.button("Upload Data", type="primary"):
        if json_text.strip():
            try:
                json_data = json.loads(json_text)
                
                with st.spinner("Uploading data..."):
                    result, status_code = upload_json_data(client_id, user_id, json_data, resource_name)
                
                if status_code == 200 and result.get("success"):
                    st.success("✅ Data uploaded successfully!")
                    st.json(result)
                    
                    # Store the uploaded data info
                    st.session_state.last_upload = result
                else:
                    st.error(f"❌ Upload failed: {result}")
            except json.JSONDecodeError as e:
                st.error(f"❌ Invalid JSON: {e}")
        else:
            st.warning("⚠️ Please enter JSON data to upload")

# Tab 2: Analysis
with tab2:
    st.header("AI Persona & Context Analysis")
    
    # Analysis query input
    analysis_query = st.text_area(
        "Analysis Query",
        value="Get the persona and context of this user based on their data",
        help="Describe what you want to analyze about the user"
    )
    
    # Predefined queries
    st.subheader("Quick Analysis Options")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Get User Persona"):
            analysis_query = "Extract the detailed persona characteristics, personality traits, and behavioral patterns of this user"
            
        if st.button("Get Context Analysis"):
            analysis_query = "Provide comprehensive contextual analysis including user's situation, environment, and circumstances"
    
    with col2:
        if st.button("Get Performance Insights"):
            analysis_query = "Analyze the user's performance metrics, achievements, and areas for improvement"
            
        if st.button("Get Recommendations"):
            analysis_query = "Provide personalized recommendations and suggestions based on the user's profile and data"
    
    if st.button("Run Analysis", type="primary"):
        if analysis_query.strip():
            with st.spinner("Running AI analysis..."):
                result, status_code = get_persona_analysis(client_id, user_id, analysis_query)
            
            if status_code == 200 and result.get("success"):
                st.success("✅ Analysis completed!")
                
                # Display results
                analysis_data = result.get("data", {})
                
                if "persona" in analysis_data:
                    st.subheader("👤 Persona Analysis")
                    st.write(analysis_data["persona"])
                
                if "context" in analysis_data:
                    st.subheader("🌍 Context Analysis")
                    st.write(analysis_data["context"])
                
                if "insights" in analysis_data:
                    st.subheader("💡 Insights")
                    st.write(analysis_data["insights"])
                
                # Show full response
                with st.expander("Full Analysis Response"):
                    st.json(result)
                    
            else:
                st.error(f"❌ Analysis failed: {result}")
                st.json(result)
        else:
            st.warning("⚠️ Please enter an analysis query")

# Tab 3: View Data
with tab3:
    st.header("User Data Overview")
    
    if st.button("Refresh Data", type="secondary"):
        with st.spinner("Loading user data..."):
            result, status_code = get_user_resources(client_id, user_id)
        
        if status_code == 200 and result.get("success"):
            resources = result.get("data", [])
            
            if resources:
                st.success(f"✅ Found {len(resources)} resources")
                
                # Display resources in a table
                df_data = []
                for resource in resources:
                    df_data.append({
                        "Resource ID": resource.get("resource_id", "N/A"),
                        "Name": resource.get("resource_name", "N/A"),
                        "Type": resource.get("resource_type", "N/A"),
                        "Size (bytes)": resource.get("file_size_bytes", 0),
                        "Created": resource.get("created_at", "N/A"),
                        "Version": resource.get("version", 1)
                    })
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True)
                
                # Show detailed view for selected resource
                if len(resources) > 0:
                    selected_idx = st.selectbox(
                        "Select resource for details:",
                        range(len(resources)),
                        format_func=lambda x: f"{resources[x].get('resource_name', 'Unknown')} ({resources[x].get('resource_id', 'N/A')[:8]}...)"
                    )
                    
                    if selected_idx is not None:
                        selected_resource = resources[selected_idx]
                        st.subheader("Resource Details")
                        st.json(selected_resource)
            else:
                st.info("📭 No resources found for this user")
        else:
            st.error(f"❌ Failed to load data: {result}")

# Footer
st.markdown("---")
st.markdown("""
**API Endpoints:**
- Data Upload (v1): `http://127.0.0.1:8000/docs`
- Analysis (v2): `http://127.0.0.1:8001/api/v2/docs`

**Current Session:**
- Client ID: `{}`
- User ID: `{}`
""".format(client_id[:8] + "...", user_id[:8] + "..."))
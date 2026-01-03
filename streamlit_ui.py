#!/usr/bin/env python3
"""
Streamlit UI for Universal Data Handler API Testing

This provides a web interface to test all API functionality:
- File uploads (CSV, JSON, Excel, Text, PDF)
- Raw JSON input
- SQL queries
- Natural language queries
- Semantic search
- AI data analysis
- Resource management
- System administration

Run with: streamlit run streamlit_ui.py
"""

import streamlit as st
import pandas as pd
import json
import uuid
import os
import tempfile
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from light_ai.api import create_api
from light_ai.config import Config


# Page configuration
st.set_page_config(
    page_title="Universal Data Handler API Tester",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'api' not in st.session_state:
    try:
        config = Config.load()
        st.session_state.api = create_api(config=config)
        st.session_state.initialized = True
    except Exception as e:
        st.session_state.initialized = False
        st.session_state.init_error = str(e)

if 'client_id' not in st.session_state:
    st.session_state.client_id = str(uuid.uuid4())
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if 'resources' not in st.session_state:
    st.session_state.resources = []


def display_response(response, title="API Response"):
    """Display API response in a nice format."""
    if response.success:
        st.success(f"✅ {title} - Success")
        with st.expander("Response Data", expanded=True):
            st.json(response.data)
        with st.expander("Metadata"):
            st.json(response.metadata)
    else:
        st.error(f"❌ {title} - Failed")
        st.error(f"Error: {response.error}")
        with st.expander("Metadata"):
            st.json(response.metadata)


def refresh_resources():
    """Refresh the list of resources."""
    if st.session_state.initialized:
        response = st.session_state.api.list_resources(
            client_id=st.session_state.client_id,
            user_id=st.session_state.user_id
        )
        if response.success:
            st.session_state.resources = response.data.get('resources', [])


# Main UI
st.title("🚀 Universal Data Handler API Tester")
st.markdown("---")

# Check initialization
if not st.session_state.get('initialized', False):
    st.error("❌ Failed to initialize API")
    st.error(f"Error: {st.session_state.get('init_error', 'Unknown error')}")
    st.info("Please check your configuration and OpenRouter API key in .env file")
    st.stop()

# Sidebar for session info
with st.sidebar:
    st.header("🔧 Session Info")
    st.text(f"Client ID: {st.session_state.client_id[:8]}...")
    st.text(f"User ID: {st.session_state.user_id[:8]}...")
    
    if st.button("🔄 Refresh Resources"):
        refresh_resources()
    
    st.header("📊 Resources")
    if st.session_state.resources:
        for resource in st.session_state.resources:
            st.text(f"• {resource.get('original_filename', 'Unknown')}")
    else:
        st.text("No resources uploaded yet")

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📤 Data Upload", 
    "🔍 Data Retrieval", 
    "📊 Metadata", 
    "⚙️ Administration",
    "🧪 Raw JSON"
])

# ==================== DATA UPLOAD TAB ====================
with tab1:
    st.header("📤 Data Ingestion & Storage (Sub-Layer 1)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📁 File Upload")
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['csv', 'json', 'txt', 'pdf', 'xlsx', 'xls', 'md'],
            help="Upload CSV, JSON, Excel, Text, PDF, or Markdown files"
        )
        
        resource_name = st.text_input("Resource Name (optional)", "")
        
        if uploaded_file is not None:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            if st.button("🚀 Upload File"):
                with st.spinner("Uploading file..."):
                    response = st.session_state.api.upload_file(
                        client_id=st.session_state.client_id,
                        user_id=st.session_state.user_id,
                        file_path=tmp_file_path,
                        resource_name=resource_name or uploaded_file.name
                    )
                    display_response(response, "File Upload")
                    if response.success:
                        refresh_resources()
                
                # Clean up temp file
                os.unlink(tmp_file_path)
    
    with col2:
        st.subheader("📦 Bulk Upload")
        
        bulk_files = st.file_uploader(
            "Choose multiple files",
            type=['csv', 'json', 'txt', 'pdf', 'xlsx', 'xls', 'md'],
            accept_multiple_files=True,
            help="Upload multiple files at once"
        )
        
        parallel_processing = st.checkbox("Parallel Processing", value=True)
        
        if bulk_files and st.button("🚀 Bulk Upload"):
            temp_paths = []
            try:
                # Save all files temporarily
                for file in bulk_files:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(file.getvalue())
                        temp_paths.append(tmp_file.name)
                
                with st.spinner("Uploading files..."):
                    response = st.session_state.api.upload_bulk(
                        client_id=st.session_state.client_id,
                        user_id=st.session_state.user_id,
                        files=temp_paths,
                        parallel=parallel_processing
                    )
                    display_response(response, "Bulk Upload")
                    if response.success:
                        refresh_resources()
            
            finally:
                # Clean up temp files
                for path in temp_paths:
                    try:
                        os.unlink(path)
                    except:
                        pass

# ==================== RAW JSON TAB ====================
with tab5:
    st.header("🧪 Raw JSON Data Upload")
    
    st.subheader("📝 JSON Input")
    
    # Provide sample JSON
    sample_json = {
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@example.com", "active": True},
            {"id": 2, "name": "Bob", "email": "bob@example.com", "active": False}
        ],
        "metadata": {
            "version": "1.0",
            "created": "2024-01-01",
            "source": "streamlit_ui"
        }
    }
    
    if st.button("📋 Load Sample JSON"):
        st.session_state.json_input = json.dumps(sample_json, indent=2)
    
    json_input = st.text_area(
        "Enter JSON data:",
        value=st.session_state.get('json_input', ''),
        height=300,
        help="Enter valid JSON data to upload"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        json_resource_name = st.text_input("JSON Resource Name", "raw_json_data")
        flatten_json = st.checkbox("Flatten nested structures", value=False)
    
    with col2:
        if st.button("🚀 Upload JSON Data"):
            if json_input.strip():
                try:
                    # Parse JSON to validate
                    json_data = json.loads(json_input)
                    
                    with st.spinner("Uploading JSON data..."):
                        response = st.session_state.api.upload_json(
                            client_id=st.session_state.client_id,
                            user_id=st.session_state.user_id,
                            json_data=json_data,
                            resource_name=json_resource_name,
                            flatten=flatten_json
                        )
                        display_response(response, "JSON Upload")
                        if response.success:
                            refresh_resources()
                
                except json.JSONDecodeError as e:
                    st.error(f"Invalid JSON: {e}")
            else:
                st.warning("Please enter JSON data")

# ==================== DATA RETRIEVAL TAB ====================
with tab2:
    st.header("🔍 Data Retrieval (Sub-Layer 2)")
    
    # Refresh resources for this tab
    refresh_resources()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 SQL Queries")
        
        sql_query = st.text_area(
            "Enter SQL Query:",
            value="SELECT * FROM sales_data LIMIT 10",
            height=100,
            help="Write SQL queries to analyze your structured data"
        )
        
        output_format = st.selectbox(
            "Output Format:",
            ["json", "dataframe", "csv", "dict"],
            index=0
        )
        
        if st.button("🔍 Execute SQL Query"):
            with st.spinner("Executing query..."):
                response = st.session_state.api.query_structured(
                    client_id=st.session_state.client_id,
                    user_id=st.session_state.user_id,
                    sql_query=sql_query,
                    output_format=output_format
                )
                display_response(response, "SQL Query")
        
        st.subheader("💬 Natural Language Queries")
        
        nl_question = st.text_input(
            "Ask a question about your data:",
            value="What are the top selling products?",
            help="Ask questions in plain English"
        )
        
        if st.button("🤖 Ask Question"):
            with st.spinner("Processing natural language query..."):
                response = st.session_state.api.query_natural(
                    client_id=st.session_state.client_id,
                    user_id=st.session_state.user_id,
                    question=nl_question,
                    output_format=output_format
                )
                display_response(response, "Natural Language Query")
    
    with col2:
        st.subheader("🔎 Semantic Search")
        
        search_query = st.text_input(
            "Search Query:",
            value="troubleshooting performance issues",
            help="Search through unstructured documents"
        )
        
        search_strategy = st.selectbox(
            "Search Strategy:",
            ["hybrid", "semantic", "keyword", "mmr"],
            index=0
        )
        
        search_limit = st.slider("Number of Results:", 1, 20, 5)
        
        if st.button("🔍 Search Documents"):
            with st.spinner("Searching documents..."):
                response = st.session_state.api.search_unstructured(
                    client_id=st.session_state.client_id,
                    user_id=st.session_state.user_id,
                    query=search_query,
                    strategy=search_strategy,
                    limit=search_limit
                )
                display_response(response, "Semantic Search")
        
        st.subheader("🧠 AI Data Analyst")
        
        analyst_question = st.text_area(
            "Analysis Question:",
            value="Analyze my data and provide insights about trends and patterns",
            height=100,
            help="Ask for comprehensive data analysis"
        )
        
        include_viz = st.checkbox("Include Visualizations", value=False)
        
        if st.button("🧠 Get AI Analysis"):
            with st.spinner("AI is analyzing your data..."):
                response = st.session_state.api.ask_data_analyst(
                    client_id=st.session_state.client_id,
                    user_id=st.session_state.user_id,
                    question=analyst_question,
                    include_visualizations=include_viz
                )
                display_response(response, "AI Data Analysis")

# ==================== METADATA TAB ====================
with tab3:
    st.header("📊 Metadata & Resource Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Resource List")
        
        if st.button("🔄 Refresh Resource List"):
            refresh_resources()
        
        if st.session_state.resources:
            # Display resources in a table
            df = pd.DataFrame(st.session_state.resources)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No resources found. Upload some data first!")
        
        st.subheader("📈 System Statistics")
        
        if st.button("📊 Get Statistics"):
            with st.spinner("Getting statistics..."):
                response = st.session_state.api.get_statistics(
                    client_id=st.session_state.client_id,
                    user_id=st.session_state.user_id
                )
                display_response(response, "System Statistics")
    
    with col2:
        st.subheader("🔍 Resource Details")
        
        if st.session_state.resources:
            resource_options = {
                f"{r.get('original_filename', 'Unknown')} ({r.get('resource_id', '')[:8]}...)": r.get('resource_id')
                for r in st.session_state.resources
            }
            
            selected_resource_name = st.selectbox(
                "Select Resource:",
                list(resource_options.keys())
            )
            
            if selected_resource_name:
                selected_resource_id = resource_options[selected_resource_name]
                
                col2a, col2b = st.columns(2)
                
                with col2a:
                    if st.button("📋 Get Metadata"):
                        response = st.session_state.api.get_resource_metadata(
                            resource_id=selected_resource_id,
                            client_id=st.session_state.client_id,
                            user_id=st.session_state.user_id
                        )
                        display_response(response, "Resource Metadata")
                
                with col2b:
                    if st.button("🗂️ Get Schema"):
                        response = st.session_state.api.get_schema(
                            resource_id=selected_resource_id,
                            client_id=st.session_state.client_id,
                            user_id=st.session_state.user_id
                        )
                        display_response(response, "Resource Schema")
                
                st.subheader("📥 Get Resource Data")
                
                get_format = st.selectbox(
                    "Data Format:",
                    ["json", "dataframe", "csv", "dict"],
                    key="get_format"
                )
                
                if st.button("📥 Get Data"):
                    response = st.session_state.api.get_resource(
                        resource_id=selected_resource_id,
                        output_format=get_format,
                        client_id=st.session_state.client_id,
                        user_id=st.session_state.user_id
                    )
                    display_response(response, "Resource Data")

# ==================== ADMINISTRATION TAB ====================
with tab4:
    st.header("⚙️ System Administration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🗂️ Cache Management")
        
        cache_scope = st.selectbox(
            "Cache Scope:",
            ["all", "query", "embedding", "metadata"]
        )
        
        if st.button("🗑️ Clear Cache"):
            response = st.session_state.api.clear_cache(scope=cache_scope)
            display_response(response, "Clear Cache")
        
        st.subheader("📊 System Stats")
        
        if st.button("📈 Get System Stats"):
            response = st.session_state.api.get_system_stats()
            display_response(response, "System Statistics")
        
        st.subheader("🔧 Storage Optimization")
        
        if st.button("⚡ Optimize Storage"):
            with st.spinner("Optimizing storage..."):
                response = st.session_state.api.optimize_storage()
                display_response(response, "Storage Optimization")
    
    with col2:
        st.subheader("💾 Backup & Export")
        
        if st.session_state.resources:
            export_resource_options = {
                f"{r.get('original_filename', 'Unknown')} ({r.get('resource_id', '')[:8]}...)": r.get('resource_id')
                for r in st.session_state.resources
            }
            
            export_resource_name = st.selectbox(
                "Select Resource to Export:",
                list(export_resource_options.keys()),
                key="export_resource"
            )
            
            export_format = st.selectbox(
                "Export Format:",
                ["json", "csv", "parquet", "excel"]
            )
            
            if st.button("📤 Export Resource"):
                selected_export_id = export_resource_options[export_resource_name]
                response = st.session_state.api.export_resource(
                    resource_id=selected_export_id,
                    export_format=export_format,
                    client_id=st.session_state.client_id,
                    user_id=st.session_state.user_id
                )
                display_response(response, "Export Resource")
        
        st.subheader("💾 System Backup")
        
        backup_path = st.text_input("Backup Path (optional):", "")
        include_raw = st.checkbox("Include Raw Files", value=True)
        
        if st.button("💾 Create Backup"):
            with st.spinner("Creating backup..."):
                response = st.session_state.api.backup_data(
                    backup_path=backup_path if backup_path else None,
                    include_raw_files=include_raw
                )
                display_response(response, "Create Backup")

# Footer
st.markdown("---")
st.markdown("🚀 **Universal Data Handler API Tester** - Test all API functionality through this web interface")
st.markdown("💡 **Tip**: Upload some test data first, then explore the different query and analysis options!")
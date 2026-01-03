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

# Initialize client_id and user_id with defaults but allow user configuration
if 'client_id' not in st.session_state:
    st.session_state.client_id = ""
if 'user_id' not in st.session_state:
    st.session_state.user_id = ""
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

# Client and User ID Configuration (Required for all operations)
st.markdown("### 🔐 Client & User Configuration")
st.markdown("**Required**: Enter your Client ID and User ID to access the system. These identify your organization and user account.")

col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    client_id_input = st.text_input(
        "Client ID (Organization):",
        value=st.session_state.client_id,
        placeholder="e.g., acme-corp, startup-xyz, enterprise-123",
        help="Unique identifier for your organization. Use a meaningful name with letters, numbers, dots, hyphens, and underscores."
    )

with col2:
    user_id_input = st.text_input(
        "User ID:",
        value=st.session_state.user_id,
        placeholder="e.g., john.doe, jane.smith, admin",
        help="Unique identifier for your user account within the organization."
    )

with col3:
    st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
    if st.button("🎲 Generate UUIDs"):
        st.session_state.client_id = f"client-{str(uuid.uuid4())[:8]}"
        st.session_state.user_id = f"user-{str(uuid.uuid4())[:8]}"
        st.rerun()

# Update session state when inputs change
if client_id_input != st.session_state.client_id:
    st.session_state.client_id = client_id_input
if user_id_input != st.session_state.user_id:
    st.session_state.user_id = user_id_input

# Validate that both IDs are provided
if not st.session_state.client_id or not st.session_state.user_id:
    st.error("❌ Please provide both Client ID and User ID to continue")
    st.info("💡 **Tip**: Use meaningful names like 'acme-corp' and 'john.doe' or click 'Generate UUIDs' for random IDs")
    st.stop()

# Validate identifier format
def is_valid_identifier(identifier):
    """Check if identifier follows the allowed format."""
    import re
    return bool(re.match(r'^[a-zA-Z0-9._-]+$', identifier)) and len(identifier) <= 255

# Show validation status
col1, col2 = st.columns(2)
with col1:
    if is_valid_identifier(st.session_state.client_id):
        st.success(f"✅ Client ID: Valid format")
    else:
        st.error(f"❌ Client ID: Invalid format (use letters, numbers, dots, hyphens, underscores only)")

with col2:
    if is_valid_identifier(st.session_state.user_id):
        st.success(f"✅ User ID: Valid format")
    else:
        st.error(f"❌ User ID: Invalid format (use letters, numbers, dots, hyphens, underscores only)")

# Stop if validation fails
if not (is_valid_identifier(st.session_state.client_id) and is_valid_identifier(st.session_state.user_id)):
    st.stop()

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
    
    # Display current IDs with copy buttons
    st.markdown("**Current Session:**")
    st.code(f"Client ID: {st.session_state.client_id}")
    st.code(f"User ID: {st.session_state.user_id}")
    
    # Quick actions
    if st.button("🔄 Refresh Resources"):
        refresh_resources()
    
    if st.button("🗑️ Clear Session"):
        st.session_state.client_id = ""
        st.session_state.user_id = ""
        st.session_state.resources = []
        st.rerun()
    
    st.header("📊 Your Resources")
    if st.session_state.resources:
        st.markdown(f"**Total: {len(st.session_state.resources)} resources**")
        for i, resource in enumerate(st.session_state.resources[:5]):  # Show first 5
            filename = resource.get('original_filename', 'Unknown')
            resource_type = resource.get('resource_type', 'unknown')
            st.markdown(f"• **{filename}** ({resource_type})")
        
        if len(st.session_state.resources) > 5:
            st.markdown(f"... and {len(st.session_state.resources) - 5} more")
    else:
        st.markdown("*No resources uploaded yet*")
        st.markdown("👆 Upload some data to get started!")

# Main tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📤 Data Upload", 
    "🔍 Data Retrieval", 
    "📊 Metadata", 
    "⚙️ Administration",
    "🧪 Raw JSON",
    "📖 Examples"
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

# ==================== EXAMPLES TAB ====================
with tab6:
    st.header("📖 Getting Started Examples")
    
    st.markdown("""
    ### 🚀 Quick Start Guide
    
    **Step 1: Set Your Identity**
    - Enter your **Client ID** (organization) and **User ID** above
    - Use meaningful names like `acme-corp` and `john.doe` or generate UUIDs
    
    **Step 2: Upload Some Data**
    - Go to the **Data Upload** tab
    - Try uploading a CSV file, JSON data, or text document
    - The system will automatically clean and organize your data
    
    **Step 3: Query Your Data**
    - Go to the **Data Retrieval** tab
    - Try SQL queries on structured data
    - Ask natural language questions
    - Search through documents
    
    **Step 4: Get AI Analysis**
    - Use the AI Data Analyst for comprehensive insights
    - Ask questions like "What trends do you see in my data?"
    """)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Sample Data Scenarios")
        
        st.markdown("""
        **Business Scenarios:**
        - **Sales Team**: Upload sales reports (CSV), customer feedback (PDF), product docs (TXT)
        - **HR Department**: Upload employee data (Excel), policies (PDF), surveys (JSON)
        - **Marketing**: Upload campaign data (CSV), content (MD), analytics (JSON)
        - **Finance**: Upload transactions (CSV), reports (PDF), budgets (Excel)
        """)
        
        st.markdown("""
        **Example Client/User Combinations:**
        ```
        Client ID: acme-corp          User ID: john.doe
        Client ID: startup-xyz        User ID: jane.smith  
        Client ID: enterprise-123     User ID: admin
        Client ID: consulting-firm    User ID: analyst-1
        ```
        """)
    
    with col2:
        st.subheader("💡 Sample Queries to Try")
        
        st.markdown("""
        **SQL Queries:**
        ```sql
        SELECT * FROM sales_data LIMIT 10
        SELECT product, SUM(revenue) FROM sales GROUP BY product
        SELECT * FROM customers WHERE status = 'active'
        ```
        
        **Natural Language Questions:**
        - "What are my top selling products?"
        - "Show me customers from California"
        - "What's the average order value?"
        - "Find all documents about pricing"
        
        **Semantic Search:**
        - "troubleshooting guide"
        - "performance optimization"
        - "customer complaints"
        - "pricing strategy"
        """)
    
    st.markdown("---")
    
    st.subheader("🔧 System Architecture")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Data Storage:**
        - **Structured Data** (CSV, Excel) → DuckDB
        - **JSON Data** → DuckDB JSONB
        - **Documents** (PDF, TXT) → ChromaDB + Embeddings
        - **Metadata** → SQLite Registry
        """)
    
    with col2:
        st.markdown("""
        **Key Features:**
        - **Multi-tenant**: Isolated by Client ID + User ID
        - **Versioned**: All changes tracked and reversible
        - **AI-Powered**: Natural language queries + analysis
        - **Fast**: Sub-second responses for most operations
        """)

# Footer
st.markdown("---")
st.markdown("🚀 **Universal Data Handler API Tester** - Test all API functionality through this web interface")
st.markdown("💡 **Tip**: Start by setting your Client ID and User ID, then upload some test data to explore the system!")
st.markdown("🔗 **Multi-tenant**: Each Client ID represents an organization, User ID represents individuals within that organization")
What I want to make here is my intent.

Multi-Layer Data Extraction System
Business Requirements Document - Non-Technical Version

What We're Building
A smart data management system that can be installed on any company's own computers (Windows, Mac, or Linux) to handle all their data - no matter what format it comes in. Think of it as a universal data assistant that can read, organize, store, and retrieve any type of information.

The Big Picture: Three Layers
We're building this in three phases:

Data Management Layer (Phase 1 - Focus of this document)

Handles all data coming in and going out
Cleans and organizes everything automatically
Works entirely on your own computers


Smart Extraction Layer (Phase 2 - Later)

AI agents that understand and extract specific information
Different agents for different types of tasks


Ready-to-Use Solutions Layer (Phase 3 - Later)

Pre-built solutions for common business needs
Customizable for different industries and use cases




Phase 1: The Data Management Foundation
What Problem Are We Solving?
Companies have data everywhere in different formats:

Spreadsheets (Excel, CSV files)
Documents (PDFs, Word files, text files)
JSON data (from APIs, databases, applications)
A mix of everything above

The Challenge:

Hard to find specific information across all these files
Time-consuming to combine data from different sources
Difficult to keep track of who uploaded what and when
No easy way to ask questions about the data in plain English

Our Solution:
A single system that:

Accepts any type of data
Organizes it automatically
Lets you ask questions in plain English
Finds answers in seconds, not hours


How the System Works: Two Main Parts
Part 1: Getting Data In (Upload & Organization)
What happens when you upload data:

You identify yourself and the data:

Who you are (user)
Which company/department (client)
What the data is (give it a name)
System automatically assigns a unique ID


System automatically cleans the data:

Removes blank rows and columns
Fixes formatting issues
Standardizes date formats
Detects data types (numbers, text, dates)
Makes everything searchable


System stores it intelligently:

Spreadsheets: Kept as files but made instantly queryable
Documents: Broken into searchable chunks with AI understanding
JSON data: Organized in a way that's easy to query
Everything tagged with who uploaded it and when


System remembers everything:

Original file is always kept
All changes are tracked (version history)
You can always go back to any previous version




Part 2: Getting Data Out (Search & Retrieval)
What you can do:
1. Get Your Original Files Back

"Show me all files I uploaded last month"
"Give me the original Excel file I uploaded yesterday"
Works at individual, team, or company level

2. Ask Questions in Plain English About Spreadsheets
Instead of writing complex formulas:
You ask: "What are the top 5 customers by revenue in 2024?"
System:

Understands your question
Finds the right spreadsheet(s)
Runs the calculation
Shows you the answer with explanation

More examples:

"How many orders did we have from California last quarter?"
"Compare sales between Q3 and Q4 by region"
"Show me customers who haven't ordered in 6 months"

3. Create Custom Calculations Automatically
You describe what you want:

"Classify travelers as business or leisure based on their booking patterns"
"Score customers as elite, premium, or standard based on their loyalty status"

System:

Creates the formula automatically
Applies it to all your data
Lets you query using these new fields

4. Search Across Documents
You ask: "What were the main challenges mentioned in Q4 reports?"
System:

Searches all PDFs, Word docs, and text files
Finds relevant sections
Summarizes findings
Shows you where the information came from

5. Smart AI Data Analyst
The ultimate capability:
You ask: "Compare Q3 and Q4 sales by region, explain the trends, and identify risks"
System:

Figures out which files contain relevant data
Analyzes spreadsheets for numbers
Reads documents for context
Combines everything into a clear report
Explains what it found and why it matters


Who Can Access What: Security Built-In
Three-Level Organization:
Company (Client)
  └─ Department/Team (User Group)
      └─ Individual Person (User)
          └─ Their Files (Resources)
Rules:

You can only see your own data (unless given permission)
Managers can see their team's data
Admins can see company-wide data
Every piece of data knows who it belongs to


Where Does Data Live?
Default Setup (Phase 1 - Simplest):
Everything stored on your own computers:

No internet connection needed
No cloud services required
Complete data privacy
Works offline

Just need:

The software installed (one-time setup)
An API key for AI features (for understanding questions)

Future Options (Phase 2+):
When you're ready to scale, you can optionally connect to:

Your company's database (PostgreSQL)
Cloud storage (AWS, Google Cloud, Azure)
Vector databases for advanced AI search
Multiple computers working together

Key point: Start simple, scale when needed. The system grows with you.

What Makes This System Special
1. Universal Data Handler

Accepts any file format
Doesn't care about structure or lack thereof
Handles small files and huge datasets

2. Intelligent Organization

Automatically understands data structure
Creates searchable indexes
Maintains relationships between files

3. Lightning Fast Retrieval

Answers in under 1 second for most questions
Searches across millions of records instantly
No waiting for reports to generate

4. Natural Language Interface

No SQL or technical knowledge needed
Ask questions like you're talking to a person
System explains what it did

5. Complete History

Never lose data
Track all changes
Audit trail of who did what

6. Smart Data Cleaning

Automatically fixes common issues
Standardizes formats
Flags potential problems

What You Get Out of the Box
Automatic Features:
✅ Data validation (catches errors)
✅ Data cleaning (fixes common issues)
✅ Smart storage (optimized for speed)
✅ Version control (never lose work)
✅ Full audit trail (who did what, when)
✅ Natural language queries (no coding needed)
✅ Cross-file analysis (connects related data)
✅ Export capabilities (get data back anytime)
No Setup Required For:
✅ User management (automatic tracking)
✅ Data organization (automatic structuring)
✅ Search indexing (automatic optimization)
✅ Backup (automatic versioning)
✅ Performance tuning (automatic optimization)

Performance You Can Expect
Upload Speed:

Small file (10MB CSV): Under 2 seconds
Large document (100 pages): Under 5 seconds
10 files at once: Under 10 seconds

Query Speed:

Simple question: Under 1 second
Complex multi-file analysis: Under 3 seconds
Full report with insights: Under 10 seconds

Data Capacity:

Tested with 1TB of data
Millions of rows in spreadsheets
Thousands of documents
Still fast!


Why This Approach?
Start Simple:

Install and use immediately
No infrastructure setup
No database administration
No IT team needed

Scale Gradually:

Starts on one computer
Add more power when needed
Connect to databases if wanted
Move to cloud if preferred

Stay In Control:

Your data stays on your computers
No vendor lock-in
Works offline
Complete privacy

Future-Proof:

Designed to scale from day one
Can grow to handle enterprise needs
Flexible architecture
Easy to extend


Success Metrics: What "Good" Looks Like
Speed Goals:

⚡ 90% of queries answered in under 1 second
⚡ Complex analysis completed in under 10 seconds
⚡ Files processed within seconds of upload

Accuracy Goals:

🎯 Natural language queries understood correctly 95%+ of the time
🎯 Data cleaning catches 99% of common issues
🎯 Search results ranked by relevance

Usability Goals:

😊 Non-technical users can operate without training
😊 Questions answered in plain English
😊 Results explained clearly

Reliability Goals:

🔒 Zero data loss (ever)
🔒 Complete audit trail
🔒 Automatic error recovery


What You Don't Need to Worry About
❌ Complex database setup
❌ Data modeling or schema design
❌ Writing SQL queries
❌ Managing servers
❌ Backup strategies (automatic)
❌ Performance tuning (automatic)
❌ Data cleaning scripts (automatic)
❌ Index management (automatic)
❌ Security configuration (built-in)

The Bottom Line
What we're building:
A system that makes all your company's data instantly accessible and useful, without requiring technical expertise.
How it works:
Upload any file → Ask questions in plain English → Get instant answers
Why it's better:

Works immediately (no setup)
Handles any data format
Understands natural language
Lightning fast
Completely private
Grows with your needs

Who it's for:
Any business that has data spread across multiple files and wants to find insights quickly without technical expertise.


What technically it may look you may update or improve this open router key is in .env and always use uv and virtual env to execute any thing

also light_ai is the whole system name light_ai_data_manage for databsase management light_ai_service_manage and light_ai_client_manage are other layers name 
All layers are independent I am making 1st layer as of now

Multi-Layer Multi-Agent Data Extraction System for light_ai_data_manage

System Overview
A library/SaaS/plugin-based multi-layer multi-agent system for data extraction from all types of data (structured and unstructured). This document focuses on Layer 1: Data Management Layer - the foundation that must work on-premises with zero external dependencies except OpenRouter API for LLM/embeddings.

Installation Philosophy
One-command install, zero configuration complexity:
bashpip install data-extraction-system
Only required configuration:
propertiesOPENROUTER_API_KEY="sk-or-v1-xxxx"
```

Everything else works out-of-the-box on Windows, Linux, or macOS.

---

## System Architecture

### Three-Layer Architecture:
1. **Data Management Layer** (THIS DOCUMENT - Phase 1)
2. **Service Layer** - Multi-agent extraction logic (Phase 2)
3. **Use Case Layer** - Domain-specific extraction templates (Phase 3)

---

## Layer 1: Data Management Layer

### Core Design Principles:
- ✅ Pure on-premises, no external services
- ✅ Python-only with pip-installable dependencies
- ✅ Zero setup beyond OpenRouter API key
- ✅ Embedded databases (no server processes)
- ✅ Single-machine optimized (scales vertically)
- ✅ File-system first, DB second
- ✅ Automatic schema detection and management

---

## Data Hierarchy & Identity

Every piece of data follows this strict hierarchy:
```
client_id (organization/tenant)
  └─ user_id (individual user)
      └─ resource_id (unique data resource)
```

**Rules:**
- `resource_id`: Primary unique identifier (UUID v4)
- `user_id`: Required for every resource (UUID v4 or string)
- `client_id`: Required for every user (UUID v4 or string)
- All three IDs stored as metadata with every data piece
- Enables fast filtering at any level (client, user, or resource)

---

## Sub-Layer 1: Data Ingestion & Storage

### Supported Input Types:
1. **Structured Files**: CSV, Excel (XLSX, XLS), TSV, Parquet
2. **JSON Data**: Raw JSON, JSONL, nested/complex JSON structures
3. **Unstructured Files**: PDF, TXT, Markdown, DOCX, HTML
4. **Semi-structured**: XML, YAML, Log files

### Storage Architecture (Default On-Prem):
```
data-extraction-system/
├── data/
│   ├── structured/              # DuckDB + original files
│   ├── json/                    # JSONB in DuckDB
│   ├── unstructured/            # ChromaDB vectors
│   └── raw/                     # Original uploaded files
├── metadata/
│   └── registry.db              # SQLite metadata store
├── cache/
│   └── query_cache/             # LRU cache for queries
└── logs/
    └── operations.log           # Audit trail
```

### Technology Stack (All pip-installable):

**Core Databases:**
- **DuckDB** - For all structured data and JSON (analytical queries, zero setup)
  - CSV/Excel: Virtual tables (queries files directly without import)
  - JSON: Native JSONB storage with indexing
  - Lightning fast OLAP queries, single-file database
  
- **ChromaDB** - For unstructured data embeddings
  - Persistent local storage
  - Built-in embedding support via OpenRouter
  - Automatic collection management per user
  
- **SQLite** - For metadata registry only
  - Resource catalog (who uploaded what, when)
  - Schema registry (detected schemas, versions)
  - Data lineage tracking

**Processing Libraries:**
- `pandas` - Data cleaning and transformation
- `polars` - High-performance DataFrames (alternative to pandas)
- `pypdf2` / `pdfplumber` - PDF extraction
- `python-docx` - DOCX processing
- `beautifulsoup4` - HTML parsing
- `lxml` - XML processing
- `openpyxl` - Excel handling

**LLM/Embeddings:**
- OpenRouter API for:
  - Text embeddings (via OpenAI/Cohere models)
  - Text-to-SQL generation
  - Schema understanding
  - Data cleaning suggestions

### Data Ingestion Flow:
```
User Upload → Validation → Cleaning → Storage → Indexing → Metadata Registration
Step 1: Validation

File type detection
Size limits (configurable, default 500MB per file)
Format validation (parse-ability check)
Duplicate detection (hash-based)
Assign: client_id, user_id, resource_id

Step 2: Cleaning (Auto-applied rules)
Structured Data (CSV/Excel):

Remove completely empty rows/columns
Strip whitespace from headers and string values
Detect and convert data types automatically
Handle missing values (configurable: keep as NULL, drop, or fill)
Detect and flag duplicates (don't auto-remove without permission)
Normalize column names (lowercase, snake_case)
Detect date formats and standardize
Remove special characters from numeric columns
Detect and catalog unique constraints

JSON Data:

Flatten nested structures (configurable depth)
Normalize key names (consistent casing)
Remove null/empty objects (configurable)
Detect array types and structures
Extract metadata (depth, key count, data types)

Unstructured Data (PDF/Text):

Extract text with layout preservation
Remove headers/footers/page numbers
Clean OCR artifacts
Detect document structure (sections, paragraphs)
Chunking strategy (configurable):

Semantic chunking (default): 512 tokens with 50 token overlap
Fixed-size chunking: User-defined size
Sentence-based: Natural boundaries
Paragraph-based: Preserve context



Step 3: Storage
Structured Data Storage:
python# DuckDB approach - files stay as files, queried virtually
# No data duplication, instant "loading"

Location: data/structured/{client_id}/{user_id}/{resource_id}/
Files: 
  - original.csv (or .xlsx, .parquet)
  - schema.json (detected schema)
  - stats.json (data statistics)

DuckDB Virtual Table:
  CREATE VIEW {resource_id} AS 
  SELECT * FROM 'data/structured/{path}/original.csv'
JSON Data Storage:
python# DuckDB with native JSONB support

Location: DuckDB database at data/json/json_store.duckdb

Table Structure:
  CREATE TABLE json_resources (
    resource_id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    client_id VARCHAR NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  
  CREATE INDEX idx_user ON json_resources(user_id);
  CREATE INDEX idx_client ON json_resources(client_id);
Unstructured Data Storage:
python# ChromaDB with embeddings

Location: data/unstructured/chroma_db/

Collection per user: {client_id}_{user_id}

Each document chunk stored with metadata:
{
  "id": "{resource_id}_{chunk_index}",
  "embedding": [...],  # From OpenRouter
  "metadata": {
    "client_id": "...",
    "user_id": "...",
    "resource_id": "...",
    "chunk_index": 0,
    "source_file": "document.pdf",
    "page_number": 1,
    "created_at": "2026-01-03T10:00:00Z"
  },
  "document": "chunk text content..."
}
Step 4: Metadata Registration
SQLite Registry (metadata/registry.db):
sql-- Resources catalog
CREATE TABLE resources (
    resource_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    client_id TEXT NOT NULL,
    resource_type TEXT NOT NULL, -- 'structured', 'json', 'unstructured'
    data_type TEXT NOT NULL,     -- 'csv', 'pdf', 'json', etc.
    original_filename TEXT,
    file_size_bytes INTEGER,
    row_count INTEGER,           -- For structured data
    column_count INTEGER,        -- For structured data
    chunk_count INTEGER,         -- For unstructured data
    storage_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- Schema registry for structured data
CREATE TABLE schemas (
    schema_id TEXT PRIMARY KEY,
    resource_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    schema_json TEXT NOT NULL,   -- JSON of column definitions
    statistics_json TEXT,        -- Data profiling stats
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resource_id) REFERENCES resources(resource_id)
);

-- Data lineage tracking
CREATE TABLE lineage (
    lineage_id TEXT PRIMARY KEY,
    resource_id TEXT NOT NULL,
    operation TEXT NOT NULL,     -- 'upload', 'clean', 'transform', 'delete'
    operation_details TEXT,      -- JSON of what was done
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resource_id) REFERENCES resources(resource_id)
);

-- Indexes for fast lookups
CREATE INDEX idx_resources_user ON resources(user_id);
CREATE INDEX idx_resources_client ON resources(client_id);
CREATE INDEX idx_resources_type ON resources(resource_type);
CREATE INDEX idx_lineage_resource ON lineage(resource_id);
```

### Versioning Strategy:

When a resource is updated:
1. Original data is kept (no destructive updates)
2. Version number increments
3. New version stored alongside old version
4. Metadata tracks all versions
5. User can retrieve any version or rollback

**Storage:**
```
data/structured/{client_id}/{user_id}/{resource_id}/
  - v1_original.csv
  - v1_schema.json
  - v2_original.csv
  - v2_schema.json
  - current -> v2_original.csv (symlink)
Transaction Management:
Upload Transaction:
python1. BEGIN TRANSACTION
2. Create staging area
3. Validate file
4. Clean data
5. Store in staging
6. Register metadata
7. Move from staging to final location
8. COMMIT
9. If any step fails → ROLLBACK (cleanup staging)
Automatic rollback on failure ensures no partial data

Sub-Layer 2: Data Retrieval (GET Actions)
Design Goals:

⚡ Lightning fast retrieval (<1 second for most queries)
🎯 Flexible querying (simple to complex)
🧠 Natural language interface (text-to-query)
📊 Cross-resource queries
💾 Built-in caching

Retrieval Capabilities:
1. Resource Retrieval (Get Original Data)
API:
python# Get single resource
get_resource(resource_id, version=None) → original data

# Get all resources for user
get_user_resources(user_id, resource_type=None) → list of resources

# Get all resources for client
get_client_resources(client_id, resource_type=None) → list of resources
2. Structured Data Queries
Simple Queries (Direct SQL):
pythonquery_structured(
    resource_id=None,      # Optional: specific resource
    user_id=None,          # Required if resource_id not provided
    query="SELECT * FROM data WHERE age > 30",
    format="dataframe"     # or 'json', 'csv', 'dict'
)
Natural Language Queries (Text-to-SQL via LLM):
pythonquery_natural(
    user_id="user123",
    question="What's the average age of users who traveled in 2024?",
    resources=["resource1", "resource2"]  # Optional: limit scope
)

# Behind the scenes:
# 1. Retrieve schemas for user's resources
# 2. Send schemas + question to OpenRouter LLM
# 3. LLM generates DuckDB SQL query
# 4. Execute query
# 5. Return results with explanation
Cross-Resource Queries:
python# DuckDB can join across multiple CSV files directly
query_structured(
    user_id="user123",
    query="""
        SELECT a.customer_name, b.total_purchases
        FROM resource_abc.csv a
        JOIN resource_xyz.csv b ON a.customer_id = b.customer_id
        WHERE b.total_purchases > 1000
    """
)
Derived Field Queries:
pythonquery_derived(
    user_id="user123",
    resource_id="resource_abc",
    derived_fields={
        "traveler_segment": {
            "description": "Classify traveler type",
            "calculation": """
                CASE 
                    WHEN travel_frequency = 'frequent' AND travel_purpose = 'business' THEN 'business'
                    WHEN travel_purpose = 'vacation' THEN 'leisure'
                    ELSE 'mixed'
                END
            """,
            "source_fields": ["travel_frequency", "travel_purpose"]
        },
        "loyalty_tier": {
            "description": "Assess loyalty program tier",
            "calculation": """
                CASE
                    WHEN loyalty_status IN ('platinum', 'diamond') THEN 'elite'
                    WHEN loyalty_status = 'gold' THEN 'premium'
                    ELSE 'standard'
                END
            """,
            "source_fields": ["loyalty_status"]
        }
    },
    query="SELECT *, traveler_segment, loyalty_tier FROM data WHERE loyalty_tier = 'elite'"
)
3. JSON Data Queries
JSON Path Queries:
pythonquery_json(
    user_id="user123",
    resource_id="resource_json1",
    json_path="$.customers[*].orders[?(@.total > 100)]",
    format="json"
)
JSON SQL Queries (DuckDB JSONB):
pythonquery_structured(
    user_id="user123",
    query="""
        SELECT 
            data->>'customer_name' as name,
            json_extract(data, '$.orders[*].total') as order_totals
        FROM json_resources
        WHERE user_id = 'user123'
        AND data->>'country' = 'USA'
    """
)
4. Unstructured Data Queries (Semantic Search)
Simple Semantic Search:
pythonsearch_unstructured(
    user_id="user123",
    query="What are the key findings about climate change?",
    top_k=5,
    resource_ids=None  # Optional: limit to specific resources
)

# Returns:
# [
#   {
#     "resource_id": "...",
#     "chunk": "text content...",
#     "similarity_score": 0.92,
#     "metadata": {...}
#   },
#   ...
# ]
Advanced Retrieval Strategies:
pythonsearch_unstructured_advanced(
    user_id="user123",
    query="Explain the company's Q4 strategy",
    strategy="hybrid",  # Options: 'semantic', 'keyword', 'hybrid', 'mmr'
    top_k=10,
    rerank=True,       # Re-rank results using LLM
    filters={
        "source_file": "Q4_report.pdf",
        "page_number": {"$gte": 10, "$lte": 20}
    }
)
Multi-Query Retrieval:
python# Generate multiple query variations for better coverage
search_multi_query(
    user_id="user123",
    query="What were the main challenges in 2024?",
    num_queries=3  # LLM generates 3 variations of the query
)

# Behind the scenes:
# Original: "What were the main challenges in 2024?"
# Query 1: "What obstacles did we face in 2024?"
# Query 2: "What difficulties were encountered during 2024?"
# Query 3: "What problems arose in the year 2024?"
# Retrieve results for all 3, deduplicate, and re-rank
5. Unified AI Data Analyst Agent
The Ultimate Query Interface:
pythonask_data_analyst(
    user_id="user123",
    question="Compare Q3 and Q4 sales by region and identify trends",
    include_resources=None,  # Auto-detect relevant resources
    output_format="markdown_report"  # or 'json', 'dataframe', 'chart'
)

# This agent:
# 1. Analyzes the question
# 2. Identifies relevant resources (structured + unstructured)
# 3. Retrieves schemas and samples
# 4. Generates and executes queries across all relevant data
# 5. Synthesizes findings from multiple sources
# 6. Produces a coherent report with insights
```

**Example Workflow:**
```
Question: "What are the top customer complaints and how do they correlate with churn?"

Agent Process:
1. Identifies resources: 
   - customer_feedback.csv (structured)
   - support_tickets.pdf (unstructured)
   - churn_data.csv (structured)

2. Queries:
   - Extracts complaints from PDF (semantic search)
   - Analyzes complaint categories in CSV (SQL aggregation)
   - Joins with churn data (SQL join)
   
3. Synthesis:
   - Generates correlation analysis
   - Creates visualizations (if requested)
   - Writes summary report
Caching Strategy:
In-Memory LRU Cache:
python# Automatic caching for:
- Query results (TTL: 5 minutes)
- Schema information (TTL: 1 hour)
- Embeddings (permanent until data changes)
- Frequently accessed resources (TTL: 15 minutes)

# Cache invalidation triggers:
- Resource update/delete
- Manual cache clear
- TTL expiration
Cache Implementation:
pythonfrom functools import lru_cache
from cachetools import TTLCache

query_cache = TTLCache(maxsize=1000, ttl=300)  # 5 min TTL
schema_cache = TTLCache(maxsize=500, ttl=3600)  # 1 hour TTL
Performance Optimizations:

Lazy Loading: Only load data when needed
Streaming Results: For large result sets, stream rows instead of loading all into memory
Parallel Execution: For multi-resource queries, execute in parallel
Query Planning: Analyze query cost before execution
Index Utilization: Automatic index creation on frequently queried columns


Data Synchronization & Consistency
Delete Operations:
When a resource is deleted:
python1. Mark as deleted in metadata (is_deleted=TRUE)
2. Remove from DuckDB views/tables
3. Delete chunks from ChromaDB collection
4. Move original files to trash/ folder (not permanent delete)
5. Log deletion in lineage table
6. Clear related cache entries
7. Update resource count statistics
Soft Delete (Default):

Data moved to trash, recoverable for 30 days
Metadata retained with is_deleted flag
Can be permanently purged after retention period

Hard Delete (Optional):

Permanent removal of all data
Metadata archived for audit purposes
Irreversible operation

Update Operations:
When a resource is updated:
python1. Version increment
2. Store new version alongside old
3. Update DuckDB views to point to new version
4. Re-generate embeddings for unstructured data (if content changed)
5. Update metadata with new schema/statistics
6. Log update in lineage table
7. Clear cache for this resource
Consistency Guarantees:

Atomicity: All-or-nothing operations (via transactions)
Isolation: Concurrent operations don't interfere
Durability: Data persisted before acknowledging success
Read-after-write: Immediately see your own writes


API Reference
Data Ingestion APIs
python# Upload file
upload_file(
    client_id: str,
    user_id: str,
    file_path: str,
    resource_name: str = None,
    cleaning_config: dict = None
) → resource_id

# Upload JSON data
upload_json(
    client_id: str,
    user_id: str,
    json_data: dict | list,
    resource_name: str,
    flatten: bool = False
) → resource_id

# Bulk upload
upload_bulk(
    client_id: str,
    user_id: str,
    files: list[str],
    parallel: bool = True
) → list[resource_id]

# Update existing resource
update_resource(
    resource_id: str,
    new_data: str | dict,
    create_version: bool = True
) → new_version_number

# Delete resource
delete_resource(
    resource_id: str,
    hard_delete: bool = False
) → success: bool
Data Retrieval APIs
python# Get original resource
get_resource(
    resource_id: str,
    version: int = None,
    format: str = 'original'  # 'original', 'dataframe', 'json'
) → data

# Get resource metadata
get_resource_metadata(
    resource_id: str
) → dict

# List user resources
list_resources(
    user_id: str = None,
    client_id: str = None,
    resource_type: str = None,
    include_deleted: bool = False
) → list[dict]

# Query structured data
query_structured(
    resource_id: str = None,
    user_id: str = None,
    query: str,
    format: str = 'dataframe'
) → results

# Natural language query
query_natural(
    user_id: str,
    question: str,
    resources: list[str] = None,
    explain: bool = True
) → {results, explanation, sql_query}

# Search unstructured data
search_unstructured(
    user_id: str,
    query: str,
    top_k: int = 5,
    resource_ids: list[str] = None,
    strategy: str = 'semantic'
) → list[dict]

# AI Data Analyst
ask_data_analyst(
    user_id: str,
    question: str,
    include_resources: list[str] = None,
    output_format: str = 'markdown'
) → report

# Get schema
get_schema(
    resource_id: str,
    version: int = None
) → dict

# Get statistics
get_statistics(
    resource_id: str
) → dict
Administration APIs
python# Clear cache
clear_cache(
    scope: str = 'all'  # 'all', 'queries', 'schemas', 'resource_id'
) → success: bool

# Get system stats
get_system_stats() → dict

# Optimize storage
optimize_storage(
    vacuum: bool = True,
    rebuild_indexes: bool = False
) → dict

# Export resource
export_resource(
    resource_id: str,
    format: str,  # 'csv', 'json', 'parquet', 'excel'
    output_path: str
) → success: bool

# Backup data
backup_data(
    backup_path: str,
    include_deleted: bool = False
) → success: bool

# Restore from backup
restore_data(
    backup_path: str
) → success: bool

Configuration File (Optional Advanced Settings)
Default works with zero config, but advanced users can customize:
yaml# config.yaml (optional)

# Storage settings
storage:
  base_path: "./data-extraction-system"
  max_file_size_mb: 500
  trash_retention_days: 30
  enable_compression: false
  
# Cleaning settings
cleaning:
  structured:
    remove_empty_rows: true
    remove_empty_columns: true
    normalize_column_names: true
    detect_duplicates: true
    auto_convert_types: true
  
  json:
    flatten_nested: false
    max_flatten_depth: 3
    remove_null_fields: true
  
  unstructured:
    chunking_strategy: "semantic"  # semantic, fixed, sentence, paragraph
    chunk_size: 512
    chunk_overlap: 50
    preserve_formatting: true

# Retrieval settings
retrieval:
  cache_ttl_seconds: 300
  max_cache_size: 1000
  enable_query_optimization: true
  max_query_time_seconds: 30
  streaming_threshold_rows: 10000

# LLM settings
llm:
  provider: "openrouter"
  default_model: "anthropic/claude-3.5-sonnet"
  embedding_model: "openai/text-embedding-3-small"
  max_tokens: 4000
  temperature: 0
  
# Performance settings
performance:
  parallel_uploads: true
  max_workers: 4
  enable_indexes: true
  query_timeout: 30

# Logging
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  log_queries: true
  log_to_file: true
  max_log_size_mb: 100
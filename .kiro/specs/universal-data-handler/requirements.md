# Requirements Document

## Introduction

A universal data management system that can be installed on any company's computers to handle all their data regardless of format. The system provides automated data ingestion, cleaning, organization, and intelligent retrieval through natural language queries. This is Layer 1 (Data Management Layer) of the light_ai multi-layer system, designed to work entirely on-premises with zero external dependencies except OpenRouter API for LLM capabilities.

## Glossary

- **System**: The universal data handler system (light_ai_data_manage)
- **Client**: Organization or company using the system (client_id)
- **User**: Individual person within a client organization (user_id)
- **Resource**: Any uploaded data file or dataset (resource_id)
- **Structured_Data**: CSV, Excel, TSV, Parquet files with tabular structure
- **JSON_Data**: Raw JSON, JSONL, nested JSON structures
- **Unstructured_Data**: PDF, TXT, Markdown, DOCX, HTML files
- **Data_Ingestion**: Process of uploading, validating, cleaning, and storing data
- **Natural_Language_Query**: Plain English questions about data
- **Semantic_Search**: AI-powered search using embeddings for unstructured content

## Requirements

### Requirement 1: Universal Data Ingestion

**User Story:** As a business user, I want to upload any type of data file, so that I can store and organize all my company's information in one place.

#### Acceptance Criteria

1. WHEN a user uploads a structured file (CSV, Excel, TSV, Parquet), THE System SHALL validate the file format and store it with automatic schema detection
2. WHEN a user uploads JSON data (raw JSON, JSONL, nested structures), THE System SHALL parse and store it in JSONB format with indexing
3. WHEN a user uploads unstructured files (PDF, TXT, Markdown, DOCX, HTML), THE System SHALL extract text content and create searchable embeddings
4. WHEN any file is uploaded, THE System SHALL assign unique identifiers (client_id, user_id, resource_id) and store metadata
5. WHEN file validation fails, THE System SHALL return descriptive error messages and prevent storage
6. THE System SHALL support files up to 500MB in size by default
7. WHEN duplicate files are detected, THE System SHALL flag them without auto-removal
8. WHEN multiple files are uploaded simultaneously, THE System SHALL support bulk upload operations with parallel processing
9. THE System SHALL provide upload progress tracking and status updates for large files

### Requirement 2: Automatic Data Cleaning

**User Story:** As a business user, I want my data automatically cleaned and standardized, so that I can work with consistent, high-quality information.

#### Acceptance Criteria

1. WHEN structured data is uploaded, THE System SHALL remove completely empty rows and columns automatically
2. WHEN structured data contains whitespace in headers or values, THE System SHALL strip whitespace automatically
3. WHEN structured data is processed, THE System SHALL detect and convert data types automatically
4. WHEN structured data contains missing values, THE System SHALL handle them according to configurable rules (NULL, drop, or fill)
5. WHEN structured data is processed, THE System SHALL normalize column names to lowercase snake_case
6. WHEN JSON data is uploaded, THE System SHALL optionally flatten nested structures to configurable depth
7. WHEN unstructured data is processed, THE System SHALL extract clean text with layout preservation and remove headers/footers/page numbers
8. WHEN unstructured data is processed, THE System SHALL chunk content using semantic chunking (512 tokens with 50 token overlap by default)

### Requirement 3: Hierarchical Data Organization

**User Story:** As a system administrator, I want data organized by client and user hierarchy, so that I can control access and maintain data security.

#### Acceptance Criteria

1. THE System SHALL enforce a three-level hierarchy: client_id → user_id → resource_id
2. WHEN any data is stored, THE System SHALL require valid client_id, user_id, and resource_id (UUID v4 format)
3. WHEN a user queries data, THE System SHALL only return resources they have permission to access
4. WHEN a manager queries data, THE System SHALL optionally include their team's data based on permissions
5. WHEN an admin queries data, THE System SHALL optionally include company-wide data based on permissions
6. THE System SHALL store all three IDs as metadata with every data piece for fast filtering

### Requirement 4: Multi-Database Storage Architecture

**User Story:** As a system architect, I want data stored in appropriate databases for optimal performance, so that queries are fast and storage is efficient.

#### Acceptance Criteria

1. WHEN structured data is stored, THE System SHALL use DuckDB with virtual tables that query original files directly
2. WHEN JSON data is stored, THE System SHALL use DuckDB with native JSONB storage and indexing
3. WHEN unstructured data is stored, THE System SHALL use ChromaDB for embeddings with persistent local storage
4. WHEN metadata is stored, THE System SHALL use SQLite for the resource registry and schema information
5. THE System SHALL maintain original uploaded files in a raw storage directory
6. THE System SHALL create automatic indexes on user_id and client_id for fast filtering
7. THE System SHALL support single-file databases with zero server setup required

### Requirement 5: Comprehensive Data Versioning

**User Story:** As a business user, I want complete version history of my data, so that I can track changes and rollback if needed.

#### Acceptance Criteria

1. WHEN a resource is updated, THE System SHALL increment the version number and store the new version alongside the old
2. WHEN a resource is updated, THE System SHALL preserve the original data without destructive changes
3. WHEN a user requests a specific version, THE System SHALL return the exact data from that version
4. WHEN a user requests current data, THE System SHALL return the latest version by default
5. THE System SHALL maintain complete audit trail of all operations (upload, clean, transform, delete) in the lineage table
6. WHEN any operation is performed, THE System SHALL log who performed it and when in the metadata registry

### Requirement 6: Lightning-Fast Data Retrieval

**User Story:** As a business user, I want to get answers to my data questions in under 1 second, so that I can make quick decisions without waiting.

#### Acceptance Criteria

1. WHEN a user requests original resource data, THE System SHALL return it in under 1 second for files up to 100MB
2. WHEN a user performs simple SQL queries on structured data, THE System SHALL return results in under 1 second
3. WHEN a user performs semantic search on unstructured data, THE System SHALL return top 5 results in under 3 seconds
4. THE System SHALL implement LRU caching with configurable TTL for query results (default 5 minutes)
5. THE System SHALL implement lazy loading to only load data when needed
6. WHEN large result sets are returned, THE System SHALL stream results instead of loading all into memory
7. THE System SHALL support parallel execution for multi-resource queries
8. WHEN processing small files (10MB CSV), THE System SHALL complete upload in under 2 seconds
9. WHEN processing large documents (100 pages), THE System SHALL complete processing in under 5 seconds
10. WHEN streaming results exceed 10,000 rows, THE System SHALL automatically switch to streaming mode

### Requirement 7: Natural Language Query Interface

**User Story:** As a business user, I want to ask questions about my data in plain English, so that I can get insights without learning SQL or technical skills.

#### Acceptance Criteria

1. WHEN a user asks a natural language question about structured data, THE System SHALL convert it to SQL using OpenRouter LLM and return results with explanation
2. WHEN a user asks questions about unstructured data, THE System SHALL perform semantic search using embeddings and return relevant chunks
3. WHEN a user asks complex questions spanning multiple resources, THE System SHALL identify relevant data sources and synthesize answers
4. THE System SHALL provide explanations of what queries were executed and why
5. WHEN natural language processing fails, THE System SHALL return helpful error messages suggesting alternative phrasings
6. THE System SHALL support follow-up questions that reference previous query context

### Requirement 8: Cross-Resource Data Analysis

**User Story:** As a data analyst, I want to query across multiple data sources simultaneously, so that I can find relationships and insights across all my data.

#### Acceptance Criteria

1. WHEN a user queries multiple structured resources, THE System SHALL support SQL joins across different CSV/Excel files
2. WHEN a user creates derived fields, THE System SHALL allow custom calculations and classifications based on existing data
3. WHEN a user searches unstructured data, THE System SHALL search across all accessible documents and return ranked results
4. THE System SHALL support filtering results by resource type, date range, or specific resources
5. WHEN cross-resource queries are performed, THE System SHALL optimize execution by identifying the most efficient query plan

### Requirement 9: AI Data Analyst Agent

**User Story:** As a business executive, I want an AI agent that can analyze my data and provide comprehensive reports, so that I can understand trends and make informed decisions.

#### Acceptance Criteria

1. WHEN a user asks a complex analytical question, THE AI_Agent SHALL identify all relevant resources automatically
2. WHEN the AI_Agent processes a question, THE System SHALL retrieve schemas and sample data to understand context
3. WHEN the AI_Agent generates analysis, THE System SHALL execute queries across both structured and unstructured data
4. WHEN the AI_Agent completes analysis, THE System SHALL synthesize findings into a coherent report with insights
5. THE AI_Agent SHALL explain its reasoning and cite specific data sources for all conclusions
6. WHEN analysis involves trends or comparisons, THE AI_Agent SHALL provide visualizations or charts if requested

### Requirement 10: Robust Data Management Operations

**User Story:** As a system administrator, I want comprehensive data management capabilities, so that I can maintain data integrity and system performance.

#### Acceptance Criteria

1. WHEN a resource is deleted, THE System SHALL implement soft delete by default (mark as deleted, move to trash, retain for 30 days)
2. WHEN hard delete is requested, THE System SHALL permanently remove all data and archive metadata for audit purposes
3. WHEN system optimization is requested, THE System SHALL support vacuum operations and index rebuilding
4. THE System SHALL support data export in multiple formats (CSV, JSON, Parquet, Excel)
5. THE System SHALL support full system backup and restore operations
6. WHEN cache management is needed, THE System SHALL support selective cache clearing by scope
7. THE System SHALL provide system statistics including storage usage, query performance, and resource counts

### Requirement 11: Zero-Configuration Installation

**User Story:** As an IT administrator, I want the system to work immediately after installation, so that I can deploy it without complex setup procedures.

#### Acceptance Criteria

1. THE System SHALL be installable with a single pip install command
2. THE System SHALL work out-of-the-box on Windows, Linux, and macOS with only OpenRouter API key configuration
3. THE System SHALL use only pip-installable dependencies with no external services required
4. THE System SHALL create all necessary directories and database files automatically on first run
5. THE System SHALL provide sensible defaults for all configuration options
6. WHEN advanced configuration is needed, THE System SHALL support optional YAML configuration file
7. THE System SHALL validate the OpenRouter API key on startup and provide clear error messages if invalid

### Requirement 12: Transaction Safety and Data Integrity

**User Story:** As a business user, I want guarantee that my data operations are safe and atomic, so that I never lose data due to system failures.

#### Acceptance Criteria

1. WHEN any upload operation is performed, THE System SHALL use transactions to ensure all-or-nothing completion
2. WHEN an upload fails at any step, THE System SHALL automatically rollback and cleanup staging areas
3. WHEN concurrent operations occur, THE System SHALL ensure isolation so operations don't interfere with each other
4. THE System SHALL guarantee read-after-write consistency so users immediately see their own changes
5. WHEN system crashes occur, THE System SHALL recover gracefully without data corruption
6. THE System SHALL validate data integrity on startup and report any inconsistencies
7. WHEN critical operations are performed, THE System SHALL ensure durability by persisting data before acknowledging success
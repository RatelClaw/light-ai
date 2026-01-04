# Implementation Plan: Universal Data Handler

## Overview

This implementation plan breaks down the Universal Data Handler system into discrete Python coding tasks. The system will be built using Python with DuckDB for structured data, ChromaDB for embeddings, SQLite for metadata, and OpenRouter for LLM capabilities. Each task builds incrementally toward a complete data management system with two sub-layers: Data Ingestion & Storage and Data Retrieval.

## Tasks

- [x] 1. Set up project structure and core dependencies
  - Create Python package structure with proper __init__.py files
  - Set up pyproject.toml with all required dependencies (duckdb, chromadb, sqlite3, pandas, openai, etc.)
  - Create configuration management system for OpenRouter API key and optional YAML config
  - Implement logging system with configurable levels and file output
  - _Requirements: 11.1, 11.3, 11.4, 11.8_

- [x] 1.1 Write unit tests for project setup
  - Test package imports and dependency availability
  - Test configuration loading and validation
  - Test logging system functionality
  - _Requirements: 11.1, 11.3_

- [x] 2. Implement core data models and hierarchy system
  - Create DataHierarchy class with client_id, user_id, resource_id (UUID v4 validation)
  - Create ResourceMetadata dataclass with all required fields
  - Create SchemaInfo dataclass for schema registry
  - Implement ID validation and hierarchy enforcement functions
  - _Requirements: 3.1, 3.2, 3.6_

- [ ]* 2.1 Write property test for data hierarchy validation
  - **Property 3: Hierarchical Data Organization**
  - **Validates: Requirements 3.1, 3.2, 3.3**

- [ ]* 2.2 Write unit tests for data models
  - Test UUID v4 validation for all ID fields
  - Test dataclass serialization and deserialization
  - Test hierarchy enforcement edge cases
  - _Requirements: 3.1, 3.2_

- [x] 3. Create storage layer foundation
  - Implement automatic directory structure creation (data/structured/, data/json/, etc.)
  - Create database connection managers for DuckDB, ChromaDB, and SQLite
  - Implement SQLite metadata registry schema with all required tables
  - Create storage path utilities and file management functions
  - _Requirements: 4.4, 4.7, 11.4, 11.8_

- [ ]* 3.1 Write property test for storage initialization
  - **Property 11: Zero-Configuration Deployment**
  - **Validates: Requirements 11.1, 11.2, 11.4, 11.8**

- [ ]* 3.2 Write unit tests for storage layer
  - Test directory creation and permissions
  - Test database connection establishment
  - Test metadata registry schema creation
  - _Requirements: 4.4, 4.7, 11.4_

- [x] 4. Implement Sub-Layer 1: File validation and upload system
  - Create file type detection and validation (CSV, Excel, JSON, PDF, TXT, etc.)
  - Implement file size validation (500MB default limit)
  - Create duplicate detection using hash-based comparison
  - Implement upload progress tracking for large files
  - Create bulk upload support with parallel processing
  - _Requirements: 1.1, 1.2, 1.3, 1.5, 1.6, 1.7, 1.8, 1.9_

- [x] 4.1 Write property test for universal file upload
  - **Property 1: Universal File Upload and Processing**
  - **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

- [ ]* 4.2 Write property test for file size and duplicate handling
  - **Property 14: File Size and Duplicate Handling**
  - **Validates: Requirements 1.5, 1.6, 1.7**

- [ ]* 4.3 Write unit tests for file validation
  - Test file type detection accuracy
  - Test size limit enforcement
  - Test duplicate detection with identical and similar files
  - _Requirements: 1.5, 1.6, 1.7_

- [x] 5. Implement data cleaning engine
  - Create structured data cleaning (remove empty rows/columns, strip whitespace, normalize column names)
  - Implement automatic data type detection and conversion
  - Create missing value handling with configurable strategies
  - Implement JSON flattening with configurable depth
  - Create unstructured data text extraction and cleaning
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

- [ ]* 5.1 Write property test for automatic data cleaning
  - **Property 2: Automatic Data Cleaning Consistency**
  - **Validates: Requirements 2.1, 2.2, 2.3, 2.5**

- [ ]* 5.2 Write unit tests for data cleaning
  - Test empty row/column removal
  - Test whitespace stripping
  - Test column name normalization
  - Test data type detection accuracy
  - _Requirements: 2.1, 2.2, 2.3, 2.5_

- [x] 6. Implement storage routing and database operations
  - Create DuckDB virtual table setup for structured data (CSV, Excel direct querying)
  - Implement DuckDB JSONB storage for JSON data with indexing
  - Create ChromaDB collection management and embedding storage
  - Implement SQLite metadata registry operations (insert, update, query)
  - Create automatic indexing on user_id and client_id for fast filtering
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [x] 6.1 Write property test for multi-database storage routing
  - **Property 4: Multi-Database Storage Routing**
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**

- [ ]* 6.2 Write unit tests for database operations
  - Test DuckDB virtual table creation and querying
  - Test ChromaDB collection creation and embedding storage
  - Test SQLite metadata operations
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 7. Implement versioning and audit system
  - Create version management with non-destructive updates
  - Implement complete audit trail logging in lineage table
  - Create version retrieval and rollback functionality
  - Implement soft delete with 30-day retention and hard delete options
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 10.1, 10.2_

- [ ]* 7.1 Write property test for non-destructive versioning
  - **Property 5: Non-Destructive Versioning**
  - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

- [ ]* 7.2 Write unit tests for versioning system
  - Test version increment and storage
  - Test audit trail logging
  - Test version retrieval accuracy
  - Test soft and hard delete operations
  - _Requirements: 5.1, 5.2, 10.1, 10.2_

- [x] 8. Checkpoint - Ensure Sub-Layer 1 (Data Ingestion & Storage) is complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Implement Sub-Layer 2: SQL query engine
  - Create DuckDB query execution with virtual table support
  - Implement cross-resource SQL joins across different CSV/Excel files
  - Create derived field calculations and custom classifications
  - Implement query optimization and execution planning
  - Add streaming support for large result sets (>10,000 rows)
  - _Requirements: 6.2, 6.6, 6.10, 8.1, 8.2, 8.5_

- [ ]* 9.1 Write unit tests for SQL query engine
  - Test basic SQL query execution
  - Test cross-resource joins
  - Test derived field calculations
  - Test streaming for large results
  - _Requirements: 6.2, 8.1, 8.2_

- [ ] 10. Implement natural language processing system
  - Create OpenRouter API integration for LLM queries
  - Implement schema-aware text-to-SQL generation
  - Create query explanation and result interpretation
  - Implement follow-up question context management
  - Add error handling with helpful alternative suggestions
  - _Requirements: 7.1, 7.3, 7.4, 7.5, 7.6_

- [-] 10.1 Write property test for natural language query processing
  - **Property 7: Natural Language Query Processing**
  - **Validates: Requirements 7.1, 7.2, 7.3, 7.4**

- [ ]* 10.2 Write unit tests for NLP system
  - Test text-to-SQL generation with various question types
  - Test query explanation generation
  - Test error handling and suggestions
  - _Requirements: 7.1, 7.4, 7.5_

- [x] 11. Implement semantic search engine
  - Create OpenRouter embedding generation integration
  - Implement ChromaDB semantic search with multiple strategies (semantic, keyword, hybrid, MMR)
  - Create multi-query retrieval with automatic query variations
  - Implement unstructured data chunking with semantic chunking (512 tokens, 50 overlap)
  - Add result ranking and relevance scoring
  - _Requirements: 2.8, 7.2, 7.7, 7.8, 8.3, 8.4_

- [ ]* 11.1 Write unit tests for semantic search
  - Test embedding generation and storage
  - Test different search strategies
  - Test multi-query retrieval
  - Test result ranking accuracy
  - _Requirements: 7.2, 7.7, 7.8_

- [x] 12. Implement AI data analyst agent
  - Create automatic resource identification for complex questions
  - Implement schema and sample data retrieval for context
  - Create cross-format data synthesis (structured + unstructured)
  - Implement report generation with insights and visualizations
  - Add reasoning explanation and source citation
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [ ]* 12.1 Write property test for AI data analyst intelligence
  - **Property 9: AI Data Analyst Intelligence**
  - **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**

- [ ]* 12.2 Write unit tests for AI analyst
  - Test resource identification accuracy
  - Test context retrieval and synthesis
  - Test report generation quality
  - _Requirements: 9.1, 9.2, 9.4_

- [SKIPPED] 13. Implement caching and performance optimization
  - Create LRU cache with configurable TTL (default 5 minutes)
  - Implement lazy loading for data access
  - Create parallel execution support for multi-resource queries
  - Add query result streaming for large datasets
  - Implement cache management and selective clearing
  - _Requirements: 6.4, 6.5, 6.7, 6.10, 10.6_
  - **Note: Skipped for now, will be implemented as improvement after final completion**

- [SKIPPED]* 13.1 Write property test for caching and optimization
  - **Property 15: Caching and Optimization Behavior**
  - **Validates: Requirements 6.4, 6.5, 6.6, 6.10, 10.6**
  - **Note: Skipped along with task 13**

- [SKIPPED]* 13.2 Write unit tests for performance features
  - Test LRU cache behavior and TTL expiration
  - Test lazy loading implementation
  - Test parallel query execution
  - _Requirements: 6.4, 6.5, 6.7_
  - **Note: Skipped along with task 13**

- [x] 14. Implement comprehensive API layer
  - Create Sub-Layer 1 APIs: upload_file(), upload_json(), upload_bulk(), update_resource(), delete_resource()
  - Create Sub-Layer 2 APIs: get_resource(), query_structured(), query_natural(), search_unstructured(), ask_data_analyst()
  - Implement metadata APIs: get_resource_metadata(), list_resources(), get_schema(), get_statistics()
  - Create administration APIs: clear_cache(), get_system_stats(), optimize_storage(), export_resource(), backup_data(), restore_data()
  - Add consistent response formatting and comprehensive error handling
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.9_

- [x] 14.1 Write property test for complete API coverage
  - **Property 12: Complete API Coverage**
  - **Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5, 12.9**

- [ ]* 14.2 Write unit tests for API layer
  - Test all Sub-Layer 1 API endpoints
  - Test all Sub-Layer 2 API endpoints
  - Test metadata and administration APIs
  - Test error handling and response formatting
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ] 15. Implement data management operations
  - Create export functionality in multiple formats (CSV, JSON, Parquet, Excel)
  - Implement full system backup and restore operations
  - Create system optimization tools (vacuum, index rebuilding)
  - Add system statistics and monitoring (storage usage, query performance, resource counts)
  - _Requirements: 10.3, 10.4, 10.5, 10.7_

- [ ]* 15.1 Write property test for data management operations
  - **Property 10: Comprehensive Data Management Operations**
  - **Validates: Requirements 10.1, 10.2, 10.4, 10.5**

- [ ]* 15.2 Write unit tests for data management
  - Test export in all supported formats
  - Test backup and restore operations
  - Test system optimization tools
  - _Requirements: 10.4, 10.5, 10.7_

- [ ] 16. Implement transaction safety and error handling
  - Create transaction management for all critical operations
  - Implement automatic rollback and cleanup on failures
  - Add concurrency control and isolation guarantees
  - Create graceful crash recovery and data integrity validation
  - Implement comprehensive error handling with descriptive messages
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7_

- [ ] 16.1 Write property test for transaction safety
  - **Property 13: Transaction Safety and Data Integrity**
  - **Validates: Requirements 15.1, 15.2, 15.4, 15.7**

- [ ]* 16.2 Write unit tests for error handling
  - Test transaction rollback on failures
  - Test concurrency control
  - Test crash recovery procedures
  - _Requirements: 15.1, 15.2, 15.5_

- [ ] 17. Implement performance benchmarking and validation
  - Create performance testing suite for all benchmark requirements
  - Implement response time validation (1 second for retrieval, 3 seconds for search)
  - Add upload performance testing (2 seconds for 10MB CSV, 5 seconds for 100-page docs)
  - Create load testing for concurrent operations
  - _Requirements: 6.1, 6.2, 6.3, 6.8, 6.9_

- [ ]* 17.1 Write property test for performance benchmarks
  - **Property 6: Performance Benchmarks**
  - **Validates: Requirements 6.1, 6.2, 6.3, 6.8, 6.9**

- [ ]* 17.2 Write performance validation tests
  - Test response time requirements
  - Test upload performance benchmarks
  - Test concurrent operation handling
  - _Requirements: 6.1, 6.2, 6.3_

- [ ] 18. Create comprehensive integration and end-to-end tests
  - Test complete data ingestion workflows (upload → clean → store → retrieve)
  - Test cross-resource analysis scenarios
  - Test AI analyst end-to-end functionality
  - Test system recovery and backup/restore workflows
  - _Requirements: All major workflows_

- [ ]* 18.1 Write integration tests for complete workflows
  - Test end-to-end data processing pipelines
  - Test cross-component interactions
  - Test system-wide error recovery
  - _Requirements: All major requirements_

- [ ] 19. Final checkpoint and system validation
  - Ensure all tests pass, ask the user if questions arise.
  - Validate all API endpoints are functional
  - Verify performance benchmarks are met
  - Confirm zero-configuration installation works on target platforms

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties with minimum 100 iterations
- Unit tests validate specific examples and edge cases
- The system uses Python with DuckDB, ChromaDB, SQLite, and OpenRouter API
- All tasks build incrementally toward a complete two-sub-layer data management system
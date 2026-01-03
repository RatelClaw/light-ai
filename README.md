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

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Set up environment:
   ```bash
   cp .env.example .env
   # Add your OpenRouter API key to .env
   ```

3. Run the demo:
   ```bash
   python3 simple_api_demo.py
   ```

4. Launch the web interface:
   ```bash
   streamlit run streamlit_ui.py
   ```

## Architecture

The system is built with two main layers:
- **Sub-Layer 1**: Data Ingestion & Storage
- **Sub-Layer 2**: Data Retrieval & Analysis

See `.kiro/specs/universal-data-handler/` for detailed documentation.
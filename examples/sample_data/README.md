# UNIVERSAL DATA HANDLER - SAMPLE DATA & TESTING GUIDE

## Overview
This directory contains comprehensive sample datasets for testing all Sub-Layer 1 and Sub-Layer 2 APIs of the Universal Data Handler system. Each user folder represents a different use case with realistic data scenarios.

## Quick Start Command
To run the Streamlit UI:
```bash
streamlit run streamlit_ui.py
```

## User Scenarios

### 👨‍💼 USER 01 - E-Commerce Business
**Use Case**: Sales analysis and customer insights
- **Data Types**: CSV (sales), JSON (feedback), TXT (manual)
- **Focus**: Business analytics, customer behavior, product performance
- **Best For Testing**: Cross-format analysis, business intelligence queries

### 👩‍💼 USER 02 - HR & Project Management  
**Use Case**: Human resources and project tracking
- **Data Types**: XLSX (employees), JSON (projects), TXT (meetings)
- **Focus**: HR analytics, project performance, team management
- **Best For Testing**: Excel integration, organizational analytics

### 💰 USER 03 - Personal Finance
**Use Case**: Personal financial management and investment tracking
- **Data Types**: CSV (transactions), JSON (portfolio), TXT (budget)
- **Focus**: Financial planning, investment analysis, spending patterns
- **Best For Testing**: Personal data scenarios, financial calculations

### 🔬 USER 04 - Research & Academia
**Use Case**: Clinical research and academic analysis
- **Data Types**: CSV (study data), JSON (results), TXT (literature)
- **Focus**: Statistical analysis, research methodology, academic insights
- **Best For Testing**: Scientific data, statistical queries, research workflows

## Complete API Testing Workflow

### 1. Start the Application
```bash
# Activate virtual environment
source .venv/bin/activate

# Run Streamlit UI
streamlit run streamlit_ui.py
```

### 2. Test Sub-Layer 1 APIs (Data Ingestion)
For each user folder:
1. **Upload Files**: Test different file formats (CSV, JSON, TXT, XLSX)
2. **Bulk Upload**: Upload multiple files simultaneously
3. **Data Cleaning**: Verify automatic data cleaning and validation
4. **Storage Verification**: Confirm data is stored in appropriate databases

### 3. Test Sub-Layer 2 APIs (Data Retrieval)
For each uploaded dataset:
1. **SQL Queries**: Execute structured data queries
2. **Natural Language**: Ask questions in plain English
3. **Semantic Search**: Search unstructured content
4. **AI Analytics**: Get comprehensive data insights

### 4. Cross-User Testing
Test access control and data isolation:
- Verify users can only access their own data
- Test invalid table access (should be denied)
- Confirm proper client/user ID validation

## Sample Client/User IDs

```python
# Use these IDs for consistent testing
USER_01 = {
    "client_id": "client-ecommerce-001",
    "user_id": "user-sales-manager-001"
}

USER_02 = {
    "client_id": "client-techcorp-002", 
    "user_id": "user-hr-manager-002"
}

USER_03 = {
    "client_id": "client-personal-003",
    "user_id": "user-individual-003"
}

USER_04 = {
    "client_id": "client-research-004",
    "user_id": "user-researcher-004"
}
```

## Expected System Behavior

### ✅ Successful Operations
- **File Upload**: All formats should upload and process successfully
- **Data Cleaning**: Automatic cleaning with statistics reported
- **SQL Queries**: Return accurate results with proper access control
- **Natural Language**: Convert questions to SQL and return data
- **Semantic Search**: Find relevant content in unstructured data
- **AI Analysis**: Provide meaningful insights and recommendations

### ❌ Expected Failures (Security Features)
- **Cross-User Access**: Should deny access to other users' data
- **Invalid Tables**: Should reject queries to non-existent tables
- **Malformed Queries**: Should handle SQL errors gracefully
- **Large Files**: Should respect file size limits (500MB default)

## Performance Benchmarks
The system should meet these performance targets:
- **File Upload**: < 2 seconds for 10MB CSV files
- **Data Retrieval**: < 1 second for basic queries
- **Semantic Search**: < 3 seconds for document search
- **AI Analysis**: < 10 seconds for complex insights

## Data Privacy & Security
- Each user's data is isolated by client_id and user_id
- Access control prevents cross-user data access
- File uploads are validated for type and size
- SQL injection protection through parameterized queries

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure virtual environment is activated
2. **Database Errors**: Check if databases are properly initialized
3. **File Not Found**: Verify file paths are correct
4. **Access Denied**: Confirm client_id and user_id are valid

### Debug Mode
Enable detailed logging by setting environment variable:
```bash
export LOG_LEVEL=DEBUG
```

## Advanced Testing Scenarios

### 1. Stress Testing
- Upload large files (approaching 500MB limit)
- Execute complex multi-table joins
- Perform bulk operations with many files

### 2. Edge Cases
- Upload empty files
- Query non-existent resources
- Use special characters in queries
- Test with malformed JSON data

### 3. Integration Testing
- Test complete workflows from upload to analysis
- Verify data consistency across operations
- Test system recovery after errors

## Support & Documentation
- Check individual user folder INSTRUCTIONS.md for detailed examples
- Review API documentation in the main project README
- Examine the tasks.md file for implementation details

## Contributing
When adding new sample data:
1. Create realistic, representative datasets
2. Include comprehensive instruction files
3. Test all API endpoints with the new data
4. Document expected results and edge cases

---

**Ready to test?** Start with USER 01 for a comprehensive introduction to all system capabilities!
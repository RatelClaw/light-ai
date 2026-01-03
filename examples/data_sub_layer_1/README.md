# Sub-Layer 1 Testing Data and Scripts

This directory contains sample data files and testing scripts for Sub-Layer 1 functionality.

## 📁 Sample Data Files

### Structured Data (CSV/TSV)
- `sample_customers.csv` - Clean customer data with various data types
- `sample_inventory.tsv` - Tab-separated inventory data
- `messy_data.csv` - Intentionally messy data for testing cleaning functionality

### JSON Data
- `sample_products.json` - Well-structured product catalog
- `sample_orders.jsonl` - JSON Lines format order data
- `nested_config.json` - Deeply nested configuration data for flattening tests

### Unstructured Data
- `sample_report.txt` - Business report with headers, sections, and formatting
- `sample_documentation.md` - Markdown API documentation
- `sample_config.html` - HTML configuration dashboard

## 🧪 Testing Scripts

### Main Test Suite: `../sub_layer_1_load.py`
Comprehensive testing script that demonstrates all Sub-Layer 1 functionality:

```bash
python examples/sub_layer_1_load.py
```

**Features tested:**
- ✅ File type detection and validation
- ✅ Duplicate detection using file hashes
- ✅ Data cleaning for all supported formats
- ✅ Upload progress tracking
- ✅ Single file upload
- ✅ Bulk parallel upload
- ✅ Supported format enumeration

### Client Scenarios: `client_scenarios.py`
Simulates different client types and use cases:

```bash
python examples/data_sub_layer_1/client_scenarios.py
```

**Scenarios tested:**
- 🏪 **Small Business**: Basic data needs, simple cleaning
- 🏢 **Enterprise**: Complex data, advanced cleaning requirements
- 📊 **Data Analyst**: Research data with missing values, custom cleaning
- 🚀 **Startup**: Mixed data types, flexible cleaning needs
- 👥 **Multi-user**: Multiple users per client
- 🚨 **Error Handling**: Invalid files, corrupted data, bad parameters

## 🎯 Data Quality Test Cases

### Clean Data Examples
- `sample_customers.csv` - Perfect data for baseline testing
- `sample_products.json` - Well-structured JSON
- `sample_inventory.tsv` - Clean tab-separated data

### Messy Data Examples
- `messy_data.csv` - Contains:
  - Extra whitespace in headers and values
  - Missing values in various columns
  - Inconsistent date formats
  - Mixed boolean representations (TRUE/false/1/0/yes/no)
  - Empty rows and columns

- `nested_config.json` - Contains:
  - Deep nesting (3+ levels)
  - Null values
  - Mixed data types
  - Complex object structures

## 🔧 Cleaning Configuration Examples

### Basic Cleaning (Small Business)
```python
CleaningConfig(
    remove_empty_rows=True,
    strip_whitespace=True,
    normalize_column_names=True,
    missing_value_strategy=MissingValueStrategy.NULL
)
```

### Advanced Cleaning (Enterprise)
```python
CleaningConfig(
    remove_empty_rows=True,
    remove_empty_columns=True,
    strip_whitespace=True,
    normalize_column_names=True,
    detect_data_types=True,
    missing_value_strategy=MissingValueStrategy.FILL_MODE,
    flatten_json=True,
    normalize_json_keys=True
)
```

### Research Data Cleaning (Data Analyst)
```python
CleaningConfig(
    remove_empty_rows=True,
    strip_whitespace=True,
    normalize_column_names=True,
    detect_data_types=True,
    missing_value_strategy=MissingValueStrategy.FILL_MEAN
)
```

## 📊 Expected Test Results

### File Validation
- All sample files should be correctly identified by type
- File sizes should be reported accurately
- MIME type validation should pass (with warnings for edge cases)

### Data Cleaning
- `messy_data.csv`: Should normalize column names, handle missing values, detect data types
- `nested_config.json`: Should flatten structure, normalize keys, remove nulls
- `sample_report.txt`: Should create semantic chunks, normalize whitespace

### Upload Operations
- Single uploads should complete with progress tracking
- Bulk uploads should process multiple files in parallel
- Duplicate detection should identify identical files

### Progress Tracking
- Should track upload progress from 0-100%
- Should handle completion and failure states
- Should provide statistics across multiple uploads

## 🚀 Running the Tests

1. **Ensure dependencies are installed:**
   ```bash
   pip install pandas numpy python-magic
   ```

2. **Run the main test suite:**
   ```bash
   python examples/sub_layer_1_load.py
   ```

3. **Run client scenario tests:**
   ```bash
   python examples/data_sub_layer_1/client_scenarios.py
   ```

4. **Check the output for:**
   - ✅ Green checkmarks for successful operations
   - ❌ Red X marks for expected failures
   - 📊 Statistics and summaries
   - 🎉 Final success message

## 🔍 Troubleshooting

### Common Issues
- **Import errors**: Ensure you're running from the project root
- **File not found**: Check that sample data files exist
- **Permission errors**: Ensure write access to data directories
- **Missing dependencies**: Install required packages (pandas, numpy, python-magic)

### Debug Mode
Add logging configuration to see detailed operation logs:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Performance Expectations

### File Processing Times (approximate)
- Small files (<1MB): <100ms
- Medium files (1-10MB): <1s
- Large files (10-100MB): <10s

### Cleaning Performance
- CSV files: ~1000 rows/second
- JSON files: ~500 objects/second
- Text files: ~10MB/second

### Upload Performance
- Sequential: Limited by I/O
- Parallel (3 workers): ~3x faster for multiple files
- Progress tracking: <1ms overhead per update
"""
Data cleaning engine for Sub-Layer 1.

Handles automatic data cleaning, standardization, and preprocessing for all data types.
"""

import json
import re
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass, field
import io
import zipfile
from datetime import datetime

# For unstructured data processing
try:
    import PyPDF2
    import docx
    from bs4 import BeautifulSoup
    import markdown
except ImportError as e:
    # These are optional dependencies for unstructured data
    pass

from ..core.models import DataType, ResourceType
from ..config import get_config
from ..logger import get_logger

logger = get_logger(__name__)


class MissingValueStrategy(Enum):
    """Strategies for handling missing values."""
    NULL = "null"           # Keep as NULL/NaN
    DROP_ROWS = "drop_rows" # Drop rows with missing values
    DROP_COLS = "drop_cols" # Drop columns with missing values
    FILL_MEAN = "fill_mean" # Fill with mean (numeric only)
    FILL_MODE = "fill_mode" # Fill with mode (most frequent)
    FILL_ZERO = "fill_zero" # Fill with zero
    FILL_EMPTY = "fill_empty" # Fill with empty string


@dataclass
class CleaningConfig:
    """Configuration for data cleaning operations."""
    
    # Structured data cleaning
    remove_empty_rows: bool = True
    remove_empty_columns: bool = True
    strip_whitespace: bool = True
    normalize_column_names: bool = True
    detect_data_types: bool = True
    missing_value_strategy: MissingValueStrategy = MissingValueStrategy.NULL
    missing_value_threshold: float = 0.5  # Drop cols/rows if >50% missing
    
    # JSON data cleaning
    flatten_json: bool = False
    max_flatten_depth: int = 3
    normalize_json_keys: bool = True
    remove_null_objects: bool = True
    
    # Unstructured data cleaning
    preserve_layout: bool = True
    remove_headers_footers: bool = True
    remove_page_numbers: bool = True
    chunk_size_tokens: int = 512
    chunk_overlap_tokens: int = 50
    min_chunk_size: int = 50  # Minimum characters per chunk
    
    # General settings
    encoding: str = "utf-8"
    date_formats: List[str] = field(default_factory=lambda: [
        "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"
    ])


class StructuredDataCleaner:
    """Cleans structured data (CSV, Excel, TSV, Parquet)."""
    
    def __init__(self, config: CleaningConfig = None):
        """Initialize structured data cleaner."""
        self.config = config or CleaningConfig()
    
    def clean_dataframe(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Clean a pandas DataFrame according to configuration.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Tuple of (cleaned_df, cleaning_stats)
        """
        original_shape = df.shape
        cleaning_stats = {
            "original_rows": original_shape[0],
            "original_columns": original_shape[1],
            "operations_performed": [],
            "columns_renamed": {},
            "data_types_detected": {},
            "missing_values_handled": {},
        }
        
        logger.info(f"Starting structured data cleaning: {original_shape[0]} rows, {original_shape[1]} columns")
        
        # 1. Strip whitespace from string columns and headers
        if self.config.strip_whitespace:
            df = self._strip_whitespace(df, cleaning_stats)
        
        # 2. Normalize column names
        if self.config.normalize_column_names:
            df = self._normalize_column_names(df, cleaning_stats)
        
        # 3. Remove completely empty rows
        if self.config.remove_empty_rows:
            df = self._remove_empty_rows(df, cleaning_stats)
        
        # 4. Remove completely empty columns
        if self.config.remove_empty_columns:
            df = self._remove_empty_columns(df, cleaning_stats)
        
        # 5. Handle missing values
        df = self._handle_missing_values(df, cleaning_stats)
        
        # 6. Detect and convert data types
        if self.config.detect_data_types:
            df = self._detect_and_convert_types(df, cleaning_stats)
        
        final_shape = df.shape
        cleaning_stats.update({
            "final_rows": final_shape[0],
            "final_columns": final_shape[1],
            "rows_removed": original_shape[0] - final_shape[0],
            "columns_removed": original_shape[1] - final_shape[1],
        })
        
        logger.info(
            f"Structured data cleaning completed: {final_shape[0]} rows, {final_shape[1]} columns "
            f"({cleaning_stats['rows_removed']} rows, {cleaning_stats['columns_removed']} columns removed)"
        )
        
        return df, cleaning_stats
    
    def _strip_whitespace(self, df: pd.DataFrame, stats: Dict[str, Any]) -> pd.DataFrame:
        """Strip whitespace from string columns and headers."""
        # Strip column names
        df.columns = df.columns.str.strip()
        
        # Strip string values
        string_columns = df.select_dtypes(include=['object']).columns
        for col in string_columns:
            df[col] = df[col].astype(str).str.strip()
            # Convert back to NaN if it was originally NaN
            df[col] = df[col].replace('nan', np.nan)
        
        stats["operations_performed"].append("strip_whitespace")
        return df
    
    def _normalize_column_names(self, df: pd.DataFrame, stats: Dict[str, Any]) -> pd.DataFrame:
        """Normalize column names to lowercase snake_case."""
        original_columns = df.columns.tolist()
        
        normalized_columns = []
        for col in original_columns:
            # Convert to string and normalize
            normalized = str(col).lower()
            # Replace spaces and special characters with underscores
            normalized = re.sub(r'[^\w\s]', '_', normalized)
            normalized = re.sub(r'\s+', '_', normalized)
            # Remove multiple consecutive underscores
            normalized = re.sub(r'_+', '_', normalized)
            # Remove leading/trailing underscores
            normalized = normalized.strip('_')
            
            # Ensure column name is not empty
            if not normalized:
                normalized = f"column_{len(normalized_columns)}"
            
            normalized_columns.append(normalized)
        
        # Handle duplicate column names
        seen = set()
        final_columns = []
        for col in normalized_columns:
            original_col = col
            counter = 1
            while col in seen:
                col = f"{original_col}_{counter}"
                counter += 1
            seen.add(col)
            final_columns.append(col)
        
        # Update DataFrame columns
        df.columns = final_columns
        
        # Record renames
        for orig, norm in zip(original_columns, final_columns):
            if orig != norm:
                stats["columns_renamed"][orig] = norm
        
        stats["operations_performed"].append("normalize_column_names")
        return df
    
    def _remove_empty_rows(self, df: pd.DataFrame, stats: Dict[str, Any]) -> pd.DataFrame:
        """Remove completely empty rows."""
        initial_rows = len(df)
        df = df.dropna(how='all')
        rows_removed = initial_rows - len(df)
        
        if rows_removed > 0:
            stats["operations_performed"].append(f"remove_empty_rows ({rows_removed} removed)")
        
        return df
    
    def _remove_empty_columns(self, df: pd.DataFrame, stats: Dict[str, Any]) -> pd.DataFrame:
        """Remove completely empty columns."""
        initial_cols = len(df.columns)
        df = df.dropna(axis=1, how='all')
        cols_removed = initial_cols - len(df.columns)
        
        if cols_removed > 0:
            stats["operations_performed"].append(f"remove_empty_columns ({cols_removed} removed)")
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame, stats: Dict[str, Any]) -> pd.DataFrame:
        """Handle missing values according to strategy."""
        strategy = self.config.missing_value_strategy
        threshold = self.config.missing_value_threshold
        
        missing_info = {}
        
        if strategy == MissingValueStrategy.NULL:
            # Keep as NaN - no action needed
            missing_info["strategy"] = "kept_as_null"
        
        elif strategy == MissingValueStrategy.DROP_ROWS:
            initial_rows = len(df)
            # Drop rows where more than threshold of values are missing
            df = df.dropna(thresh=int(len(df.columns) * (1 - threshold)))
            rows_dropped = initial_rows - len(df)
            missing_info["strategy"] = "drop_rows"
            missing_info["rows_dropped"] = rows_dropped
        
        elif strategy == MissingValueStrategy.DROP_COLS:
            initial_cols = len(df.columns)
            # Drop columns where more than threshold of values are missing
            df = df.dropna(axis=1, thresh=int(len(df) * (1 - threshold)))
            cols_dropped = initial_cols - len(df.columns)
            missing_info["strategy"] = "drop_cols"
            missing_info["cols_dropped"] = cols_dropped
        
        elif strategy == MissingValueStrategy.FILL_MEAN:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if df[col].isna().any():
                    mean_val = df[col].mean()
                    df[col].fillna(mean_val, inplace=True)
                    missing_info[col] = f"filled_with_mean_{mean_val:.2f}"
            missing_info["strategy"] = "fill_mean"
        
        elif strategy == MissingValueStrategy.FILL_MODE:
            for col in df.columns:
                if df[col].isna().any():
                    mode_val = df[col].mode()
                    if not mode_val.empty:
                        df[col].fillna(mode_val.iloc[0], inplace=True)
                        missing_info[col] = f"filled_with_mode_{mode_val.iloc[0]}"
            missing_info["strategy"] = "fill_mode"
        
        elif strategy == MissingValueStrategy.FILL_ZERO:
            df.fillna(0, inplace=True)
            missing_info["strategy"] = "fill_zero"
        
        elif strategy == MissingValueStrategy.FILL_EMPTY:
            df.fillna("", inplace=True)
            missing_info["strategy"] = "fill_empty"
        
        stats["missing_values_handled"] = missing_info
        if missing_info.get("strategy") != "kept_as_null":
            stats["operations_performed"].append(f"handle_missing_values ({strategy.value})")
        
        return df
    
    def _detect_and_convert_types(self, df: pd.DataFrame, stats: Dict[str, Any]) -> pd.DataFrame:
        """Detect and convert data types automatically."""
        type_conversions = {}
        
        for col in df.columns:
            original_dtype = str(df[col].dtype)
            
            # Skip if already numeric
            if df[col].dtype in [np.int64, np.float64, np.bool_]:
                continue
            
            # Try to convert to numeric
            numeric_series = pd.to_numeric(df[col], errors='coerce')
            if not numeric_series.isna().all():
                # Check if it's integer or float
                if numeric_series.dropna().apply(lambda x: x.is_integer()).all():
                    df[col] = numeric_series.astype('Int64')  # Nullable integer
                    type_conversions[col] = f"{original_dtype} -> Int64"
                else:
                    df[col] = numeric_series
                    type_conversions[col] = f"{original_dtype} -> float64"
                continue
            
            # Try to convert to datetime
            for date_format in self.config.date_formats:
                try:
                    df[col] = pd.to_datetime(df[col], format=date_format, errors='coerce')
                    if not df[col].isna().all():
                        type_conversions[col] = f"{original_dtype} -> datetime64"
                        break
                except:
                    continue
            else:
                # Try general datetime parsing
                try:
                    datetime_series = pd.to_datetime(df[col], errors='coerce')
                    if not datetime_series.isna().all():
                        df[col] = datetime_series
                        type_conversions[col] = f"{original_dtype} -> datetime64"
                        continue
                except:
                    pass
            
            # Try to convert to boolean (only for string columns)
            if df[col].dtype == 'object':
                try:
                    string_values = df[col].dropna().astype(str).str.lower()
                    if string_values.isin(['true', 'false', '1', '0', 'yes', 'no']).all() and len(string_values) > 0:
                        bool_map = {'true': True, 'false': False, '1': True, '0': False, 
                                   'yes': True, 'no': False}
                        df[col] = df[col].astype(str).str.lower().map(bool_map)
                        type_conversions[col] = f"{original_dtype} -> bool"
                except:
                    pass
        
        stats["data_types_detected"] = type_conversions
        if type_conversions:
            stats["operations_performed"].append("detect_and_convert_types")
        
        return df


class JSONDataCleaner:
    """Cleans JSON data with optional flattening."""
    
    def __init__(self, config: CleaningConfig = None):
        """Initialize JSON data cleaner."""
        self.config = config or CleaningConfig()
    
    def clean_json(self, data: Union[Dict, List, str]) -> Tuple[Union[Dict, List], Dict[str, Any]]:
        """
        Clean JSON data according to configuration.
        
        Args:
            data: JSON data (dict, list, or JSON string)
            
        Returns:
            Tuple of (cleaned_data, cleaning_stats)
        """
        cleaning_stats = {
            "operations_performed": [],
            "keys_normalized": {},
            "objects_removed": 0,
            "flattened": False,
        }
        
        # Parse JSON string if needed
        if isinstance(data, str):
            try:
                data = json.loads(data)
                cleaning_stats["operations_performed"].append("parse_json_string")
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON string: {e}")
        
        logger.info(f"Starting JSON data cleaning: {type(data).__name__}")
        
        # Remove null objects if configured
        if self.config.remove_null_objects:
            data = self._remove_null_objects(data, cleaning_stats)
        
        # Normalize keys if configured
        if self.config.normalize_json_keys:
            data = self._normalize_keys(data, cleaning_stats)
        
        # Flatten if configured
        if self.config.flatten_json:
            data = self._flatten_json(data, cleaning_stats)
        
        logger.info(f"JSON data cleaning completed: {len(cleaning_stats['operations_performed'])} operations")
        
        return data, cleaning_stats
    
    def _remove_null_objects(self, data: Union[Dict, List], stats: Dict[str, Any]) -> Union[Dict, List]:
        """Remove null/empty objects from JSON data."""
        removed_count = 0
        
        if isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                if value is None or value == {} or value == []:
                    removed_count += 1
                elif isinstance(value, (dict, list)):
                    cleaned[key] = self._remove_null_objects(value, stats)
                else:
                    cleaned[key] = value
            data = cleaned
        
        elif isinstance(data, list):
            cleaned = []
            for item in data:
                if item is None or item == {} or item == []:
                    removed_count += 1
                elif isinstance(item, (dict, list)):
                    cleaned.append(self._remove_null_objects(item, stats))
                else:
                    cleaned.append(item)
            data = cleaned
        
        if removed_count > 0:
            stats["objects_removed"] += removed_count
            if "remove_null_objects" not in stats["operations_performed"]:
                stats["operations_performed"].append("remove_null_objects")
        
        return data
    
    def _normalize_keys(self, data: Union[Dict, List], stats: Dict[str, Any]) -> Union[Dict, List]:
        """Normalize dictionary keys to snake_case."""
        if isinstance(data, dict):
            normalized = {}
            for key, value in data.items():
                # Normalize key
                if isinstance(key, str):
                    normalized_key = re.sub(r'[^\w\s]', '_', key.lower())
                    normalized_key = re.sub(r'\s+', '_', normalized_key)
                    normalized_key = re.sub(r'_+', '_', normalized_key).strip('_')
                    
                    if normalized_key != key:
                        stats["keys_normalized"][key] = normalized_key
                else:
                    normalized_key = key
                
                # Recursively normalize nested structures
                if isinstance(value, (dict, list)):
                    normalized[normalized_key] = self._normalize_keys(value, stats)
                else:
                    normalized[normalized_key] = value
            
            data = normalized
        
        elif isinstance(data, list):
            data = [self._normalize_keys(item, stats) if isinstance(item, (dict, list)) else item 
                   for item in data]
        
        if stats["keys_normalized"] and "normalize_keys" not in stats["operations_performed"]:
            stats["operations_performed"].append("normalize_keys")
        
        return data
    
    def _flatten_json(self, data: Union[Dict, List], stats: Dict[str, Any]) -> Union[Dict, List]:
        """Flatten nested JSON structures up to max depth."""
        if isinstance(data, dict):
            flattened = self._flatten_dict(data, max_depth=self.config.max_flatten_depth)
            stats["flattened"] = True
            stats["operations_performed"].append("flatten_json")
            return flattened
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            # Flatten each dict in the list
            flattened_list = [self._flatten_dict(item, max_depth=self.config.max_flatten_depth) 
                             for item in data if isinstance(item, dict)]
            stats["flattened"] = True
            stats["operations_performed"].append("flatten_json")
            return flattened_list
        
        return data
    
    def _flatten_dict(self, data: Dict, parent_key: str = '', sep: str = '_', 
                     max_depth: int = 3, current_depth: int = 0) -> Dict:
        """Recursively flatten a dictionary."""
        if current_depth >= max_depth:
            return data
        
        items = []
        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            
            if isinstance(value, dict) and current_depth < max_depth:
                items.extend(
                    self._flatten_dict(value, new_key, sep, max_depth, current_depth + 1).items()
                )
            else:
                items.append((new_key, value))
        
        return dict(items)


class UnstructuredDataCleaner:
    """Cleans unstructured data (PDF, TXT, DOCX, HTML, Markdown)."""
    
    def __init__(self, config: CleaningConfig = None):
        """Initialize unstructured data cleaner."""
        self.config = config or CleaningConfig()
    
    def clean_text(self, text: str, data_type: DataType) -> Tuple[str, List[str], Dict[str, Any]]:
        """
        Clean text content and create semantic chunks.
        
        Args:
            text: Raw text content
            data_type: Type of the original document
            
        Returns:
            Tuple of (cleaned_text, chunks, cleaning_stats)
        """
        cleaning_stats = {
            "original_length": len(text),
            "operations_performed": [],
            "chunks_created": 0,
        }
        
        logger.info(f"Starting unstructured data cleaning: {data_type.value}, {len(text)} characters")
        
        # Clean the text
        cleaned_text = self._clean_text_content(text, data_type, cleaning_stats)
        
        # Create semantic chunks
        chunks = self._create_semantic_chunks(cleaned_text, cleaning_stats)
        
        cleaning_stats.update({
            "final_length": len(cleaned_text),
            "chunks_created": len(chunks),
        })
        
        logger.info(
            f"Unstructured data cleaning completed: {len(cleaned_text)} characters, "
            f"{len(chunks)} chunks created"
        )
        
        return cleaned_text, chunks, cleaning_stats
    
    def extract_text_from_file(self, file_path: Path, data_type: DataType) -> str:
        """
        Extract text content from various file types.
        
        Args:
            file_path: Path to the file
            data_type: Type of the file
            
        Returns:
            Extracted text content
        """
        try:
            if data_type == DataType.TXT or data_type == DataType.MARKDOWN:
                with open(file_path, 'r', encoding=self.config.encoding) as f:
                    return f.read()
            
            elif data_type == DataType.PDF:
                return self._extract_pdf_text(file_path)
            
            elif data_type == DataType.DOCX:
                return self._extract_docx_text(file_path)
            
            elif data_type == DataType.HTML:
                return self._extract_html_text(file_path)
            
            else:
                raise ValueError(f"Unsupported data type for text extraction: {data_type}")
        
        except Exception as e:
            logger.error(f"Failed to extract text from {file_path}: {e}")
            raise
    
    def _extract_pdf_text(self, file_path: Path) -> str:
        """Extract text from PDF file."""
        try:
            import PyPDF2
            text = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except ImportError:
            raise ImportError("PyPDF2 is required for PDF text extraction. Install with: pip install PyPDF2")
    
    def _extract_docx_text(self, file_path: Path) -> str:
        """Extract text from DOCX file."""
        try:
            import docx
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except ImportError:
            raise ImportError("python-docx is required for DOCX text extraction. Install with: pip install python-docx")
    
    def _extract_html_text(self, file_path: Path) -> str:
        """Extract text from HTML file."""
        try:
            from bs4 import BeautifulSoup
            with open(file_path, 'r', encoding=self.config.encoding) as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                return soup.get_text()
        except ImportError:
            raise ImportError("beautifulsoup4 is required for HTML text extraction. Install with: pip install beautifulsoup4")
    
    def _clean_text_content(self, text: str, data_type: DataType, stats: Dict[str, Any]) -> str:
        """Clean text content according to configuration."""
        # Remove headers and footers if configured
        if self.config.remove_headers_footers:
            text = self._remove_headers_footers(text, stats)
        
        # Remove page numbers if configured
        if self.config.remove_page_numbers:
            text = self._remove_page_numbers(text, stats)
        
        # Normalize whitespace
        text = self._normalize_whitespace(text, stats)
        
        return text
    
    def _remove_headers_footers(self, text: str, stats: Dict[str, Any]) -> str:
        """Remove common header and footer patterns."""
        # Remove page headers (lines that appear at the start and are repeated)
        lines = text.split('\n')
        if len(lines) > 5:  # Only process if we have enough lines
            # Simple heuristic: remove lines that are very short and at the beginning/end
            cleaned_lines = []
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                # Skip very short lines at the beginning or end that look like headers/footers
                if (i < 2 or i >= len(lines) - 2) and len(line_stripped) < 20:
                    # Check if it looks like a page number or header
                    if (line_stripped.startswith('Page ') or 
                        line_stripped.isdigit() or 
                        len(line_stripped) < 5):
                        continue
                cleaned_lines.append(line)
            
            if len(cleaned_lines) < len(lines):
                text = '\n'.join(cleaned_lines)
                stats["operations_performed"].append("remove_headers_footers")
        
        return text
    
    def _remove_page_numbers(self, text: str, stats: Dict[str, Any]) -> str:
        """Remove page number patterns."""
        # Remove standalone numbers that are likely page numbers
        original_text = text
        
        # Pattern for standalone page numbers
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        text = re.sub(r'\n\s*Page\s+\d+\s*\n', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'\n\s*\d+\s*/\s*\d+\s*\n', '\n', text)
        
        if text != original_text:
            stats["operations_performed"].append("remove_page_numbers")
        
        return text
    
    def _normalize_whitespace(self, text: str, stats: Dict[str, Any]) -> str:
        """Normalize whitespace while preserving layout if configured."""
        original_text = text
        
        if self.config.preserve_layout:
            # Preserve paragraph breaks but normalize other whitespace
            text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
            text = re.sub(r'\n[ \t]+', '\n', text)  # Remove leading whitespace on lines
            text = re.sub(r'[ \t]+\n', '\n', text)  # Remove trailing whitespace on lines
            text = re.sub(r'\n{3,}', '\n\n', text)  # Multiple newlines to double newline
        else:
            # Aggressive whitespace normalization
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
        
        if text != original_text:
            stats["operations_performed"].append("normalize_whitespace")
        
        return text
    
    def _create_semantic_chunks(self, text: str, stats: Dict[str, Any]) -> List[str]:
        """Create semantic chunks from text."""
        # Simple token-based chunking (approximating tokens as words)
        words = text.split()
        chunk_size = self.config.chunk_size_tokens
        overlap = self.config.chunk_overlap_tokens
        min_size = self.config.min_chunk_size
        
        # If text is too short, return as single chunk
        if len(text) < min_size:
            return [text] if text.strip() else []
        
        chunks = []
        start = 0
        
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk_words = words[start:end]
            chunk_text = ' '.join(chunk_words)
            
            # Only add chunk if it meets minimum size requirement
            if len(chunk_text) >= min_size:
                chunks.append(chunk_text)
            
            # Move start position with overlap
            if end >= len(words):
                break
            start = max(start + 1, end - overlap)
        
        # If no chunks were created, create one from the entire text
        if not chunks and text.strip():
            chunks.append(text.strip())
        
        return chunks


class DataCleaningEngine:
    """
    Main data cleaning engine that coordinates cleaning for all data types.
    """
    
    def __init__(self, config: CleaningConfig = None):
        """Initialize data cleaning engine."""
        self.config = config or CleaningConfig()
        self.structured_cleaner = StructuredDataCleaner(self.config)
        self.json_cleaner = JSONDataCleaner(self.config)
        self.unstructured_cleaner = UnstructuredDataCleaner(self.config)
    
    def clean_data(self, data: Any, data_type: DataType, 
                  file_path: Optional[Path] = None) -> Tuple[Any, Dict[str, Any]]:
        """
        Clean data based on its type.
        
        Args:
            data: Raw data to clean
            data_type: Type of the data
            file_path: Optional path to the original file
            
        Returns:
            Tuple of (cleaned_data, cleaning_stats)
        """
        logger.info(f"Starting data cleaning for type: {data_type.value}")
        
        if data_type in [DataType.CSV, DataType.TSV, DataType.EXCEL, DataType.PARQUET]:
            # Structured data - expect pandas DataFrame
            if not isinstance(data, pd.DataFrame):
                raise ValueError(f"Expected pandas DataFrame for {data_type.value}, got {type(data)}")
            return self.structured_cleaner.clean_dataframe(data)
        
        elif data_type in [DataType.JSON, DataType.JSONL]:
            # JSON data
            return self.json_cleaner.clean_json(data)
        
        elif data_type in [DataType.PDF, DataType.TXT, DataType.MARKDOWN, DataType.DOCX, DataType.HTML]:
            # Unstructured data
            if isinstance(data, str):
                # Text content provided directly
                text = data
            elif file_path:
                # Extract text from file
                text = self.unstructured_cleaner.extract_text_from_file(file_path, data_type)
            else:
                raise ValueError(f"For {data_type.value}, either text content or file_path must be provided")
            
            # Get the 3-tuple from unstructured cleaner
            cleaned_text, chunks, stats = self.unstructured_cleaner.clean_text(text, data_type)
            
            # Return consistent 2-tuple format: (cleaned_data_dict, stats)
            cleaned_data = {
                "text": cleaned_text,
                "chunks": chunks
            }
            return cleaned_data, stats
        
        else:
            raise ValueError(f"Unsupported data type for cleaning: {data_type}")
    
    def get_cleaning_config(self) -> CleaningConfig:
        """Get current cleaning configuration."""
        return self.config
    
    def update_cleaning_config(self, **kwargs) -> None:
        """Update cleaning configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                logger.warning(f"Unknown configuration option: {key}")
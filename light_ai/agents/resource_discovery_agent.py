"""
Resource Discovery Agent for Intelligent Data Analysis.

This AI agent specializes in automatic data source cataloging, schema analysis,
field mapping, relationship detection, data quality assessment, and semantic
tagging across all data formats.
"""

import json
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import re

from .base import BaseAgent, AgentConfig
from .logging import get_activity_logger
from ..core.models import ResourceMetadata, ResourceType, DataType, SchemaInfo
from ..storage.metadata_registry import MetadataRegistry
from ..storage.storage_router import StorageRouter
from ..storage.database_managers import DatabaseManagers
from ..config import Config, get_config
from ..logger import get_logger

logger = get_logger(__name__)


@dataclass
class SchemaAnalysis:
    """AI analysis of data schema."""
    resource_id: str
    schema_type: str  # structured, json, unstructured
    fields: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    data_quality_score: float
    semantic_tags: List[str]
    suggested_joins: List[Dict[str, Any]]
    field_mappings: Dict[str, Any]
    analysis_confidence: float
    analysis_timestamp: datetime


@dataclass
class FieldAnalysis:
    """AI analysis of individual field."""
    name: str
    data_type: str
    semantic_type: str  # e.g., "person_name", "monetary_amount", "date"
    nullable: bool
    unique_values: int
    sample_values: List[Any]
    quality_score: float
    suggested_mappings: List[str]
    patterns: List[str]
    anomalies: List[str]


@dataclass
class RelationshipAnalysis:
    """Analysis of relationships between fields/resources."""
    source_resource_id: str
    target_resource_id: str
    source_field: str
    target_field: str
    relationship_type: str  # foreign_key, semantic_match, correlation
    confidence_score: float
    join_suggestion: Dict[str, Any]


@dataclass
class DataQualityAssessment:
    """Comprehensive data quality assessment."""
    resource_id: str
    overall_score: float
    completeness_score: float
    consistency_score: float
    accuracy_score: float
    uniqueness_score: float
    validity_score: float
    quality_issues: List[Dict[str, Any]]
    recommendations: List[str]


class ResourceDiscoveryAgent(BaseAgent):
    """
    AI Agent for Resource Discovery and Schema Intelligence.
    
    This agent specializes in:
    - Automatic data source cataloging
    - Schema analysis across all data formats
    - Intelligent field mapping and relationship detection
    - Data quality assessment and scoring
    - Semantic tagging and categorization
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the Resource Discovery Agent."""
        
        system_prompt = """You are an expert AI Data Discovery Agent specializing in automatic data source cataloging and schema analysis.

Your capabilities:
1. Analyze data schemas across structured, JSON, and unstructured formats
2. Identify field types, patterns, and semantic meanings
3. Detect relationships and potential joins between data sources
4. Assess data quality and identify issues
5. Generate semantic tags and categorizations
6. Suggest field mappings and data transformations

Analysis Framework:
- For structured data: Analyze column types, patterns, distributions, and relationships
- For JSON data: Flatten nested structures, identify key patterns, and extract schema
- For unstructured data: Extract entities, relationships, and semantic content
- Always provide confidence scores and quality assessments
- Identify potential data quality issues and suggest improvements

Quality Assessment Criteria:
- Completeness: Percentage of non-null values
- Consistency: Data format and type consistency
- Accuracy: Validity of data values
- Uniqueness: Duplicate detection
- Validity: Adherence to expected patterns/constraints

Semantic Analysis:
- Identify semantic field types (names, addresses, amounts, dates, etc.)
- Detect business entities and relationships
- Suggest standardization and normalization opportunities
- Identify potential privacy/sensitive data

Always provide detailed analysis with confidence scores and actionable recommendations."""

        agent_config = AgentConfig(
            name="resource_discovery_agent",
            model_name=config.openrouter.default_model if config else "anthropic/claude-3.5-sonnet",
            temperature=0.2,  # Lower temperature for analytical consistency
            max_tokens=4096,
            timeout_seconds=120,
            system_prompt=system_prompt
        )
        
        super().__init__(agent_config, config)
        
        # Initialize dependencies
        self.metadata_registry = MetadataRegistry(config)
        self.storage_router = StorageRouter(config)
        self.db_managers = DatabaseManagers(config)
        self.activity_logger = get_activity_logger()
        
        # Initialize caches for performance
        self.schema_cache: Dict[str, SchemaAnalysis] = {}
        self.field_mapping_cache: Dict[str, Dict[str, Any]] = {}
        self.relationship_cache: Dict[str, List[RelationshipAnalysis]] = {}
        
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize the agent and dependencies."""
        if not self._initialized:
            self.metadata_registry.initialize()
            self.storage_router.initialize()
            self.db_managers.initialize_all()
            self._initialized = True
            logger.info("Resource Discovery Agent initialized")
    
    async def catalog_data_sources(self, client_id: str, user_id: str) -> Dict[str, Any]:
        """
        Automatically catalog all available data sources for a user.
        
        Args:
            client_id: Client identifier
            user_id: User identifier
            
        Returns:
            Comprehensive catalog of data sources with analysis
        """
        start_time = time.time()
        
        try:
            self.initialize()
            
            logger.info(f"Starting data source cataloging for user {user_id}")
            
            # Log agent activity
            self.activity_logger.log_agent_query(
                self.agent_config.name, user_id, client_id,
                "catalog_data_sources", None
            )
            
            # Get all user resources
            resources = self.metadata_registry.list_resources(client_id, user_id)
            
            if not resources:
                return {
                    "catalog": [],
                    "summary": {
                        "total_resources": 0,
                        "resource_types": {},
                        "data_quality_overview": {},
                        "recommendations": ["Upload data to begin analysis"]
                    }
                }
            
            # Analyze each resource
            catalog_entries = []
            quality_scores = []
            
            for resource in resources:
                try:
                    # Perform comprehensive analysis
                    schema_analysis = await self.analyze_resource_schema(resource)
                    quality_assessment = await self.assess_data_quality(resource)
                    
                    catalog_entry = {
                        "resource_id": resource.resource_id,
                        "filename": resource.original_filename,
                        "resource_type": resource.resource_type.value,
                        "data_type": resource.data_type.value,
                        "file_size_mb": round(resource.file_size_bytes / (1024 * 1024), 2),
                        "created_at": resource.created_at.isoformat(),
                        "schema_analysis": asdict(schema_analysis),
                        "quality_assessment": asdict(quality_assessment),
                        "processing_status": resource.processing_status
                    }
                    
                    catalog_entries.append(catalog_entry)
                    quality_scores.append(quality_assessment.overall_score)
                    
                except Exception as e:
                    logger.warning(f"Failed to analyze resource {resource.resource_id}: {e}")
                    # Add basic entry without analysis
                    catalog_entries.append({
                        "resource_id": resource.resource_id,
                        "filename": resource.original_filename,
                        "resource_type": resource.resource_type.value,
                        "data_type": resource.data_type.value,
                        "error": f"Analysis failed: {str(e)}"
                    })
            
            # Generate cross-resource relationship analysis
            relationships = await self.detect_cross_resource_relationships(resources)
            
            # Create summary
            resource_type_counts = {}
            for resource in resources:
                resource_type_counts[resource.resource_type.value] = resource_type_counts.get(resource.resource_type.value, 0) + 1
            
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            
            summary = {
                "total_resources": len(resources),
                "resource_types": resource_type_counts,
                "data_quality_overview": {
                    "average_quality_score": round(avg_quality, 2),
                    "high_quality_resources": len([s for s in quality_scores if s >= 0.8]),
                    "medium_quality_resources": len([s for s in quality_scores if 0.6 <= s < 0.8]),
                    "low_quality_resources": len([s for s in quality_scores if s < 0.6])
                },
                "cross_resource_relationships": len(relationships),
                "recommendations": await self._generate_catalog_recommendations(catalog_entries, relationships)
            }
            
            execution_time = (time.time() - start_time) * 1000
            
            # Log completion
            self.activity_logger.log_agent_response(
                self.agent_config.name, user_id, client_id,
                f"Cataloged {len(resources)} data sources",
                execution_time, self.agent_config.model_name,
                None, None,
                {"resources_analyzed": len(resources), "avg_quality": avg_quality}
            )
            
            return {
                "catalog": catalog_entries,
                "relationships": [asdict(r) for r in relationships],
                "summary": summary,
                "execution_time_ms": execution_time
            }
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Data source cataloging failed: {str(e)}"
            logger.error(error_msg)
            
            self.activity_logger.log_agent_error(
                self.agent_config.name, user_id, client_id,
                error_msg, None
            )
            
            return {
                "error": error_msg,
                "execution_time_ms": execution_time
            }
    
    async def analyze_resource_schema(self, resource: ResourceMetadata) -> SchemaAnalysis:
        """
        Perform comprehensive schema analysis on a resource.
        
        Args:
            resource: Resource metadata to analyze
            
        Returns:
            Detailed schema analysis
        """
        # Check cache first
        cache_key = f"{resource.resource_id}_{resource.version}"
        if cache_key in self.schema_cache:
            return self.schema_cache[cache_key]
        
        try:
            if resource.resource_type == ResourceType.STRUCTURED:
                analysis = await self._analyze_structured_schema(resource)
            elif resource.resource_type == ResourceType.JSON:
                analysis = await self._analyze_json_schema(resource)
            elif resource.resource_type == ResourceType.UNSTRUCTURED:
                analysis = await self._analyze_unstructured_schema(resource)
            else:
                raise ValueError(f"Unsupported resource type: {resource.resource_type}")
            
            # Cache the result
            self.schema_cache[cache_key] = analysis
            return analysis
            
        except Exception as e:
            logger.error(f"Schema analysis failed for {resource.resource_id}: {e}")
            # Return minimal analysis on error
            return SchemaAnalysis(
                resource_id=resource.resource_id,
                schema_type=resource.resource_type.value,
                fields=[],
                relationships=[],
                data_quality_score=0.0,
                semantic_tags=[],
                suggested_joins=[],
                field_mappings={},
                analysis_confidence=0.0,
                analysis_timestamp=datetime.utcnow()
            )
    
    async def _analyze_structured_schema(self, resource: ResourceMetadata) -> SchemaAnalysis:
        """Analyze structured data schema."""
        fields = []
        semantic_tags = []
        
        try:
            # Get schema information from metadata registry
            schema_info = self.metadata_registry.get_schema_info(resource.resource_id)
            
            if schema_info:
                schema_data = json.loads(schema_info.schema_json)
                
                # Analyze each column
                for col_name, col_info in schema_data.get("columns", {}).items():
                    field_analysis = await self._analyze_field(
                        col_name, col_info, resource.resource_id
                    )
                    fields.append(asdict(field_analysis))
                    
                    # Extract semantic tags
                    if field_analysis.semantic_type not in semantic_tags:
                        semantic_tags.append(field_analysis.semantic_type)
            
            # Generate AI-powered analysis prompt
            analysis_prompt = self._build_schema_analysis_prompt(resource, fields)
            ai_analysis = await self.execute(analysis_prompt)
            
            # Parse AI analysis for additional insights
            ai_insights = self._parse_ai_schema_analysis(ai_analysis)
            
            # Calculate overall quality score
            quality_score = self._calculate_schema_quality_score(fields)
            
            return SchemaAnalysis(
                resource_id=resource.resource_id,
                schema_type="structured",
                fields=fields,
                relationships=ai_insights.get("relationships", []),
                data_quality_score=quality_score,
                semantic_tags=semantic_tags + ai_insights.get("additional_tags", []),
                suggested_joins=ai_insights.get("join_suggestions", []),
                field_mappings=ai_insights.get("field_mappings", {}),
                analysis_confidence=ai_insights.get("confidence", 0.8),
                analysis_timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Structured schema analysis failed: {e}")
            raise
    
    async def _analyze_json_schema(self, resource: ResourceMetadata) -> SchemaAnalysis:
        """Analyze JSON data schema."""
        try:
            # Sample JSON data to understand structure
            table_name = f"json_{resource.resource_id.replace('-', '_')}"
            
            # Get sample data from DuckDB
            sample_query = f"""
            SELECT * FROM json_data.{table_name} 
            WHERE resource_id = ? 
            LIMIT 10
            """
            
            sample_data = self.storage_router.query_json_data(
                table_name, resource.client_id, resource.user_id
            )
            
            if not sample_data:
                raise ValueError("No JSON data found for analysis")
            
            # Flatten JSON structure and analyze fields
            flattened_fields = self._flatten_json_structure(sample_data)
            
            fields = []
            semantic_tags = []
            
            for field_path, field_info in flattened_fields.items():
                field_analysis = FieldAnalysis(
                    name=field_path,
                    data_type=field_info["type"],
                    semantic_type=self._infer_semantic_type(field_path, field_info["sample_values"]),
                    nullable=field_info["nullable"],
                    unique_values=field_info["unique_count"],
                    sample_values=field_info["sample_values"][:5],
                    quality_score=self._calculate_field_quality(field_info),
                    suggested_mappings=[],
                    patterns=field_info.get("patterns", []),
                    anomalies=field_info.get("anomalies", [])
                )
                
                fields.append(asdict(field_analysis))
                
                if field_analysis.semantic_type not in semantic_tags:
                    semantic_tags.append(field_analysis.semantic_type)
            
            # Generate AI analysis
            analysis_prompt = self._build_json_analysis_prompt(resource, sample_data, fields)
            ai_analysis = await self.execute(analysis_prompt)
            ai_insights = self._parse_ai_schema_analysis(ai_analysis)
            
            quality_score = self._calculate_schema_quality_score(fields)
            
            return SchemaAnalysis(
                resource_id=resource.resource_id,
                schema_type="json",
                fields=fields,
                relationships=ai_insights.get("relationships", []),
                data_quality_score=quality_score,
                semantic_tags=semantic_tags + ai_insights.get("additional_tags", []),
                suggested_joins=ai_insights.get("join_suggestions", []),
                field_mappings=ai_insights.get("field_mappings", {}),
                analysis_confidence=ai_insights.get("confidence", 0.7),
                analysis_timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"JSON schema analysis failed: {e}")
            raise
    
    async def _analyze_unstructured_schema(self, resource: ResourceMetadata) -> SchemaAnalysis:
        """Analyze unstructured data schema."""
        try:
            # Get sample content from ChromaDB
            collection_name = f"unstructured_{resource.resource_id.replace('-', '_')}"
            
            # Query for sample documents
            sample_embeddings = [[0.0] * 384]  # Dummy embedding for sampling
            search_results = self.storage_router.search_unstructured_data(
                sample_embeddings, resource.client_id, resource.user_id, n_results=5
            )
            
            documents = []
            if search_results.get("documents"):
                documents = search_results["documents"][0] if search_results["documents"] else []
            
            # Extract entities and patterns from text
            entities = []
            patterns = []
            semantic_tags = []
            
            if documents:
                # Generate AI analysis of unstructured content
                analysis_prompt = self._build_unstructured_analysis_prompt(resource, documents)
                ai_analysis = await self.execute(analysis_prompt)
                ai_insights = self._parse_unstructured_analysis(ai_analysis)
                
                entities = ai_insights.get("entities", [])
                patterns = ai_insights.get("patterns", [])
                semantic_tags = ai_insights.get("semantic_tags", [])
            
            # Create field representations for unstructured data
            fields = [
                {
                    "name": "content",
                    "data_type": "text",
                    "semantic_type": "unstructured_text",
                    "nullable": False,
                    "unique_values": len(documents),
                    "sample_values": documents[:3],
                    "quality_score": 0.8 if documents else 0.0,
                    "suggested_mappings": [],
                    "patterns": patterns,
                    "anomalies": []
                },
                {
                    "name": "entities",
                    "data_type": "extracted_entities",
                    "semantic_type": "named_entities",
                    "nullable": True,
                    "unique_values": len(entities),
                    "sample_values": entities[:5],
                    "quality_score": 0.7 if entities else 0.3,
                    "suggested_mappings": [],
                    "patterns": [],
                    "anomalies": []
                }
            ]
            
            quality_score = 0.8 if documents else 0.2
            
            return SchemaAnalysis(
                resource_id=resource.resource_id,
                schema_type="unstructured",
                fields=fields,
                relationships=[],
                data_quality_score=quality_score,
                semantic_tags=semantic_tags,
                suggested_joins=[],
                field_mappings={},
                analysis_confidence=0.6,
                analysis_timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Unstructured schema analysis failed: {e}")
            raise
    
    async def _analyze_field(self, field_name: str, field_info: Dict[str, Any], 
                           resource_id: str) -> FieldAnalysis:
        """Analyze individual field characteristics."""
        
        # Infer semantic type from field name and data
        semantic_type = self._infer_semantic_type(field_name, field_info.get("sample_values", []))
        
        # Detect patterns in the data
        patterns = self._detect_field_patterns(field_info.get("sample_values", []))
        
        # Identify anomalies
        anomalies = self._detect_field_anomalies(field_info)
        
        # Calculate quality score
        quality_score = self._calculate_field_quality(field_info)
        
        return FieldAnalysis(
            name=field_name,
            data_type=field_info.get("type", "unknown"),
            semantic_type=semantic_type,
            nullable=field_info.get("nullable", True),
            unique_values=field_info.get("unique_values", 0),
            sample_values=field_info.get("sample_values", [])[:5],
            quality_score=quality_score,
            suggested_mappings=[],
            patterns=patterns,
            anomalies=anomalies
        )
    
    def _infer_semantic_type(self, field_name: str, sample_values: List[Any]) -> str:
        """Infer semantic type from field name and sample values."""
        field_name_lower = field_name.lower()
        
        # Name patterns
        if any(keyword in field_name_lower for keyword in ['name', 'title', 'label']):
            return "name"
        elif any(keyword in field_name_lower for keyword in ['email', 'mail']):
            return "email"
        elif any(keyword in field_name_lower for keyword in ['phone', 'tel', 'mobile']):
            return "phone"
        elif any(keyword in field_name_lower for keyword in ['address', 'street', 'city', 'zip']):
            return "address"
        elif any(keyword in field_name_lower for keyword in ['date', 'time', 'created', 'updated']):
            return "datetime"
        elif any(keyword in field_name_lower for keyword in ['price', 'cost', 'amount', 'salary', 'revenue']):
            return "monetary_amount"
        elif any(keyword in field_name_lower for keyword in ['id', 'key', 'uuid']):
            return "identifier"
        elif any(keyword in field_name_lower for keyword in ['count', 'number', 'quantity', 'age']):
            return "numeric"
        elif any(keyword in field_name_lower for keyword in ['url', 'link', 'website']):
            return "url"
        elif any(keyword in field_name_lower for keyword in ['category', 'type', 'status', 'group']):
            return "category"
        
        # Value-based inference
        if sample_values:
            # Check for email patterns
            if any(isinstance(v, str) and '@' in v and '.' in v for v in sample_values[:5]):
                return "email"
            
            # Check for URL patterns
            if any(isinstance(v, str) and v.startswith(('http://', 'https://')) for v in sample_values[:5]):
                return "url"
            
            # Check for phone patterns
            if any(isinstance(v, str) and re.match(r'[\d\-\(\)\+\s]+', str(v)) and len(str(v)) > 7 for v in sample_values[:5]):
                return "phone"
        
        return "general"
    
    def _detect_field_patterns(self, sample_values: List[Any]) -> List[str]:
        """Detect patterns in field values."""
        patterns = []
        
        if not sample_values:
            return patterns
        
        # Check for common patterns
        string_values = [str(v) for v in sample_values if v is not None]
        
        if string_values:
            # Email pattern
            if any('@' in v and '.' in v for v in string_values):
                patterns.append("email_format")
            
            # Phone pattern
            if any(re.match(r'[\d\-\(\)\+\s]+', v) and len(v) > 7 for v in string_values):
                patterns.append("phone_format")
            
            # Date pattern
            if any(re.match(r'\d{4}-\d{2}-\d{2}', v) for v in string_values):
                patterns.append("iso_date")
            
            # UUID pattern
            if any(re.match(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', v, re.I) for v in string_values):
                patterns.append("uuid_format")
            
            # Consistent length
            lengths = [len(v) for v in string_values]
            if len(set(lengths)) == 1 and lengths[0] > 1:
                patterns.append(f"fixed_length_{lengths[0]}")
        
        return patterns
    
    def _detect_field_anomalies(self, field_info: Dict[str, Any]) -> List[str]:
        """Detect anomalies in field data."""
        anomalies = []
        
        # High null percentage
        if field_info.get("null_percentage", 0) > 0.5:
            anomalies.append("high_null_rate")
        
        # Very low uniqueness for non-categorical data
        total_values = field_info.get("total_values", 1)
        unique_values = field_info.get("unique_values", 1)
        uniqueness_ratio = unique_values / total_values
        
        if uniqueness_ratio < 0.1 and field_info.get("type") not in ["category", "boolean"]:
            anomalies.append("low_uniqueness")
        
        # Inconsistent data types
        if field_info.get("type_consistency", 1.0) < 0.9:
            anomalies.append("inconsistent_types")
        
        return anomalies
    
    def _calculate_field_quality(self, field_info: Dict[str, Any]) -> float:
        """Calculate quality score for a field."""
        score = 1.0
        
        # Penalize high null rates
        null_rate = field_info.get("null_percentage", 0)
        score -= null_rate * 0.3
        
        # Penalize type inconsistency
        type_consistency = field_info.get("type_consistency", 1.0)
        score -= (1.0 - type_consistency) * 0.4
        
        # Reward good uniqueness (context-dependent)
        uniqueness = field_info.get("unique_values", 1) / max(field_info.get("total_values", 1), 1)
        if 0.1 <= uniqueness <= 0.9:  # Good range for most fields
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_schema_quality_score(self, fields: List[Dict[str, Any]]) -> float:
        """Calculate overall schema quality score."""
        if not fields:
            return 0.0
        
        field_scores = [field.get("quality_score", 0.0) for field in fields]
        return sum(field_scores) / len(field_scores)
    
    def _flatten_json_structure(self, json_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Flatten nested JSON structure for analysis."""
        flattened = {}
        
        for record in json_data:
            self._flatten_json_record(record, "", flattened)
        
        # Calculate statistics for each field
        for field_path, field_info in flattened.items():
            values = field_info["values"]
            field_info["unique_count"] = len(set(str(v) for v in values if v is not None))
            field_info["nullable"] = None in values
            field_info["sample_values"] = list(set(values))[:10]
            
            # Infer type
            non_null_values = [v for v in values if v is not None]
            if non_null_values:
                if all(isinstance(v, bool) for v in non_null_values):
                    field_info["type"] = "boolean"
                elif all(isinstance(v, int) for v in non_null_values):
                    field_info["type"] = "integer"
                elif all(isinstance(v, (int, float)) for v in non_null_values):
                    field_info["type"] = "numeric"
                elif all(isinstance(v, str) for v in non_null_values):
                    field_info["type"] = "string"
                else:
                    field_info["type"] = "mixed"
            else:
                field_info["type"] = "null"
        
        return flattened
    
    def _flatten_json_record(self, record: Dict[str, Any], prefix: str, 
                           flattened: Dict[str, Dict[str, Any]]) -> None:
        """Recursively flatten a JSON record."""
        for key, value in record.items():
            if key in ['client_id', 'user_id', 'resource_id']:  # Skip system fields
                continue
                
            field_path = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                self._flatten_json_record(value, field_path, flattened)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                # Handle array of objects
                for i, item in enumerate(value[:3]):  # Limit to first 3 items
                    self._flatten_json_record(item, f"{field_path}[{i}]", flattened)
            else:
                # Leaf value
                if field_path not in flattened:
                    flattened[field_path] = {"values": []}
                flattened[field_path]["values"].append(value)
    
    def _build_schema_analysis_prompt(self, resource: ResourceMetadata, 
                                    fields: List[Dict[str, Any]]) -> str:
        """Build AI prompt for schema analysis."""
        return f"""
Analyze the schema for structured data resource: {resource.original_filename}

Resource Information:
- Type: {resource.resource_type.value}
- Data Type: {resource.data_type.value}
- Rows: {resource.row_count}
- Columns: {resource.column_count}

Fields Analysis:
{json.dumps(fields, indent=2)}

Please provide:
1. Relationships between fields (foreign keys, dependencies)
2. Additional semantic tags for the dataset
3. Suggested joins with other potential datasets
4. Field mapping recommendations
5. Data quality insights
6. Confidence score (0.0-1.0) for your analysis

Format your response as JSON with keys: relationships, additional_tags, join_suggestions, field_mappings, quality_insights, confidence
"""
    
    def _build_json_analysis_prompt(self, resource: ResourceMetadata, 
                                  sample_data: List[Dict[str, Any]], 
                                  fields: List[Dict[str, Any]]) -> str:
        """Build AI prompt for JSON schema analysis."""
        return f"""
Analyze the JSON data structure for resource: {resource.original_filename}

Sample Data (first 3 records):
{json.dumps(sample_data[:3], indent=2)}

Flattened Fields Analysis:
{json.dumps(fields, indent=2)}

Please provide:
1. Nested structure relationships and hierarchies
2. Semantic tags for the JSON data
3. Suggested normalization strategies
4. Field mapping recommendations
5. Data quality assessment
6. Confidence score (0.0-1.0) for your analysis

Format your response as JSON with keys: relationships, additional_tags, join_suggestions, field_mappings, quality_insights, confidence
"""
    
    def _build_unstructured_analysis_prompt(self, resource: ResourceMetadata, 
                                          documents: List[str]) -> str:
        """Build AI prompt for unstructured data analysis."""
        sample_text = "\n\n".join(documents[:3])
        
        return f"""
Analyze the unstructured text data for resource: {resource.original_filename}

Sample Content:
{sample_text[:2000]}...

Please extract and analyze:
1. Named entities (people, organizations, locations, etc.)
2. Key topics and themes
3. Document structure patterns
4. Semantic tags for categorization
5. Potential relationships with structured data
6. Content quality assessment

Format your response as JSON with keys: entities, patterns, semantic_tags, relationships, quality_assessment
"""
    
    def _parse_ai_schema_analysis(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI analysis response."""
        try:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        
        # Fallback to default structure
        return {
            "relationships": [],
            "additional_tags": [],
            "join_suggestions": [],
            "field_mappings": {},
            "quality_insights": [],
            "confidence": 0.5
        }
    
    def _parse_unstructured_analysis(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI analysis response for unstructured data."""
        try:
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        
        return {
            "entities": [],
            "patterns": [],
            "semantic_tags": [],
            "relationships": [],
            "quality_assessment": "Unable to analyze"
        }
    
    async def assess_data_quality(self, resource: ResourceMetadata) -> DataQualityAssessment:
        """
        Perform comprehensive data quality assessment.
        
        Args:
            resource: Resource to assess
            
        Returns:
            Detailed quality assessment
        """
        try:
            # Get schema analysis for quality metrics
            schema_analysis = await self.analyze_resource_schema(resource)
            
            # Calculate quality dimensions
            completeness_score = self._calculate_completeness_score(schema_analysis.fields)
            consistency_score = self._calculate_consistency_score(schema_analysis.fields)
            accuracy_score = self._calculate_accuracy_score(schema_analysis.fields)
            uniqueness_score = self._calculate_uniqueness_score(schema_analysis.fields)
            validity_score = self._calculate_validity_score(schema_analysis.fields)
            
            # Overall score (weighted average)
            overall_score = (
                completeness_score * 0.25 +
                consistency_score * 0.25 +
                accuracy_score * 0.20 +
                uniqueness_score * 0.15 +
                validity_score * 0.15
            )
            
            # Identify quality issues
            quality_issues = self._identify_quality_issues(schema_analysis.fields)
            
            # Generate recommendations
            recommendations = self._generate_quality_recommendations(quality_issues, schema_analysis)
            
            return DataQualityAssessment(
                resource_id=resource.resource_id,
                overall_score=round(overall_score, 2),
                completeness_score=round(completeness_score, 2),
                consistency_score=round(consistency_score, 2),
                accuracy_score=round(accuracy_score, 2),
                uniqueness_score=round(uniqueness_score, 2),
                validity_score=round(validity_score, 2),
                quality_issues=quality_issues,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Data quality assessment failed for {resource.resource_id}: {e}")
            return DataQualityAssessment(
                resource_id=resource.resource_id,
                overall_score=0.0,
                completeness_score=0.0,
                consistency_score=0.0,
                accuracy_score=0.0,
                uniqueness_score=0.0,
                validity_score=0.0,
                quality_issues=[{"type": "analysis_error", "description": str(e)}],
                recommendations=["Fix data analysis issues before quality assessment"]
            )
    
    def _calculate_completeness_score(self, fields: List[Dict[str, Any]]) -> float:
        """Calculate data completeness score."""
        if not fields:
            return 0.0
        
        completeness_scores = []
        for field in fields:
            # Assume high completeness if no anomalies indicate otherwise
            if "high_null_rate" in field.get("anomalies", []):
                completeness_scores.append(0.3)
            else:
                completeness_scores.append(0.9)
        
        return sum(completeness_scores) / len(completeness_scores)
    
    def _calculate_consistency_score(self, fields: List[Dict[str, Any]]) -> float:
        """Calculate data consistency score."""
        if not fields:
            return 0.0
        
        consistency_scores = []
        for field in fields:
            if "inconsistent_types" in field.get("anomalies", []):
                consistency_scores.append(0.4)
            else:
                consistency_scores.append(0.9)
        
        return sum(consistency_scores) / len(consistency_scores)
    
    def _calculate_accuracy_score(self, fields: List[Dict[str, Any]]) -> float:
        """Calculate data accuracy score."""
        # This is a simplified implementation
        # In practice, accuracy would require domain knowledge or reference data
        return 0.8
    
    def _calculate_uniqueness_score(self, fields: List[Dict[str, Any]]) -> float:
        """Calculate data uniqueness score."""
        if not fields:
            return 0.0
        
        uniqueness_scores = []
        for field in fields:
            if "low_uniqueness" in field.get("anomalies", []):
                uniqueness_scores.append(0.3)
            else:
                uniqueness_scores.append(0.8)
        
        return sum(uniqueness_scores) / len(uniqueness_scores)
    
    def _calculate_validity_score(self, fields: List[Dict[str, Any]]) -> float:
        """Calculate data validity score."""
        if not fields:
            return 0.0
        
        validity_scores = []
        for field in fields:
            # Check if field has expected patterns
            patterns = field.get("patterns", [])
            if patterns:
                validity_scores.append(0.9)
            else:
                validity_scores.append(0.7)
        
        return sum(validity_scores) / len(validity_scores)
    
    def _identify_quality_issues(self, fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify specific data quality issues."""
        issues = []
        
        for field in fields:
            field_name = field.get("name", "unknown")
            anomalies = field.get("anomalies", [])
            
            for anomaly in anomalies:
                if anomaly == "high_null_rate":
                    issues.append({
                        "type": "completeness",
                        "field": field_name,
                        "description": f"Field '{field_name}' has high percentage of null values",
                        "severity": "medium"
                    })
                elif anomaly == "inconsistent_types":
                    issues.append({
                        "type": "consistency",
                        "field": field_name,
                        "description": f"Field '{field_name}' has inconsistent data types",
                        "severity": "high"
                    })
                elif anomaly == "low_uniqueness":
                    issues.append({
                        "type": "uniqueness",
                        "field": field_name,
                        "description": f"Field '{field_name}' has unexpectedly low uniqueness",
                        "severity": "low"
                    })
        
        return issues
    
    def _generate_quality_recommendations(self, quality_issues: List[Dict[str, Any]], 
                                        schema_analysis: SchemaAnalysis) -> List[str]:
        """Generate recommendations for improving data quality."""
        recommendations = []
        
        # Issue-specific recommendations
        for issue in quality_issues:
            if issue["type"] == "completeness":
                recommendations.append(f"Consider data imputation or collection improvement for {issue['field']}")
            elif issue["type"] == "consistency":
                recommendations.append(f"Standardize data format for {issue['field']}")
            elif issue["type"] == "uniqueness":
                recommendations.append(f"Review duplicate detection for {issue['field']}")
        
        # General recommendations
        if schema_analysis.data_quality_score < 0.7:
            recommendations.append("Consider implementing data validation rules")
            recommendations.append("Review data collection processes")
        
        if not recommendations:
            recommendations.append("Data quality is good - consider regular monitoring")
        
        return recommendations
    
    async def detect_cross_resource_relationships(self, resources: List[ResourceMetadata]) -> List[RelationshipAnalysis]:
        """
        Detect relationships between different resources.
        
        Args:
            resources: List of resources to analyze
            
        Returns:
            List of detected relationships
        """
        relationships = []
        
        try:
            # Only analyze structured resources for now
            structured_resources = [r for r in resources if r.resource_type == ResourceType.STRUCTURED]
            
            if len(structured_resources) < 2:
                return relationships
            
            # Compare each pair of resources
            for i, resource1 in enumerate(structured_resources):
                for resource2 in structured_resources[i+1:]:
                    try:
                        resource_relationships = await self._analyze_resource_pair(resource1, resource2)
                        relationships.extend(resource_relationships)
                    except Exception as e:
                        logger.warning(f"Failed to analyze relationship between {resource1.resource_id} and {resource2.resource_id}: {e}")
            
            return relationships
            
        except Exception as e:
            logger.error(f"Cross-resource relationship detection failed: {e}")
            return relationships
    
    async def _analyze_resource_pair(self, resource1: ResourceMetadata, 
                                   resource2: ResourceMetadata) -> List[RelationshipAnalysis]:
        """Analyze potential relationships between two resources."""
        relationships = []
        
        try:
            # Get schema analyses for both resources
            schema1 = await self.analyze_resource_schema(resource1)
            schema2 = await self.analyze_resource_schema(resource2)
            
            # Compare fields for potential relationships
            for field1 in schema1.fields:
                for field2 in schema2.fields:
                    relationship_score = self._calculate_field_relationship_score(field1, field2)
                    
                    if relationship_score > 0.6:  # Threshold for potential relationship
                        relationship_type = self._determine_relationship_type(field1, field2, relationship_score)
                        
                        relationships.append(RelationshipAnalysis(
                            source_resource_id=resource1.resource_id,
                            target_resource_id=resource2.resource_id,
                            source_field=field1["name"],
                            target_field=field2["name"],
                            relationship_type=relationship_type,
                            confidence_score=relationship_score,
                            join_suggestion={
                                "join_type": "inner" if relationship_score > 0.8 else "left",
                                "condition": f"{field1['name']} = {field2['name']}",
                                "estimated_match_rate": relationship_score
                            }
                        ))
            
            return relationships
            
        except Exception as e:
            logger.error(f"Resource pair analysis failed: {e}")
            return relationships
    
    def _calculate_field_relationship_score(self, field1: Dict[str, Any], 
                                          field2: Dict[str, Any]) -> float:
        """Calculate relationship score between two fields."""
        score = 0.0
        
        # Name similarity
        name1 = field1.get("name", "").lower()
        name2 = field2.get("name", "").lower()
        
        if name1 == name2:
            score += 0.4
        elif name1 in name2 or name2 in name1:
            score += 0.3
        elif any(word in name2 for word in name1.split('_')):
            score += 0.2
        
        # Semantic type similarity
        semantic1 = field1.get("semantic_type", "")
        semantic2 = field2.get("semantic_type", "")
        
        if semantic1 == semantic2 and semantic1 != "general":
            score += 0.3
        
        # Data type compatibility
        type1 = field1.get("data_type", "")
        type2 = field2.get("data_type", "")
        
        if type1 == type2:
            score += 0.2
        elif self._are_compatible_types(type1, type2):
            score += 0.1
        
        # Pattern similarity
        patterns1 = set(field1.get("patterns", []))
        patterns2 = set(field2.get("patterns", []))
        
        if patterns1 & patterns2:  # Common patterns
            score += 0.1
        
        return min(score, 1.0)
    
    def _are_compatible_types(self, type1: str, type2: str) -> bool:
        """Check if two data types are compatible for relationships."""
        numeric_types = {"integer", "float", "numeric", "number"}
        string_types = {"string", "text", "varchar"}
        
        return (
            (type1 in numeric_types and type2 in numeric_types) or
            (type1 in string_types and type2 in string_types)
        )
    
    def _determine_relationship_type(self, field1: Dict[str, Any], field2: Dict[str, Any], 
                                   score: float) -> str:
        """Determine the type of relationship between fields."""
        name1 = field1.get("name", "").lower()
        name2 = field2.get("name", "").lower()
        
        # Check for ID patterns
        if ("id" in name1 or "key" in name1) and ("id" in name2 or "key" in name2):
            return "foreign_key"
        
        # High score with same semantic type
        if score > 0.8 and field1.get("semantic_type") == field2.get("semantic_type"):
            return "semantic_match"
        
        # Medium score suggests correlation
        if score > 0.6:
            return "correlation"
        
        return "potential_match"
    
    async def _generate_catalog_recommendations(self, catalog_entries: List[Dict[str, Any]], 
                                              relationships: List[RelationshipAnalysis]) -> List[str]:
        """Generate recommendations based on catalog analysis."""
        recommendations = []
        
        # Data quality recommendations
        low_quality_resources = [
            entry for entry in catalog_entries 
            if entry.get("quality_assessment", {}).get("overall_score", 0) < 0.6
        ]
        
        if low_quality_resources:
            recommendations.append(f"Improve data quality for {len(low_quality_resources)} resources")
        
        # Relationship recommendations
        if relationships:
            recommendations.append(f"Consider joining {len(relationships)} related datasets for richer analysis")
        
        # Schema standardization
        structured_resources = [e for e in catalog_entries if e.get("resource_type") == "structured"]
        if len(structured_resources) > 1:
            recommendations.append("Consider standardizing field names across structured datasets")
        
        # Data completeness
        incomplete_resources = [
            entry for entry in catalog_entries
            if entry.get("quality_assessment", {}).get("completeness_score", 0) < 0.7
        ]
        
        if incomplete_resources:
            recommendations.append("Address missing data in incomplete datasets")
        
        if not recommendations:
            recommendations.append("Data catalog is well-organized and high quality")
        
        return recommendations
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the Resource Discovery Agent."""
        try:
            self.initialize()
            
            # Test basic functionality
            test_response = await self.execute("Analyze this test: field_name='test', data_type='string'")
            
            return {
                "status": "healthy",
                "agent_info": self.get_agent_info(),
                "cache_stats": {
                    "schema_cache_size": len(self.schema_cache),
                    "field_mapping_cache_size": len(self.field_mapping_cache),
                    "relationship_cache_size": len(self.relationship_cache)
                },
                "test_response_length": len(test_response)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "agent_info": self.get_agent_info()
            }
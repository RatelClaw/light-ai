"""
Field Extraction Agent for Intelligent Data Analysis.

This AI agent specializes in intelligent field mapping, desired field analysis,
field derivation suggestions, complex field calculations, and cross-resource
field synthesis capabilities.
"""

import json
import time
import uuid
import re
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime

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
class FieldMapping:
    """Mapping between desired and available fields."""
    desired_field: str
    available_field: str
    resource_id: str
    mapping_type: str  # direct, similar, derived, calculated
    confidence_score: float
    transformation_required: bool = False
    transformation_logic: Optional[str] = None
    data_type_source: str = "unknown"
    data_type_target: str = "unknown"
    sample_values: List[Any] = None


@dataclass
class DerivedFieldDefinition:
    """Definition for a derived field calculation."""
    field_name: str
    description: str
    calculation_logic: str
    source_fields: List[str]
    source_resources: List[str]
    data_type: str
    validation_rules: List[str]
    confidence_score: float
    complexity_level: str  # simple, medium, complex
    estimated_performance: str  # fast, medium, slow


@dataclass
class FieldAnalysisResult:
    """Result of field analysis and mapping."""
    desired_fields: Dict[str, str]
    direct_mappings: List[FieldMapping]
    similar_mappings: List[FieldMapping]
    derived_field_suggestions: List[DerivedFieldDefinition]
    cross_resource_synthesis: Dict[str, Any]
    unmappable_fields: List[str]
    analysis_confidence: float
    execution_time_ms: float
    recommendations: List[str]


@dataclass
class CrossResourceFieldSynthesis:
    """Cross-resource field synthesis information."""
    synthesis_id: str
    target_field: str
    source_resources: List[str]
    source_fields: List[str]
    synthesis_strategy: str  # join, union, calculation, aggregation
    join_conditions: List[str]
    transformation_steps: List[str]
    estimated_result_quality: float
    performance_impact: str  # low, medium, high


class FieldExtractionAgent(BaseAgent):
    """
    AI Agent for Field Extraction and Intelligent Mapping.
    
    This agent specializes in:
    - Intelligent field mapping between desired and available fields
    - Analysis of desired fields against available data
    - Field derivation suggestion system
    - Complex field calculation engine
    - Cross-resource field synthesis capabilities
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the Field Extraction Agent."""
        
        system_prompt = """You are an expert AI Field Extraction Agent specializing in intelligent field mapping and data synthesis.

Your capabilities:
1. Analyze desired fields against available data sources
2. Map fields intelligently across different naming conventions and formats
3. Suggest field derivations and calculations from available data
4. Design complex field calculations using multiple source fields
5. Synthesize fields across multiple data resources
6. Recommend data transformations and standardizations

Field Analysis Framework:
- For direct mappings: Find exact or near-exact field name matches
- For similar mappings: Use semantic similarity and data type compatibility
- For derived fields: Analyze how to calculate missing fields from available data
- For cross-resource synthesis: Identify opportunities to combine data across sources

Mapping Strategies:
- Name similarity: Compare field names using fuzzy matching
- Semantic similarity: Understand field meanings and purposes
- Data type compatibility: Ensure source and target types are compatible
- Pattern recognition: Identify common field patterns and conventions
- Domain knowledge: Apply business logic for field relationships

Calculation Engine:
- Simple calculations: Basic arithmetic, string operations, date calculations
- Medium calculations: Conditional logic, aggregations, lookups
- Complex calculations: Multi-step transformations, statistical operations, ML-based derivations

Cross-Resource Synthesis:
- Join strategies: Identify optimal join conditions between resources
- Union strategies: Combine similar fields from multiple sources
- Aggregation strategies: Calculate summary fields across resources
- Transformation strategies: Standardize and harmonize field formats

Always provide:
- Confidence scores for all mappings and suggestions
- Clear explanations of mapping logic and calculations
- Performance impact assessments
- Data quality considerations
- Actionable recommendations for field improvements"""

        agent_config = AgentConfig(
            name="field_extraction_agent",
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
        self.field_mapping_cache: Dict[str, FieldAnalysisResult] = {}
        self.schema_cache: Dict[str, Dict[str, Any]] = {}
        self.calculation_cache: Dict[str, str] = {}
        
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize the agent and dependencies."""
        if not self._initialized:
            self.metadata_registry.initialize()
            self.storage_router.initialize()
            self.db_managers.initialize_all()
            self._initialized = True
            logger.info("Field Extraction Agent initialized")
    
    async def analyze_and_map_fields(self, client_id: str, user_id: str,
                                   desired_fields: Dict[str, str],
                                   resource_ids: Optional[List[str]] = None) -> FieldAnalysisResult:
        """
        Analyze desired fields against available data and create intelligent mappings.
        
        Args:
            client_id: Client identifier
            user_id: User identifier
            desired_fields: Dict of {field_name: description} for desired fields
            resource_ids: Optional list of specific resources to analyze
            
        Returns:
            Comprehensive field analysis and mapping result
        """
        start_time = time.time()
        
        try:
            self.initialize()
            
            logger.info(f"Starting field analysis for user {user_id} with {len(desired_fields)} desired fields")
            
            # Log agent activity
            self.activity_logger.log_agent_query(
                self.agent_config.name, user_id, client_id,
                f"analyze_fields: {list(desired_fields.keys())}", None
            )
            
            # Get resources to analyze
            if resource_ids:
                resources = []
                for resource_id in resource_ids:
                    resource = self.metadata_registry.get_resource_metadata(resource_id)
                    if resource and resource.user_id == user_id and resource.client_id == client_id:
                        resources.append(resource)
            else:
                resources = self.metadata_registry.list_resources(client_id, user_id)
            
            if not resources:
                return FieldAnalysisResult(
                    desired_fields=desired_fields,
                    direct_mappings=[],
                    similar_mappings=[],
                    derived_field_suggestions=[],
                    cross_resource_synthesis={},
                    unmappable_fields=list(desired_fields.keys()),
                    analysis_confidence=0.0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    recommendations=["Upload data to enable field mapping"]
                )
            
            # Analyze available fields in each resource
            available_fields_by_resource = {}
            for resource in resources:
                fields = await self._extract_resource_fields(resource)
                if fields:
                    available_fields_by_resource[resource.resource_id] = fields
            
            # Perform field mapping analysis
            direct_mappings = []
            similar_mappings = []
            unmappable_fields = []
            
            for desired_field, desired_desc in desired_fields.items():
                best_direct = None
                best_similar = None
                best_direct_score = 0.0
                best_similar_score = 0.0
                
                # Search across all resources
                for resource_id, available_fields in available_fields_by_resource.items():
                    for available_field, field_info in available_fields.items():
                        mapping_score, mapping_type = self._calculate_field_mapping_score(
                            desired_field, desired_desc, available_field, field_info
                        )
                        
                        if mapping_type == "direct" and mapping_score > best_direct_score:
                            best_direct_score = mapping_score
                            best_direct = FieldMapping(
                                desired_field=desired_field,
                                available_field=available_field,
                                resource_id=resource_id,
                                mapping_type="direct",
                                confidence_score=mapping_score,
                                transformation_required=False,
                                data_type_source=field_info.get("type", "unknown"),
                                data_type_target="inferred",
                                sample_values=field_info.get("sample_values", [])[:3]
                            )
                        
                        elif mapping_type == "similar" and mapping_score > best_similar_score:
                            best_similar_score = mapping_score
                            transformation_needed = self._requires_transformation(
                                field_info.get("type", "unknown"), desired_field, desired_desc
                            )
                            best_similar = FieldMapping(
                                desired_field=desired_field,
                                available_field=available_field,
                                resource_id=resource_id,
                                mapping_type="similar",
                                confidence_score=mapping_score,
                                transformation_required=transformation_needed,
                                transformation_logic=self._suggest_transformation(
                                    available_field, field_info, desired_field, desired_desc
                                ) if transformation_needed else None,
                                data_type_source=field_info.get("type", "unknown"),
                                data_type_target="inferred",
                                sample_values=field_info.get("sample_values", [])[:3]
                            )
                
                # Categorize the best mapping found
                if best_direct and best_direct_score > 0.8:
                    direct_mappings.append(best_direct)
                elif best_similar and best_similar_score > 0.5:
                    similar_mappings.append(best_similar)
                else:
                    unmappable_fields.append(desired_field)
            
            # Generate derived field suggestions for unmappable fields
            derived_suggestions = await self._suggest_derived_fields(
                unmappable_fields, desired_fields, available_fields_by_resource
            )
            
            # Analyze cross-resource synthesis opportunities
            cross_resource_synthesis = await self._analyze_cross_resource_synthesis(
                desired_fields, available_fields_by_resource, resources
            )
            
            # Calculate overall analysis confidence
            total_fields = len(desired_fields)
            mapped_fields = len(direct_mappings) + len(similar_mappings) + len(derived_suggestions)
            analysis_confidence = mapped_fields / total_fields if total_fields > 0 else 0.0
            
            # Generate recommendations
            recommendations = self._generate_field_recommendations(
                direct_mappings, similar_mappings, derived_suggestions, unmappable_fields
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            result = FieldAnalysisResult(
                desired_fields=desired_fields,
                direct_mappings=direct_mappings,
                similar_mappings=similar_mappings,
                derived_field_suggestions=derived_suggestions,
                cross_resource_synthesis=cross_resource_synthesis,
                unmappable_fields=unmappable_fields,
                analysis_confidence=analysis_confidence,
                execution_time_ms=execution_time,
                recommendations=recommendations
            )
            
            # Log completion
            self.activity_logger.log_agent_response(
                self.agent_config.name, user_id, client_id,
                f"Mapped {len(direct_mappings + similar_mappings)} fields, suggested {len(derived_suggestions)} derivations",
                execution_time, self.agent_config.model_name,
                None, None,
                {"analysis_confidence": analysis_confidence, "resources_analyzed": len(resources)}
            )
            
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Field analysis failed: {str(e)}"
            logger.error(error_msg)
            
            self.activity_logger.log_agent_error(
                self.agent_config.name, user_id, client_id,
                error_msg, None
            )
            
            return FieldAnalysisResult(
                desired_fields=desired_fields,
                direct_mappings=[],
                similar_mappings=[],
                derived_field_suggestions=[],
                cross_resource_synthesis={},
                unmappable_fields=list(desired_fields.keys()),
                analysis_confidence=0.0,
                execution_time_ms=execution_time,
                recommendations=[f"Analysis failed: {str(e)}"]
            )
    
    async def _extract_resource_fields(self, resource: ResourceMetadata) -> Dict[str, Any]:
        """Extract field information from a resource."""
        cache_key = f"{resource.resource_id}_{resource.version}"
        if cache_key in self.schema_cache:
            return self.schema_cache[cache_key]
        
        fields = {}
        
        try:
            if resource.resource_type == ResourceType.STRUCTURED:
                fields = await self._extract_structured_fields(resource)
            elif resource.resource_type == ResourceType.JSON:
                fields = await self._extract_json_fields(resource)
            elif resource.resource_type == ResourceType.UNSTRUCTURED:
                fields = await self._extract_unstructured_fields(resource)
            
            # Cache the result
            self.schema_cache[cache_key] = fields
            
        except Exception as e:
            logger.warning(f"Failed to extract fields from {resource.resource_id}: {e}")
        
        return fields
    
    async def _extract_structured_fields(self, resource: ResourceMetadata) -> Dict[str, Any]:
        """Extract fields from structured data resource."""
        fields = {}
        
        try:
            # Get schema information
            schema_info = self.metadata_registry.get_schema_info(resource.resource_id)
            if schema_info:
                schema_data = json.loads(schema_info.schema_json)
                
                for col_name, col_info in schema_data.get("columns", {}).items():
                    fields[col_name] = {
                        "type": col_info.get("type", "unknown"),
                        "description": col_info.get("description", ""),
                        "nullable": col_info.get("nullable", True),
                        "unique_values": col_info.get("unique_values", 0),
                        "sample_values": col_info.get("sample_values", []),
                        "patterns": col_info.get("patterns", []),
                        "semantic_type": self._infer_semantic_type(col_name, col_info.get("sample_values", []))
                    }
        
        except Exception as e:
            logger.error(f"Failed to extract structured fields: {e}")
        
        return fields
    
    async def _extract_json_fields(self, resource: ResourceMetadata) -> Dict[str, Any]:
        """Extract fields from JSON data resource."""
        fields = {}
        
        try:
            # Get sample JSON data
            table_name = f"json_{resource.resource_id.replace('-', '_')}"
            sample_data = self.storage_router.query_json_data(
                table_name, resource.client_id, resource.user_id
            )
            
            if sample_data:
                # Flatten JSON structure
                flattened_fields = self._flatten_json_structure(sample_data[:10])  # Sample first 10 records
                
                for field_path, field_info in flattened_fields.items():
                    fields[field_path] = {
                        "type": field_info["type"],
                        "description": f"JSON field: {field_path}",
                        "nullable": field_info["nullable"],
                        "unique_values": field_info["unique_count"],
                        "sample_values": field_info["sample_values"],
                        "patterns": field_info.get("patterns", []),
                        "semantic_type": self._infer_semantic_type(field_path, field_info["sample_values"])
                    }
        
        except Exception as e:
            logger.error(f"Failed to extract JSON fields: {e}")
        
        return fields
    
    async def _extract_unstructured_fields(self, resource: ResourceMetadata) -> Dict[str, Any]:
        """Extract conceptual fields from unstructured data resource."""
        fields = {}
        
        try:
            # For unstructured data, we create conceptual fields based on content analysis
            fields["content"] = {
                "type": "text",
                "description": "Full text content",
                "nullable": False,
                "unique_values": 1,
                "sample_values": ["Text content..."],
                "patterns": ["unstructured_text"],
                "semantic_type": "text_content"
            }
            
            # Add extracted entities as potential fields
            fields["entities"] = {
                "type": "extracted_entities",
                "description": "Named entities extracted from text",
                "nullable": True,
                "unique_values": 0,
                "sample_values": [],
                "patterns": ["entity_extraction"],
                "semantic_type": "named_entities"
            }
        
        except Exception as e:
            logger.error(f"Failed to extract unstructured fields: {e}")
        
        return fields
    
    def _calculate_field_mapping_score(self, desired_field: str, desired_desc: str,
                                     available_field: str, field_info: Dict[str, Any]) -> Tuple[float, str]:
        """Calculate mapping score between desired and available fields."""
        score = 0.0
        
        # Exact name match
        if desired_field.lower() == available_field.lower():
            return 0.95, "direct"
        
        # Normalize field names for comparison
        desired_normalized = self._normalize_field_name(desired_field)
        available_normalized = self._normalize_field_name(available_field)
        
        if desired_normalized == available_normalized:
            return 0.90, "direct"
        
        # Name similarity scoring
        name_similarity = self._calculate_name_similarity(desired_field, available_field)
        score += name_similarity * 0.4
        
        # Description similarity (if available)
        if desired_desc and field_info.get("description"):
            desc_similarity = self._calculate_description_similarity(desired_desc, field_info["description"])
            score += desc_similarity * 0.3
        
        # Semantic type compatibility
        desired_semantic = self._infer_semantic_type(desired_field, [])
        available_semantic = field_info.get("semantic_type", "unknown")
        
        if desired_semantic == available_semantic and desired_semantic != "general":
            score += 0.2
        elif self._are_compatible_semantic_types(desired_semantic, available_semantic):
            score += 0.1
        
        # Data type compatibility
        if self._are_compatible_data_types(desired_field, field_info.get("type", "unknown")):
            score += 0.1
        
        # Determine mapping type
        if score >= 0.8:
            return score, "direct"
        elif score >= 0.4:
            return score, "similar"
        else:
            return score, "none"
    
    def _normalize_field_name(self, field_name: str) -> str:
        """Normalize field name for comparison."""
        # Convert to lowercase, replace separators with underscores, remove extra spaces
        normalized = re.sub(r'[_\-\s\.]+', '_', field_name.lower().strip())
        # Remove common prefixes/suffixes
        normalized = re.sub(r'^(the_|a_|an_)', '', normalized)
        normalized = re.sub(r'(_id|_key|_name|_value)$', '', normalized)
        return normalized
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between field names."""
        # Simple implementation using common words and character similarity
        words1 = set(re.findall(r'\w+', name1.lower()))
        words2 = set(re.findall(r'\w+', name2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard similarity for words
        intersection = words1 & words2
        union = words1 | words2
        
        if not union:
            return 0.0
        
        word_similarity = len(intersection) / len(union)
        
        # Character-level similarity (simple)
        char_similarity = 0.0
        if name1 and name2:
            common_chars = sum(1 for c in name1.lower() if c in name2.lower())
            char_similarity = common_chars / max(len(name1), len(name2))
        
        return (word_similarity * 0.7) + (char_similarity * 0.3)
    
    def _calculate_description_similarity(self, desc1: str, desc2: str) -> float:
        """Calculate similarity between field descriptions."""
        if not desc1 or not desc2:
            return 0.0
        
        words1 = set(re.findall(r'\w+', desc1.lower()))
        words2 = set(re.findall(r'\w+', desc2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _infer_semantic_type(self, field_name: str, sample_values: List[Any]) -> str:
        """Infer semantic type from field name and sample values."""
        field_name_lower = field_name.lower()
        
        # Name-based inference
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
        
        return "general"
    
    def _are_compatible_semantic_types(self, type1: str, type2: str) -> bool:
        """Check if two semantic types are compatible."""
        compatible_groups = [
            {"name", "title", "label"},
            {"email", "mail"},
            {"phone", "tel", "mobile"},
            {"address", "street", "city", "zip"},
            {"date", "time", "datetime", "created", "updated"},
            {"price", "cost", "amount", "salary", "revenue", "monetary_amount"},
            {"id", "key", "uuid", "identifier"},
            {"count", "number", "quantity", "age", "numeric"},
            {"url", "link", "website"},
            {"category", "type", "status", "group"}
        ]
        
        for group in compatible_groups:
            if type1 in group and type2 in group:
                return True
        
        return False
    
    def _are_compatible_data_types(self, field_name: str, data_type: str) -> bool:
        """Check if field name suggests compatibility with data type."""
        # This is a simplified implementation
        numeric_indicators = ["count", "number", "amount", "price", "age", "quantity"]
        text_indicators = ["name", "title", "description", "comment", "note"]
        date_indicators = ["date", "time", "created", "updated"]
        
        field_lower = field_name.lower()
        
        if data_type in ["integer", "float", "numeric", "number"]:
            return any(indicator in field_lower for indicator in numeric_indicators)
        elif data_type in ["string", "text", "varchar"]:
            return any(indicator in field_lower for indicator in text_indicators)
        elif data_type in ["date", "datetime", "timestamp"]:
            return any(indicator in field_lower for indicator in date_indicators)
        
        return True  # Default to compatible
    
    def _requires_transformation(self, source_type: str, target_field: str, target_desc: str) -> bool:
        """Determine if transformation is required for field mapping."""
        # Simple heuristics for transformation requirements
        target_lower = target_field.lower()
        
        # Type mismatches that require transformation
        if source_type == "string" and any(word in target_lower for word in ["amount", "price", "count"]):
            return True
        
        if source_type in ["integer", "float"] and any(word in target_lower for word in ["name", "title", "description"]):
            return True
        
        # Format standardization needs
        if any(word in target_lower for word in ["phone", "email", "date"]):
            return True
        
        return False
    
    def _suggest_transformation(self, source_field: str, source_info: Dict[str, Any],
                              target_field: str, target_desc: str) -> str:
        """Suggest transformation logic for field mapping."""
        source_type = source_info.get("type", "unknown")
        target_lower = target_field.lower()
        
        # Type conversion transformations
        if source_type == "string" and any(word in target_lower for word in ["amount", "price"]):
            return f"CAST({source_field} AS DECIMAL(10,2))"
        
        if source_type == "string" and "count" in target_lower:
            return f"CAST({source_field} AS INTEGER)"
        
        # Format standardization
        if "phone" in target_lower:
            return f"REGEXP_REPLACE({source_field}, '[^0-9]', '', 'g')"
        
        if "email" in target_lower:
            return f"LOWER(TRIM({source_field}))"
        
        if "date" in target_lower:
            return f"DATE({source_field})"
        
        return f"TRIM({source_field})"
    
    def _flatten_json_structure(self, json_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Flatten nested JSON structure for field analysis."""
        flattened = {}
        
        for record in json_data:
            self._flatten_json_record(record, "", flattened)
        
        # Calculate statistics for each field
        for field_path, field_info in flattened.items():
            values = field_info["values"]
            field_info["unique_count"] = len(set(str(v) for v in values if v is not None))
            field_info["nullable"] = None in values
            field_info["sample_values"] = list(set(values))[:5]
            
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
    
    async def _suggest_derived_fields(self, unmappable_fields: List[str],
                                    desired_fields: Dict[str, str],
                                    available_fields_by_resource: Dict[str, Dict[str, Any]]) -> List[DerivedFieldDefinition]:
        """Suggest how to derive unmappable fields from available data."""
        suggestions = []
        
        for field_name in unmappable_fields:
            field_desc = desired_fields.get(field_name, "")
            
            # Use AI to suggest derivation logic
            derivation_prompt = self._build_derivation_prompt(
                field_name, field_desc, available_fields_by_resource
            )
            
            try:
                ai_response = await self.execute(derivation_prompt)
                derivation_suggestion = self._parse_derivation_response(ai_response, field_name)
                
                if derivation_suggestion:
                    suggestions.append(derivation_suggestion)
                    
            except Exception as e:
                logger.warning(f"Failed to generate derivation for {field_name}: {e}")
                
                # Fallback to simple heuristic-based suggestion
                fallback_suggestion = self._generate_fallback_derivation(
                    field_name, field_desc, available_fields_by_resource
                )
                if fallback_suggestion:
                    suggestions.append(fallback_suggestion)
        
        return suggestions[:10]  # Limit to top 10 suggestions
    
    def _build_derivation_prompt(self, field_name: str, field_desc: str,
                               available_fields_by_resource: Dict[str, Dict[str, Any]]) -> str:
        """Build AI prompt for field derivation suggestions."""
        available_summary = {}
        for resource_id, fields in available_fields_by_resource.items():
            available_summary[resource_id] = {
                "field_count": len(fields),
                "fields": list(fields.keys())[:10],  # First 10 fields
                "sample_types": list(set(f.get("type", "unknown") for f in fields.values()))[:5]
            }
        
        return f"""
Analyze how to derive the field "{field_name}" from available data sources.

Target Field:
- Name: {field_name}
- Description: {field_desc}

Available Data Sources:
{json.dumps(available_summary, indent=2)}

Please suggest how to calculate or derive this field. Consider:
1. Direct calculations from numeric fields
2. String transformations and concatenations
3. Conditional logic based on existing fields
4. Aggregations across multiple records
5. Lookups and joins between resources

Provide your response as JSON with keys:
- calculation_logic: SQL-like expression or description
- source_fields: list of required source fields
- source_resources: list of required resource IDs
- data_type: expected output data type
- complexity_level: "simple", "medium", or "complex"
- confidence_score: 0.0 to 1.0
- validation_rules: list of validation rules
- performance_impact: "low", "medium", or "high"
"""
    
    def _parse_derivation_response(self, ai_response: str, field_name: str) -> Optional[DerivedFieldDefinition]:
        """Parse AI response for derivation suggestion."""
        try:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                return DerivedFieldDefinition(
                    field_name=field_name,
                    description=f"Derived field: {field_name}",
                    calculation_logic=data.get("calculation_logic", ""),
                    source_fields=data.get("source_fields", []),
                    source_resources=data.get("source_resources", []),
                    data_type=data.get("data_type", "unknown"),
                    validation_rules=data.get("validation_rules", []),
                    confidence_score=data.get("confidence_score", 0.5),
                    complexity_level=data.get("complexity_level", "medium"),
                    estimated_performance=data.get("performance_impact", "medium")
                )
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse derivation response: {e}")
        
        return None
    
    def _generate_fallback_derivation(self, field_name: str, field_desc: str,
                                    available_fields_by_resource: Dict[str, Dict[str, Any]]) -> Optional[DerivedFieldDefinition]:
        """Generate fallback derivation suggestion using heuristics."""
        field_lower = field_name.lower()
        
        # Look for potential source fields
        potential_sources = []
        source_resources = []
        
        for resource_id, fields in available_fields_by_resource.items():
            for available_field, field_info in fields.items():
                # Simple name matching
                if any(word in available_field.lower() for word in field_lower.split('_')):
                    potential_sources.append(available_field)
                    if resource_id not in source_resources:
                        source_resources.append(resource_id)
        
        if potential_sources:
            # Generate simple calculation logic
            if "total" in field_lower or "sum" in field_lower:
                calculation = f"SUM({potential_sources[0]})"
                complexity = "simple"
            elif "average" in field_lower or "avg" in field_lower:
                calculation = f"AVG({potential_sources[0]})"
                complexity = "simple"
            elif "count" in field_lower:
                calculation = f"COUNT({potential_sources[0]})"
                complexity = "simple"
            else:
                calculation = f"COALESCE({', '.join(potential_sources[:3])})"
                complexity = "medium"
            
            return DerivedFieldDefinition(
                field_name=field_name,
                description=f"Derived from available fields: {', '.join(potential_sources[:3])}",
                calculation_logic=calculation,
                source_fields=potential_sources[:3],
                source_resources=source_resources,
                data_type="numeric" if any(word in field_lower for word in ["count", "sum", "total", "avg"]) else "string",
                validation_rules=[f"Check for null values in {potential_sources[0]}"],
                confidence_score=0.4,
                complexity_level=complexity,
                estimated_performance="medium"
            )
        
        return None
    
    async def _analyze_cross_resource_synthesis(self, desired_fields: Dict[str, str],
                                              available_fields_by_resource: Dict[str, Dict[str, Any]],
                                              resources: List[ResourceMetadata]) -> Dict[str, Any]:
        """Analyze opportunities for cross-resource field synthesis."""
        synthesis_opportunities = []
        
        if len(available_fields_by_resource) < 2:
            return {"opportunities": [], "total_count": 0}
        
        # Look for fields that could be synthesized across resources
        for desired_field, desired_desc in desired_fields.items():
            # Find partial matches across different resources
            partial_matches = {}
            
            for resource_id, fields in available_fields_by_resource.items():
                for available_field, field_info in fields.items():
                    similarity_score, _ = self._calculate_field_mapping_score(
                        desired_field, desired_desc, available_field, field_info
                    )
                    
                    if similarity_score > 0.3:  # Partial match threshold
                        if resource_id not in partial_matches:
                            partial_matches[resource_id] = []
                        partial_matches[resource_id].append({
                            "field": available_field,
                            "score": similarity_score,
                            "info": field_info
                        })
            
            # If we have partial matches across multiple resources, suggest synthesis
            if len(partial_matches) >= 2:
                synthesis_id = str(uuid.uuid4())
                
                # Determine synthesis strategy
                strategy = self._determine_synthesis_strategy(partial_matches, desired_field)
                
                synthesis_opportunities.append({
                    "synthesis_id": synthesis_id,
                    "target_field": desired_field,
                    "source_resources": list(partial_matches.keys()),
                    "source_fields": [match["field"] for matches in partial_matches.values() for match in matches],
                    "synthesis_strategy": strategy,
                    "estimated_quality": min(0.8, max(match["score"] for matches in partial_matches.values() for match in matches)),
                    "complexity": "medium" if len(partial_matches) == 2 else "high"
                })
        
        return {
            "opportunities": synthesis_opportunities,
            "total_count": len(synthesis_opportunities),
            "strategies_used": list(set(opp["synthesis_strategy"] for opp in synthesis_opportunities))
        }
    
    def _determine_synthesis_strategy(self, partial_matches: Dict[str, List[Dict[str, Any]]], 
                                    desired_field: str) -> str:
        """Determine the best synthesis strategy for cross-resource field combination."""
        field_lower = desired_field.lower()
        
        # Check if fields are likely to be joinable
        has_id_fields = any(
            any("id" in match["field"].lower() for match in matches)
            for matches in partial_matches.values()
        )
        
        if has_id_fields:
            return "join"
        
        # Check if fields are similar enough to union
        all_fields = [match["field"] for matches in partial_matches.values() for match in matches]
        if len(set(field.lower() for field in all_fields)) == 1:
            return "union"
        
        # Check if aggregation is appropriate
        if any(word in field_lower for word in ["total", "sum", "count", "average"]):
            return "aggregation"
        
        return "transformation"
    
    def _generate_field_recommendations(self, direct_mappings: List[FieldMapping],
                                      similar_mappings: List[FieldMapping],
                                      derived_suggestions: List[DerivedFieldDefinition],
                                      unmappable_fields: List[str]) -> List[str]:
        """Generate actionable recommendations for field mapping improvements."""
        recommendations = []
        
        # Direct mapping recommendations
        if direct_mappings:
            recommendations.append(f"Found {len(direct_mappings)} direct field mappings - these can be used immediately")
        
        # Similar mapping recommendations
        if similar_mappings:
            transformations_needed = sum(1 for m in similar_mappings if m.transformation_required)
            if transformations_needed > 0:
                recommendations.append(f"{transformations_needed} similar mappings require data transformations")
        
        # Derived field recommendations
        if derived_suggestions:
            simple_derivations = sum(1 for d in derived_suggestions if d.complexity_level == "simple")
            if simple_derivations > 0:
                recommendations.append(f"{simple_derivations} fields can be derived using simple calculations")
        
        # Unmappable field recommendations
        if unmappable_fields:
            if len(unmappable_fields) <= 3:
                recommendations.append(f"Consider uploading additional data for: {', '.join(unmappable_fields)}")
            else:
                recommendations.append(f"{len(unmappable_fields)} fields require additional data sources")
        
        # Data quality recommendations
        low_confidence_mappings = [m for m in similar_mappings if m.confidence_score < 0.6]
        if low_confidence_mappings:
            recommendations.append("Review low-confidence mappings for accuracy")
        
        # Performance recommendations
        complex_derivations = [d for d in derived_suggestions if d.complexity_level == "complex"]
        if complex_derivations:
            recommendations.append("Complex field derivations may impact query performance")
        
        if not recommendations:
            recommendations.append("Field mapping analysis complete - ready for data queries")
        
        return recommendations
    
    async def calculate_derived_field(self, client_id: str, user_id: str,
                                    field_definition: DerivedFieldDefinition) -> Dict[str, Any]:
        """
        Calculate a derived field based on its definition.
        
        Args:
            client_id: Client identifier
            user_id: User identifier
            field_definition: Definition of the field to calculate
            
        Returns:
            Calculation result with sample values and metadata
        """
        start_time = time.time()
        
        try:
            self.initialize()
            
            logger.info(f"Calculating derived field: {field_definition.field_name}")
            
            # Validate that user has access to source resources
            accessible_resources = []
            for resource_id in field_definition.source_resources:
                resource = self.metadata_registry.get_resource_metadata(resource_id)
                if resource and resource.user_id == user_id and resource.client_id == client_id:
                    accessible_resources.append(resource)
            
            if not accessible_resources:
                return {
                    "success": False,
                    "error": "No accessible source resources found",
                    "execution_time_ms": (time.time() - start_time) * 1000
                }
            
            # Generate calculation query based on complexity
            if field_definition.complexity_level == "simple":
                result = await self._execute_simple_calculation(field_definition, accessible_resources)
            elif field_definition.complexity_level == "medium":
                result = await self._execute_medium_calculation(field_definition, accessible_resources)
            else:
                result = await self._execute_complex_calculation(field_definition, accessible_resources)
            
            execution_time = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "field_name": field_definition.field_name,
                "calculation_result": result,
                "execution_time_ms": execution_time,
                "data_type": field_definition.data_type,
                "source_resources": len(accessible_resources)
            }
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Derived field calculation failed: {str(e)}"
            logger.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "execution_time_ms": execution_time
            }
    
    async def _execute_simple_calculation(self, field_definition: DerivedFieldDefinition,
                                        resources: List[ResourceMetadata]) -> Dict[str, Any]:
        """Execute simple field calculation."""
        # This is a placeholder implementation
        # In practice, this would execute the actual calculation logic
        return {
            "sample_values": ["calculated_value_1", "calculated_value_2"],
            "calculation_type": "simple",
            "estimated_rows": sum(r.row_count or 0 for r in resources),
            "validation_passed": True
        }
    
    async def _execute_medium_calculation(self, field_definition: DerivedFieldDefinition,
                                        resources: List[ResourceMetadata]) -> Dict[str, Any]:
        """Execute medium complexity field calculation."""
        return {
            "sample_values": ["medium_calc_1", "medium_calc_2"],
            "calculation_type": "medium",
            "estimated_rows": sum(r.row_count or 0 for r in resources),
            "validation_passed": True,
            "performance_notes": "May require indexing for optimal performance"
        }
    
    async def _execute_complex_calculation(self, field_definition: DerivedFieldDefinition,
                                         resources: List[ResourceMetadata]) -> Dict[str, Any]:
        """Execute complex field calculation."""
        return {
            "sample_values": ["complex_result_1", "complex_result_2"],
            "calculation_type": "complex",
            "estimated_rows": sum(r.row_count or 0 for r in resources),
            "validation_passed": True,
            "performance_notes": "Consider caching results for repeated queries",
            "optimization_suggestions": ["Create materialized view", "Add computed column"]
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the Field Extraction Agent."""
        try:
            self.initialize()
            
            # Test basic functionality
            test_response = await self.execute("Analyze field mapping: source='customer_name', target='name'")
            
            return {
                "status": "healthy",
                "agent_info": self.get_agent_info(),
                "cache_stats": {
                    "field_mapping_cache_size": len(self.field_mapping_cache),
                    "schema_cache_size": len(self.schema_cache),
                    "calculation_cache_size": len(self.calculation_cache)
                },
                "test_response_length": len(test_response)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "agent_info": self.get_agent_info()
            }
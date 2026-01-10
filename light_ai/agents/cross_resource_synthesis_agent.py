"""
Cross-Resource Synthesis Agent for Intelligent Data Analysis.

This AI agent specializes in multi-source data combination, intelligent join
strategy selection, schema conflict resolution, data type harmonization,
and unified view generation with lineage tracking.
"""

import json
import time
import uuid
import re
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from .base import BaseAgent, AgentConfig
from .logging import get_activity_logger
from ..core.models import ResourceMetadata, ResourceType, DataType, SchemaInfo
from ..storage.metadata_registry import MetadataRegistry
from ..storage.storage_router import StorageRouter
from ..storage.database_managers import DatabaseManagers
from ..config import Config, get_config
from ..logger import get_logger

logger = get_logger(__name__)


class JoinStrategy(Enum):
    """Available join strategies for cross-resource synthesis."""
    INNER_JOIN = "inner_join"
    LEFT_JOIN = "left_join"
    RIGHT_JOIN = "right_join"
    FULL_OUTER_JOIN = "full_outer_join"
    CROSS_JOIN = "cross_join"
    UNION = "union"
    UNION_ALL = "union_all"


class SynthesisStrategy(Enum):
    """Available synthesis strategies."""
    JOIN_BASED = "join_based"
    UNION_BASED = "union_based"
    AGGREGATION_BASED = "aggregation_based"
    TRANSFORMATION_BASED = "transformation_based"
    CORRELATION_BASED = "correlation_based"


@dataclass
class JoinCondition:
    """Definition of a join condition between resources."""
    left_resource_id: str
    right_resource_id: str
    left_field: str
    right_field: str
    join_type: JoinStrategy
    confidence_score: float
    data_type_compatibility: bool
    transformation_required: bool = False
    transformation_logic: Optional[str] = None


@dataclass
class SchemaConflict:
    """Represents a schema conflict between resources."""
    conflict_id: str
    conflict_type: str  # field_name, data_type, format, semantic
    resource_ids: List[str]
    field_names: List[str]
    data_types: List[str]
    sample_values: List[Any]
    resolution_strategy: Optional[str] = None
    resolution_logic: Optional[str] = None
    confidence_score: float = 0.0


@dataclass
class DataTypeHarmonization:
    """Data type harmonization specification."""
    harmonization_id: str
    source_types: List[str]
    target_type: str
    conversion_logic: str
    validation_rules: List[str]
    precision_loss: bool = False
    fallback_strategy: Optional[str] = None


@dataclass
class UnifiedView:
    """Specification for a unified view across resources."""
    view_id: str
    view_name: str
    source_resources: List[str]
    unified_schema: Dict[str, str]
    synthesis_strategy: SynthesisStrategy
    join_conditions: List[JoinCondition]
    field_mappings: Dict[str, Dict[str, str]]  # {unified_field: {resource_id: source_field}}
    data_transformations: List[str]
    lineage_tracking: Dict[str, List[str]]  # {unified_field: [source_resource.field]}
    estimated_row_count: int
    quality_score: float
    performance_impact: str  # low, medium, high


@dataclass
class SynthesisResult:
    """Result of cross-resource synthesis operation."""
    synthesis_id: str
    unified_view: UnifiedView
    conflicts_resolved: List[SchemaConflict]
    harmonizations_applied: List[DataTypeHarmonization]
    execution_plan: List[str]
    estimated_execution_time_ms: float
    data_quality_assessment: Dict[str, Any]
    recommendations: List[str]
    warnings: List[str]


class CrossResourceSynthesisAgent(BaseAgent):
    """
    AI Agent for Cross-Resource Data Synthesis.
    
    This agent specializes in:
    - Multi-source data combination strategies
    - Intelligent join strategy selection
    - Schema conflict detection and resolution
    - Data type harmonization across sources
    - Unified view generation with complete lineage tracking
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the Cross-Resource Synthesis Agent."""
        
        system_prompt = """You are an expert AI Cross-Resource Synthesis Agent specializing in intelligent multi-source data combination and harmonization.

Your capabilities:
1. Analyze multiple data sources for synthesis opportunities
2. Detect and resolve schema conflicts intelligently
3. Select optimal join strategies based on data characteristics
4. Harmonize data types across different sources
5. Generate unified views with complete lineage tracking
6. Assess data quality and synthesis feasibility

Synthesis Analysis Framework:
- For join-based synthesis: Identify common fields, assess join cardinality, optimize join order
- For union-based synthesis: Align schemas, resolve field conflicts, standardize formats
- For aggregation-based synthesis: Design aggregation strategies, handle grouping conflicts
- For transformation-based synthesis: Create transformation pipelines, preserve data integrity

Schema Conflict Resolution:
- Field name conflicts: Use semantic similarity and domain knowledge
- Data type conflicts: Apply safe type conversions with minimal precision loss
- Format conflicts: Standardize formats while preserving original meaning
- Semantic conflicts: Resolve using business logic and data context

Join Strategy Selection:
- Analyze data distribution and cardinality
- Consider performance implications
- Assess data quality and completeness
- Optimize for query patterns and use cases

Data Type Harmonization:
- Preserve data integrity during type conversions
- Handle precision and scale differences
- Implement fallback strategies for conversion failures
- Validate conversion results

Quality Assessment:
- Evaluate synthesis feasibility and data compatibility
- Assess potential data loss or quality degradation
- Identify performance bottlenecks and optimization opportunities
- Provide actionable recommendations for improvement

Always provide:
- Detailed synthesis strategies with confidence scores
- Complete lineage tracking for all transformations
- Performance impact assessments
- Data quality considerations and warnings
- Clear explanations of resolution logic and trade-offs"""

        agent_config = AgentConfig(
            name="cross_resource_synthesis_agent",
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
        self.synthesis_cache: Dict[str, SynthesisResult] = {}
        self.schema_cache: Dict[str, Dict[str, Any]] = {}
        self.join_analysis_cache: Dict[str, List[JoinCondition]] = {}
        
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize the agent and dependencies."""
        if not self._initialized:
            self.metadata_registry.initialize()
            self.storage_router.initialize()
            self.db_managers.initialize_all()
            self._initialized = True
            logger.info("Cross-Resource Synthesis Agent initialized")
    
    async def synthesize_resources(self, client_id: str, user_id: str,
                                 resource_ids: List[str],
                                 synthesis_goal: str,
                                 desired_fields: Optional[Dict[str, str]] = None) -> SynthesisResult:
        """
        Synthesize data from multiple resources into a unified view.
        
        Args:
            client_id: Client identifier
            user_id: User identifier
            resource_ids: List of resource IDs to synthesize
            synthesis_goal: Description of the synthesis objective
            desired_fields: Optional dict of {field_name: description} for target schema
            
        Returns:
            Comprehensive synthesis result with unified view and lineage
        """
        start_time = time.time()
        synthesis_id = str(uuid.uuid4())
        
        try:
            self.initialize()
            
            logger.info(f"Starting cross-resource synthesis for user {user_id} with {len(resource_ids)} resources")
            
            # Log agent activity
            self.activity_logger.log_agent_query(
                self.agent_config.name, user_id, client_id,
                f"synthesize_resources: {synthesis_goal}", None
            )
            
            # Validate and get resources
            resources = await self._validate_and_get_resources(client_id, user_id, resource_ids)
            
            if len(resources) < 2:
                return self._create_error_result(
                    synthesis_id, "At least 2 resources required for synthesis",
                    (time.time() - start_time) * 1000
                )
            
            # Analyze resource schemas
            schema_analysis = await self._analyze_resource_schemas(resources)
            
            # Detect schema conflicts
            conflicts = await self._detect_schema_conflicts(schema_analysis, synthesis_goal)
            
            # Resolve conflicts and create harmonization plan
            resolved_conflicts, harmonizations = await self._resolve_conflicts_and_harmonize(
                conflicts, schema_analysis
            )
            
            # Determine optimal synthesis strategy
            synthesis_strategy = await self._determine_synthesis_strategy(
                resources, schema_analysis, synthesis_goal, desired_fields
            )
            
            # Generate join conditions if applicable
            join_conditions = []
            if synthesis_strategy in [SynthesisStrategy.JOIN_BASED, SynthesisStrategy.CORRELATION_BASED]:
                join_conditions = await self._generate_join_conditions(resources, schema_analysis)
            
            # Create unified view specification
            unified_view = await self._create_unified_view(
                synthesis_id, resources, schema_analysis, synthesis_strategy,
                join_conditions, desired_fields, resolved_conflicts, harmonizations
            )
            
            # Generate execution plan
            execution_plan = await self._generate_execution_plan(
                unified_view, resolved_conflicts, harmonizations
            )
            
            # Assess data quality and performance
            quality_assessment = await self._assess_synthesis_quality(
                unified_view, resources, schema_analysis
            )
            
            # Generate recommendations and warnings
            recommendations, warnings = await self._generate_recommendations_and_warnings(
                unified_view, conflicts, harmonizations, quality_assessment
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            result = SynthesisResult(
                synthesis_id=synthesis_id,
                unified_view=unified_view,
                conflicts_resolved=resolved_conflicts,
                harmonizations_applied=harmonizations,
                execution_plan=execution_plan,
                estimated_execution_time_ms=execution_time * 2,  # Estimate actual execution time
                data_quality_assessment=quality_assessment,
                recommendations=recommendations,
                warnings=warnings
            )
            
            # Cache the result
            cache_key = f"{user_id}_{hash(tuple(sorted(resource_ids)))}"
            self.synthesis_cache[cache_key] = result
            
            # Log completion
            self.activity_logger.log_agent_response(
                self.agent_config.name, user_id, client_id,
                f"Synthesis completed with {len(resolved_conflicts)} conflicts resolved",
                execution_time, self.agent_config.model_name,
                None, None,
                {"synthesis_strategy": synthesis_strategy.value, "quality_score": unified_view.quality_score}
            )
            
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Cross-resource synthesis failed: {str(e)}"
            logger.error(error_msg)
            
            self.activity_logger.log_agent_error(
                self.agent_config.name, user_id, client_id,
                error_msg, None
            )
            
            return self._create_error_result(synthesis_id, error_msg, execution_time)
    
    async def _validate_and_get_resources(self, client_id: str, user_id: str,
                                        resource_ids: List[str]) -> List[ResourceMetadata]:
        """Validate and retrieve resource metadata."""
        resources = []
        
        for resource_id in resource_ids:
            resource = self.metadata_registry.get_resource_metadata(resource_id)
            if not resource:
                raise ValueError(f"Resource not found: {resource_id}")
            
            if resource.user_id != user_id or resource.client_id != client_id:
                raise ValueError(f"Access denied to resource: {resource_id}")
            
            if resource.processing_status != "completed":
                raise ValueError(f"Resource not ready for synthesis: {resource_id}")
            
            resources.append(resource)
        
        return resources
    
    async def _analyze_resource_schemas(self, resources: List[ResourceMetadata]) -> Dict[str, Dict[str, Any]]:
        """Analyze schemas of all resources."""
        schema_analysis = {}
        
        for resource in resources:
            try:
                if resource.resource_type == ResourceType.STRUCTURED:
                    schema = await self._analyze_structured_schema(resource)
                elif resource.resource_type == ResourceType.JSON:
                    schema = await self._analyze_json_schema(resource)
                elif resource.resource_type == ResourceType.UNSTRUCTURED:
                    schema = await self._analyze_unstructured_schema(resource)
                else:
                    schema = {"fields": {}, "metadata": {"error": "Unsupported resource type"}}
                
                schema_analysis[resource.resource_id] = schema
                
            except Exception as e:
                logger.warning(f"Failed to analyze schema for {resource.resource_id}: {e}")
                schema_analysis[resource.resource_id] = {
                    "fields": {},
                    "metadata": {"error": str(e)}
                }
        
        return schema_analysis
    
    async def _analyze_structured_schema(self, resource: ResourceMetadata) -> Dict[str, Any]:
        """Analyze structured data schema."""
        schema_info = self.metadata_registry.get_schema_info(resource.resource_id)
        
        if not schema_info:
            return {"fields": {}, "metadata": {"error": "No schema information available"}}
        
        try:
            schema_data = json.loads(schema_info.schema_json)
            
            fields = {}
            for col_name, col_info in schema_data.get("columns", {}).items():
                fields[col_name] = {
                    "type": col_info.get("type", "unknown"),
                    "nullable": col_info.get("nullable", True),
                    "unique_values": col_info.get("unique_values", 0),
                    "sample_values": col_info.get("sample_values", []),
                    "semantic_type": self._infer_semantic_type(col_name, col_info.get("sample_values", [])),
                    "patterns": col_info.get("patterns", [])
                }
            
            return {
                "fields": fields,
                "metadata": {
                    "resource_type": "structured",
                    "row_count": resource.row_count,
                    "column_count": len(fields)
                }
            }
            
        except json.JSONDecodeError as e:
            return {"fields": {}, "metadata": {"error": f"Invalid schema JSON: {e}"}}
    
    async def _analyze_json_schema(self, resource: ResourceMetadata) -> Dict[str, Any]:
        """Analyze JSON data schema."""
        try:
            # Get sample JSON data
            table_name = f"json_{resource.resource_id.replace('-', '_')}"
            sample_data = self.storage_router.query_json_data(
                table_name, resource.client_id, resource.user_id
            )
            
            if not sample_data:
                return {"fields": {}, "metadata": {"error": "No JSON data available"}}
            
            # Flatten and analyze JSON structure
            flattened_fields = self._flatten_json_structure(sample_data[:10])
            
            fields = {}
            for field_path, field_info in flattened_fields.items():
                fields[field_path] = {
                    "type": field_info["type"],
                    "nullable": field_info["nullable"],
                    "unique_values": field_info["unique_count"],
                    "sample_values": field_info["sample_values"],
                    "semantic_type": self._infer_semantic_type(field_path, field_info["sample_values"]),
                    "patterns": field_info.get("patterns", [])
                }
            
            return {
                "fields": fields,
                "metadata": {
                    "resource_type": "json",
                    "row_count": len(sample_data),
                    "column_count": len(fields)
                }
            }
            
        except Exception as e:
            return {"fields": {}, "metadata": {"error": f"JSON analysis failed: {e}"}}
    
    async def _analyze_unstructured_schema(self, resource: ResourceMetadata) -> Dict[str, Any]:
        """Analyze unstructured data schema."""
        # For unstructured data, create conceptual fields
        fields = {
            "content": {
                "type": "text",
                "nullable": False,
                "unique_values": 1,
                "sample_values": ["Text content..."],
                "semantic_type": "text_content",
                "patterns": ["unstructured_text"]
            },
            "entities": {
                "type": "extracted_entities",
                "nullable": True,
                "unique_values": 0,
                "sample_values": [],
                "semantic_type": "named_entities",
                "patterns": ["entity_extraction"]
            }
        }
        
        return {
            "fields": fields,
            "metadata": {
                "resource_type": "unstructured",
                "chunk_count": resource.chunk_count,
                "column_count": len(fields)
            }
        }
    
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
    
    async def _detect_schema_conflicts(self, schema_analysis: Dict[str, Dict[str, Any]],
                                     synthesis_goal: str) -> List[SchemaConflict]:
        """Detect conflicts between resource schemas."""
        conflicts = []
        
        # Group fields by name across resources
        field_groups = {}
        for resource_id, schema in schema_analysis.items():
            for field_name, field_info in schema.get("fields", {}).items():
                if field_name not in field_groups:
                    field_groups[field_name] = []
                field_groups[field_name].append({
                    "resource_id": resource_id,
                    "field_info": field_info
                })
        
        # Detect conflicts in each field group
        for field_name, field_instances in field_groups.items():
            if len(field_instances) > 1:
                conflict = self._analyze_field_conflict(field_name, field_instances)
                if conflict:
                    conflicts.append(conflict)
        
        # Use AI to analyze complex conflicts
        if conflicts:
            ai_analysis = await self._analyze_conflicts_with_ai(conflicts, synthesis_goal)
            conflicts = self._enhance_conflicts_with_ai_analysis(conflicts, ai_analysis)
        
        return conflicts
    
    def _analyze_field_conflict(self, field_name: str, 
                              field_instances: List[Dict[str, Any]]) -> Optional[SchemaConflict]:
        """Analyze a specific field conflict."""
        resource_ids = [instance["resource_id"] for instance in field_instances]
        field_infos = [instance["field_info"] for instance in field_instances]
        
        # Check for data type conflicts
        data_types = [info["type"] for info in field_infos]
        semantic_types = [info["semantic_type"] for info in field_infos]
        
        if len(set(data_types)) > 1 or len(set(semantic_types)) > 1:
            conflict_id = str(uuid.uuid4())
            
            # Determine conflict type
            if len(set(data_types)) > 1:
                conflict_type = "data_type"
            elif len(set(semantic_types)) > 1:
                conflict_type = "semantic"
            else:
                conflict_type = "format"
            
            return SchemaConflict(
                conflict_id=conflict_id,
                conflict_type=conflict_type,
                resource_ids=resource_ids,
                field_names=[field_name] * len(resource_ids),
                data_types=data_types,
                sample_values=[info.get("sample_values", [])[:3] for info in field_infos],
                confidence_score=0.8
            )
        
        return None
    
    async def _analyze_conflicts_with_ai(self, conflicts: List[SchemaConflict],
                                       synthesis_goal: str) -> Dict[str, Any]:
        """Use AI to analyze complex schema conflicts."""
        conflict_summary = []
        for conflict in conflicts:
            conflict_summary.append({
                "field_name": conflict.field_names[0],
                "conflict_type": conflict.conflict_type,
                "data_types": conflict.data_types,
                "sample_values": conflict.sample_values
            })
        
        analysis_prompt = f"""
Analyze schema conflicts for cross-resource data synthesis.

Synthesis Goal: {synthesis_goal}

Conflicts Detected:
{json.dumps(conflict_summary, indent=2)}

For each conflict, provide:
1. Resolution strategy (cast, standardize, rename, merge)
2. Recommended target data type
3. Transformation logic (SQL-like expression)
4. Potential data loss assessment
5. Confidence score (0.0 to 1.0)

Respond in JSON format with conflict analysis.
"""
        
        try:
            ai_response = await self.execute(analysis_prompt)
            # Parse AI response (simplified implementation)
            return {"ai_analysis": ai_response}
        except Exception as e:
            logger.warning(f"AI conflict analysis failed: {e}")
            return {"ai_analysis": "AI analysis unavailable"}
    
    def _enhance_conflicts_with_ai_analysis(self, conflicts: List[SchemaConflict],
                                          ai_analysis: Dict[str, Any]) -> List[SchemaConflict]:
        """Enhance conflicts with AI analysis results."""
        # This is a simplified implementation
        # In practice, would parse AI response and update conflict resolution strategies
        
        for conflict in conflicts:
            if not conflict.resolution_strategy:
                # Apply default resolution strategies
                if conflict.conflict_type == "data_type":
                    conflict.resolution_strategy = "cast_to_string"
                    conflict.resolution_logic = f"CAST({conflict.field_names[0]} AS VARCHAR)"
                elif conflict.conflict_type == "semantic":
                    conflict.resolution_strategy = "standardize_format"
                    conflict.resolution_logic = f"STANDARDIZE({conflict.field_names[0]})"
                else:
                    conflict.resolution_strategy = "keep_first"
                    conflict.resolution_logic = f"COALESCE({conflict.field_names[0]})"
                
                conflict.confidence_score = 0.6  # Default confidence
        
        return conflicts
    
    async def _resolve_conflicts_and_harmonize(self, conflicts: List[SchemaConflict],
                                             schema_analysis: Dict[str, Dict[str, Any]]) -> Tuple[List[SchemaConflict], List[DataTypeHarmonization]]:
        """Resolve conflicts and create harmonization plan."""
        resolved_conflicts = []
        harmonizations = []
        
        for conflict in conflicts:
            # Create resolution strategy
            if not conflict.resolution_strategy:
                conflict.resolution_strategy = self._determine_resolution_strategy(conflict)
                conflict.resolution_logic = self._generate_resolution_logic(conflict)
            
            resolved_conflicts.append(conflict)
            
            # Create harmonization if needed
            if conflict.conflict_type == "data_type":
                harmonization = DataTypeHarmonization(
                    harmonization_id=str(uuid.uuid4()),
                    source_types=conflict.data_types,
                    target_type=self._determine_target_type(conflict.data_types),
                    conversion_logic=conflict.resolution_logic,
                    validation_rules=[f"CHECK ({conflict.field_names[0]} IS NOT NULL)"],
                    precision_loss=self._assess_precision_loss(conflict.data_types)
                )
                harmonizations.append(harmonization)
        
        return resolved_conflicts, harmonizations
    
    def _determine_resolution_strategy(self, conflict: SchemaConflict) -> str:
        """Determine the best resolution strategy for a conflict."""
        if conflict.conflict_type == "data_type":
            # Check if all types are numeric
            numeric_types = {"integer", "float", "numeric", "decimal"}
            if all(dt in numeric_types for dt in conflict.data_types):
                return "cast_to_numeric"
            else:
                return "cast_to_string"
        elif conflict.conflict_type == "semantic":
            return "standardize_format"
        else:
            return "keep_first_non_null"
    
    def _generate_resolution_logic(self, conflict: SchemaConflict) -> str:
        """Generate SQL-like resolution logic for a conflict."""
        field_name = conflict.field_names[0]
        
        if conflict.resolution_strategy == "cast_to_numeric":
            return f"CAST({field_name} AS DECIMAL(18,6))"
        elif conflict.resolution_strategy == "cast_to_string":
            return f"CAST({field_name} AS VARCHAR(255))"
        elif conflict.resolution_strategy == "standardize_format":
            return f"UPPER(TRIM({field_name}))"
        else:
            return f"COALESCE({field_name})"
    
    def _determine_target_type(self, source_types: List[str]) -> str:
        """Determine the best target type for harmonization."""
        # Prioritize more general types
        if "string" in source_types or "varchar" in source_types:
            return "varchar"
        elif any(t in ["decimal", "numeric", "float"] for t in source_types):
            return "decimal"
        elif "integer" in source_types:
            return "integer"
        else:
            return "varchar"  # Default fallback
    
    def _assess_precision_loss(self, source_types: List[str]) -> bool:
        """Assess if precision loss might occur during harmonization."""
        numeric_types = {"integer", "float", "numeric", "decimal"}
        has_numeric = any(t in numeric_types for t in source_types)
        has_string = any(t not in numeric_types for t in source_types)
        
        # Precision loss if converting from numeric to string or vice versa
        return has_numeric and has_string
    
    async def _determine_synthesis_strategy(self, resources: List[ResourceMetadata],
                                          schema_analysis: Dict[str, Dict[str, Any]],
                                          synthesis_goal: str,
                                          desired_fields: Optional[Dict[str, str]]) -> SynthesisStrategy:
        """Determine the optimal synthesis strategy."""
        # Analyze for potential join keys
        potential_joins = await self._analyze_join_potential(schema_analysis)
        
        # Check if resources have similar schemas for union
        schema_similarity = self._calculate_schema_similarity(schema_analysis)
        
        # Use AI to determine strategy
        strategy_prompt = f"""
Determine the best synthesis strategy for cross-resource data combination.

Synthesis Goal: {synthesis_goal}
Number of Resources: {len(resources)}
Potential Join Keys: {len(potential_joins)}
Schema Similarity Score: {schema_similarity:.2f}

Resource Types: {[r.resource_type.value for r in resources]}
Desired Fields: {desired_fields or "Not specified"}

Available Strategies:
1. JOIN_BASED: Combine resources using common keys
2. UNION_BASED: Stack similar resources vertically
3. AGGREGATION_BASED: Aggregate data across resources
4. TRANSFORMATION_BASED: Transform and combine with complex logic
5. CORRELATION_BASED: Find correlations and relationships

Recommend the best strategy and explain why.
"""
        
        try:
            ai_response = await self.execute(strategy_prompt)
            
            # Parse AI response to extract strategy (simplified)
            if "join" in ai_response.lower() and potential_joins:
                return SynthesisStrategy.JOIN_BASED
            elif "union" in ai_response.lower() and schema_similarity > 0.7:
                return SynthesisStrategy.UNION_BASED
            elif "aggregat" in ai_response.lower():
                return SynthesisStrategy.AGGREGATION_BASED
            elif "correlat" in ai_response.lower():
                return SynthesisStrategy.CORRELATION_BASED
            else:
                return SynthesisStrategy.TRANSFORMATION_BASED
                
        except Exception as e:
            logger.warning(f"AI strategy determination failed: {e}")
            
            # Fallback logic
            if potential_joins and len(resources) <= 3:
                return SynthesisStrategy.JOIN_BASED
            elif schema_similarity > 0.7:
                return SynthesisStrategy.UNION_BASED
            else:
                return SynthesisStrategy.TRANSFORMATION_BASED
    
    async def _analyze_join_potential(self, schema_analysis: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze potential for joins between resources."""
        potential_joins = []
        resource_ids = list(schema_analysis.keys())
        
        # Compare each pair of resources
        for i in range(len(resource_ids)):
            for j in range(i + 1, len(resource_ids)):
                resource1_id = resource_ids[i]
                resource2_id = resource_ids[j]
                
                schema1 = schema_analysis[resource1_id]
                schema2 = schema_analysis[resource2_id]
                
                # Find potential join fields
                for field1_name, field1_info in schema1.get("fields", {}).items():
                    for field2_name, field2_info in schema2.get("fields", {}).items():
                        join_score = self._calculate_join_compatibility(
                            field1_name, field1_info, field2_name, field2_info
                        )
                        
                        if join_score > 0.5:  # Threshold for potential join
                            potential_joins.append({
                                "resource1": resource1_id,
                                "resource2": resource2_id,
                                "field1": field1_name,
                                "field2": field2_name,
                                "score": join_score
                            })
        
        return potential_joins
    
    def _calculate_join_compatibility(self, field1_name: str, field1_info: Dict[str, Any],
                                    field2_name: str, field2_info: Dict[str, Any]) -> float:
        """Calculate compatibility score for potential join fields."""
        score = 0.0
        
        # Name similarity
        if field1_name.lower() == field2_name.lower():
            score += 0.4
        elif any(word in field1_name.lower() for word in field2_name.lower().split('_')):
            score += 0.2
        
        # Semantic type compatibility
        if field1_info.get("semantic_type") == field2_info.get("semantic_type"):
            score += 0.3
        
        # Data type compatibility
        if field1_info.get("type") == field2_info.get("type"):
            score += 0.2
        
        # Identifier patterns (likely join keys)
        if any(keyword in field1_name.lower() for keyword in ["id", "key", "uuid"]):
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_schema_similarity(self, schema_analysis: Dict[str, Dict[str, Any]]) -> float:
        """Calculate overall schema similarity across resources."""
        if len(schema_analysis) < 2:
            return 0.0
        
        all_fields = set()
        resource_fields = {}
        
        for resource_id, schema in schema_analysis.items():
            fields = set(schema.get("fields", {}).keys())
            resource_fields[resource_id] = fields
            all_fields.update(fields)
        
        if not all_fields:
            return 0.0
        
        # Calculate Jaccard similarity between all pairs
        similarities = []
        resource_ids = list(resource_fields.keys())
        
        for i in range(len(resource_ids)):
            for j in range(i + 1, len(resource_ids)):
                fields1 = resource_fields[resource_ids[i]]
                fields2 = resource_fields[resource_ids[j]]
                
                intersection = fields1 & fields2
                union = fields1 | fields2
                
                if union:
                    similarity = len(intersection) / len(union)
                    similarities.append(similarity)
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    async def _generate_join_conditions(self, resources: List[ResourceMetadata],
                                      schema_analysis: Dict[str, Dict[str, Any]]) -> List[JoinCondition]:
        """Generate optimal join conditions between resources."""
        join_conditions = []
        potential_joins = await self._analyze_join_potential(schema_analysis)
        
        # Sort by join score and select best joins
        potential_joins.sort(key=lambda x: x["score"], reverse=True)
        
        for join_info in potential_joins[:5]:  # Limit to top 5 joins
            join_condition = JoinCondition(
                left_resource_id=join_info["resource1"],
                right_resource_id=join_info["resource2"],
                left_field=join_info["field1"],
                right_field=join_info["field2"],
                join_type=JoinStrategy.INNER_JOIN,  # Default to inner join
                confidence_score=join_info["score"],
                data_type_compatibility=True,  # Simplified assumption
                transformation_required=False
            )
            
            join_conditions.append(join_condition)
        
        return join_conditions
    
    async def _create_unified_view(self, synthesis_id: str, resources: List[ResourceMetadata],
                                 schema_analysis: Dict[str, Dict[str, Any]],
                                 synthesis_strategy: SynthesisStrategy,
                                 join_conditions: List[JoinCondition],
                                 desired_fields: Optional[Dict[str, str]],
                                 resolved_conflicts: List[SchemaConflict],
                                 harmonizations: List[DataTypeHarmonization]) -> UnifiedView:
        """Create unified view specification."""
        
        # Generate unified schema
        unified_schema = self._generate_unified_schema(
            schema_analysis, desired_fields, resolved_conflicts, harmonizations
        )
        
        # Create field mappings
        field_mappings = self._create_field_mappings(schema_analysis, unified_schema)
        
        # Generate lineage tracking
        lineage_tracking = self._generate_lineage_tracking(field_mappings, resources)
        
        # Estimate row count
        estimated_row_count = self._estimate_unified_row_count(
            resources, synthesis_strategy, join_conditions
        )
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(
            schema_analysis, resolved_conflicts, harmonizations
        )
        
        # Assess performance impact
        performance_impact = self._assess_performance_impact(
            resources, synthesis_strategy, estimated_row_count
        )
        
        return UnifiedView(
            view_id=f"unified_view_{synthesis_id}",
            view_name=f"Synthesized View {datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            source_resources=[r.resource_id for r in resources],
            unified_schema=unified_schema,
            synthesis_strategy=synthesis_strategy,
            join_conditions=join_conditions,
            field_mappings=field_mappings,
            data_transformations=[h.conversion_logic for h in harmonizations],
            lineage_tracking=lineage_tracking,
            estimated_row_count=estimated_row_count,
            quality_score=quality_score,
            performance_impact=performance_impact
        )
    
    def _generate_unified_schema(self, schema_analysis: Dict[str, Dict[str, Any]],
                               desired_fields: Optional[Dict[str, str]],
                               resolved_conflicts: List[SchemaConflict],
                               harmonizations: List[DataTypeHarmonization]) -> Dict[str, str]:
        """Generate unified schema for the synthesized view."""
        unified_schema = {}
        
        # Start with desired fields if specified
        if desired_fields:
            for field_name, field_desc in desired_fields.items():
                unified_schema[field_name] = "varchar"  # Default type
        
        # Add all unique fields from source schemas
        all_fields = set()
        for resource_id, schema in schema_analysis.items():
            for field_name, field_info in schema.get("fields", {}).items():
                all_fields.add(field_name)
        
        # Apply harmonizations to determine final types
        harmonization_map = {h.harmonization_id: h.target_type for h in harmonizations}
        
        for field_name in all_fields:
            if field_name not in unified_schema:
                # Find the most common type across resources
                field_types = []
                for resource_id, schema in schema_analysis.items():
                    if field_name in schema.get("fields", {}):
                        field_types.append(schema["fields"][field_name]["type"])
                
                if field_types:
                    # Use most common type or apply harmonization
                    most_common_type = max(set(field_types), key=field_types.count)
                    unified_schema[field_name] = most_common_type
        
        return unified_schema
    
    def _create_field_mappings(self, schema_analysis: Dict[str, Dict[str, Any]],
                             unified_schema: Dict[str, str]) -> Dict[str, Dict[str, str]]:
        """Create field mappings from source resources to unified schema."""
        field_mappings = {}
        
        for unified_field in unified_schema.keys():
            field_mappings[unified_field] = {}
            
            for resource_id, schema in schema_analysis.items():
                if unified_field in schema.get("fields", {}):
                    field_mappings[unified_field][resource_id] = unified_field
        
        return field_mappings
    
    def _generate_lineage_tracking(self, field_mappings: Dict[str, Dict[str, str]],
                                 resources: List[ResourceMetadata]) -> Dict[str, List[str]]:
        """Generate complete lineage tracking for all fields."""
        lineage_tracking = {}
        
        for unified_field, resource_mappings in field_mappings.items():
            lineage = []
            for resource_id, source_field in resource_mappings.items():
                # Find resource filename for better lineage description
                resource_name = next(
                    (r.original_filename for r in resources if r.resource_id == resource_id),
                    resource_id
                )
                lineage.append(f"{resource_name}.{source_field}")
            
            lineage_tracking[unified_field] = lineage
        
        return lineage_tracking
    
    def _estimate_unified_row_count(self, resources: List[ResourceMetadata],
                                  synthesis_strategy: SynthesisStrategy,
                                  join_conditions: List[JoinCondition]) -> int:
        """Estimate row count for unified view."""
        if synthesis_strategy == SynthesisStrategy.UNION_BASED:
            # Sum of all resource row counts
            return sum(r.row_count or 0 for r in resources)
        
        elif synthesis_strategy == SynthesisStrategy.JOIN_BASED:
            # Estimate based on join selectivity (simplified)
            if not resources:
                return 0
            
            base_count = max(r.row_count or 0 for r in resources)
            # Assume 70% join selectivity
            return int(base_count * 0.7)
        
        else:
            # Conservative estimate for other strategies
            return max(r.row_count or 0 for r in resources)
    
    def _calculate_quality_score(self, schema_analysis: Dict[str, Dict[str, Any]],
                               resolved_conflicts: List[SchemaConflict],
                               harmonizations: List[DataTypeHarmonization]) -> float:
        """Calculate overall quality score for the synthesis."""
        base_score = 1.0
        
        # Penalize for conflicts
        conflict_penalty = len(resolved_conflicts) * 0.1
        base_score -= min(conflict_penalty, 0.5)
        
        # Penalize for harmonizations with precision loss
        precision_loss_penalty = sum(0.1 for h in harmonizations if h.precision_loss)
        base_score -= min(precision_loss_penalty, 0.3)
        
        # Reward for schema completeness
        total_fields = sum(len(schema.get("fields", {})) for schema in schema_analysis.values())
        if total_fields > 0:
            completeness_bonus = min(total_fields / 50, 0.2)  # Max 0.2 bonus
            base_score += completeness_bonus
        
        return max(0.0, min(1.0, base_score))
    
    def _assess_performance_impact(self, resources: List[ResourceMetadata],
                                 synthesis_strategy: SynthesisStrategy,
                                 estimated_row_count: int) -> str:
        """Assess performance impact of the synthesis."""
        total_size_mb = sum(r.file_size_bytes for r in resources) / (1024 * 1024)
        
        if synthesis_strategy == SynthesisStrategy.JOIN_BASED and len(resources) > 3:
            return "high"
        elif total_size_mb > 100 or estimated_row_count > 100000:
            return "medium"
        else:
            return "low"
    
    async def _generate_execution_plan(self, unified_view: UnifiedView,
                                     resolved_conflicts: List[SchemaConflict],
                                     harmonizations: List[DataTypeHarmonization]) -> List[str]:
        """Generate step-by-step execution plan."""
        plan = []
        
        # Step 1: Data preparation
        plan.append("1. Prepare source data and validate access permissions")
        
        # Step 2: Apply harmonizations
        if harmonizations:
            plan.append(f"2. Apply {len(harmonizations)} data type harmonizations")
            for i, harm in enumerate(harmonizations):
                plan.append(f"   2.{i+1}. {harm.conversion_logic}")
        
        # Step 3: Resolve conflicts
        if resolved_conflicts:
            plan.append(f"3. Resolve {len(resolved_conflicts)} schema conflicts")
            for i, conflict in enumerate(resolved_conflicts):
                plan.append(f"   3.{i+1}. {conflict.resolution_strategy}: {conflict.resolution_logic}")
        
        # Step 4: Execute synthesis strategy
        if unified_view.synthesis_strategy == SynthesisStrategy.JOIN_BASED:
            plan.append("4. Execute join-based synthesis")
            for i, join in enumerate(unified_view.join_conditions):
                plan.append(f"   4.{i+1}. {join.join_type.value} on {join.left_field} = {join.right_field}")
        
        elif unified_view.synthesis_strategy == SynthesisStrategy.UNION_BASED:
            plan.append("4. Execute union-based synthesis")
            plan.append("   4.1. Align schemas and stack data vertically")
        
        else:
            plan.append(f"4. Execute {unified_view.synthesis_strategy.value} synthesis")
        
        # Step 5: Generate unified view
        plan.append("5. Generate unified view with lineage tracking")
        plan.append("6. Validate data quality and completeness")
        
        return plan
    
    async def _assess_synthesis_quality(self, unified_view: UnifiedView,
                                      resources: List[ResourceMetadata],
                                      schema_analysis: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Assess data quality of the synthesis."""
        return {
            "overall_score": unified_view.quality_score,
            "completeness": {
                "source_resources": len(resources),
                "unified_fields": len(unified_view.unified_schema),
                "field_coverage": len(unified_view.field_mappings) / len(unified_view.unified_schema) if unified_view.unified_schema else 0
            },
            "consistency": {
                "schema_conflicts_resolved": len([c for c in [] if c.resolution_strategy]),
                "data_type_harmonizations": len(unified_view.data_transformations)
            },
            "performance": {
                "estimated_row_count": unified_view.estimated_row_count,
                "performance_impact": unified_view.performance_impact,
                "join_complexity": len(unified_view.join_conditions)
            }
        }
    
    async def _generate_recommendations_and_warnings(self, unified_view: UnifiedView,
                                                   conflicts: List[SchemaConflict],
                                                   harmonizations: List[DataTypeHarmonization],
                                                   quality_assessment: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Generate recommendations and warnings for the synthesis."""
        recommendations = []
        warnings = []
        
        # Quality-based recommendations
        if unified_view.quality_score < 0.7:
            recommendations.append("Consider reviewing and cleaning source data to improve synthesis quality")
        
        if len(conflicts) > 5:
            recommendations.append("High number of schema conflicts detected - consider standardizing data formats")
        
        if unified_view.performance_impact == "high":
            recommendations.append("Consider implementing data partitioning or indexing for better performance")
        
        # Harmonization warnings
        precision_loss_count = sum(1 for h in harmonizations if h.precision_loss)
        if precision_loss_count > 0:
            warnings.append(f"Data precision loss may occur in {precision_loss_count} field harmonizations")
        
        # Join warnings
        if len(unified_view.join_conditions) > 3:
            warnings.append("Complex join operations may impact query performance")
        
        # Data volume warnings
        if unified_view.estimated_row_count > 1000000:
            warnings.append("Large result set expected - consider using pagination or filtering")
        
        # Default recommendations
        if not recommendations:
            recommendations.append("Synthesis plan looks good - ready for execution")
        
        return recommendations, warnings
    
    def _create_error_result(self, synthesis_id: str, error_message: str, 
                           execution_time: float) -> SynthesisResult:
        """Create error result for failed synthesis."""
        return SynthesisResult(
            synthesis_id=synthesis_id,
            unified_view=UnifiedView(
                view_id=f"error_view_{synthesis_id}",
                view_name="Error View",
                source_resources=[],
                unified_schema={},
                synthesis_strategy=SynthesisStrategy.TRANSFORMATION_BASED,
                join_conditions=[],
                field_mappings={},
                data_transformations=[],
                lineage_tracking={},
                estimated_row_count=0,
                quality_score=0.0,
                performance_impact="low"
            ),
            conflicts_resolved=[],
            harmonizations_applied=[],
            execution_plan=[f"Error: {error_message}"],
            estimated_execution_time_ms=execution_time,
            data_quality_assessment={"error": error_message},
            recommendations=[],
            warnings=[error_message]
        )
    
    async def get_synthesis_status(self, synthesis_id: str) -> Dict[str, Any]:
        """Get status of a synthesis operation."""
        # Check cache for synthesis result
        for cached_result in self.synthesis_cache.values():
            if cached_result.synthesis_id == synthesis_id:
                return {
                    "synthesis_id": synthesis_id,
                    "status": "completed",
                    "quality_score": cached_result.unified_view.quality_score,
                    "estimated_execution_time_ms": cached_result.estimated_execution_time_ms,
                    "conflicts_resolved": len(cached_result.conflicts_resolved),
                    "harmonizations_applied": len(cached_result.harmonizations_applied)
                }
        
        return {
            "synthesis_id": synthesis_id,
            "status": "not_found",
            "error": "Synthesis not found in cache"
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the Cross-Resource Synthesis Agent."""
        try:
            self.initialize()
            
            # Test basic functionality
            test_response = await self.execute("Analyze cross-resource synthesis: join customer data with order data")
            
            return {
                "status": "healthy",
                "agent_info": self.get_agent_info(),
                "cache_stats": {
                    "synthesis_cache_size": len(self.synthesis_cache),
                    "schema_cache_size": len(self.schema_cache),
                    "join_analysis_cache_size": len(self.join_analysis_cache)
                },
                "test_response_length": len(test_response)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "agent_info": self.get_agent_info()
            }
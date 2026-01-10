"""
Query Planning Agent for Intelligent Data Analysis.

This AI agent specializes in optimal query execution planning, cost-based optimization,
streaming and pagination strategies for large data, parallel execution planning,
and resource allocation and management.
"""

import asyncio
import json
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from .base import BaseAgent, AgentConfig
from .logging import get_activity_logger
from ..core.models import ResourceMetadata, ResourceType, DataType, AccessLevel
from ..storage.metadata_registry import MetadataRegistry
from ..storage.storage_router import StorageRouter
from ..storage.database_managers import DatabaseManagers
from ..config import Config, get_config
from ..logger import get_logger

logger = get_logger(__name__)


class QueryComplexity(Enum):
    """Query complexity levels for optimization."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ExecutionStrategy(Enum):
    """Query execution strategies."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    STREAMING = "streaming"
    BATCH = "batch"
    HYBRID = "hybrid"


class OptimizationTechnique(Enum):
    """Query optimization techniques."""
    INDEX_SCAN = "index_scan"
    HASH_JOIN = "hash_join"
    MERGE_JOIN = "merge_join"
    NESTED_LOOP = "nested_loop"
    PARTITION_PRUNING = "partition_pruning"
    PREDICATE_PUSHDOWN = "predicate_pushdown"
    COLUMN_PRUNING = "column_pruning"
    AGGREGATION_PUSHDOWN = "aggregation_pushdown"


@dataclass
class ResourceRequirements:
    """Resource requirements for query execution."""
    estimated_memory_mb: float
    estimated_cpu_cores: int
    estimated_io_operations: int
    estimated_network_mb: float
    max_concurrent_connections: int
    temporary_storage_mb: float


@dataclass
class ExecutionStep:
    """Individual step in query execution plan."""
    step_id: str
    step_type: str  # discovery, extraction, calculation, synthesis, aggregation
    operation: str
    input_dependencies: List[str]
    output_schema: Dict[str, str]
    estimated_time_ms: float
    estimated_memory_mb: float
    parallelizable: bool
    optimization_techniques: List[OptimizationTechnique]
    streaming_capable: bool
    batch_size: Optional[int] = None


@dataclass
class QueryPlan:
    """AI-generated query execution plan."""
    plan_id: str
    original_query: str
    query_type: str
    execution_steps: List[ExecutionStep]
    execution_strategy: ExecutionStrategy
    estimated_cost: float
    estimated_time_ms: float
    estimated_memory_mb: float
    resource_requirements: ResourceRequirements
    optimization_notes: List[str]
    fallback_plans: List['QueryPlan']
    streaming_config: Optional[Dict[str, Any]] = None
    pagination_config: Optional[Dict[str, Any]] = None
    parallel_config: Optional[Dict[str, Any]] = None


@dataclass
class StreamingConfig:
    """Configuration for streaming query execution."""
    chunk_size: int
    buffer_size_mb: float
    max_concurrent_streams: int
    backpressure_threshold: float
    timeout_seconds: int


@dataclass
class PaginationConfig:
    """Configuration for paginated query execution."""
    page_size: int
    max_pages: int
    cursor_field: str
    sort_order: str  # "asc" or "desc"
    prefetch_pages: int


@dataclass
class ParallelConfig:
    """Configuration for parallel query execution."""
    max_workers: int
    partition_strategy: str  # "hash", "range", "round_robin"
    partition_field: Optional[str]
    merge_strategy: str  # "union", "join", "aggregate"
    coordination_timeout_seconds: int


@dataclass
class ExecutionMetrics:
    """Metrics from query execution."""
    actual_time_ms: float
    actual_memory_mb: float
    rows_processed: int
    bytes_processed: int
    cache_hits: int
    cache_misses: int
    optimization_effectiveness: float
    resource_utilization: Dict[str, float]


class QueryPlanningAgent(BaseAgent):
    """
    AI Agent for Query Planning and Optimization.
    
    This agent specializes in:
    - Optimal query execution planning
    - Cost-based query optimization
    - Streaming and pagination strategies for large data
    - Parallel execution planning
    - Resource allocation and management system
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the Query Planning Agent."""
        
        system_prompt = """You are an expert AI Query Planning Agent specializing in optimal query execution planning and resource management.

Your capabilities:
1. Analyze queries to determine optimal execution strategies
2. Create cost-based execution plans with resource estimates
3. Design streaming and pagination strategies for large datasets
4. Plan parallel execution with optimal resource allocation
5. Optimize queries using various techniques (indexing, joins, pushdowns)
6. Manage resource allocation and prevent system overload
7. Create fallback plans for error recovery

Query Analysis Framework:
- Assess query complexity based on operations, data size, and joins
- Estimate resource requirements (CPU, memory, I/O, network)
- Identify optimization opportunities (predicate pushdown, column pruning, etc.)
- Determine optimal execution strategy (sequential, parallel, streaming, batch)
- Plan resource allocation to prevent contention

Optimization Techniques:
- Index usage optimization
- Join order optimization
- Predicate and aggregation pushdown
- Column pruning and projection optimization
- Partition pruning for large datasets
- Caching strategies for repeated operations

Streaming and Pagination:
- Design streaming for memory-efficient processing
- Configure pagination for large result sets
- Implement backpressure handling
- Optimize chunk sizes based on data characteristics

Parallel Execution:
- Partition data optimally for parallel processing
- Coordinate parallel workers efficiently
- Merge results from parallel streams
- Handle failures and load balancing

Always provide:
- Detailed execution plans with time and resource estimates
- Multiple optimization alternatives
- Fallback strategies for error scenarios
- Resource allocation recommendations
- Performance monitoring suggestions"""

        agent_config = AgentConfig(
            name="query_planning_agent",
            model_name=config.openrouter.default_model if config else "anthropic/claude-3.5-sonnet",
            temperature=0.1,  # Very low temperature for consistent planning
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
        self.plan_cache: Dict[str, QueryPlan] = {}
        self.resource_stats_cache: Dict[str, Dict[str, Any]] = {}
        self.optimization_history: List[Dict[str, Any]] = []
        
        # Resource management
        self.active_executions: Dict[str, Dict[str, Any]] = {}
        self.resource_pool = {
            "max_memory_mb": 8192,  # 8GB default
            "max_cpu_cores": 8,
            "max_concurrent_queries": 10,
            "max_io_operations": 1000
        }
        
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize the agent and dependencies."""
        if not self._initialized:
            self.metadata_registry.initialize()
            self.storage_router.initialize()
            self.db_managers.initialize_all()
            self._initialized = True
            logger.info("Query Planning Agent initialized")
    
    async def create_execution_plan(self, user_id: str, client_id: str, 
                                  query: str, query_type: str = "analytical",
                                  desired_fields: Optional[Dict[str, str]] = None,
                                  resource_constraints: Optional[Dict[str, Any]] = None,
                                  access_level: AccessLevel = AccessLevel.USER) -> QueryPlan:
        """
        Create optimal execution plan for a query.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            query: Query to plan
            query_type: Type of query (analytical, aggregation, search, etc.)
            desired_fields: Optional desired fields specification
            resource_constraints: Optional resource constraints
            access_level: User access level
            
        Returns:
            Optimized query execution plan
        """
        start_time = time.time()
        plan_id = f"plan_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        
        try:
            self.initialize()
            
            logger.info(f"Creating execution plan for user {user_id}: {query}")
            
            # Log planning activity
            self.activity_logger.log_agent_query(
                self.agent_config.name, user_id, client_id,
                f"create_execution_plan: {query_type}", None
            )
            
            # Step 1: Analyze query complexity and requirements
            complexity_analysis = await self._analyze_query_complexity(
                query, query_type, user_id, client_id
            )
            
            # Step 2: Discover relevant resources
            relevant_resources = await self._discover_relevant_resources(
                user_id, client_id, query, desired_fields
            )
            
            # Step 3: Estimate resource requirements
            resource_requirements = await self._estimate_resource_requirements(
                complexity_analysis, relevant_resources, resource_constraints
            )
            
            # Step 4: Generate execution steps
            execution_steps = await self._generate_execution_steps(
                query, query_type, complexity_analysis, relevant_resources, desired_fields
            )
            
            # Step 5: Determine optimal execution strategy
            execution_strategy = self._determine_execution_strategy(
                complexity_analysis, resource_requirements, len(relevant_resources)
            )
            
            # Step 6: Apply optimizations
            optimized_steps = await self._apply_optimizations(
                execution_steps, relevant_resources, complexity_analysis
            )
            
            # Step 7: Configure streaming/pagination if needed
            streaming_config, pagination_config = self._configure_streaming_pagination(
                complexity_analysis, resource_requirements, execution_strategy
            )
            
            # Step 8: Configure parallel execution if beneficial
            parallel_config = self._configure_parallel_execution(
                execution_strategy, resource_requirements, optimized_steps
            )
            
            # Step 9: Generate fallback plans
            fallback_plans = await self._generate_fallback_plans(
                query, query_type, complexity_analysis, relevant_resources
            )
            
            # Step 10: Calculate final estimates
            total_estimated_time = sum(step.estimated_time_ms for step in optimized_steps)
            total_estimated_memory = max(step.estimated_memory_mb for step in optimized_steps) if optimized_steps else 0
            estimated_cost = self._calculate_execution_cost(
                total_estimated_time, total_estimated_memory, resource_requirements
            )
            
            # Create the execution plan
            execution_plan = QueryPlan(
                plan_id=plan_id,
                original_query=query,
                query_type=query_type,
                execution_steps=optimized_steps,
                execution_strategy=execution_strategy,
                estimated_cost=estimated_cost,
                estimated_time_ms=total_estimated_time,
                estimated_memory_mb=total_estimated_memory,
                resource_requirements=resource_requirements,
                optimization_notes=self._generate_optimization_notes(optimized_steps, complexity_analysis),
                fallback_plans=fallback_plans,
                streaming_config=streaming_config,
                pagination_config=pagination_config,
                parallel_config=parallel_config
            )
            
            # Cache the plan
            cache_key = self._generate_plan_cache_key(query, query_type, user_id, client_id)
            self.plan_cache[cache_key] = execution_plan
            
            execution_time = (time.time() - start_time) * 1000
            
            # Log completion
            self.activity_logger.log_agent_response(
                self.agent_config.name, user_id, client_id,
                f"Execution plan created with {len(optimized_steps)} steps",
                execution_time, self.agent_config.model_name,
                None, None,
                {
                    "plan_id": plan_id,
                    "execution_strategy": execution_strategy.value,
                    "estimated_time_ms": total_estimated_time,
                    "complexity": complexity_analysis["complexity"].value
                }
            )
            
            logger.info(f"Execution plan created in {execution_time:.2f}ms")
            return execution_plan
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Execution plan creation failed: {str(e)}"
            logger.error(error_msg)
            
            # Log error
            self.activity_logger.log_agent_error(
                self.agent_config.name, user_id, client_id,
                error_msg, None
            )
            
            # Return minimal fallback plan
            return QueryPlan(
                plan_id=plan_id,
                original_query=query,
                query_type=query_type,
                execution_steps=[],
                execution_strategy=ExecutionStrategy.SEQUENTIAL,
                estimated_cost=0.0,
                estimated_time_ms=execution_time,
                estimated_memory_mb=0.0,
                resource_requirements=ResourceRequirements(
                    estimated_memory_mb=512,
                    estimated_cpu_cores=1,
                    estimated_io_operations=10,
                    estimated_network_mb=1,
                    max_concurrent_connections=1,
                    temporary_storage_mb=100
                ),
                optimization_notes=[f"Planning failed: {str(e)}"],
                fallback_plans=[]
            )
    
    async def _analyze_query_complexity(self, query: str, query_type: str, 
                                      user_id: str, client_id: str) -> Dict[str, Any]:
        """Analyze query complexity and characteristics."""
        
        # Build analysis prompt for AI
        analysis_prompt = f"""
Analyze the complexity and characteristics of this query:

Query: {query}
Query Type: {query_type}

Please analyze:
1. Query complexity level (low, medium, high, very_high)
2. Operations involved (aggregation, joins, filtering, sorting, etc.)
3. Expected data volume requirements
4. Computational intensity
5. Memory requirements
6. I/O patterns
7. Parallelization opportunities
8. Optimization opportunities

Provide analysis as JSON with keys: complexity, operations, data_volume, computational_intensity, memory_pattern, io_pattern, parallelizable, optimization_opportunities
"""
        
        try:
            ai_response = await self.execute(analysis_prompt)
            
            # Parse AI response
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                # Fallback analysis
                analysis = {
                    "complexity": "medium",
                    "operations": ["filtering", "aggregation"],
                    "data_volume": "medium",
                    "computational_intensity": "medium",
                    "memory_pattern": "sequential",
                    "io_pattern": "sequential_read",
                    "parallelizable": True,
                    "optimization_opportunities": ["predicate_pushdown", "column_pruning"]
                }
            
            # Convert complexity to enum
            complexity_map = {
                "low": QueryComplexity.LOW,
                "medium": QueryComplexity.MEDIUM,
                "high": QueryComplexity.HIGH,
                "very_high": QueryComplexity.VERY_HIGH
            }
            analysis["complexity"] = complexity_map.get(analysis.get("complexity", "medium"), QueryComplexity.MEDIUM)
            
            return analysis
            
        except Exception as e:
            logger.warning(f"AI complexity analysis failed, using heuristics: {e}")
            return self._heuristic_complexity_analysis(query, query_type)
    
    def _heuristic_complexity_analysis(self, query: str, query_type: str) -> Dict[str, Any]:
        """Fallback heuristic complexity analysis."""
        import re
        
        query_lower = query.lower()
        
        # Count complexity indicators
        complexity_score = 0
        operations = []
        
        # Aggregation operations
        if any(op in query_lower for op in ['sum', 'count', 'avg', 'max', 'min', 'group by']):
            complexity_score += 2
            operations.append("aggregation")
        
        # Join operations
        join_count = len(re.findall(r'\bjoin\b', query_lower))
        complexity_score += join_count * 3
        if join_count > 0:
            operations.append("joins")
        
        # Subqueries
        subquery_count = query_lower.count('select') - 1  # Subtract main query
        complexity_score += subquery_count * 2
        if subquery_count > 0:
            operations.append("subqueries")
        
        # Sorting
        if 'order by' in query_lower:
            complexity_score += 1
            operations.append("sorting")
        
        # Filtering
        if any(op in query_lower for op in ['where', 'having', 'filter']):
            complexity_score += 1
            operations.append("filtering")
        
        # Determine complexity level
        if complexity_score <= 2:
            complexity = QueryComplexity.LOW
        elif complexity_score <= 5:
            complexity = QueryComplexity.MEDIUM
        elif complexity_score <= 10:
            complexity = QueryComplexity.HIGH
        else:
            complexity = QueryComplexity.VERY_HIGH
        
        return {
            "complexity": complexity,
            "operations": operations,
            "data_volume": "medium",
            "computational_intensity": "medium" if complexity_score <= 5 else "high",
            "memory_pattern": "sequential",
            "io_pattern": "sequential_read",
            "parallelizable": complexity_score > 3,
            "optimization_opportunities": ["predicate_pushdown", "column_pruning"]
        }
    
    async def _discover_relevant_resources(self, user_id: str, client_id: str, 
                                         query: str, desired_fields: Optional[Dict[str, str]]) -> List[ResourceMetadata]:
        """Discover resources relevant to the query."""
        try:
            # Get all user resources
            all_resources = self.metadata_registry.list_resources(client_id, user_id)
            
            if not all_resources:
                return []
            
            # Score resources based on query relevance
            scored_resources = []
            
            for resource in all_resources:
                relevance_score = self._calculate_resource_relevance(resource, query, desired_fields)
                if relevance_score > 0.1:  # Minimum relevance threshold
                    scored_resources.append((resource, relevance_score))
            
            # Sort by relevance and return top resources
            scored_resources.sort(key=lambda x: x[1], reverse=True)
            return [resource for resource, score in scored_resources[:10]]  # Top 10 resources
            
        except Exception as e:
            logger.warning(f"Resource discovery failed: {e}")
            return []
    
    def _calculate_resource_relevance(self, resource: ResourceMetadata, query: str, 
                                    desired_fields: Optional[Dict[str, str]]) -> float:
        """Calculate relevance score for a resource."""
        import re
        
        score = 0.0
        query_words = set(re.findall(r'\w+', query.lower()))
        
        # Filename relevance
        filename_words = set(re.findall(r'\w+', resource.original_filename.lower()))
        if filename_words:
            common_words = query_words & filename_words
            score += len(common_words) / len(filename_words) * 0.3
        
        # Field relevance (for structured data)
        if desired_fields and resource.resource_type == ResourceType.STRUCTURED:
            try:
                schema_info = self.metadata_registry.get_schema_info(resource.resource_id)
                if schema_info:
                    schema_data = json.loads(schema_info.schema_json)
                    available_fields = set(schema_data.get("columns", {}).keys())
                    desired_field_names = set(desired_fields.keys())
                    
                    if available_fields:
                        field_overlap = len(desired_field_names & available_fields) / len(desired_field_names)
                        score += field_overlap * 0.5
            except Exception:
                pass
        
        # Recency boost
        days_old = (datetime.utcnow() - resource.created_at).days
        if days_old < 7:
            score += 0.1
        elif days_old < 30:
            score += 0.05
        
        # Size consideration (prefer non-empty resources)
        if resource.row_count and resource.row_count > 0:
            score += 0.1
        elif resource.chunk_count and resource.chunk_count > 0:
            score += 0.1
        
        return min(score, 1.0)
    
    async def _estimate_resource_requirements(self, complexity_analysis: Dict[str, Any],
                                            relevant_resources: List[ResourceMetadata],
                                            constraints: Optional[Dict[str, Any]]) -> ResourceRequirements:
        """Estimate resource requirements for query execution."""
        
        # Base requirements by complexity
        complexity = complexity_analysis["complexity"]
        
        if complexity == QueryComplexity.LOW:
            base_memory = 128
            base_cpu = 1
            base_io = 50
        elif complexity == QueryComplexity.MEDIUM:
            base_memory = 512
            base_cpu = 2
            base_io = 200
        elif complexity == QueryComplexity.HIGH:
            base_memory = 1024
            base_cpu = 4
            base_io = 500
        else:  # VERY_HIGH
            base_memory = 2048
            base_cpu = 8
            base_io = 1000
        
        # Adjust based on data volume
        total_data_size = sum(
            resource.file_size_bytes for resource in relevant_resources
        ) / (1024 * 1024)  # Convert to MB
        
        # Memory scaling based on data size
        memory_multiplier = 1.0
        if total_data_size > 100:  # > 100MB
            memory_multiplier = 1.5
        if total_data_size > 1000:  # > 1GB
            memory_multiplier = 2.0
        if total_data_size > 10000:  # > 10GB
            memory_multiplier = 3.0
        
        estimated_memory = base_memory * memory_multiplier
        
        # Adjust for operations
        operations = complexity_analysis.get("operations", [])
        if "joins" in operations:
            estimated_memory *= 1.5
            base_cpu += 1
        if "aggregation" in operations:
            estimated_memory *= 1.2
        if "sorting" in operations:
            estimated_memory *= 1.3
        
        # Network requirements (for distributed operations)
        estimated_network = min(total_data_size * 0.1, 1000)  # Max 1GB network
        
        # Temporary storage (for intermediate results)
        temp_storage = estimated_memory * 0.5
        
        # Apply constraints if provided
        if constraints:
            estimated_memory = min(estimated_memory, constraints.get("max_memory_mb", estimated_memory))
            base_cpu = min(base_cpu, constraints.get("max_cpu_cores", base_cpu))
        
        return ResourceRequirements(
            estimated_memory_mb=estimated_memory,
            estimated_cpu_cores=base_cpu,
            estimated_io_operations=base_io,
            estimated_network_mb=estimated_network,
            max_concurrent_connections=min(base_cpu * 2, 10),
            temporary_storage_mb=temp_storage
        )
    
    async def _generate_execution_steps(self, query: str, query_type: str,
                                      complexity_analysis: Dict[str, Any],
                                      relevant_resources: List[ResourceMetadata],
                                      desired_fields: Optional[Dict[str, str]]) -> List[ExecutionStep]:
        """Generate detailed execution steps for the query."""
        
        steps = []
        step_counter = 1
        
        # Step 1: Resource Discovery (if needed)
        if relevant_resources:
            steps.append(ExecutionStep(
                step_id=f"step_{step_counter}",
                step_type="discovery",
                operation="resource_discovery",
                input_dependencies=[],
                output_schema={"resources": "list", "metadata": "dict"},
                estimated_time_ms=100.0,
                estimated_memory_mb=50.0,
                parallelizable=False,
                optimization_techniques=[],
                streaming_capable=False
            ))
            step_counter += 1
        
        # Step 2: Data Loading/Access
        for i, resource in enumerate(relevant_resources[:5]):  # Limit to top 5 resources
            steps.append(ExecutionStep(
                step_id=f"step_{step_counter}",
                step_type="data_access",
                operation=f"load_{resource.resource_type.value}_data",
                input_dependencies=[f"step_{step_counter-1}"] if i == 0 else [],
                output_schema={"data": "table", "schema": "dict"},
                estimated_time_ms=self._estimate_data_load_time(resource),
                estimated_memory_mb=self._estimate_data_load_memory(resource),
                parallelizable=True,
                optimization_techniques=[OptimizationTechnique.COLUMN_PRUNING],
                streaming_capable=True,
                batch_size=1000 if resource.row_count and resource.row_count > 10000 else None
            ))
            step_counter += 1
        
        # Step 3: Field Extraction/Mapping (if needed)
        if desired_fields:
            steps.append(ExecutionStep(
                step_id=f"step_{step_counter}",
                step_type="extraction",
                operation="field_extraction_mapping",
                input_dependencies=[f"step_{i}" for i in range(2, step_counter)],
                output_schema={"mapped_fields": "dict", "derived_fields": "dict"},
                estimated_time_ms=200.0,
                estimated_memory_mb=100.0,
                parallelizable=True,
                optimization_techniques=[OptimizationTechnique.PREDICATE_PUSHDOWN],
                streaming_capable=False
            ))
            step_counter += 1
        
        # Step 4: Data Processing (based on operations)
        operations = complexity_analysis.get("operations", [])
        
        if "filtering" in operations:
            steps.append(ExecutionStep(
                step_id=f"step_{step_counter}",
                step_type="processing",
                operation="data_filtering",
                input_dependencies=[f"step_{step_counter-1}"],
                output_schema={"filtered_data": "table"},
                estimated_time_ms=self._estimate_operation_time("filtering", relevant_resources),
                estimated_memory_mb=self._estimate_operation_memory("filtering", relevant_resources),
                parallelizable=True,
                optimization_techniques=[OptimizationTechnique.PREDICATE_PUSHDOWN, OptimizationTechnique.PARTITION_PRUNING],
                streaming_capable=True,
                batch_size=5000
            ))
            step_counter += 1
        
        if "joins" in operations and len(relevant_resources) > 1:
            steps.append(ExecutionStep(
                step_id=f"step_{step_counter}",
                step_type="processing",
                operation="data_joining",
                input_dependencies=[f"step_{i}" for i in range(max(1, step_counter-3), step_counter)],
                output_schema={"joined_data": "table"},
                estimated_time_ms=self._estimate_operation_time("joins", relevant_resources),
                estimated_memory_mb=self._estimate_operation_memory("joins", relevant_resources),
                parallelizable=True,
                optimization_techniques=[OptimizationTechnique.HASH_JOIN, OptimizationTechnique.INDEX_SCAN],
                streaming_capable=False
            ))
            step_counter += 1
        
        if "aggregation" in operations:
            steps.append(ExecutionStep(
                step_id=f"step_{step_counter}",
                step_type="processing",
                operation="data_aggregation",
                input_dependencies=[f"step_{step_counter-1}"],
                output_schema={"aggregated_data": "table"},
                estimated_time_ms=self._estimate_operation_time("aggregation", relevant_resources),
                estimated_memory_mb=self._estimate_operation_memory("aggregation", relevant_resources),
                parallelizable=True,
                optimization_techniques=[OptimizationTechnique.AGGREGATION_PUSHDOWN],
                streaming_capable=True,
                batch_size=10000
            ))
            step_counter += 1
        
        if "sorting" in operations:
            steps.append(ExecutionStep(
                step_id=f"step_{step_counter}",
                step_type="processing",
                operation="data_sorting",
                input_dependencies=[f"step_{step_counter-1}"],
                output_schema={"sorted_data": "table"},
                estimated_time_ms=self._estimate_operation_time("sorting", relevant_resources),
                estimated_memory_mb=self._estimate_operation_memory("sorting", relevant_resources),
                parallelizable=True,
                optimization_techniques=[OptimizationTechnique.INDEX_SCAN],
                streaming_capable=False
            ))
            step_counter += 1
        
        # Step 5: Result Synthesis
        steps.append(ExecutionStep(
            step_id=f"step_{step_counter}",
            step_type="synthesis",
            operation="result_synthesis",
            input_dependencies=[f"step_{step_counter-1}"],
            output_schema={"results": "list", "insights": "list", "metadata": "dict"},
            estimated_time_ms=100.0,
            estimated_memory_mb=50.0,
            parallelizable=False,
            optimization_techniques=[],
            streaming_capable=True
        ))
        
        return steps
    
    def _estimate_data_load_time(self, resource: ResourceMetadata) -> float:
        """Estimate time to load data from a resource."""
        # Base time by resource type
        base_times = {
            ResourceType.STRUCTURED: 50.0,  # ms per MB
            ResourceType.JSON: 100.0,
            ResourceType.UNSTRUCTURED: 200.0
        }
        
        base_time = base_times.get(resource.resource_type, 100.0)
        size_mb = resource.file_size_bytes / (1024 * 1024)
        
        return base_time * max(size_mb, 0.1)  # Minimum 0.1 MB
    
    def _estimate_data_load_memory(self, resource: ResourceMetadata) -> float:
        """Estimate memory required to load data from a resource."""
        size_mb = resource.file_size_bytes / (1024 * 1024)
        
        # Memory multipliers by type
        multipliers = {
            ResourceType.STRUCTURED: 1.2,  # Slight overhead for parsing
            ResourceType.JSON: 2.0,        # Higher overhead for JSON parsing
            ResourceType.UNSTRUCTURED: 1.5  # Moderate overhead for text processing
        }
        
        multiplier = multipliers.get(resource.resource_type, 1.5)
        return max(size_mb * multiplier, 10.0)  # Minimum 10 MB
    
    def _estimate_operation_time(self, operation: str, resources: List[ResourceMetadata]) -> float:
        """Estimate time for a specific operation."""
        total_rows = sum(resource.row_count or 0 for resource in resources)
        total_size_mb = sum(resource.file_size_bytes for resource in resources) / (1024 * 1024)
        
        # Time estimates per operation (ms per 1000 rows or per MB)
        operation_times = {
            "filtering": 0.5,    # Fast operation
            "joins": 5.0,        # Expensive operation
            "aggregation": 2.0,  # Medium operation
            "sorting": 3.0       # Medium-expensive operation
        }
        
        base_time = operation_times.get(operation, 1.0)
        
        if total_rows > 0:
            return base_time * (total_rows / 1000)
        else:
            return base_time * total_size_mb
    
    def _estimate_operation_memory(self, operation: str, resources: List[ResourceMetadata]) -> float:
        """Estimate memory for a specific operation."""
        total_size_mb = sum(resource.file_size_bytes for resource in resources) / (1024 * 1024)
        
        # Memory multipliers per operation
        operation_multipliers = {
            "filtering": 1.1,    # Minimal overhead
            "joins": 2.5,        # High memory for hash tables
            "aggregation": 1.5,  # Moderate for grouping
            "sorting": 2.0       # High for sorting buffers
        }
        
        multiplier = operation_multipliers.get(operation, 1.2)
        return max(total_size_mb * multiplier, 50.0)  # Minimum 50 MB
    
    def _determine_execution_strategy(self, complexity_analysis: Dict[str, Any],
                                    resource_requirements: ResourceRequirements,
                                    resource_count: int) -> ExecutionStrategy:
        """Determine optimal execution strategy."""
        
        complexity = complexity_analysis["complexity"]
        estimated_memory = resource_requirements.estimated_memory_mb
        parallelizable = complexity_analysis.get("parallelizable", False)
        
        # High memory or very high complexity suggests streaming
        if estimated_memory > 4096 or complexity == QueryComplexity.VERY_HIGH:
            return ExecutionStrategy.STREAMING
        
        # Multiple resources and parallelizable suggests parallel
        if resource_count > 1 and parallelizable and complexity in [QueryComplexity.HIGH, QueryComplexity.VERY_HIGH]:
            return ExecutionStrategy.PARALLEL
        
        # Medium complexity with moderate resources suggests hybrid
        if complexity == QueryComplexity.MEDIUM and estimated_memory > 1024:
            return ExecutionStrategy.HYBRID
        
        # Large datasets suggest batch processing
        if estimated_memory > 2048:
            return ExecutionStrategy.BATCH
        
        # Default to sequential for simple queries
        return ExecutionStrategy.SEQUENTIAL
    
    async def _apply_optimizations(self, execution_steps: List[ExecutionStep],
                                 relevant_resources: List[ResourceMetadata],
                                 complexity_analysis: Dict[str, Any]) -> List[ExecutionStep]:
        """Apply optimizations to execution steps."""
        
        optimized_steps = []
        
        for step in execution_steps:
            optimized_step = step
            
            # Apply predicate pushdown for filtering operations
            if step.operation in ["data_filtering", "load_structured_data"]:
                if OptimizationTechnique.PREDICATE_PUSHDOWN not in step.optimization_techniques:
                    optimized_step.optimization_techniques.append(OptimizationTechnique.PREDICATE_PUSHDOWN)
                    optimized_step.estimated_time_ms *= 0.7  # 30% improvement
            
            # Apply column pruning for data loading
            if "load_" in step.operation:
                if OptimizationTechnique.COLUMN_PRUNING not in step.optimization_techniques:
                    optimized_step.optimization_techniques.append(OptimizationTechnique.COLUMN_PRUNING)
                    optimized_step.estimated_memory_mb *= 0.8  # 20% memory reduction
            
            # Optimize join operations
            if step.operation == "data_joining":
                # Choose optimal join algorithm based on data size
                total_size = sum(r.file_size_bytes for r in relevant_resources)
                if total_size > 100 * 1024 * 1024:  # > 100MB
                    optimized_step.optimization_techniques = [OptimizationTechnique.HASH_JOIN]
                else:
                    optimized_step.optimization_techniques = [OptimizationTechnique.NESTED_LOOP]
            
            # Enable streaming for large operations
            if step.estimated_memory_mb > 1000 and step.streaming_capable:
                optimized_step.batch_size = min(step.batch_size or 1000, 5000)
                optimized_step.estimated_memory_mb *= 0.6  # Streaming reduces memory
            
            optimized_steps.append(optimized_step)
        
        return optimized_steps
    
    def _configure_streaming_pagination(self, complexity_analysis: Dict[str, Any],
                                      resource_requirements: ResourceRequirements,
                                      execution_strategy: ExecutionStrategy) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Configure streaming and pagination settings."""
        
        streaming_config = None
        pagination_config = None
        
        # Configure streaming for high memory requirements or streaming strategy
        if (resource_requirements.estimated_memory_mb > 2048 or 
            execution_strategy in [ExecutionStrategy.STREAMING, ExecutionStrategy.HYBRID]):
            
            streaming_config = asdict(StreamingConfig(
                chunk_size=min(10000, max(1000, int(resource_requirements.estimated_memory_mb / 10))),
                buffer_size_mb=min(512, resource_requirements.estimated_memory_mb * 0.2),
                max_concurrent_streams=min(4, resource_requirements.estimated_cpu_cores),
                backpressure_threshold=0.8,
                timeout_seconds=300
            ))
        
        # Configure pagination for large result sets
        if complexity_analysis["complexity"] in [QueryComplexity.HIGH, QueryComplexity.VERY_HIGH]:
            pagination_config = asdict(PaginationConfig(
                page_size=min(1000, max(100, int(resource_requirements.estimated_memory_mb / 5))),
                max_pages=100,
                cursor_field="id",  # Default cursor field
                sort_order="asc",
                prefetch_pages=2
            ))
        
        return streaming_config, pagination_config
    
    def _configure_parallel_execution(self, execution_strategy: ExecutionStrategy,
                                    resource_requirements: ResourceRequirements,
                                    execution_steps: List[ExecutionStep]) -> Optional[Dict[str, Any]]:
        """Configure parallel execution settings."""
        
        if execution_strategy not in [ExecutionStrategy.PARALLEL, ExecutionStrategy.HYBRID]:
            return None
        
        # Count parallelizable steps
        parallelizable_steps = sum(1 for step in execution_steps if step.parallelizable)
        
        if parallelizable_steps < 2:
            return None
        
        return asdict(ParallelConfig(
            max_workers=min(resource_requirements.estimated_cpu_cores, 8),
            partition_strategy="hash",  # Default partitioning
            partition_field=None,  # Will be determined at runtime
            merge_strategy="union",  # Default merge strategy
            coordination_timeout_seconds=600
        ))
    
    async def _generate_fallback_plans(self, query: str, query_type: str,
                                     complexity_analysis: Dict[str, Any],
                                     relevant_resources: List[ResourceMetadata]) -> List[QueryPlan]:
        """Generate fallback execution plans."""
        
        fallback_plans = []
        
        try:
            # Fallback 1: Sequential execution with reduced resources
            if len(relevant_resources) > 1:
                limited_resources = relevant_resources[:2]  # Use only top 2 resources
                
                # Create simplified steps
                simple_steps = [
                    ExecutionStep(
                        step_id="fallback_1",
                        step_type="data_access",
                        operation="load_structured_data",
                        input_dependencies=[],
                        output_schema={"data": "table"},
                        estimated_time_ms=500.0,
                        estimated_memory_mb=256.0,
                        parallelizable=False,
                        optimization_techniques=[],
                        streaming_capable=True
                    ),
                    ExecutionStep(
                        step_id="fallback_2",
                        step_type="synthesis",
                        operation="simple_analysis",
                        input_dependencies=["fallback_1"],
                        output_schema={"results": "list"},
                        estimated_time_ms=200.0,
                        estimated_memory_mb=128.0,
                        parallelizable=False,
                        optimization_techniques=[],
                        streaming_capable=False
                    )
                ]
                
                fallback_plan = QueryPlan(
                    plan_id=f"fallback_{int(time.time())}_1",
                    original_query=query,
                    query_type=query_type,
                    execution_steps=simple_steps,
                    execution_strategy=ExecutionStrategy.SEQUENTIAL,
                    estimated_cost=50.0,
                    estimated_time_ms=700.0,
                    estimated_memory_mb=256.0,
                    resource_requirements=ResourceRequirements(
                        estimated_memory_mb=256,
                        estimated_cpu_cores=1,
                        estimated_io_operations=50,
                        estimated_network_mb=10,
                        max_concurrent_connections=1,
                        temporary_storage_mb=50
                    ),
                    optimization_notes=["Simplified fallback plan with reduced resources"],
                    fallback_plans=[]
                )
                
                fallback_plans.append(fallback_plan)
            
            # Fallback 2: Error recovery plan
            error_recovery_steps = [
                ExecutionStep(
                    step_id="error_recovery",
                    step_type="discovery",
                    operation="basic_resource_scan",
                    input_dependencies=[],
                    output_schema={"available_data": "list"},
                    estimated_time_ms=100.0,
                    estimated_memory_mb=64.0,
                    parallelizable=False,
                    optimization_techniques=[],
                    streaming_capable=False
                )
            ]
            
            error_recovery_plan = QueryPlan(
                plan_id=f"fallback_{int(time.time())}_error",
                original_query=query,
                query_type="error_recovery",
                execution_steps=error_recovery_steps,
                execution_strategy=ExecutionStrategy.SEQUENTIAL,
                estimated_cost=10.0,
                estimated_time_ms=100.0,
                estimated_memory_mb=64.0,
                resource_requirements=ResourceRequirements(
                    estimated_memory_mb=64,
                    estimated_cpu_cores=1,
                    estimated_io_operations=10,
                    estimated_network_mb=1,
                    max_concurrent_connections=1,
                    temporary_storage_mb=10
                ),
                optimization_notes=["Minimal error recovery plan"],
                fallback_plans=[]
            )
            
            fallback_plans.append(error_recovery_plan)
            
        except Exception as e:
            logger.warning(f"Fallback plan generation failed: {e}")
        
        return fallback_plans
    
    def _calculate_execution_cost(self, estimated_time_ms: float, estimated_memory_mb: float,
                                resource_requirements: ResourceRequirements) -> float:
        """Calculate execution cost based on resource usage."""
        
        # Cost factors (arbitrary units)
        time_cost = estimated_time_ms / 1000 * 0.1  # $0.1 per second
        memory_cost = estimated_memory_mb / 1024 * 0.05  # $0.05 per GB
        cpu_cost = resource_requirements.estimated_cpu_cores * 0.02  # $0.02 per core
        io_cost = resource_requirements.estimated_io_operations / 1000 * 0.01  # $0.01 per 1000 ops
        
        return time_cost + memory_cost + cpu_cost + io_cost
    
    def _generate_optimization_notes(self, execution_steps: List[ExecutionStep],
                                   complexity_analysis: Dict[str, Any]) -> List[str]:
        """Generate optimization notes for the execution plan."""
        
        notes = []
        
        # Count optimization techniques used
        all_techniques = []
        for step in execution_steps:
            all_techniques.extend(step.optimization_techniques)
        
        technique_counts = {}
        for technique in all_techniques:
            technique_counts[technique] = technique_counts.get(technique, 0) + 1
        
        if technique_counts:
            notes.append(f"Applied {len(technique_counts)} optimization techniques across {len(execution_steps)} steps")
        
        # Streaming optimizations
        streaming_steps = [step for step in execution_steps if step.streaming_capable and step.batch_size]
        if streaming_steps:
            notes.append(f"Enabled streaming for {len(streaming_steps)} steps to reduce memory usage")
        
        # Parallelization opportunities
        parallel_steps = [step for step in execution_steps if step.parallelizable]
        if parallel_steps:
            notes.append(f"Identified {len(parallel_steps)} steps suitable for parallel execution")
        
        # Complexity-based notes
        complexity = complexity_analysis["complexity"]
        if complexity == QueryComplexity.HIGH:
            notes.append("High complexity query - consider breaking into smaller operations")
        elif complexity == QueryComplexity.VERY_HIGH:
            notes.append("Very high complexity query - strongly recommend streaming and parallel execution")
        
        return notes
    
    def _generate_plan_cache_key(self, query: str, query_type: str, user_id: str, client_id: str) -> str:
        """Generate cache key for execution plan."""
        import hashlib
        
        key_data = f"{query}:{query_type}:{user_id}:{client_id}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def optimize_existing_plan(self, plan_id: str, execution_metrics: ExecutionMetrics) -> Optional[QueryPlan]:
        """
        Optimize an existing plan based on execution metrics.
        
        Args:
            plan_id: ID of the plan to optimize
            execution_metrics: Metrics from previous execution
            
        Returns:
            Optimized query plan or None if optimization not possible
        """
        try:
            # Find the original plan
            original_plan = None
            for cached_plan in self.plan_cache.values():
                if cached_plan.plan_id == plan_id:
                    original_plan = cached_plan
                    break
            
            if not original_plan:
                logger.warning(f"Original plan {plan_id} not found for optimization")
                return None
            
            # Analyze performance vs estimates
            time_ratio = execution_metrics.actual_time_ms / original_plan.estimated_time_ms
            memory_ratio = execution_metrics.actual_memory_mb / original_plan.estimated_memory_mb
            
            # Create optimized plan
            optimized_steps = []
            for step in original_plan.execution_steps:
                optimized_step = step
                
                # Adjust estimates based on actual performance
                optimized_step.estimated_time_ms *= time_ratio
                optimized_step.estimated_memory_mb *= memory_ratio
                
                # Apply additional optimizations based on metrics
                if execution_metrics.cache_hits > execution_metrics.cache_misses:
                    # Good cache performance - can be more aggressive
                    optimized_step.estimated_time_ms *= 0.9
                
                if execution_metrics.resource_utilization.get("cpu", 0) < 0.5:
                    # Low CPU utilization - can increase parallelism
                    optimized_step.parallelizable = True
                
                optimized_steps.append(optimized_step)
            
            # Create optimized plan
            optimized_plan = QueryPlan(
                plan_id=f"{plan_id}_optimized_{int(time.time())}",
                original_query=original_plan.original_query,
                query_type=original_plan.query_type,
                execution_steps=optimized_steps,
                execution_strategy=original_plan.execution_strategy,
                estimated_cost=original_plan.estimated_cost * 0.9,  # Assume 10% improvement
                estimated_time_ms=sum(step.estimated_time_ms for step in optimized_steps),
                estimated_memory_mb=max(step.estimated_memory_mb for step in optimized_steps),
                resource_requirements=original_plan.resource_requirements,
                optimization_notes=original_plan.optimization_notes + [
                    f"Optimized based on execution metrics (time ratio: {time_ratio:.2f}, memory ratio: {memory_ratio:.2f})"
                ],
                fallback_plans=original_plan.fallback_plans,
                streaming_config=original_plan.streaming_config,
                pagination_config=original_plan.pagination_config,
                parallel_config=original_plan.parallel_config
            )
            
            # Store optimization history
            self.optimization_history.append({
                "original_plan_id": plan_id,
                "optimized_plan_id": optimized_plan.plan_id,
                "optimization_timestamp": datetime.utcnow().isoformat(),
                "performance_improvement": {
                    "time_improvement": max(0, 1 - time_ratio),
                    "memory_improvement": max(0, 1 - memory_ratio)
                },
                "execution_metrics": asdict(execution_metrics)
            })
            
            logger.info(f"Plan {plan_id} optimized to {optimized_plan.plan_id}")
            return optimized_plan
            
        except Exception as e:
            logger.error(f"Plan optimization failed: {e}")
            return None
    
    def check_resource_availability(self, resource_requirements: ResourceRequirements) -> Dict[str, Any]:
        """
        Check if required resources are available.
        
        Args:
            resource_requirements: Required resources for execution
            
        Returns:
            Resource availability status
        """
        try:
            # Calculate current resource usage
            current_usage = {
                "memory_mb": sum(
                    exec_info.get("memory_mb", 0) 
                    for exec_info in self.active_executions.values()
                ),
                "cpu_cores": sum(
                    exec_info.get("cpu_cores", 0) 
                    for exec_info in self.active_executions.values()
                ),
                "concurrent_queries": len(self.active_executions)
            }
            
            # Check availability
            available_memory = self.resource_pool["max_memory_mb"] - current_usage["memory_mb"]
            available_cpu = self.resource_pool["max_cpu_cores"] - current_usage["cpu_cores"]
            available_query_slots = self.resource_pool["max_concurrent_queries"] - current_usage["concurrent_queries"]
            
            can_execute = (
                available_memory >= resource_requirements.estimated_memory_mb and
                available_cpu >= resource_requirements.estimated_cpu_cores and
                available_query_slots > 0
            )
            
            return {
                "can_execute": can_execute,
                "available_resources": {
                    "memory_mb": available_memory,
                    "cpu_cores": available_cpu,
                    "query_slots": available_query_slots
                },
                "required_resources": {
                    "memory_mb": resource_requirements.estimated_memory_mb,
                    "cpu_cores": resource_requirements.estimated_cpu_cores,
                    "query_slots": 1
                },
                "current_usage": current_usage,
                "resource_pool": self.resource_pool
            }
            
        except Exception as e:
            logger.error(f"Resource availability check failed: {e}")
            return {
                "can_execute": False,
                "error": str(e)
            }
    
    def reserve_resources(self, execution_id: str, resource_requirements: ResourceRequirements) -> bool:
        """
        Reserve resources for query execution.
        
        Args:
            execution_id: Unique execution identifier
            resource_requirements: Resources to reserve
            
        Returns:
            True if resources were successfully reserved
        """
        try:
            availability = self.check_resource_availability(resource_requirements)
            
            if not availability["can_execute"]:
                return False
            
            # Reserve resources
            self.active_executions[execution_id] = {
                "memory_mb": resource_requirements.estimated_memory_mb,
                "cpu_cores": resource_requirements.estimated_cpu_cores,
                "start_time": time.time(),
                "resource_requirements": asdict(resource_requirements)
            }
            
            logger.info(f"Resources reserved for execution {execution_id}")
            return True
            
        except Exception as e:
            logger.error(f"Resource reservation failed: {e}")
            return False
    
    def release_resources(self, execution_id: str) -> None:
        """
        Release resources after query execution.
        
        Args:
            execution_id: Execution identifier to release resources for
        """
        try:
            if execution_id in self.active_executions:
                execution_info = self.active_executions.pop(execution_id)
                execution_time = time.time() - execution_info["start_time"]
                
                logger.info(f"Resources released for execution {execution_id} after {execution_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Resource release failed: {e}")
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get statistics about query planning and execution."""
        try:
            return {
                "cached_plans": len(self.plan_cache),
                "active_executions": len(self.active_executions),
                "optimization_history_count": len(self.optimization_history),
                "resource_pool": self.resource_pool,
                "current_resource_usage": {
                    "memory_mb": sum(
                        exec_info.get("memory_mb", 0) 
                        for exec_info in self.active_executions.values()
                    ),
                    "cpu_cores": sum(
                        exec_info.get("cpu_cores", 0) 
                        for exec_info in self.active_executions.values()
                    ),
                    "concurrent_queries": len(self.active_executions)
                }
            }
            
        except Exception as e:
            logger.error(f"Statistics generation failed: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the Query Planning Agent."""
        try:
            self.initialize()
            
            # Test basic functionality
            test_response = await self.execute("Analyze query complexity: SELECT * FROM test_table")
            
            return {
                "status": "healthy",
                "agent_info": self.get_agent_info(),
                "cache_stats": {
                    "plan_cache_size": len(self.plan_cache),
                    "resource_stats_cache_size": len(self.resource_stats_cache),
                    "optimization_history_size": len(self.optimization_history)
                },
                "resource_stats": self.get_execution_statistics(),
                "test_response_length": len(test_response)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "agent_info": self.get_agent_info()
            }
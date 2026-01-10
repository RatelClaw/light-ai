"""
Comprehensive Data Analysis Engine for Intelligent AI Data Analyst System.

This module implements advanced data analysis capabilities including:
- Automated trend and pattern detection
- Statistical analysis and correlation finding
- Anomaly detection and alerting system
- Predictive analytics capabilities
- Comprehensive report generation with insights

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""

import asyncio
import json
import numpy as np
import pandas as pd
import uuid
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

# Statistical and ML imports
try:
    from scipy import stats
    from scipy.signal import find_peaks
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_squared_error, r2_score
    import statsmodels.api as sm
    from statsmodels.tsa.seasonal import seasonal_decompose
    from statsmodels.tsa.arima.model import ARIMA
    ADVANCED_ANALYTICS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Advanced analytics libraries not available: {e}")
    ADVANCED_ANALYTICS_AVAILABLE = False
    # Create dummy classes to prevent NameError
    class LinearRegression:
        def fit(self, X, y): pass
        def predict(self, X): return []
        def score(self, X, y): return 0.0
        @property
        def coef_(self): return [0.0]
    
    class IsolationForest:
        def __init__(self, **kwargs): pass
        def fit_predict(self, X): return []
        def decision_function(self, X): return []
    
    def find_peaks(data, **kwargs): return [], {}
    
    class stats:
        @staticmethod
        def zscore(data): return []
        @staticmethod
        def pearsonr(x, y): return 0.0, 0.05
        @staticmethod
        def shapiro(data): return 0.0, 0.05

from ..core.models import ResourceType, AccessLevel
from ..storage.metadata_registry import MetadataRegistry
from ..storage.storage_router import StorageRouter
from .sql_query_engine import SQLQueryEngine
from .semantic_search_engine import SemanticSearchEngine
from ..config import Config, get_config
from ..logger import get_logger

logger = get_logger(__name__)


class TrendType(Enum):
    """Types of trends that can be detected."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    SEASONAL = "seasonal"
    CYCLICAL = "cyclical"
    STABLE = "stable"
    VOLATILE = "volatile"


class AnomalyType(Enum):
    """Types of anomalies that can be detected."""
    OUTLIER = "outlier"
    SPIKE = "spike"
    DROP = "drop"
    PATTERN_BREAK = "pattern_break"
    SEASONAL_ANOMALY = "seasonal_anomaly"


class PredictionType(Enum):
    """Types of predictions that can be made."""
    LINEAR_TREND = "linear_trend"
    SEASONAL_FORECAST = "seasonal_forecast"
    ARIMA_FORECAST = "arima_forecast"
    REGRESSION_PREDICTION = "regression_prediction"


@dataclass
class TrendAnalysis:
    """Result of trend analysis."""
    trend_type: TrendType
    confidence: float
    description: str
    slope: Optional[float] = None
    r_squared: Optional[float] = None
    seasonal_period: Optional[int] = None
    supporting_data: List[Dict[str, Any]] = field(default_factory=list)
    visualization_data: Optional[Dict[str, Any]] = None


@dataclass
class CorrelationAnalysis:
    """Result of correlation analysis."""
    variable1: str
    variable2: str
    correlation_coefficient: float
    p_value: float
    correlation_type: str  # pearson, spearman, kendall
    significance_level: str  # strong, moderate, weak, none
    description: str
    supporting_data: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AnomalyDetection:
    """Result of anomaly detection."""
    anomaly_type: AnomalyType
    timestamp: Optional[datetime] = None
    value: Optional[float] = None
    expected_value: Optional[float] = None
    deviation_score: float = 0.0
    confidence: float = 0.0
    description: str = ""
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PredictiveAnalysis:
    """Result of predictive analysis."""
    prediction_type: PredictionType
    predictions: List[Dict[str, Any]]
    confidence_intervals: Optional[List[Dict[str, Any]]] = None
    model_accuracy: Optional[float] = None
    forecast_horizon: int = 0
    description: str = ""
    methodology: str = ""
    limitations: List[str] = field(default_factory=list)


@dataclass
class StatisticalSummary:
    """Statistical summary of data."""
    variable_name: str
    count: int
    mean: Optional[float] = None
    median: Optional[float] = None
    std_dev: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    quartiles: Optional[Dict[str, float]] = None
    distribution_type: Optional[str] = None
    normality_test: Optional[Dict[str, Any]] = None


@dataclass
class ComprehensiveAnalysisReport:
    """Comprehensive analysis report with all insights."""
    analysis_id: str
    user_id: str
    client_id: str
    original_query: str
    
    # Core analysis results
    statistical_summaries: List[StatisticalSummary] = field(default_factory=list)
    trend_analyses: List[TrendAnalysis] = field(default_factory=list)
    correlation_analyses: List[CorrelationAnalysis] = field(default_factory=list)
    anomaly_detections: List[AnomalyDetection] = field(default_factory=list)
    predictive_analyses: List[PredictiveAnalysis] = field(default_factory=list)
    
    # Report metadata
    executive_summary: str = ""
    key_insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    data_sources: List[str] = field(default_factory=list)
    methodology: str = ""
    limitations: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    execution_time_ms: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "analysis_id": self.analysis_id,
            "user_id": self.user_id,
            "client_id": self.client_id,
            "original_query": self.original_query,
            "statistical_summaries": [asdict(s) for s in self.statistical_summaries],
            "trend_analyses": [asdict(t) for t in self.trend_analyses],
            "correlation_analyses": [asdict(c) for c in self.correlation_analyses],
            "anomaly_detections": [asdict(a) for a in self.anomaly_detections],
            "predictive_analyses": [asdict(p) for p in self.predictive_analyses],
            "executive_summary": self.executive_summary,
            "key_insights": self.key_insights,
            "recommendations": self.recommendations,
            "data_sources": self.data_sources,
            "methodology": self.methodology,
            "limitations": self.limitations,
            "confidence_score": self.confidence_score,
            "execution_time_ms": self.execution_time_ms,
            "created_at": self.created_at.isoformat()
        }


class ComprehensiveAnalysisEngine:
    """
    Comprehensive Data Analysis Engine for advanced analytics.
    
    Features:
    - Automated trend and pattern detection using statistical methods
    - Correlation analysis across multiple variables
    - Anomaly detection using isolation forests and statistical methods
    - Predictive analytics with time series forecasting
    - Comprehensive report generation with insights and recommendations
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the comprehensive analysis engine."""
        self.config = config or get_config()
        self.metadata_registry = MetadataRegistry(config)
        self.storage_router = StorageRouter(config)
        self.sql_engine = SQLQueryEngine(config)
        self.semantic_search = SemanticSearchEngine(config)
        
        # Check if advanced analytics libraries are available
        if not ADVANCED_ANALYTICS_AVAILABLE:
            logger.warning("Advanced analytics libraries not available. Some features will be limited.")
        
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize the analysis engine and dependencies."""
        if not self._initialized:
            self.metadata_registry.initialize()
            self.storage_router.initialize()
            self.sql_engine.initialize()
            self.semantic_search.initialize()
            self._initialized = True
            logger.info("Comprehensive Analysis Engine initialized")
    
    async def analyze_comprehensive(self, query: str, client_id: str, user_id: str,
                                  access_level: AccessLevel = AccessLevel.USER,
                                  include_predictions: bool = True,
                                  include_anomalies: bool = True,
                                  forecast_horizon: int = 30) -> ComprehensiveAnalysisReport:
        """
        Perform comprehensive data analysis including trends, correlations, anomalies, and predictions.
        
        Args:
            query: Natural language query describing the analysis needed
            client_id: Client ID for access control
            user_id: User ID for access control
            access_level: Access level for the user
            include_predictions: Whether to include predictive analytics
            include_anomalies: Whether to include anomaly detection
            forecast_horizon: Number of periods to forecast (for time series)
            
        Returns:
            ComprehensiveAnalysisReport with all analysis results
        """
        self.initialize()
        
        start_time = datetime.utcnow()
        analysis_id = str(uuid.uuid4())
        
        try:
            logger.info(f"Starting comprehensive analysis for user {user_id}: {query}")
            
            # Step 1: Identify and retrieve relevant data
            data_sources = await self._identify_data_sources(query, client_id, user_id, access_level)
            
            if not data_sources:
                return self._create_empty_report(analysis_id, query, client_id, user_id, start_time,
                                               "No relevant data sources found for analysis.")
            
            # Step 2: Load and prepare data for analysis
            analysis_data = await self._prepare_analysis_data(data_sources, client_id, user_id)
            
            if not analysis_data:
                return self._create_empty_report(analysis_id, query, client_id, user_id, start_time,
                                               "Unable to load data for analysis.")
            
            # Step 3: Perform statistical analysis
            statistical_summaries = await self._perform_statistical_analysis(analysis_data)
            
            # Step 4: Detect trends and patterns
            trend_analyses = await self._detect_trends_and_patterns(analysis_data)
            
            # Step 5: Analyze correlations
            correlation_analyses = await self._analyze_correlations(analysis_data)
            
            # Step 6: Detect anomalies (if requested)
            anomaly_detections = []
            if include_anomalies:
                anomaly_detections = await self._detect_anomalies(analysis_data)
            
            # Step 7: Perform predictive analysis (if requested)
            predictive_analyses = []
            if include_predictions:
                predictive_analyses = await self._perform_predictive_analysis(
                    analysis_data, forecast_horizon
                )
            
            # Step 8: Generate comprehensive report
            report = await self._generate_comprehensive_report(
                analysis_id, query, client_id, user_id, data_sources,
                statistical_summaries, trend_analyses, correlation_analyses,
                anomaly_detections, predictive_analyses, start_time
            )
            
            logger.info(f"Comprehensive analysis completed for user {user_id}")
            return report
            
        except Exception as e:
            logger.error(f"Comprehensive analysis failed: {e}")
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return ComprehensiveAnalysisReport(
                analysis_id=analysis_id,
                user_id=user_id,
                client_id=client_id,
                original_query=query,
                executive_summary=f"Analysis failed: {str(e)}",
                execution_time_ms=execution_time
            )
    
    async def _identify_data_sources(self, query: str, client_id: str, user_id: str,
                                   access_level: AccessLevel) -> List[Dict[str, Any]]:
        """Identify relevant data sources for the analysis."""
        try:
            # Get all accessible resources
            all_resources = self.metadata_registry.list_resources(
                client_id, user_id if access_level == AccessLevel.USER else None
            )
            
            if not all_resources:
                return []
            
            # Focus on structured data for comprehensive analysis
            structured_resources = [r for r in all_resources if r.resource_type == ResourceType.STRUCTURED]
            
            # Score resources based on relevance and data quality
            scored_resources = []
            for resource in structured_resources:
                score = self._calculate_analysis_relevance(query, resource)
                if score > 0.1:  # Minimum relevance threshold
                    scored_resources.append({
                        "resource": resource,
                        "relevance_score": score
                    })
            
            # Sort by relevance and return top resources
            scored_resources.sort(key=lambda x: x["relevance_score"], reverse=True)
            return scored_resources[:5]  # Top 5 most relevant resources
            
        except Exception as e:
            logger.error(f"Failed to identify data sources: {e}")
            return []
    
    def _calculate_analysis_relevance(self, query: str, resource) -> float:
        """Calculate relevance score for comprehensive analysis."""
        score = 0.0
        query_lower = query.lower()
        
        # Filename relevance
        filename_lower = resource.original_filename.lower()
        if any(word in filename_lower for word in query_lower.split()):
            score += 0.3
        
        # Data size relevance (larger datasets better for statistical analysis)
        if resource.row_count:
            if resource.row_count > 1000:
                score += 0.3
            elif resource.row_count > 100:
                score += 0.2
            elif resource.row_count > 10:
                score += 0.1
        
        # Column count relevance (more columns = more analysis opportunities)
        if resource.column_count:
            if resource.column_count > 10:
                score += 0.2
            elif resource.column_count > 5:
                score += 0.1
        
        # Recent data gets boost
        days_old = (datetime.utcnow() - resource.created_at).days
        if days_old < 7:
            score += 0.2
        elif days_old < 30:
            score += 0.1
        
        return min(score, 1.0)
    
    async def _prepare_analysis_data(self, data_sources: List[Dict[str, Any]],
                                   client_id: str, user_id: str) -> Dict[str, pd.DataFrame]:
        """Prepare data for comprehensive analysis."""
        analysis_data = {}
        
        for source_info in data_sources:
            try:
                resource = source_info["resource"]
                
                # Query the structured data
                table_name = f"structured_data.resource_{resource.resource_id.replace('-', '_')}_enhanced"
                sql = f"SELECT * FROM {table_name} LIMIT 10000"  # Limit for performance
                
                results = self.storage_router.query_structured_data(sql, client_id, user_id)
                
                if results:
                    # Convert to pandas DataFrame
                    df = pd.DataFrame(results)
                    
                    # Remove system columns
                    system_columns = ['client_id', 'user_id', 'resource_id']
                    df = df.drop(columns=[col for col in system_columns if col in df.columns])
                    
                    # Convert numeric columns
                    df = self._convert_numeric_columns(df)
                    
                    # Convert datetime columns
                    df = self._convert_datetime_columns(df)
                    
                    analysis_data[resource.original_filename] = df
                    
            except Exception as e:
                logger.warning(f"Failed to prepare data for {source_info['resource'].original_filename}: {e}")
                continue
        
        return analysis_data
    
    def _convert_numeric_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert columns to numeric where possible."""
        for col in df.columns:
            try:
                # Try to convert to numeric
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except:
                pass
        return df
    
    def _convert_datetime_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert columns to datetime where possible."""
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['date', 'time', 'created', 'updated']):
                try:
                    df[col] = pd.to_datetime(df[col], errors='ignore')
                except:
                    pass
        return df
    
    async def _perform_statistical_analysis(self, analysis_data: Dict[str, pd.DataFrame]) -> List[StatisticalSummary]:
        """Perform comprehensive statistical analysis on the data."""
        summaries = []
        
        for source_name, df in analysis_data.items():
            try:
                # Analyze numeric columns
                numeric_columns = df.select_dtypes(include=[np.number]).columns
                
                for col in numeric_columns:
                    if df[col].notna().sum() < 2:  # Need at least 2 values
                        continue
                    
                    series = df[col].dropna()
                    
                    # Basic statistics
                    summary = StatisticalSummary(
                        variable_name=f"{source_name}.{col}",
                        count=len(series),
                        mean=float(series.mean()),
                        median=float(series.median()),
                        std_dev=float(series.std()),
                        min_value=float(series.min()),
                        max_value=float(series.max()),
                        quartiles={
                            "q1": float(series.quantile(0.25)),
                            "q3": float(series.quantile(0.75))
                        }
                    )
                    
                    # Distribution analysis
                    if ADVANCED_ANALYTICS_AVAILABLE and len(series) > 8:
                        try:
                            # Normality test
                            stat, p_value = stats.shapiro(series.sample(min(5000, len(series))))
                            summary.normality_test = {
                                "test": "shapiro",
                                "statistic": float(stat),
                                "p_value": float(p_value),
                                "is_normal": p_value > 0.05
                            }
                            
                            # Distribution type estimation
                            if p_value > 0.05:
                                summary.distribution_type = "normal"
                            elif series.skew() > 1:
                                summary.distribution_type = "right_skewed"
                            elif series.skew() < -1:
                                summary.distribution_type = "left_skewed"
                            else:
                                summary.distribution_type = "unknown"
                                
                        except Exception as e:
                            logger.warning(f"Failed distribution analysis for {col}: {e}")
                    
                    summaries.append(summary)
                    
            except Exception as e:
                logger.warning(f"Failed statistical analysis for {source_name}: {e}")
                continue
        
        return summaries
    
    async def _detect_trends_and_patterns(self, analysis_data: Dict[str, pd.DataFrame]) -> List[TrendAnalysis]:
        """Detect trends and patterns in time series data."""
        trends = []
        
        for source_name, df in analysis_data.items():
            try:
                # Look for datetime columns
                datetime_columns = df.select_dtypes(include=['datetime64']).columns
                numeric_columns = df.select_dtypes(include=[np.number]).columns
                
                if len(datetime_columns) == 0 or len(numeric_columns) == 0:
                    continue
                
                # Analyze each numeric column against time
                for date_col in datetime_columns:
                    for num_col in numeric_columns:
                        try:
                            # Create time series
                            ts_data = df[[date_col, num_col]].dropna().sort_values(date_col)
                            
                            if len(ts_data) < 10:  # Need sufficient data points
                                continue
                            
                            # Detect trend
                            trend_analysis = self._analyze_time_series_trend(
                                ts_data, date_col, num_col, f"{source_name}.{num_col}"
                            )
                            
                            if trend_analysis:
                                trends.append(trend_analysis)
                                
                        except Exception as e:
                            logger.warning(f"Failed trend analysis for {num_col}: {e}")
                            continue
                            
            except Exception as e:
                logger.warning(f"Failed trend detection for {source_name}: {e}")
                continue
        
        return trends
    
    def _analyze_time_series_trend(self, ts_data: pd.DataFrame, date_col: str,
                                 value_col: str, variable_name: str) -> Optional[TrendAnalysis]:
        """Analyze trend in a time series."""
        try:
            if not ADVANCED_ANALYTICS_AVAILABLE:
                return None
            
            # Prepare data for regression
            ts_data = ts_data.copy()
            ts_data['time_numeric'] = (ts_data[date_col] - ts_data[date_col].min()).dt.days
            
            X = ts_data['time_numeric'].values.reshape(-1, 1)
            y = ts_data[value_col].values
            
            # Linear regression for trend
            model = LinearRegression()
            model.fit(X, y)
            
            slope = model.coef_[0]
            r_squared = model.score(X, y)
            
            # Determine trend type
            if abs(slope) < 0.001:  # Very small slope
                trend_type = TrendType.STABLE
                confidence = r_squared
            elif slope > 0:
                trend_type = TrendType.INCREASING
                confidence = r_squared
            else:
                trend_type = TrendType.DECREASING
                confidence = r_squared
            
            # Check for seasonality if enough data
            seasonal_period = None
            if len(ts_data) > 24:  # Need sufficient data for seasonality
                try:
                    # Simple seasonality detection using autocorrelation
                    values = ts_data[value_col].values
                    autocorr = np.correlate(values, values, mode='full')
                    autocorr = autocorr[autocorr.size // 2:]
                    
                    # Find peaks in autocorrelation
                    peaks, _ = find_peaks(autocorr[1:], height=0.3 * np.max(autocorr))
                    if len(peaks) > 0:
                        seasonal_period = peaks[0] + 1
                        if seasonal_period > 2:
                            trend_type = TrendType.SEASONAL
                            
                except Exception:
                    pass
            
            # Generate description
            if trend_type == TrendType.INCREASING:
                description = f"Strong upward trend detected with slope {slope:.4f}"
            elif trend_type == TrendType.DECREASING:
                description = f"Strong downward trend detected with slope {slope:.4f}"
            elif trend_type == TrendType.SEASONAL:
                description = f"Seasonal pattern detected with period {seasonal_period}"
            else:
                description = f"Stable pattern with minimal trend (slope: {slope:.4f})"
            
            # Prepare supporting data
            supporting_data = [
                {"date": row[date_col].isoformat(), "value": float(row[value_col])}
                for _, row in ts_data.head(10).iterrows()
            ]
            
            return TrendAnalysis(
                trend_type=trend_type,
                confidence=float(confidence),
                description=description,
                slope=float(slope),
                r_squared=float(r_squared),
                seasonal_period=seasonal_period,
                supporting_data=supporting_data,
                visualization_data={
                    "chart_type": "line_chart",
                    "x_axis": date_col,
                    "y_axis": value_col,
                    "trend_line": True
                }
            )
            
        except Exception as e:
            logger.warning(f"Failed to analyze trend for {variable_name}: {e}")
            return None
    async def _analyze_correlations(self, analysis_data: Dict[str, pd.DataFrame]) -> List[CorrelationAnalysis]:
        """Analyze correlations between variables."""
        correlations = []
        
        for source_name, df in analysis_data.items():
            try:
                # Get numeric columns
                numeric_columns = df.select_dtypes(include=[np.number]).columns
                
                if len(numeric_columns) < 2:
                    continue
                
                # Calculate correlations between all pairs
                for i, col1 in enumerate(numeric_columns):
                    for col2 in numeric_columns[i+1:]:
                        try:
                            # Get clean data
                            data1 = df[col1].dropna()
                            data2 = df[col2].dropna()
                            
                            # Find common indices
                            common_idx = data1.index.intersection(data2.index)
                            if len(common_idx) < 10:  # Need sufficient data
                                continue
                            
                            x = data1.loc[common_idx]
                            y = data2.loc[common_idx]
                            
                            # Calculate Pearson correlation
                            if ADVANCED_ANALYTICS_AVAILABLE:
                                corr_coef, p_value = stats.pearsonr(x, y)
                            else:
                                corr_coef = np.corrcoef(x, y)[0, 1]
                                p_value = 0.05  # Default assumption
                            
                            # Determine significance level
                            abs_corr = abs(corr_coef)
                            if abs_corr >= 0.7:
                                significance = "strong"
                            elif abs_corr >= 0.5:
                                significance = "moderate"
                            elif abs_corr >= 0.3:
                                significance = "weak"
                            else:
                                significance = "none"
                            
                            # Generate description
                            direction = "positive" if corr_coef > 0 else "negative"
                            description = f"{significance.capitalize()} {direction} correlation between {col1} and {col2}"
                            
                            # Supporting data
                            supporting_data = [
                                {"x": float(x.iloc[i]), "y": float(y.iloc[i])}
                                for i in range(min(20, len(x)))
                            ]
                            
                            correlations.append(CorrelationAnalysis(
                                variable1=f"{source_name}.{col1}",
                                variable2=f"{source_name}.{col2}",
                                correlation_coefficient=float(corr_coef),
                                p_value=float(p_value),
                                correlation_type="pearson",
                                significance_level=significance,
                                description=description,
                                supporting_data=supporting_data
                            ))
                            
                        except Exception as e:
                            logger.warning(f"Failed correlation analysis for {col1} vs {col2}: {e}")
                            continue
                            
            except Exception as e:
                logger.warning(f"Failed correlation analysis for {source_name}: {e}")
                continue
        
        # Sort by absolute correlation coefficient
        correlations.sort(key=lambda x: abs(x.correlation_coefficient), reverse=True)
        return correlations[:10]  # Top 10 correlations
    
    async def _detect_anomalies(self, analysis_data: Dict[str, pd.DataFrame]) -> List[AnomalyDetection]:
        """Detect anomalies in the data using statistical methods."""
        anomalies = []
        
        if not ADVANCED_ANALYTICS_AVAILABLE:
            logger.warning("Advanced analytics not available for anomaly detection")
            return anomalies
        
        for source_name, df in analysis_data.items():
            try:
                # Get numeric columns
                numeric_columns = df.select_dtypes(include=[np.number]).columns
                
                for col in numeric_columns:
                    try:
                        series = df[col].dropna()
                        
                        if len(series) < 10:  # Need sufficient data
                            continue
                        
                        # Method 1: Statistical outliers (Z-score)
                        z_scores = np.abs(stats.zscore(series))
                        outlier_indices = np.where(z_scores > 3)[0]
                        
                        for idx in outlier_indices[:5]:  # Limit to top 5 outliers
                            original_idx = series.index[idx]
                            value = series.iloc[idx]
                            z_score = z_scores[idx]
                            
                            anomalies.append(AnomalyDetection(
                                anomaly_type=AnomalyType.OUTLIER,
                                value=float(value),
                                expected_value=float(series.mean()),
                                deviation_score=float(z_score),
                                confidence=min(float(z_score / 3), 1.0),
                                description=f"Statistical outlier in {source_name}.{col}: value {value:.2f} (Z-score: {z_score:.2f})",
                                context={
                                    "variable": f"{source_name}.{col}",
                                    "method": "z_score",
                                    "threshold": 3.0
                                }
                            ))
                        
                        # Method 2: Isolation Forest (if enough data)
                        if len(series) > 50:
                            try:
                                iso_forest = IsolationForest(contamination=0.1, random_state=42)
                                outlier_labels = iso_forest.fit_predict(series.values.reshape(-1, 1))
                                anomaly_scores = iso_forest.decision_function(series.values.reshape(-1, 1))
                                
                                # Find anomalies
                                anomaly_indices = np.where(outlier_labels == -1)[0]
                                
                                for idx in anomaly_indices[:3]:  # Top 3 anomalies
                                    value = series.iloc[idx]
                                    score = anomaly_scores[idx]
                                    
                                    anomalies.append(AnomalyDetection(
                                        anomaly_type=AnomalyType.PATTERN_BREAK,
                                        value=float(value),
                                        deviation_score=float(abs(score)),
                                        confidence=min(float(abs(score)), 1.0),
                                        description=f"Pattern anomaly in {source_name}.{col}: value {value:.2f}",
                                        context={
                                            "variable": f"{source_name}.{col}",
                                            "method": "isolation_forest",
                                            "anomaly_score": float(score)
                                        }
                                    ))
                                    
                            except Exception as e:
                                logger.warning(f"Isolation forest failed for {col}: {e}")
                        
                        # Method 3: Time series anomalies (if datetime column exists)
                        datetime_columns = df.select_dtypes(include=['datetime64']).columns
                        if len(datetime_columns) > 0:
                            date_col = datetime_columns[0]
                            ts_anomalies = self._detect_time_series_anomalies(
                                df, date_col, col, source_name
                            )
                            anomalies.extend(ts_anomalies)
                            
                    except Exception as e:
                        logger.warning(f"Failed anomaly detection for {col}: {e}")
                        continue
                        
            except Exception as e:
                logger.warning(f"Failed anomaly detection for {source_name}: {e}")
                continue
        
        # Sort by confidence and return top anomalies
        anomalies.sort(key=lambda x: x.confidence, reverse=True)
        return anomalies[:20]  # Top 20 anomalies
    
    def _detect_time_series_anomalies(self, df: pd.DataFrame, date_col: str,
                                    value_col: str, source_name: str) -> List[AnomalyDetection]:
        """Detect anomalies in time series data."""
        anomalies = []
        
        try:
            # Create time series
            ts_data = df[[date_col, value_col]].dropna().sort_values(date_col)
            
            if len(ts_data) < 20:  # Need sufficient data
                return anomalies
            
            values = ts_data[value_col].values
            dates = ts_data[date_col].values
            
            # Method 1: Sudden spikes/drops
            diff = np.diff(values)
            diff_std = np.std(diff)
            diff_mean = np.mean(diff)
            
            # Find significant changes
            spike_threshold = diff_mean + 3 * diff_std
            drop_threshold = diff_mean - 3 * diff_std
            
            spike_indices = np.where(diff > spike_threshold)[0]
            drop_indices = np.where(diff < drop_threshold)[0]
            
            # Add spike anomalies
            for idx in spike_indices[:3]:  # Top 3 spikes
                if idx + 1 < len(values):
                    anomalies.append(AnomalyDetection(
                        anomaly_type=AnomalyType.SPIKE,
                        timestamp=pd.to_datetime(dates[idx + 1]),
                        value=float(values[idx + 1]),
                        expected_value=float(values[idx]),
                        deviation_score=float(abs(diff[idx]) / diff_std),
                        confidence=min(float(abs(diff[idx]) / (3 * diff_std)), 1.0),
                        description=f"Sudden spike in {source_name}.{value_col}",
                        context={
                            "variable": f"{source_name}.{value_col}",
                            "change": float(diff[idx]),
                            "method": "time_series_spike"
                        }
                    ))
            
            # Add drop anomalies
            for idx in drop_indices[:3]:  # Top 3 drops
                if idx + 1 < len(values):
                    anomalies.append(AnomalyDetection(
                        anomaly_type=AnomalyType.DROP,
                        timestamp=pd.to_datetime(dates[idx + 1]),
                        value=float(values[idx + 1]),
                        expected_value=float(values[idx]),
                        deviation_score=float(abs(diff[idx]) / diff_std),
                        confidence=min(float(abs(diff[idx]) / (3 * diff_std)), 1.0),
                        description=f"Sudden drop in {source_name}.{value_col}",
                        context={
                            "variable": f"{source_name}.{value_col}",
                            "change": float(diff[idx]),
                            "method": "time_series_drop"
                        }
                    ))
            
        except Exception as e:
            logger.warning(f"Failed time series anomaly detection: {e}")
        
        return anomalies
    
    async def _perform_predictive_analysis(self, analysis_data: Dict[str, pd.DataFrame],
                                         forecast_horizon: int) -> List[PredictiveAnalysis]:
        """Perform predictive analysis and forecasting."""
        predictions = []
        
        if not ADVANCED_ANALYTICS_AVAILABLE:
            logger.warning("Advanced analytics not available for predictive analysis")
            return predictions
        
        for source_name, df in analysis_data.items():
            try:
                # Look for time series data
                datetime_columns = df.select_dtypes(include=['datetime64']).columns
                numeric_columns = df.select_dtypes(include=[np.number]).columns
                
                if len(datetime_columns) == 0 or len(numeric_columns) == 0:
                    continue
                
                # Analyze each numeric column for forecasting
                for date_col in datetime_columns:
                    for num_col in numeric_columns:
                        try:
                            # Create time series
                            ts_data = df[[date_col, num_col]].dropna().sort_values(date_col)
                            
                            if len(ts_data) < 20:  # Need sufficient historical data
                                continue
                            
                            # Perform different types of predictions
                            
                            # 1. Linear trend prediction
                            linear_prediction = self._predict_linear_trend(
                                ts_data, date_col, num_col, forecast_horizon, source_name
                            )
                            if linear_prediction:
                                predictions.append(linear_prediction)
                            
                            # 2. ARIMA forecasting (if enough data)
                            if len(ts_data) > 50:
                                arima_prediction = self._predict_arima(
                                    ts_data, date_col, num_col, forecast_horizon, source_name
                                )
                                if arima_prediction:
                                    predictions.append(arima_prediction)
                            
                        except Exception as e:
                            logger.warning(f"Failed prediction for {num_col}: {e}")
                            continue
                            
            except Exception as e:
                logger.warning(f"Failed predictive analysis for {source_name}: {e}")
                continue
        
        return predictions
    
    def _predict_linear_trend(self, ts_data: pd.DataFrame, date_col: str, value_col: str,
                            forecast_horizon: int, source_name: str) -> Optional[PredictiveAnalysis]:
        """Predict future values using linear trend."""
        try:
            # Prepare data
            ts_data = ts_data.copy()
            ts_data['time_numeric'] = (ts_data[date_col] - ts_data[date_col].min()).dt.days
            
            X = ts_data['time_numeric'].values.reshape(-1, 1)
            y = ts_data[value_col].values
            
            # Fit linear regression
            model = LinearRegression()
            model.fit(X, y)
            
            # Calculate model accuracy
            y_pred = model.predict(X)
            r2 = r2_score(y, y_pred)
            rmse = np.sqrt(mean_squared_error(y, y_pred))
            
            # Generate future predictions
            last_date = ts_data[date_col].max()
            future_dates = pd.date_range(
                start=last_date + pd.Timedelta(days=1),
                periods=forecast_horizon,
                freq='D'
            )
            
            future_time_numeric = (future_dates - ts_data[date_col].min()).days
            future_predictions = model.predict(future_time_numeric.values.reshape(-1, 1))
            
            # Calculate confidence intervals (simple approach)
            std_error = rmse
            confidence_intervals = []
            
            predictions_list = []
            for i, (date, pred) in enumerate(zip(future_dates, future_predictions)):
                # Confidence interval widens with time
                interval_width = std_error * (1 + i * 0.1)
                
                predictions_list.append({
                    "date": date.isoformat(),
                    "predicted_value": float(pred),
                    "period": i + 1
                })
                
                confidence_intervals.append({
                    "date": date.isoformat(),
                    "lower_bound": float(pred - 1.96 * interval_width),
                    "upper_bound": float(pred + 1.96 * interval_width)
                })
            
            return PredictiveAnalysis(
                prediction_type=PredictionType.LINEAR_TREND,
                predictions=predictions_list,
                confidence_intervals=confidence_intervals,
                model_accuracy=float(r2),
                forecast_horizon=forecast_horizon,
                description=f"Linear trend forecast for {source_name}.{value_col}",
                methodology="Linear regression on time series data with confidence intervals",
                limitations=[
                    "Assumes linear trend continues",
                    "Does not account for seasonality",
                    "Confidence intervals may be underestimated"
                ]
            )
            
        except Exception as e:
            logger.warning(f"Failed linear trend prediction: {e}")
            return None
    
    def _predict_arima(self, ts_data: pd.DataFrame, date_col: str, value_col: str,
                      forecast_horizon: int, source_name: str) -> Optional[PredictiveAnalysis]:
        """Predict future values using ARIMA model."""
        try:
            # Prepare time series
            ts = ts_data.set_index(date_col)[value_col].asfreq('D')
            ts = ts.dropna()
            
            if len(ts) < 50:  # Need sufficient data for ARIMA
                return None
            
            # Fit ARIMA model (simple auto-selection)
            try:
                # Try different ARIMA parameters
                best_aic = float('inf')
                best_model = None
                
                for p in range(3):
                    for d in range(2):
                        for q in range(3):
                            try:
                                model = ARIMA(ts, order=(p, d, q))
                                fitted_model = model.fit()
                                
                                if fitted_model.aic < best_aic:
                                    best_aic = fitted_model.aic
                                    best_model = fitted_model
                                    
                            except:
                                continue
                
                if best_model is None:
                    return None
                
                # Generate forecast
                forecast = best_model.forecast(steps=forecast_horizon)
                conf_int = best_model.get_forecast(steps=forecast_horizon).conf_int()
                
                # Prepare predictions
                future_dates = pd.date_range(
                    start=ts.index[-1] + pd.Timedelta(days=1),
                    periods=forecast_horizon,
                    freq='D'
                )
                
                predictions_list = []
                confidence_intervals = []
                
                for i, (date, pred) in enumerate(zip(future_dates, forecast)):
                    predictions_list.append({
                        "date": date.isoformat(),
                        "predicted_value": float(pred),
                        "period": i + 1
                    })
                    
                    confidence_intervals.append({
                        "date": date.isoformat(),
                        "lower_bound": float(conf_int.iloc[i, 0]),
                        "upper_bound": float(conf_int.iloc[i, 1])
                    })
                
                return PredictiveAnalysis(
                    prediction_type=PredictionType.ARIMA_FORECAST,
                    predictions=predictions_list,
                    confidence_intervals=confidence_intervals,
                    model_accuracy=None,  # ARIMA doesn't have R²
                    forecast_horizon=forecast_horizon,
                    description=f"ARIMA forecast for {source_name}.{value_col}",
                    methodology=f"ARIMA model with AIC: {best_aic:.2f}",
                    limitations=[
                        "Assumes stationarity after differencing",
                        "May not capture complex patterns",
                        "Forecast accuracy decreases with horizon"
                    ]
                )
                
            except Exception as e:
                logger.warning(f"ARIMA model fitting failed: {e}")
                return None
                
        except Exception as e:
            logger.warning(f"Failed ARIMA prediction: {e}")
            return None
    
    async def _generate_comprehensive_report(self, analysis_id: str, query: str, client_id: str,
                                           user_id: str, data_sources: List[Dict[str, Any]],
                                           statistical_summaries: List[StatisticalSummary],
                                           trend_analyses: List[TrendAnalysis],
                                           correlation_analyses: List[CorrelationAnalysis],
                                           anomaly_detections: List[AnomalyDetection],
                                           predictive_analyses: List[PredictiveAnalysis],
                                           start_time: datetime) -> ComprehensiveAnalysisReport:
        """Generate comprehensive analysis report with insights and recommendations."""
        try:
            # Generate executive summary
            executive_summary = self._generate_executive_summary(
                query, data_sources, statistical_summaries, trend_analyses,
                correlation_analyses, anomaly_detections, predictive_analyses
            )
            
            # Generate key insights
            key_insights = self._generate_key_insights(
                statistical_summaries, trend_analyses, correlation_analyses,
                anomaly_detections, predictive_analyses
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                trend_analyses, correlation_analyses, anomaly_detections, predictive_analyses
            )
            
            # Calculate overall confidence
            confidence_score = self._calculate_overall_confidence(
                trend_analyses, correlation_analyses, predictive_analyses
            )
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return ComprehensiveAnalysisReport(
                analysis_id=analysis_id,
                user_id=user_id,
                client_id=client_id,
                original_query=query,
                statistical_summaries=statistical_summaries,
                trend_analyses=trend_analyses,
                correlation_analyses=correlation_analyses,
                anomaly_detections=anomaly_detections,
                predictive_analyses=predictive_analyses,
                executive_summary=executive_summary,
                key_insights=key_insights,
                recommendations=recommendations,
                data_sources=[ds["resource"].original_filename for ds in data_sources],
                methodology=self._generate_methodology_description(),
                limitations=self._generate_limitations(),
                confidence_score=confidence_score,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            logger.error(f"Failed to generate comprehensive report: {e}")
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return ComprehensiveAnalysisReport(
                analysis_id=analysis_id,
                user_id=user_id,
                client_id=client_id,
                original_query=query,
                executive_summary=f"Report generation failed: {str(e)}",
                execution_time_ms=execution_time
            )
    
    def _generate_executive_summary(self, query: str, data_sources: List[Dict[str, Any]],
                                  statistical_summaries: List[StatisticalSummary],
                                  trend_analyses: List[TrendAnalysis],
                                  correlation_analyses: List[CorrelationAnalysis],
                                  anomaly_detections: List[AnomalyDetection],
                                  predictive_analyses: List[PredictiveAnalysis]) -> str:
        """Generate executive summary of the comprehensive analysis."""
        
        summary_parts = [
            f"Comprehensive analysis of {len(data_sources)} data sources completed."
        ]
        
        # Statistical insights
        if statistical_summaries:
            summary_parts.append(f"Statistical analysis performed on {len(statistical_summaries)} variables.")
        
        # Trend insights
        if trend_analyses:
            increasing_trends = len([t for t in trend_analyses if t.trend_type == TrendType.INCREASING])
            decreasing_trends = len([t for t in trend_analyses if t.trend_type == TrendType.DECREASING])
            seasonal_trends = len([t for t in trend_analyses if t.trend_type == TrendType.SEASONAL])
            
            if increasing_trends > 0:
                summary_parts.append(f"Detected {increasing_trends} increasing trends.")
            if decreasing_trends > 0:
                summary_parts.append(f"Detected {decreasing_trends} decreasing trends.")
            if seasonal_trends > 0:
                summary_parts.append(f"Identified {seasonal_trends} seasonal patterns.")
        
        # Correlation insights
        if correlation_analyses:
            strong_correlations = len([c for c in correlation_analyses if c.significance_level == "strong"])
            if strong_correlations > 0:
                summary_parts.append(f"Found {strong_correlations} strong correlations between variables.")
        
        # Anomaly insights
        if anomaly_detections:
            summary_parts.append(f"Detected {len(anomaly_detections)} anomalies requiring attention.")
        
        # Prediction insights
        if predictive_analyses:
            summary_parts.append(f"Generated {len(predictive_analyses)} predictive forecasts.")
        
        return " ".join(summary_parts)
    
    def _generate_key_insights(self, statistical_summaries: List[StatisticalSummary],
                             trend_analyses: List[TrendAnalysis],
                             correlation_analyses: List[CorrelationAnalysis],
                             anomaly_detections: List[AnomalyDetection],
                             predictive_analyses: List[PredictiveAnalysis]) -> List[str]:
        """Generate key insights from all analyses."""
        insights = []
        
        # Statistical insights
        if statistical_summaries:
            # Find variables with high variability
            high_var_vars = [s for s in statistical_summaries 
                           if s.std_dev and s.mean and (s.std_dev / abs(s.mean)) > 0.5]
            if high_var_vars:
                insights.append(f"High variability detected in {len(high_var_vars)} variables")
        
        # Trend insights
        for trend in trend_analyses[:3]:  # Top 3 trends
            if trend.confidence > 0.7:
                insights.append(f"{trend.description} (confidence: {trend.confidence:.2f})")
        
        # Correlation insights
        for corr in correlation_analyses[:3]:  # Top 3 correlations
            if corr.significance_level in ["strong", "moderate"]:
                insights.append(f"{corr.description} (r={corr.correlation_coefficient:.3f})")
        
        # Anomaly insights
        high_conf_anomalies = [a for a in anomaly_detections if a.confidence > 0.8]
        if high_conf_anomalies:
            insights.append(f"Critical anomalies detected in {len(high_conf_anomalies)} cases")
        
        # Prediction insights
        for pred in predictive_analyses[:2]:  # Top 2 predictions
            if pred.model_accuracy and pred.model_accuracy > 0.7:
                insights.append(f"High-confidence forecast available for {pred.description}")
        
        return insights
    
    def _generate_recommendations(self, trend_analyses: List[TrendAnalysis],
                               correlation_analyses: List[CorrelationAnalysis],
                               anomaly_detections: List[AnomalyDetection],
                               predictive_analyses: List[PredictiveAnalysis]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Trend-based recommendations
        increasing_trends = [t for t in trend_analyses if t.trend_type == TrendType.INCREASING and t.confidence > 0.7]
        if increasing_trends:
            recommendations.append("Monitor increasing trends for potential capacity or resource planning needs")
        
        decreasing_trends = [t for t in trend_analyses if t.trend_type == TrendType.DECREASING and t.confidence > 0.7]
        if decreasing_trends:
            recommendations.append("Investigate causes of decreasing trends and implement corrective measures")
        
        # Correlation-based recommendations
        strong_correlations = [c for c in correlation_analyses if c.significance_level == "strong"]
        if strong_correlations:
            recommendations.append("Leverage strong correlations for predictive modeling and decision making")
        
        # Anomaly-based recommendations
        critical_anomalies = [a for a in anomaly_detections if a.confidence > 0.8]
        if critical_anomalies:
            recommendations.append("Investigate critical anomalies immediately to prevent potential issues")
        
        # Prediction-based recommendations
        if predictive_analyses:
            recommendations.append("Use predictive forecasts for strategic planning and resource allocation")
        
        # General recommendations
        if not recommendations:
            recommendations.append("Continue regular monitoring and analysis to identify emerging patterns")
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def _calculate_overall_confidence(self, trend_analyses: List[TrendAnalysis],
                                    correlation_analyses: List[CorrelationAnalysis],
                                    predictive_analyses: List[PredictiveAnalysis]) -> float:
        """Calculate overall confidence score for the analysis."""
        confidence_scores = []
        
        # Add trend confidences
        for trend in trend_analyses:
            confidence_scores.append(trend.confidence)
        
        # Add correlation confidences (based on significance)
        for corr in correlation_analyses:
            if corr.significance_level == "strong":
                confidence_scores.append(0.9)
            elif corr.significance_level == "moderate":
                confidence_scores.append(0.7)
            elif corr.significance_level == "weak":
                confidence_scores.append(0.5)
        
        # Add prediction confidences
        for pred in predictive_analyses:
            if pred.model_accuracy:
                confidence_scores.append(pred.model_accuracy)
            else:
                confidence_scores.append(0.6)  # Default for ARIMA
        
        if confidence_scores:
            return float(np.mean(confidence_scores))
        else:
            return 0.5  # Default confidence
    
    def _generate_methodology_description(self) -> str:
        """Generate description of the analysis methodology."""
        methods = [
            "Statistical analysis using descriptive statistics and distribution testing",
            "Trend detection using linear regression and time series analysis",
            "Correlation analysis using Pearson correlation coefficients",
        ]
        
        if ADVANCED_ANALYTICS_AVAILABLE:
            methods.extend([
                "Anomaly detection using isolation forests and statistical outlier detection",
                "Predictive analytics using ARIMA models and linear trend forecasting"
            ])
        
        return "; ".join(methods) + "."
    
    def _generate_limitations(self) -> List[str]:
        """Generate list of analysis limitations."""
        limitations = [
            "Analysis is based on available data at the time of execution",
            "Statistical significance may be affected by sample size",
            "Predictions assume historical patterns continue"
        ]
        
        if not ADVANCED_ANALYTICS_AVAILABLE:
            limitations.append("Advanced analytics features limited due to missing dependencies")
        
        return limitations
    
    def _create_empty_report(self, analysis_id: str, query: str, client_id: str,
                           user_id: str, start_time: datetime, message: str) -> ComprehensiveAnalysisReport:
        """Create empty report when no data is available."""
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return ComprehensiveAnalysisReport(
            analysis_id=analysis_id,
            user_id=user_id,
            client_id=client_id,
            original_query=query,
            executive_summary=message,
            execution_time_ms=execution_time,
            recommendations=["Upload relevant data to enable comprehensive analysis"]
        )
    
    def get_analysis_capabilities(self) -> Dict[str, Any]:
        """Get information about comprehensive analysis capabilities."""
        capabilities = {
            "statistical_analysis": True,
            "trend_detection": True,
            "correlation_analysis": True,
            "anomaly_detection": ADVANCED_ANALYTICS_AVAILABLE,
            "predictive_analytics": ADVANCED_ANALYTICS_AVAILABLE,
            "supported_trend_types": [t.value for t in TrendType],
            "supported_anomaly_types": [a.value for a in AnomalyType],
            "supported_prediction_types": [p.value for p in PredictionType],
            "features": [
                "Automated trend and pattern detection",
                "Statistical analysis and correlation finding",
                "Comprehensive report generation with insights"
            ]
        }
        
        if ADVANCED_ANALYTICS_AVAILABLE:
            capabilities["features"].extend([
                "Anomaly detection and alerting system",
                "Predictive analytics capabilities"
            ])
        
        return capabilities
    
    def close(self) -> None:
        """Close the comprehensive analysis engine and clean up resources."""
        self.sql_engine.close()
        self.storage_router.close()
        logger.info("Comprehensive Analysis Engine closed")
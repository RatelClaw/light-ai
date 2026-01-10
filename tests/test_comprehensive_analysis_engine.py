"""
Tests for Comprehensive Data Analysis Engine.

Tests cover:
- Automated trend and pattern detection
- Statistical analysis and correlation finding
- Anomaly detection and alerting system
- Predictive analytics capabilities
- Comprehensive report generation with insights

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""

import pytest
import pytest_asyncio
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

from light_ai.sub_layer_2.comprehensive_analysis_engine import (
    ComprehensiveAnalysisEngine,
    TrendType, AnomalyType, PredictionType,
    TrendAnalysis, CorrelationAnalysis, AnomalyDetection,
    PredictiveAnalysis, StatisticalSummary, ComprehensiveAnalysisReport
)
from light_ai.core.models import ResourceType, AccessLevel, ResourceMetadata
from light_ai.config import Config


class TestComprehensiveAnalysisEngine:
    """Test suite for Comprehensive Data Analysis Engine."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = Mock(spec=Config)
        config.openrouter = Mock()
        config.openrouter.api_key = "test-key"
        config.openrouter.base_url = "https://test.api"
        config.openrouter.default_model = "test-model"
        
        # Add database configuration
        config.database = Mock()
        config.database.sqlite_path = "test.db"
        config.get_full_path = Mock(return_value="/tmp/test.db")
        
        # Add storage configuration
        config.storage = Mock()
        config.storage.base_directory = "/tmp/test_storage"
        
        return config
    
    @pytest.fixture
    def sample_time_series_data(self):
        """Create sample time series data for testing."""
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        np.random.seed(42)
        
        # Create trend with seasonality and noise
        trend = np.linspace(100, 200, len(dates))
        seasonal = 20 * np.sin(2 * np.pi * np.arange(len(dates)) / 30)
        noise = np.random.normal(0, 5, len(dates))
        values = trend + seasonal + noise
        
        # Add some anomalies
        anomaly_indices = [50, 150, 250]
        values[anomaly_indices] += [100, -80, 120]
        
        return pd.DataFrame({
            'date': dates,
            'sales': values,
            'marketing': values * 0.1 + np.random.normal(0, 2, len(dates)),
            'satisfaction': 80 + (values - values.mean()) / values.std() * 3 + np.random.normal(0, 1, len(dates))
        })
    
    @pytest.fixture
    def mock_dependencies(self, mock_config):
        """Create mock dependencies for the analysis engine."""
        with patch('light_ai.sub_layer_2.comprehensive_analysis_engine.MetadataRegistry') as mock_registry, \
             patch('light_ai.sub_layer_2.comprehensive_analysis_engine.StorageRouter') as mock_storage, \
             patch('light_ai.sub_layer_2.comprehensive_analysis_engine.SQLQueryEngine') as mock_sql, \
             patch('light_ai.sub_layer_2.comprehensive_analysis_engine.SemanticSearchEngine') as mock_semantic:
            
            # Setup mock registry
            mock_registry_instance = Mock()
            mock_registry.return_value = mock_registry_instance
            
            # Setup mock storage
            mock_storage_instance = Mock()
            mock_storage.return_value = mock_storage_instance
            
            # Setup mock SQL engine
            mock_sql_instance = Mock()
            mock_sql.return_value = mock_sql_instance
            
            # Setup mock semantic search
            mock_semantic_instance = Mock()
            mock_semantic.return_value = mock_semantic_instance
            
            yield {
                'registry': mock_registry_instance,
                'storage': mock_storage_instance,
                'sql': mock_sql_instance,
                'semantic': mock_semantic_instance
            }
    
    @pytest.fixture
    def analysis_engine(self, mock_config, mock_dependencies):
        """Create analysis engine with mocked dependencies."""
        engine = ComprehensiveAnalysisEngine(mock_config)
        
        # Replace dependencies with mocks
        engine.metadata_registry = mock_dependencies['registry']
        engine.storage_router = mock_dependencies['storage']
        engine.sql_engine = mock_dependencies['sql']
        engine.semantic_search = mock_dependencies['semantic']
        
        return engine
    
    def test_initialization(self, mock_config):
        """Test analysis engine initialization."""
        engine = ComprehensiveAnalysisEngine(mock_config)
        
        assert engine.config == mock_config
        assert not engine._initialized
        
        # Test initialization
        with patch.object(engine, 'metadata_registry') as mock_registry, \
             patch.object(engine, 'storage_router') as mock_storage, \
             patch.object(engine, 'sql_engine') as mock_sql, \
             patch.object(engine, 'semantic_search') as mock_semantic:
            
            engine.initialize()
            
            assert engine._initialized
            mock_registry.initialize.assert_called_once()
            mock_storage.initialize.assert_called_once()
            mock_sql.initialize.assert_called_once()
            mock_semantic.initialize.assert_called_once()
    
    def test_calculate_analysis_relevance(self, analysis_engine):
        """Test resource relevance calculation for analysis."""
        # Create mock resource
        resource = Mock()
        resource.original_filename = "sales_data.csv"
        resource.row_count = 1000
        resource.column_count = 10
        resource.created_at = datetime.utcnow() - timedelta(days=5)
        
        # Test relevance calculation
        score = analysis_engine._calculate_analysis_relevance("analyze sales trends", resource)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be relevant due to filename match and good data size
    
    def test_convert_numeric_columns(self, analysis_engine):
        """Test numeric column conversion."""
        # Create test DataFrame
        df = pd.DataFrame({
            'text_col': ['a', 'b', 'c'],
            'numeric_str': ['1', '2', '3'],
            'mixed': ['1', 'text', '3'],
            'float_col': [1.1, 2.2, 3.3]
        })
        
        result = analysis_engine._convert_numeric_columns(df)
        
        # Check that numeric strings were converted
        assert pd.api.types.is_numeric_dtype(result['numeric_str'])
        assert pd.api.types.is_numeric_dtype(result['float_col'])
        # Mixed column should remain as object (not converted)
        assert not pd.api.types.is_numeric_dtype(result['mixed'])
    
    def test_convert_datetime_columns(self, analysis_engine):
        """Test datetime column conversion."""
        # Create test DataFrame
        df = pd.DataFrame({
            'date_col': ['2023-01-01', '2023-01-02', '2023-01-03'],
            'created_at': ['2023-01-01 10:00:00', '2023-01-02 11:00:00', '2023-01-03 12:00:00'],
            'regular_col': ['a', 'b', 'c']
        })
        
        result = analysis_engine._convert_datetime_columns(df)
        
        # Check that date columns were converted
        assert pd.api.types.is_datetime64_any_dtype(result['date_col'])
        assert pd.api.types.is_datetime64_any_dtype(result['created_at'])
        # Regular column should remain unchanged
        assert not pd.api.types.is_datetime64_any_dtype(result['regular_col'])
    
    @pytest.mark.asyncio
    async def test_perform_statistical_analysis(self, analysis_engine, sample_time_series_data):
        """Test statistical analysis functionality."""
        analysis_data = {"test_data": sample_time_series_data}
        
        summaries = await analysis_engine._perform_statistical_analysis(analysis_data)
        
        assert len(summaries) > 0
        
        # Check that we have summaries for numeric columns
        variable_names = [s.variable_name for s in summaries]
        assert any('sales' in name for name in variable_names)
        assert any('marketing' in name for name in variable_names)
        assert any('satisfaction' in name for name in variable_names)
        
        # Check statistical properties
        sales_summary = next(s for s in summaries if 'sales' in s.variable_name)
        assert sales_summary.count > 0
        assert sales_summary.mean is not None
        assert sales_summary.std_dev is not None
        assert sales_summary.min_value is not None
        assert sales_summary.max_value is not None
        assert sales_summary.quartiles is not None
    
    @pytest.mark.asyncio
    async def test_detect_trends_and_patterns(self, analysis_engine, sample_time_series_data):
        """Test trend and pattern detection."""
        analysis_data = {"test_data": sample_time_series_data}
        
        with patch('light_ai.sub_layer_2.comprehensive_analysis_engine.ADVANCED_ANALYTICS_AVAILABLE', True):
            trends = await analysis_engine._detect_trends_and_patterns(analysis_data)
        
        assert len(trends) > 0
        
        # Check trend properties
        trend = trends[0]
        assert isinstance(trend.trend_type, TrendType)
        assert 0.0 <= trend.confidence <= 1.0
        assert trend.description is not None
        assert trend.slope is not None
        assert trend.r_squared is not None
    
    def test_analyze_time_series_trend(self, analysis_engine, sample_time_series_data):
        """Test time series trend analysis."""
        ts_data = sample_time_series_data[['date', 'sales']].copy()
        
        with patch('light_ai.sub_layer_2.comprehensive_analysis_engine.ADVANCED_ANALYTICS_AVAILABLE', True):
            trend_analysis = analysis_engine._analyze_time_series_trend(
                ts_data, 'date', 'sales', 'test.sales'
            )
        
        assert trend_analysis is not None
        assert isinstance(trend_analysis.trend_type, TrendType)
        assert 0.0 <= trend_analysis.confidence <= 1.0
        assert trend_analysis.slope is not None
        assert trend_analysis.r_squared is not None
        assert len(trend_analysis.supporting_data) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_correlations(self, analysis_engine, sample_time_series_data):
        """Test correlation analysis."""
        analysis_data = {"test_data": sample_time_series_data}
        
        correlations = await analysis_engine._analyze_correlations(analysis_data)
        
        assert len(correlations) > 0
        
        # Check correlation properties
        corr = correlations[0]
        assert corr.variable1 is not None
        assert corr.variable2 is not None
        assert -1.0 <= corr.correlation_coefficient <= 1.0
        assert corr.correlation_type == "pearson"
        assert corr.significance_level in ["strong", "moderate", "weak", "none"]
        assert len(corr.supporting_data) > 0
    
    @pytest.mark.asyncio
    async def test_detect_anomalies(self, analysis_engine, sample_time_series_data):
        """Test anomaly detection."""
        analysis_data = {"test_data": sample_time_series_data}
        
        with patch('light_ai.sub_layer_2.comprehensive_analysis_engine.ADVANCED_ANALYTICS_AVAILABLE', True):
            anomalies = await analysis_engine._detect_anomalies(analysis_data)
        
        assert len(anomalies) > 0
        
        # Check anomaly properties
        anomaly = anomalies[0]
        assert isinstance(anomaly.anomaly_type, AnomalyType)
        assert 0.0 <= anomaly.confidence <= 1.0
        assert anomaly.description is not None
        assert anomaly.value is not None
    
    def test_detect_time_series_anomalies(self, analysis_engine, sample_time_series_data):
        """Test time series specific anomaly detection."""
        anomalies = analysis_engine._detect_time_series_anomalies(
            sample_time_series_data, 'date', 'sales', 'test_data'
        )
        
        # Should detect the anomalies we added to the sample data
        assert len(anomalies) > 0
        
        # Check for spike and drop anomalies
        anomaly_types = [a.anomaly_type for a in anomalies]
        assert AnomalyType.SPIKE in anomaly_types or AnomalyType.DROP in anomaly_types
    
    @pytest.mark.asyncio
    async def test_perform_predictive_analysis(self, analysis_engine, sample_time_series_data):
        """Test predictive analysis."""
        analysis_data = {"test_data": sample_time_series_data}
        
        with patch('light_ai.sub_layer_2.comprehensive_analysis_engine.ADVANCED_ANALYTICS_AVAILABLE', True):
            predictions = await analysis_engine._perform_predictive_analysis(analysis_data, 30)
        
        assert len(predictions) > 0
        
        # Check prediction properties
        prediction = predictions[0]
        assert isinstance(prediction.prediction_type, PredictionType)
        assert len(prediction.predictions) > 0
        assert prediction.forecast_horizon == 30
        assert prediction.description is not None
        assert prediction.methodology is not None
    
    def test_predict_linear_trend(self, analysis_engine, sample_time_series_data):
        """Test linear trend prediction."""
        ts_data = sample_time_series_data[['date', 'sales']].copy()
        
        prediction = analysis_engine._predict_linear_trend(
            ts_data, 'date', 'sales', 30, 'test_data'
        )
        
        assert prediction is not None
        assert prediction.prediction_type == PredictionType.LINEAR_TREND
        assert len(prediction.predictions) == 30
        assert prediction.model_accuracy is not None
        assert len(prediction.confidence_intervals) == 30
    
    @pytest.mark.asyncio
    async def test_comprehensive_analysis_no_data(self, analysis_engine, mock_dependencies):
        """Test comprehensive analysis with no data sources."""
        # Mock no resources found
        mock_dependencies['registry'].list_resources.return_value = []
        
        report = await analysis_engine.analyze_comprehensive(
            query="test query",
            client_id="test-client",
            user_id="test-user"
        )
        
        assert report.analysis_id is not None
        assert "No relevant data sources found" in report.executive_summary
        assert len(report.statistical_summaries) == 0
        assert len(report.trend_analyses) == 0
    
    @pytest.mark.asyncio
    async def test_comprehensive_analysis_with_data(self, analysis_engine, mock_dependencies, sample_time_series_data):
        """Test comprehensive analysis with sample data."""
        # Mock resource metadata
        mock_resource = Mock()
        mock_resource.resource_id = "test-resource-id"
        mock_resource.resource_type = ResourceType.STRUCTURED
        mock_resource.original_filename = "sales_data.csv"
        mock_resource.row_count = 365
        mock_resource.column_count = 4
        mock_resource.created_at = datetime.utcnow()
        
        mock_dependencies['registry'].list_resources.return_value = [mock_resource]
        
        # Mock data retrieval
        sample_dict = sample_time_series_data.to_dict('records')
        mock_dependencies['storage'].query_structured_data.return_value = sample_dict
        
        with patch('light_ai.sub_layer_2.comprehensive_analysis_engine.ADVANCED_ANALYTICS_AVAILABLE', True):
            report = await analysis_engine.analyze_comprehensive(
                query="analyze sales trends and patterns",
                client_id="test-client",
                user_id="test-user",
                include_predictions=True,
                include_anomalies=True,
                forecast_horizon=30
            )
        
        assert report.analysis_id is not None
        assert report.user_id == "test-user"
        assert report.client_id == "test-client"
        assert len(report.data_sources) > 0
        assert report.confidence_score > 0.0
        assert report.execution_time_ms > 0.0
        
        # Should have various types of analysis
        assert len(report.statistical_summaries) > 0
        assert len(report.key_insights) > 0
        assert len(report.recommendations) > 0
    
    def test_generate_executive_summary(self, analysis_engine):
        """Test executive summary generation."""
        # Create mock data sources
        data_sources = [{"resource": Mock(original_filename="test.csv")}]
        
        # Create mock analysis results
        statistical_summaries = [Mock()]
        trend_analyses = [Mock(trend_type=TrendType.INCREASING)]
        correlation_analyses = [Mock(significance_level="strong")]
        anomaly_detections = [Mock()]
        predictive_analyses = [Mock()]
        
        summary = analysis_engine._generate_executive_summary(
            "test query", data_sources, statistical_summaries,
            trend_analyses, correlation_analyses, anomaly_detections, predictive_analyses
        )
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "data sources" in summary.lower()
    
    def test_generate_key_insights(self, analysis_engine):
        """Test key insights generation."""
        # Create mock analysis results
        statistical_summaries = [Mock(std_dev=10, mean=100, variable_name="test.var")]
        trend_analyses = [Mock(confidence=0.8, description="Strong upward trend")]
        correlation_analyses = [Mock(significance_level="strong", description="Strong correlation", correlation_coefficient=0.85)]
        anomaly_detections = [Mock(confidence=0.9)]
        predictive_analyses = [Mock(model_accuracy=0.8, description="Sales forecast")]
        
        insights = analysis_engine._generate_key_insights(
            statistical_summaries, trend_analyses, correlation_analyses,
            anomaly_detections, predictive_analyses
        )
        
        assert isinstance(insights, list)
        assert len(insights) > 0
        assert all(isinstance(insight, str) for insight in insights)
    
    def test_generate_recommendations(self, analysis_engine):
        """Test recommendations generation."""
        # Create mock analysis results
        trend_analyses = [Mock(trend_type=TrendType.INCREASING, confidence=0.8)]
        correlation_analyses = [Mock(significance_level="strong")]
        anomaly_detections = [Mock(confidence=0.9)]
        predictive_analyses = [Mock()]
        
        recommendations = analysis_engine._generate_recommendations(
            trend_analyses, correlation_analyses, anomaly_detections, predictive_analyses
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert all(isinstance(rec, str) for rec in recommendations)
    
    def test_calculate_overall_confidence(self, analysis_engine):
        """Test overall confidence calculation."""
        # Create mock analysis results
        trend_analyses = [Mock(confidence=0.8), Mock(confidence=0.9)]
        correlation_analyses = [Mock(significance_level="strong"), Mock(significance_level="moderate")]
        predictive_analyses = [Mock(model_accuracy=0.85)]
        
        confidence = analysis_engine._calculate_overall_confidence(
            trend_analyses, correlation_analyses, predictive_analyses
        )
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should be reasonably high given the mock data
    
    def test_get_analysis_capabilities(self, analysis_engine):
        """Test analysis capabilities reporting."""
        capabilities = analysis_engine.get_analysis_capabilities()
        
        assert isinstance(capabilities, dict)
        assert "statistical_analysis" in capabilities
        assert "trend_detection" in capabilities
        assert "correlation_analysis" in capabilities
        assert "supported_trend_types" in capabilities
        assert "features" in capabilities
        
        # Check that features list contains expected items
        features = capabilities["features"]
        assert "Automated trend and pattern detection" in features
        assert "Statistical analysis and correlation finding" in features
    
    def test_close(self, analysis_engine, mock_dependencies):
        """Test engine cleanup."""
        analysis_engine.close()
        
        mock_dependencies['sql'].close.assert_called_once()
        mock_dependencies['storage'].close.assert_called_once()


class TestDataModels:
    """Test data models used by the comprehensive analysis engine."""
    
    def test_trend_analysis_creation(self):
        """Test TrendAnalysis data model."""
        trend = TrendAnalysis(
            trend_type=TrendType.INCREASING,
            confidence=0.85,
            description="Strong upward trend",
            slope=1.5,
            r_squared=0.92
        )
        
        assert trend.trend_type == TrendType.INCREASING
        assert trend.confidence == 0.85
        assert trend.description == "Strong upward trend"
        assert trend.slope == 1.5
        assert trend.r_squared == 0.92
    
    def test_correlation_analysis_creation(self):
        """Test CorrelationAnalysis data model."""
        corr = CorrelationAnalysis(
            variable1="sales",
            variable2="marketing",
            correlation_coefficient=0.75,
            p_value=0.001,
            correlation_type="pearson",
            significance_level="strong",
            description="Strong positive correlation"
        )
        
        assert corr.variable1 == "sales"
        assert corr.variable2 == "marketing"
        assert corr.correlation_coefficient == 0.75
        assert corr.significance_level == "strong"
    
    def test_anomaly_detection_creation(self):
        """Test AnomalyDetection data model."""
        anomaly = AnomalyDetection(
            anomaly_type=AnomalyType.SPIKE,
            timestamp=datetime(2023, 1, 15),
            value=1500.0,
            expected_value=1000.0,
            deviation_score=3.2,
            confidence=0.95,
            description="Sudden spike detected"
        )
        
        assert anomaly.anomaly_type == AnomalyType.SPIKE
        assert anomaly.value == 1500.0
        assert anomaly.confidence == 0.95
    
    def test_predictive_analysis_creation(self):
        """Test PredictiveAnalysis data model."""
        prediction = PredictiveAnalysis(
            prediction_type=PredictionType.LINEAR_TREND,
            predictions=[{"date": "2024-01-01", "value": 1200}],
            model_accuracy=0.88,
            forecast_horizon=30,
            description="30-day sales forecast"
        )
        
        assert prediction.prediction_type == PredictionType.LINEAR_TREND
        assert len(prediction.predictions) == 1
        assert prediction.model_accuracy == 0.88
        assert prediction.forecast_horizon == 30
    
    def test_comprehensive_analysis_report_to_dict(self):
        """Test ComprehensiveAnalysisReport serialization."""
        report = ComprehensiveAnalysisReport(
            analysis_id="test-id",
            user_id="test-user",
            client_id="test-client",
            original_query="test query",
            executive_summary="Test summary",
            confidence_score=0.8,
            execution_time_ms=1500.0
        )
        
        report_dict = report.to_dict()
        
        assert isinstance(report_dict, dict)
        assert report_dict["analysis_id"] == "test-id"
        assert report_dict["user_id"] == "test-user"
        assert report_dict["confidence_score"] == 0.8
        assert "created_at" in report_dict


if __name__ == "__main__":
    pytest.main([__file__])
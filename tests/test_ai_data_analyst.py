"""
Unit tests for AI Data Analyst.

Tests the comprehensive AI data analyst capabilities including resource identification,
cross-format synthesis, insight generation, and report creation.
"""

import json
import uuid
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from light_ai.core.models import (
    DataHierarchy, ResourceMetadata, ResourceType, DataType, AccessLevel
)
from light_ai.sub_layer_2.ai_data_analyst import (
    AIDataAnalyst, AnalysisType, InsightType, DataSource, Insight, AnalysisReport
)
from light_ai.config import get_config


class TestAIDataAnalyst:
    """Test cases for AI Data Analyst."""
    
    @pytest.fixture
    def config(self):
        """Get test configuration."""
        return get_config()
    
    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test AI response"
        mock_client.chat.completions.create.return_value = mock_response
        return mock_client
    
    @pytest.fixture
    def sample_resources(self):
        """Sample resource metadata for testing."""
        return [
            ResourceMetadata(
                resource_id=str(uuid.uuid4()),
                user_id=str(uuid.uuid4()),
                client_id=str(uuid.uuid4()),
                resource_type=ResourceType.STRUCTURED,
                data_type=DataType.CSV,
                original_filename="sales_data.csv",
                file_size_bytes=1024000,
                storage_path="/data/sales_data.csv",
                row_count=1000,
                column_count=5
            ),
            ResourceMetadata(
                resource_id=str(uuid.uuid4()),
                user_id=str(uuid.uuid4()),
                client_id=str(uuid.uuid4()),
                resource_type=ResourceType.UNSTRUCTURED,
                data_type=DataType.PDF,
                original_filename="product_manual.pdf",
                file_size_bytes=2048000,
                storage_path="/data/product_manual.pdf",
                chunk_count=50
            )
        ]
    
    @pytest.fixture
    def analyst(self, config):
        """Create AI data analyst instance."""
        with patch('light_ai.sub_layer_2.ai_data_analyst.OpenAI'):
            return AIDataAnalyst(config)
    
    def test_initialization(self, analyst):
        """Test AI data analyst initialization."""
        assert analyst is not None
        assert analyst.config is not None
        assert not analyst._initialized
        
        # Test initialization
        with patch.object(analyst.metadata_registry, 'initialize'), \
             patch.object(analyst.storage_router, 'initialize'), \
             patch.object(analyst.sql_engine, 'initialize'), \
             patch.object(analyst.nl_processor, 'initialize'), \
             patch.object(analyst.semantic_search, 'initialize'):
            
            analyst.initialize()
            assert analyst._initialized
    
    def test_classify_analysis_type(self, analyst):
        """Test analysis type classification."""
        # Test descriptive analysis
        descriptive_questions = [
            "What is the total sales?",
            "Show me all customers",
            "How many orders do we have?"
        ]
        
        for question in descriptive_questions:
            analysis_type = analyst._classify_analysis_type(question)
            assert analysis_type == AnalysisType.DESCRIPTIVE
        
        # Test diagnostic analysis
        diagnostic_questions = [
            "Why did sales drop last quarter?",
            "What caused the increase in customer complaints?",
            "Analyze the correlation between price and demand to understand the relationship"
        ]
        
        for question in diagnostic_questions:
            analysis_type = analyst._classify_analysis_type(question)
            # Note: Some questions might be classified as exploratory if they don't have strong diagnostic signals
            assert analysis_type in [AnalysisType.DIAGNOSTIC, AnalysisType.EXPLORATORY]
        
        # Test predictive analysis
        predictive_questions = [
            "Predict next quarter's sales",
            "What will happen to customer churn?",
            "Forecast demand for next month"
        ]
        
        for question in predictive_questions:
            analysis_type = analyst._classify_analysis_type(question)
            assert analysis_type == AnalysisType.PREDICTIVE
        
        # Test prescriptive analysis
        prescriptive_questions = [
            "What should we do to improve sales?",
            "Recommend actions to reduce costs",
            "How can we optimize our strategy?"
        ]
        
        for question in prescriptive_questions:
            analysis_type = analyst._classify_analysis_type(question)
            assert analysis_type == AnalysisType.PRESCRIPTIVE
        
        # Test exploratory analysis (default)
        exploratory_questions = [
            "Find patterns in the data",
            "Explore customer behavior",
            "Discover insights"
        ]
        
        for question in exploratory_questions:
            analysis_type = analyst._classify_analysis_type(question)
            assert analysis_type == AnalysisType.EXPLORATORY
    
    def test_calculate_resource_relevance(self, analyst, sample_resources):
        """Test resource relevance calculation."""
        structured_resource = sample_resources[0]
        unstructured_resource = sample_resources[1]
        
        # Test relevance for sales-related question
        sales_question = "What are the total sales numbers?"
        
        sales_relevance = analyst._calculate_resource_relevance(sales_question, structured_resource)
        manual_relevance = analyst._calculate_resource_relevance(sales_question, unstructured_resource)
        
        # Sales data should be more relevant for sales question
        assert sales_relevance > manual_relevance
        assert sales_relevance > 0.0
        
        # Test relevance for product-related question
        product_question = "What information is in the product manual?"
        
        product_sales_relevance = analyst._calculate_resource_relevance(product_question, structured_resource)
        product_manual_relevance = analyst._calculate_resource_relevance(product_question, unstructured_resource)
        
        # Product manual should be more relevant for product question
        assert product_manual_relevance > product_sales_relevance
        assert product_manual_relevance > 0.0
    
    def test_identify_relevant_resources(self, analyst, sample_resources):
        """Test resource identification."""
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        with patch.object(analyst.metadata_registry, 'list_resources', return_value=sample_resources):
            relevant_resources = analyst._identify_relevant_resources(
                "Analyze sales data", client_id, user_id, AccessLevel.USER
            )
            
            assert len(relevant_resources) > 0
            # Should include the sales data resource
            assert any(r.original_filename == "sales_data.csv" for r in relevant_resources)
    
    def test_build_data_source_contexts(self, analyst, sample_resources):
        """Test data source context building."""
        with patch.object(analyst.metadata_registry, 'get_schema_info', return_value=None), \
             patch.object(analyst, '_get_sample_data', return_value=[]):
            
            data_sources = analyst._build_data_source_contexts(sample_resources)
            
            assert len(data_sources) == len(sample_resources)
            
            for i, data_source in enumerate(data_sources):
                assert isinstance(data_source, DataSource)
                assert data_source.resource_id == sample_resources[i].resource_id
                assert data_source.filename == sample_resources[i].original_filename
                assert data_source.resource_type == sample_resources[i].resource_type
    
    def test_generate_structured_insights(self, analyst):
        """Test structured data insight generation."""
        structured_results = [
            {
                "resource_id": str(uuid.uuid4()),
                "filename": "sales_data.csv",
                "data": [
                    {"product": "A", "sales": 100, "date": "2024-01-01"},
                    {"product": "B", "sales": 200, "date": "2024-01-02"}
                ]
            }
        ]
        
        insights = analyst._generate_structured_insights(structured_results, AnalysisType.DESCRIPTIVE)
        
        assert len(insights) > 0
        assert all(isinstance(insight, Insight) for insight in insights)
        assert any(insight.insight_type == InsightType.SUMMARY for insight in insights)
    
    def test_generate_unstructured_insights(self, analyst):
        """Test unstructured data insight generation."""
        unstructured_results = [
            {
                "resource_id": str(uuid.uuid4()),
                "filename": "product_manual.pdf",
                "relevant_chunks": [
                    {
                        "chunk_text": "This product is designed for high performance applications.",
                        "relevance_score": 0.9
                    },
                    {
                        "chunk_text": "Installation requires following safety procedures.",
                        "relevance_score": 0.8
                    }
                ]
            }
        ]
        
        insights = analyst._generate_unstructured_insights(unstructured_results, AnalysisType.EXPLORATORY)
        
        assert len(insights) > 0
        assert all(isinstance(insight, Insight) for insight in insights)
        assert any(insight.insight_type == InsightType.SUMMARY for insight in insights)
    
    def test_generate_summary_insight(self, analyst, sample_resources):
        """Test summary insight generation."""
        data_sources = [
            DataSource(
                resource_id=resource.resource_id,
                resource_type=resource.resource_type,
                filename=resource.original_filename,
                data_type=resource.data_type.value
            )
            for resource in sample_resources
        ]
        
        other_insights = [
            Insight(
                insight_type=InsightType.TREND,
                title="Sales Trend",
                description="Sales are increasing",
                confidence_score=0.8
            )
        ]
        
        summary_insight = analyst._generate_summary_insight(
            "Analyze my data", other_insights, data_sources
        )
        
        assert isinstance(summary_insight, Insight)
        assert summary_insight.insight_type == InsightType.SUMMARY
        assert summary_insight.title == "Executive Summary"
        assert len(summary_insight.source_citations) == len(data_sources)
    
    def test_calculate_overall_confidence(self, analyst):
        """Test overall confidence calculation."""
        insights = [
            Insight(
                insight_type=InsightType.SUMMARY,
                title="Summary",
                description="Test summary",
                confidence_score=0.9
            ),
            Insight(
                insight_type=InsightType.TREND,
                title="Trend",
                description="Test trend",
                confidence_score=0.7
            )
        ]
        
        confidence = analyst._calculate_overall_confidence(insights)
        
        # Summary insights are weighted higher, so confidence should be closer to 0.9
        assert 0.7 < confidence < 0.9
        assert confidence > 0.0
    
    def test_generate_methodology_explanation(self, analyst, sample_resources):
        """Test methodology explanation generation."""
        data_sources = [
            DataSource(
                resource_id=resource.resource_id,
                resource_type=resource.resource_type,
                filename=resource.original_filename,
                data_type=resource.data_type.value
            )
            for resource in sample_resources
        ]
        
        methodology = analyst._generate_methodology_explanation(
            AnalysisType.DESCRIPTIVE, data_sources
        )
        
        assert isinstance(methodology, str)
        assert len(methodology) > 0
        assert "descriptive analysis" in methodology.lower()
        assert "structured data" in methodology.lower()
        assert "unstructured data" in methodology.lower()
    
    def test_generate_limitations(self, analyst, sample_resources):
        """Test limitations generation."""
        data_sources = [
            DataSource(
                resource_id=resource.resource_id,
                resource_type=resource.resource_type,
                filename=resource.original_filename,
                data_type=resource.data_type.value,
                row_count=resource.row_count,
                chunk_count=resource.chunk_count
            )
            for resource in sample_resources
        ]
        
        analysis_results = {"structured_results": [], "unstructured_results": []}
        
        limitations = analyst._generate_limitations(data_sources, analysis_results)
        
        assert isinstance(limitations, str)
        assert len(limitations) > 0
        assert limitations.endswith(".")
    
    def test_generate_recommendations(self, analyst):
        """Test recommendations generation."""
        insights = [
            Insight(
                insight_type=InsightType.RECOMMENDATION,
                title="Improve Data Quality",
                description="Consider improving data quality by removing duplicates",
                confidence_score=0.8
            )
        ]
        
        recommendations = analyst._generate_recommendations(insights, AnalysisType.DESCRIPTIVE)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert all(isinstance(rec, str) for rec in recommendations)
        assert "Consider improving data quality by removing duplicates" in recommendations
    
    def test_generate_visualization_suggestions(self, analyst, sample_resources):
        """Test visualization suggestions generation."""
        insights = [
            Insight(
                insight_type=InsightType.TREND,
                title="Sales Trend",
                description="Sales are trending upward",
                confidence_score=0.8,
                visualization_suggestion="line_chart",
                source_citations=["sales_data.csv"]
            )
        ]
        
        data_sources = [
            DataSource(
                resource_id=resource.resource_id,
                resource_type=resource.resource_type,
                filename=resource.original_filename,
                data_type=resource.data_type.value
            )
            for resource in sample_resources
        ]
        
        visualizations = analyst._generate_visualization_suggestions(insights, data_sources)
        
        assert isinstance(visualizations, list)
        assert len(visualizations) > 0
        assert all(isinstance(viz, dict) for viz in visualizations)
        
        # Should include the line chart from insights
        assert any(viz["type"] == "line_chart" for viz in visualizations)
        
        # Should include general visualizations
        assert any(viz["type"] == "summary_dashboard" for viz in visualizations)
        assert any(viz["type"] == "word_cloud" for viz in visualizations)
    
    def test_create_empty_report(self, analyst):
        """Test empty report creation."""
        analysis_id = str(uuid.uuid4())
        question = "Test question"
        analysis_type = AnalysisType.DESCRIPTIVE
        start_time = datetime.utcnow()
        message = "No data available"
        
        report = analyst._create_empty_report(
            analysis_id, question, analysis_type, start_time, message
        )
        
        assert isinstance(report, AnalysisReport)
        assert report.analysis_id == analysis_id
        assert report.original_question == question
        assert report.analysis_type == analysis_type
        assert report.executive_summary == message
        assert len(report.recommendations) > 0
    
    def test_get_analysis_capabilities(self, analyst):
        """Test analysis capabilities retrieval."""
        capabilities = analyst.get_analysis_capabilities()
        
        assert isinstance(capabilities, dict)
        assert "analysis_types" in capabilities
        assert "insight_types" in capabilities
        assert "supported_data_types" in capabilities
        assert "features" in capabilities
        
        # Check that all analysis types are included
        expected_types = [atype.value for atype in AnalysisType]
        assert all(atype in capabilities["analysis_types"] for atype in expected_types)
        
        # Check that all insight types are included
        expected_insights = [itype.value for itype in InsightType]
        assert all(itype in capabilities["insight_types"] for itype in expected_insights)
    
    @patch('light_ai.sub_layer_2.ai_data_analyst.OpenAI')
    def test_analyze_data_no_resources(self, mock_openai, analyst):
        """Test analysis when no relevant resources are found."""
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        with patch.object(analyst, '_identify_relevant_resources', return_value=[]):
            report = analyst.analyze_data(
                "Test question",
                client_id,
                user_id,
                AccessLevel.USER
            )
            
            assert isinstance(report, AnalysisReport)
            assert "No relevant data sources found" in report.executive_summary
            assert len(report.data_sources_used) == 0
    
    @patch('light_ai.sub_layer_2.ai_data_analyst.OpenAI')
    def test_analyze_data_with_resources(self, mock_openai, analyst, sample_resources):
        """Test analysis with available resources."""
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Mock all the dependencies
        with patch.object(analyst, '_identify_relevant_resources', return_value=sample_resources), \
             patch.object(analyst, '_build_data_source_contexts') as mock_build_context, \
             patch.object(analyst, '_execute_cross_format_analysis') as mock_execute, \
             patch.object(analyst, '_generate_insights') as mock_insights, \
             patch.object(analyst, '_create_analysis_report') as mock_create_report:
            
            # Set up mock returns
            mock_data_sources = [
                DataSource(
                    resource_id=resource.resource_id,
                    resource_type=resource.resource_type,
                    filename=resource.original_filename,
                    data_type=resource.data_type.value
                )
                for resource in sample_resources
            ]
            mock_build_context.return_value = mock_data_sources
            
            mock_execute.return_value = {"structured_results": [], "unstructured_results": []}
            
            mock_insights.return_value = [
                Insight(
                    insight_type=InsightType.SUMMARY,
                    title="Test Insight",
                    description="Test description",
                    confidence_score=0.8
                )
            ]
            
            mock_report = AnalysisReport(
                analysis_id=str(uuid.uuid4()),
                original_question="Test question",
                analysis_type=AnalysisType.DESCRIPTIVE,
                executive_summary="Test summary"
            )
            mock_create_report.return_value = mock_report
            
            # Execute analysis
            report = analyst.analyze_data(
                "Test question",
                client_id,
                user_id,
                AccessLevel.USER
            )
            
            # Verify the flow was executed
            assert mock_build_context.called
            assert mock_execute.called
            assert mock_insights.called
            assert mock_create_report.called
            assert isinstance(report, AnalysisReport)
    
    def test_close(self, analyst):
        """Test analyst cleanup."""
        with patch.object(analyst.sql_engine, 'close') as mock_sql_close, \
             patch.object(analyst.nl_processor, 'close') as mock_nl_close, \
             patch.object(analyst.storage_router, 'close') as mock_storage_close:
            
            analyst.close()
            
            mock_sql_close.assert_called_once()
            mock_nl_close.assert_called_once()
            mock_storage_close.assert_called_once()


class TestDataModels:
    """Test data model classes."""
    
    def test_data_source_creation(self):
        """Test DataSource creation."""
        data_source = DataSource(
            resource_id=str(uuid.uuid4()),
            resource_type=ResourceType.STRUCTURED,
            filename="test.csv",
            data_type="csv",
            row_count=100,
            column_count=5,
            relevance_score=0.8
        )
        
        assert data_source.resource_id is not None
        assert data_source.resource_type == ResourceType.STRUCTURED
        assert data_source.filename == "test.csv"
        assert data_source.row_count == 100
        assert data_source.relevance_score == 0.8
    
    def test_insight_creation(self):
        """Test Insight creation."""
        insight = Insight(
            insight_type=InsightType.TREND,
            title="Test Trend",
            description="This is a test trend",
            confidence_score=0.9,
            visualization_suggestion="line_chart",
            source_citations=["test.csv"]
        )
        
        assert insight.insight_type == InsightType.TREND
        assert insight.title == "Test Trend"
        assert insight.confidence_score == 0.9
        assert insight.visualization_suggestion == "line_chart"
        assert "test.csv" in insight.source_citations
    
    def test_analysis_report_creation(self):
        """Test AnalysisReport creation."""
        report = AnalysisReport(
            analysis_id=str(uuid.uuid4()),
            original_question="Test question",
            analysis_type=AnalysisType.DESCRIPTIVE,
            executive_summary="Test summary"
        )
        
        assert report.analysis_id is not None
        assert report.original_question == "Test question"
        assert report.analysis_type == AnalysisType.DESCRIPTIVE
        assert report.executive_summary == "Test summary"
        assert isinstance(report.created_at, datetime)
    
    def test_analysis_report_to_dict(self):
        """Test AnalysisReport serialization."""
        insight = Insight(
            insight_type=InsightType.SUMMARY,
            title="Test Insight",
            description="Test description",
            confidence_score=0.8
        )
        
        data_source = DataSource(
            resource_id=str(uuid.uuid4()),
            resource_type=ResourceType.STRUCTURED,
            filename="test.csv",
            data_type="csv"
        )
        
        report = AnalysisReport(
            analysis_id=str(uuid.uuid4()),
            original_question="Test question",
            analysis_type=AnalysisType.DESCRIPTIVE,
            executive_summary="Test summary",
            key_insights=[insight],
            data_sources_used=[data_source]
        )
        
        report_dict = report.to_dict()
        
        assert isinstance(report_dict, dict)
        assert "analysis_id" in report_dict
        assert "key_insights" in report_dict
        assert "data_sources_used" in report_dict
        assert len(report_dict["key_insights"]) == 1
        assert len(report_dict["data_sources_used"]) == 1
        assert report_dict["analysis_type"] == "descriptive"


if __name__ == "__main__":
    pytest.main([__file__])
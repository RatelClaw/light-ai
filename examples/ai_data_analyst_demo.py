#!/usr/bin/env python3
"""
AI Data Analyst Demo for Universal Data Handler.

Demonstrates the comprehensive AI data analyst capabilities including:
- Automatic resource identification
- Cross-format data synthesis
- Report generation with insights
- Visualization suggestions
- Source citation and reasoning
"""

import json
import uuid
from pathlib import Path
from datetime import datetime

from light_ai.core.models import DataHierarchy, ResourceMetadata, ResourceType, DataType, AccessLevel
from light_ai.sub_layer_2.ai_data_analyst import AIDataAnalyst, AnalysisType
from light_ai.config import get_config
from light_ai.logger import get_logger

logger = get_logger(__name__)


def main():
    """Demonstrate AI data analyst capabilities."""
    print("🤖 AI Data Analyst Demo")
    print("=" * 50)
    
    try:
        # Initialize AI data analyst
        config = get_config()
        analyst = AIDataAnalyst(config)
        
        # Demo client and user IDs
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        print(f"Client ID: {client_id}")
        print(f"User ID: {user_id}")
        print()
        
        # Demo 1: Descriptive Analysis
        print("📊 Demo 1: Descriptive Analysis")
        print("-" * 30)
        
        descriptive_question = "What data do I have available and what are the key statistics?"
        
        print(f"Question: {descriptive_question}")
        print("Analyzing...")
        
        try:
            report = analyst.analyze_data(
                question=descriptive_question,
                client_id=client_id,
                user_id=user_id,
                access_level=AccessLevel.USER,
                analysis_type=AnalysisType.DESCRIPTIVE,
                include_visualizations=True
            )
            
            print_analysis_report(report)
            
        except Exception as e:
            print(f"❌ Descriptive analysis failed: {e}")
        
        print()
        
        # Demo 2: Diagnostic Analysis
        print("🔍 Demo 2: Diagnostic Analysis")
        print("-" * 30)
        
        diagnostic_question = "Why are there patterns in my sales data and what factors influence customer behavior?"
        
        print(f"Question: {diagnostic_question}")
        print("Analyzing...")
        
        try:
            report = analyst.analyze_data(
                question=diagnostic_question,
                client_id=client_id,
                user_id=user_id,
                access_level=AccessLevel.USER,
                analysis_type=AnalysisType.DIAGNOSTIC,
                include_visualizations=True
            )
            
            print_analysis_report(report)
            
        except Exception as e:
            print(f"❌ Diagnostic analysis failed: {e}")
        
        print()
        
        # Demo 3: Exploratory Analysis
        print("🔬 Demo 3: Exploratory Analysis")
        print("-" * 30)
        
        exploratory_question = "Find interesting patterns and insights across all my data sources"
        
        print(f"Question: {exploratory_question}")
        print("Analyzing...")
        
        try:
            report = analyst.analyze_data(
                question=exploratory_question,
                client_id=client_id,
                user_id=user_id,
                access_level=AccessLevel.USER,
                analysis_type=AnalysisType.EXPLORATORY,
                include_visualizations=True
            )
            
            print_analysis_report(report)
            
        except Exception as e:
            print(f"❌ Exploratory analysis failed: {e}")
        
        print()
        
        # Demo 4: Prescriptive Analysis
        print("💡 Demo 4: Prescriptive Analysis")
        print("-" * 30)
        
        prescriptive_question = "What actions should I take to improve my business performance based on the data?"
        
        print(f"Question: {prescriptive_question}")
        print("Analyzing...")
        
        try:
            report = analyst.analyze_data(
                question=prescriptive_question,
                client_id=client_id,
                user_id=user_id,
                access_level=AccessLevel.USER,
                analysis_type=AnalysisType.PRESCRIPTIVE,
                include_visualizations=True
            )
            
            print_analysis_report(report)
            
        except Exception as e:
            print(f"❌ Prescriptive analysis failed: {e}")
        
        print()
        
        # Demo 5: Auto-Detection Analysis
        print("🎯 Demo 5: Auto-Detection Analysis")
        print("-" * 30)
        
        auto_question = "Compare customer satisfaction scores with sales performance trends"
        
        print(f"Question: {auto_question}")
        print("Analyzing (auto-detecting analysis type)...")
        
        try:
            report = analyst.analyze_data(
                question=auto_question,
                client_id=client_id,
                user_id=user_id,
                access_level=AccessLevel.USER,
                # No analysis_type specified - will auto-detect
                include_visualizations=True
            )
            
            print_analysis_report(report)
            
        except Exception as e:
            print(f"❌ Auto-detection analysis failed: {e}")
        
        print()
        
        # Demo 6: Analysis Capabilities
        print("⚙️ Demo 6: Analysis Capabilities")
        print("-" * 30)
        
        capabilities = analyst.get_analysis_capabilities()
        print("AI Data Analyst Capabilities:")
        print(json.dumps(capabilities, indent=2))
        
        print()
        
        # Demo 7: Complex Multi-Source Analysis
        print("🌐 Demo 7: Complex Multi-Source Analysis")
        print("-" * 30)
        
        complex_question = """
        Analyze the relationship between our product documentation quality, 
        customer support tickets, and sales conversion rates. Identify areas 
        where improving documentation could reduce support burden and increase sales.
        """
        
        print(f"Question: {complex_question.strip()}")
        print("Analyzing across multiple data sources...")
        
        try:
            report = analyst.analyze_data(
                question=complex_question.strip(),
                client_id=client_id,
                user_id=user_id,
                access_level=AccessLevel.MANAGER,  # Manager level for broader access
                include_visualizations=True
            )
            
            print_analysis_report(report)
            
        except Exception as e:
            print(f"❌ Complex analysis failed: {e}")
        
        # Clean up
        analyst.close()
        
        print("\n✅ AI Data Analyst demo completed successfully!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"❌ Demo failed: {e}")


def print_analysis_report(report):
    """Print a formatted analysis report."""
    print(f"📋 Analysis Report")
    print(f"Analysis ID: {report.analysis_id}")
    print(f"Analysis Type: {report.analysis_type.value.title()}")
    print(f"Execution Time: {report.execution_time_ms:.1f}ms")
    print(f"Confidence Score: {report.confidence_score:.2f}")
    print()
    
    print("📝 Executive Summary:")
    print(f"   {report.executive_summary}")
    print()
    
    if report.data_sources_used:
        print(f"📊 Data Sources Used ({len(report.data_sources_used)}):")
        for i, source in enumerate(report.data_sources_used, 1):
            print(f"   {i}. {source.filename} ({source.resource_type.value})")
            if source.row_count:
                print(f"      - {source.row_count:,} rows, {source.column_count} columns")
            elif source.chunk_count:
                print(f"      - {source.chunk_count} text chunks")
        print()
    
    if report.key_insights:
        print(f"💡 Key Insights ({len(report.key_insights)}):")
        for i, insight in enumerate(report.key_insights, 1):
            print(f"   {i}. {insight.title} ({insight.insight_type.value})")
            print(f"      {insight.description}")
            print(f"      Confidence: {insight.confidence_score:.2f}")
            if insight.source_citations:
                print(f"      Sources: {', '.join(insight.source_citations)}")
            if insight.visualization_suggestion:
                print(f"      Visualization: {insight.visualization_suggestion}")
            print()
    
    if report.methodology:
        print("🔬 Methodology:")
        print(f"   {report.methodology}")
        print()
    
    if report.limitations:
        print("⚠️ Limitations:")
        print(f"   {report.limitations}")
        print()
    
    if report.recommendations:
        print(f"🎯 Recommendations ({len(report.recommendations)}):")
        for i, rec in enumerate(report.recommendations, 1):
            print(f"   {i}. {rec}")
        print()
    
    if report.visualizations:
        print(f"📈 Visualization Suggestions ({len(report.visualizations)}):")
        for i, viz in enumerate(report.visualizations, 1):
            print(f"   {i}. {viz['title']} ({viz['type']})")
            print(f"      {viz['description']}")
            print(f"      Data Source: {viz['data_source']}")
        print()
    
    print("-" * 50)


def demo_with_sample_data():
    """Demo with sample data if available."""
    print("\n🗂️ Checking for sample data...")
    
    # Check if sample data exists
    sample_data_dir = Path("examples/data_sub_layer_1")
    if not sample_data_dir.exists():
        print("No sample data directory found. Run sub_layer_1_load.py first to create sample data.")
        return
    
    sample_files = list(sample_data_dir.glob("*"))
    if not sample_files:
        print("No sample files found. Run sub_layer_1_load.py first to create sample data.")
        return
    
    print(f"Found {len(sample_files)} sample files:")
    for file in sample_files:
        print(f"  - {file.name}")
    
    print("\nNote: To see the AI Data Analyst work with real data, first run:")
    print("  python examples/sub_layer_1_load.py")
    print("This will upload sample data that the analyst can then analyze.")


if __name__ == "__main__":
    main()
    demo_with_sample_data()
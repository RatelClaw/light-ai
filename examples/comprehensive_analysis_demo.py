#!/usr/bin/env python3
"""
Comprehensive Data Analysis Engine Demo

This demo showcases the comprehensive data analysis capabilities including:
- Automated trend and pattern detection
- Statistical analysis and correlation finding
- Anomaly detection and alerting system
- Predictive analytics capabilities
- Comprehensive report generation with insights

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from light_ai.config import get_config
from light_ai.sub_layer_2.comprehensive_analysis_engine import ComprehensiveAnalysisEngine
from light_ai.core.models import AccessLevel
from light_ai.sub_layer_1.file_upload import FileUploadAPI
from light_ai.logger import get_logger

logger = get_logger(__name__)


async def create_sample_data():
    """Create sample data for comprehensive analysis demonstration."""
    print("📊 Creating sample data for comprehensive analysis...")
    
    config = get_config()
    upload_manager = FileUploadAPI(config)
    upload_manager.initialize()
    
    # Sample time series data with trends, seasonality, and anomalies
    import pandas as pd
    import numpy as np
    
    # Generate sample sales data with trends and seasonality
    dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')
    np.random.seed(42)
    
    # Base trend (increasing)
    trend = np.linspace(1000, 2000, len(dates))
    
    # Seasonal pattern (weekly and monthly)
    seasonal_weekly = 100 * np.sin(2 * np.pi * np.arange(len(dates)) / 7)
    seasonal_monthly = 200 * np.sin(2 * np.pi * np.arange(len(dates)) / 30)
    
    # Random noise
    noise = np.random.normal(0, 50, len(dates))
    
    # Combine components
    sales = trend + seasonal_weekly + seasonal_monthly + noise
    
    # Add some anomalies
    anomaly_indices = np.random.choice(len(dates), size=10, replace=False)
    sales[anomaly_indices] += np.random.choice([-500, 500], size=10)
    
    # Create correlated variables
    marketing_spend = sales * 0.1 + np.random.normal(0, 20, len(dates))
    customer_satisfaction = 85 + (sales - sales.mean()) / sales.std() * 5 + np.random.normal(0, 2, len(dates))
    
    # Create DataFrame
    sample_data = pd.DataFrame({
        'date': dates,
        'sales_amount': sales,
        'marketing_spend': marketing_spend,
        'customer_satisfaction': customer_satisfaction,
        'region': np.random.choice(['North', 'South', 'East', 'West'], len(dates)),
        'product_category': np.random.choice(['Electronics', 'Clothing', 'Books', 'Home'], len(dates))
    })
    
    # Save to CSV
    sample_file = project_root / "temp" / "comprehensive_analysis_sample.csv"
    sample_file.parent.mkdir(exist_ok=True)
    sample_data.to_csv(sample_file, index=False)
    
    # Upload the sample data
    try:
        result = upload_manager.upload_file(
            file_path=str(sample_file),
            client_id="demo-client",
            user_id="demo-user",
            original_filename="comprehensive_analysis_sample.csv"
        )
        
        if result.success:
            print(f"✅ Sample data uploaded successfully: {result.resource_id}")
            return result.resource_id
        else:
            print(f"❌ Failed to upload sample data: {result.message}")
            return None
            
    except Exception as e:
        print(f"❌ Error uploading sample data: {e}")
        return None
    finally:
        upload_manager.close()


async def demonstrate_comprehensive_analysis():
    """Demonstrate comprehensive data analysis capabilities."""
    print("\n🔍 Comprehensive Data Analysis Engine Demo")
    print("=" * 60)
    
    # Initialize the analysis engine
    config = get_config()
    analysis_engine = ComprehensiveAnalysisEngine(config)
    
    try:
        # Create sample data
        resource_id = await create_sample_data()
        if not resource_id:
            print("❌ Cannot proceed without sample data")
            return
        
        print(f"\n📈 Starting comprehensive analysis...")
        
        # Test different types of analysis queries
        test_queries = [
            {
                "query": "Analyze sales trends and patterns over time",
                "description": "Trend Analysis and Pattern Detection"
            },
            {
                "query": "Find correlations between sales, marketing spend, and customer satisfaction",
                "description": "Correlation Analysis"
            },
            {
                "query": "Detect anomalies in sales data and predict future sales",
                "description": "Anomaly Detection and Predictive Analytics"
            },
            {
                "query": "Comprehensive statistical analysis of all business metrics",
                "description": "Complete Statistical Analysis"
            }
        ]
        
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n📊 Test {i}: {test_case['description']}")
            print("-" * 50)
            
            try:
                # Perform comprehensive analysis
                report = await analysis_engine.analyze_comprehensive(
                    query=test_case["query"],
                    client_id="demo-client",
                    user_id="demo-user",
                    access_level=AccessLevel.USER,
                    include_predictions=True,
                    include_anomalies=True,
                    forecast_horizon=30
                )
                
                # Display results
                print(f"Analysis ID: {report.analysis_id}")
                print(f"Execution Time: {report.execution_time_ms:.2f}ms")
                print(f"Confidence Score: {report.confidence_score:.3f}")
                print(f"Data Sources: {', '.join(report.data_sources)}")
                
                print(f"\n📋 Executive Summary:")
                print(f"   {report.executive_summary}")
                
                if report.statistical_summaries:
                    print(f"\n📊 Statistical Analysis:")
                    for summary in report.statistical_summaries[:3]:  # Show first 3
                        print(f"   • {summary.variable_name}: mean={summary.mean:.2f}, std={summary.std_dev:.2f}")
                
                if report.trend_analyses:
                    print(f"\n📈 Trend Analysis:")
                    for trend in report.trend_analyses[:3]:  # Show first 3
                        print(f"   • {trend.description} (confidence: {trend.confidence:.3f})")
                
                if report.correlation_analyses:
                    print(f"\n🔗 Correlation Analysis:")
                    for corr in report.correlation_analyses[:3]:  # Show first 3
                        print(f"   • {corr.description} (r={corr.correlation_coefficient:.3f})")
                
                if report.anomaly_detections:
                    print(f"\n⚠️  Anomaly Detection:")
                    for anomaly in report.anomaly_detections[:3]:  # Show first 3
                        print(f"   • {anomaly.description} (confidence: {anomaly.confidence:.3f})")
                
                if report.predictive_analyses:
                    print(f"\n🔮 Predictive Analytics:")
                    for prediction in report.predictive_analyses[:2]:  # Show first 2
                        print(f"   • {prediction.description}")
                        if prediction.model_accuracy:
                            print(f"     Model Accuracy: {prediction.model_accuracy:.3f}")
                        print(f"     Forecast Horizon: {prediction.forecast_horizon} periods")
                
                if report.key_insights:
                    print(f"\n💡 Key Insights:")
                    for insight in report.key_insights[:5]:  # Show first 5
                        print(f"   • {insight}")
                
                if report.recommendations:
                    print(f"\n🎯 Recommendations:")
                    for rec in report.recommendations[:3]:  # Show first 3
                        print(f"   • {rec}")
                
                print(f"\n📝 Methodology: {report.methodology}")
                
                if report.limitations:
                    print(f"\n⚠️  Limitations:")
                    for limitation in report.limitations:
                        print(f"   • {limitation}")
                
                # Save detailed report
                report_file = project_root / "temp" / f"analysis_report_{i}.json"
                with open(report_file, 'w') as f:
                    json.dump(report.to_dict(), f, indent=2, default=str)
                print(f"\n💾 Detailed report saved to: {report_file}")
                
            except Exception as e:
                print(f"❌ Analysis failed: {e}")
                logger.error(f"Comprehensive analysis failed for test {i}: {e}")
        
        # Demonstrate analysis capabilities
        print(f"\n🛠️  Analysis Engine Capabilities:")
        capabilities = analysis_engine.get_analysis_capabilities()
        for key, value in capabilities.items():
            if isinstance(value, list):
                print(f"   • {key}: {', '.join(value)}")
            else:
                print(f"   • {key}: {value}")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        logger.error(f"Comprehensive analysis demo failed: {e}")
    
    finally:
        analysis_engine.close()


async def demonstrate_real_time_insights():
    """Demonstrate real-time insights and monitoring capabilities."""
    print(f"\n🔄 Real-Time Insights Demo")
    print("-" * 40)
    
    config = get_config()
    analysis_engine = ComprehensiveAnalysisEngine(config)
    
    try:
        # Simulate continuous monitoring
        print("🔍 Simulating continuous data monitoring...")
        
        queries = [
            "Monitor for sudden changes in sales patterns",
            "Track correlation changes between marketing and sales",
            "Detect emerging trends in customer satisfaction"
        ]
        
        for query in queries:
            print(f"\n📊 Monitoring: {query}")
            
            report = await analysis_engine.analyze_comprehensive(
                query=query,
                client_id="demo-client",
                user_id="demo-user",
                access_level=AccessLevel.USER,
                include_predictions=False,  # Focus on current state
                include_anomalies=True,
                forecast_horizon=7  # Short-term monitoring
            )
            
            print(f"   Status: {report.executive_summary}")
            
            if report.anomaly_detections:
                print(f"   🚨 Alerts: {len(report.anomaly_detections)} anomalies detected")
            else:
                print(f"   ✅ No anomalies detected")
        
    except Exception as e:
        print(f"❌ Real-time monitoring demo failed: {e}")
    
    finally:
        analysis_engine.close()


async def main():
    """Main demo function."""
    print("🚀 Starting Comprehensive Data Analysis Engine Demo")
    print("=" * 60)
    
    try:
        # Run comprehensive analysis demonstration
        await demonstrate_comprehensive_analysis()
        
        # Run real-time insights demonstration
        await demonstrate_real_time_insights()
        
        print(f"\n✅ Comprehensive Data Analysis Engine Demo completed successfully!")
        print("\nKey Features Demonstrated:")
        print("• Automated trend and pattern detection")
        print("• Statistical analysis and correlation finding")
        print("• Anomaly detection and alerting system")
        print("• Predictive analytics capabilities")
        print("• Comprehensive report generation with insights")
        print("• Real-time monitoring and insights")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        logger.error(f"Comprehensive analysis demo failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
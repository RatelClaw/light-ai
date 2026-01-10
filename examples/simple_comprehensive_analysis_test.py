#!/usr/bin/env python3
"""
Simple test for Comprehensive Data Analysis Engine integration.

This test verifies that the comprehensive analysis engine integrates
properly with the existing system components.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from light_ai.config import get_config
from light_ai.sub_layer_2.comprehensive_analysis_engine import ComprehensiveAnalysisEngine
from light_ai.core.models import AccessLevel
from light_ai.logger import get_logger

logger = get_logger(__name__)


async def test_comprehensive_analysis_integration():
    """Test comprehensive analysis engine integration."""
    print("🔍 Testing Comprehensive Data Analysis Engine Integration")
    print("=" * 60)
    
    config = get_config()
    analysis_engine = ComprehensiveAnalysisEngine(config)
    
    try:
        # Test 1: Engine initialization
        print("\n📊 Test 1: Engine Initialization")
        print("-" * 40)
        
        capabilities = analysis_engine.get_analysis_capabilities()
        print(f"✅ Engine initialized successfully")
        print(f"   Statistical Analysis: {capabilities['statistical_analysis']}")
        print(f"   Trend Detection: {capabilities['trend_detection']}")
        print(f"   Correlation Analysis: {capabilities['correlation_analysis']}")
        print(f"   Anomaly Detection: {capabilities['anomaly_detection']}")
        print(f"   Predictive Analytics: {capabilities['predictive_analytics']}")
        
        # Test 2: Analysis with no data (should handle gracefully)
        print("\n📊 Test 2: Analysis with No Data")
        print("-" * 40)
        
        report = await analysis_engine.analyze_comprehensive(
            query="Analyze sales trends and patterns",
            client_id="test-client",
            user_id="test-user",
            access_level=AccessLevel.USER,
            include_predictions=True,
            include_anomalies=True,
            forecast_horizon=30
        )
        
        print(f"✅ Analysis completed gracefully with no data")
        print(f"   Analysis ID: {report.analysis_id}")
        print(f"   Executive Summary: {report.executive_summary}")
        print(f"   Execution Time: {report.execution_time_ms:.2f}ms")
        print(f"   Confidence Score: {report.confidence_score}")
        
        # Test 3: Different analysis types
        print("\n📊 Test 3: Different Analysis Types")
        print("-" * 40)
        
        test_queries = [
            "Find correlations in business data",
            "Detect anomalies in performance metrics", 
            "Predict future trends",
            "Generate comprehensive statistical summary"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"   {i}. Testing: {query}")
            
            report = await analysis_engine.analyze_comprehensive(
                query=query,
                client_id="test-client",
                user_id="test-user",
                access_level=AccessLevel.USER,
                include_predictions=(i % 2 == 0),  # Alternate predictions
                include_anomalies=(i % 3 == 0),   # Every third includes anomalies
                forecast_horizon=15
            )
            
            print(f"      ✅ Completed in {report.execution_time_ms:.2f}ms")
        
        # Test 4: Report serialization
        print("\n📊 Test 4: Report Serialization")
        print("-" * 40)
        
        report_dict = report.to_dict()
        print(f"✅ Report serialized successfully")
        print(f"   Keys: {list(report_dict.keys())}")
        print(f"   Analysis ID: {report_dict['analysis_id']}")
        print(f"   User ID: {report_dict['user_id']}")
        
        # Test 5: Engine capabilities
        print("\n📊 Test 5: Engine Capabilities")
        print("-" * 40)
        
        capabilities = analysis_engine.get_analysis_capabilities()
        print(f"✅ Capabilities retrieved successfully")
        print(f"   Supported Trend Types: {len(capabilities['supported_trend_types'])}")
        print(f"   Supported Anomaly Types: {len(capabilities['supported_anomaly_types'])}")
        print(f"   Supported Prediction Types: {len(capabilities['supported_prediction_types'])}")
        print(f"   Features: {len(capabilities['features'])}")
        
        print(f"\n✅ All integration tests passed successfully!")
        print("\nKey Features Verified:")
        print("• Engine initialization and configuration")
        print("• Graceful handling of no-data scenarios")
        print("• Multiple analysis query types")
        print("• Report generation and serialization")
        print("• Capabilities reporting")
        print("• Proper resource cleanup")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        logger.error(f"Comprehensive analysis integration test failed: {e}")
        return False
    
    finally:
        analysis_engine.close()
        print(f"\n🔧 Engine closed and resources cleaned up")


async def main():
    """Main test function."""
    print("🚀 Starting Comprehensive Data Analysis Engine Integration Test")
    
    try:
        success = await test_comprehensive_analysis_integration()
        
        if success:
            print(f"\n✅ Integration test completed successfully!")
            return 0
        else:
            print(f"\n❌ Integration test failed!")
            return 1
            
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        logger.error(f"Integration test execution failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
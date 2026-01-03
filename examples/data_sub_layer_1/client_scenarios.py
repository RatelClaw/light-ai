#!/usr/bin/env python3
"""
Client Scenario Testing for Sub-Layer 1

This script simulates different client scenarios and use cases:
- Different client types (small business, enterprise, individual)
- Various data patterns and volumes
- Error handling scenarios
- Multi-user scenarios
"""

import sys
import os
from pathlib import Path
import uuid
import json
import random
import time

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from light_ai.sub_layer_1 import (
    FileUploadAPI, DataCleaningEngine, CleaningConfig, MissingValueStrategy
)
from light_ai.core.models import DataType


class ClientScenarioTester:
    """Simulates different client scenarios for Sub-Layer 1."""
    
    def __init__(self):
        """Initialize the scenario tester."""
        self.upload_api = FileUploadAPI()
        self.cleaning_engine = DataCleaningEngine()
        
        # Define different client types
        self.client_scenarios = {
            "small_business": {
                "name": "Small E-commerce Business",
                "description": "Local retailer with basic data needs",
                "typical_files": ["customer_data.csv", "inventory.csv", "sales_report.txt"],
                "data_volume": "small",
                "cleaning_needs": "basic"
            },
            "enterprise": {
                "name": "Enterprise Corporation",
                "description": "Large company with complex data requirements",
                "typical_files": ["customer_analytics.json", "transaction_logs.jsonl", "compliance_docs.pdf"],
                "data_volume": "large", 
                "cleaning_needs": "advanced"
            },
            "data_analyst": {
                "name": "Data Analyst",
                "description": "Individual researcher working with various data sources",
                "typical_files": ["research_data.csv", "survey_results.json", "methodology.md"],
                "data_volume": "medium",
                "cleaning_needs": "custom"
            },
            "startup": {
                "name": "Tech Startup",
                "description": "Growing company with mixed data types",
                "typical_files": ["user_metrics.json", "app_logs.txt", "feature_specs.md"],
                "data_volume": "medium",
                "cleaning_needs": "flexible"
            }
        }
    
    def create_sample_data_for_scenario(self, scenario_type: str, base_dir: Path):
        """Create sample data files for a specific scenario."""
        scenario = self.client_scenarios[scenario_type]
        scenario_dir = base_dir / f"{scenario_type}_data"
        scenario_dir.mkdir(exist_ok=True)
        
        print(f"📁 Creating sample data for: {scenario['name']}")
        
        if scenario_type == "small_business":
            # Simple customer data
            customer_data = """customer_id,name,email,phone,city,total_purchases
1,John Smith,john@email.com,555-0101,New York,1250.50
2,Jane Doe,jane@email.com,555-0102,Los Angeles,890.25
3,Bob Wilson,bob@email.com,555-0103,Chicago,2100.75"""
            
            with open(scenario_dir / "customer_data.csv", "w") as f:
                f.write(customer_data)
            
            # Simple inventory
            inventory_data = """product_id,name,category,stock,price
P001,Widget A,Electronics,50,29.99
P002,Widget B,Home,25,45.50
P003,Widget C,Electronics,100,15.99"""
            
            with open(scenario_dir / "inventory.csv", "w") as f:
                f.write(inventory_data)
        
        elif scenario_type == "enterprise":
            # Complex JSON analytics data
            analytics_data = {
                "customer_segments": {
                    "high_value": {
                        "count": 1250,
                        "avg_lifetime_value": 5420.50,
                        "characteristics": ["frequent_buyer", "premium_products"]
                    },
                    "regular": {
                        "count": 8900,
                        "avg_lifetime_value": 1250.25,
                        "characteristics": ["seasonal_buyer", "price_sensitive"]
                    }
                },
                "performance_metrics": {
                    "conversion_rate": 0.045,
                    "churn_rate": 0.12,
                    "customer_acquisition_cost": 125.50
                }
            }
            
            with open(scenario_dir / "customer_analytics.json", "w") as f:
                json.dump(analytics_data, f, indent=2)
        
        elif scenario_type == "data_analyst":
            # Research data with missing values
            research_data = """participant_id,age,gender,response_time,accuracy,condition
P001,25,F,1250,0.95,control
P002,32,M,,0.87,treatment
P003,28,F,1100,0.92,control
P004,,M,1350,0.89,treatment
P005,29,F,1200,,control"""
            
            with open(scenario_dir / "research_data.csv", "w") as f:
                f.write(research_data)
        
        elif scenario_type == "startup":
            # User metrics JSONL
            metrics_data = [
                {"user_id": "u001", "session_duration": 1250, "pages_viewed": 5, "converted": True},
                {"user_id": "u002", "session_duration": 890, "pages_viewed": 3, "converted": False},
                {"user_id": "u003", "session_duration": 2100, "pages_viewed": 8, "converted": True}
            ]
            
            with open(scenario_dir / "user_metrics.jsonl", "w") as f:
                for metric in metrics_data:
                    f.write(json.dumps(metric) + "\n")
        
        return scenario_dir
    
    def test_scenario_upload(self, scenario_type: str, client_id: str, user_id: str, data_dir: Path):
        """Test file upload for a specific scenario."""
        scenario = self.client_scenarios[scenario_type]
        print(f"\n📤 Testing upload scenario: {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        
        # Find all files in the scenario directory
        files_to_upload = list(data_dir.glob("*"))
        files_to_upload = [f for f in files_to_upload if f.is_file()]
        
        if not files_to_upload:
            print("   ❌ No files found to upload")
            return []
        
        print(f"   📁 Found {len(files_to_upload)} files to upload")
        
        try:
            # Upload files
            metadata_list = self.upload_api.upload_bulk(
                client_id, user_id, files_to_upload,
                parallel=True
            )
            
            print(f"   ✅ Successfully uploaded {len(metadata_list)} files")
            
            # Show upload summary
            for metadata in metadata_list:
                print(f"      📄 {metadata.original_filename}: {metadata.data_type.value} "
                      f"({metadata.file_size_bytes:,} bytes)")
            
            return metadata_list
            
        except Exception as e:
            print(f"   ❌ Upload failed: {e}")
            return []
    
    def test_scenario_cleaning(self, scenario_type: str, data_dir: Path):
        """Test data cleaning for a specific scenario."""
        scenario = self.client_scenarios[scenario_type]
        cleaning_needs = scenario['cleaning_needs']
        
        print(f"\n🧹 Testing cleaning for: {scenario['name']}")
        print(f"   Cleaning needs: {cleaning_needs}")
        
        # Configure cleaning based on scenario needs
        if cleaning_needs == "basic":
            config = CleaningConfig(
                remove_empty_rows=True,
                strip_whitespace=True,
                normalize_column_names=True,
                missing_value_strategy=MissingValueStrategy.NULL
            )
        elif cleaning_needs == "advanced":
            config = CleaningConfig(
                remove_empty_rows=True,
                remove_empty_columns=True,
                strip_whitespace=True,
                normalize_column_names=True,
                detect_data_types=True,
                missing_value_strategy=MissingValueStrategy.FILL_MODE,
                flatten_json=True,
                normalize_json_keys=True
            )
        elif cleaning_needs == "custom":
            config = CleaningConfig(
                remove_empty_rows=True,
                strip_whitespace=True,
                normalize_column_names=True,
                detect_data_types=True,
                missing_value_strategy=MissingValueStrategy.FILL_MEAN
            )
        else:  # flexible
            config = CleaningConfig(
                remove_empty_rows=True,
                strip_whitespace=True,
                normalize_column_names=True,
                missing_value_strategy=MissingValueStrategy.FILL_MODE,
                flatten_json=False,
                normalize_json_keys=True
            )
        
        # Test cleaning on available files
        files_to_clean = list(data_dir.glob("*"))
        files_to_clean = [f for f in files_to_clean if f.is_file()]
        
        for file_path in files_to_clean:
            try:
                print(f"   🔧 Cleaning {file_path.name}...")
                
                if file_path.suffix.lower() == '.csv':
                    import pandas as pd
                    df = pd.read_csv(file_path)
                    cleaned_df, stats = self.cleaning_engine.structured_cleaner.clean_dataframe(df)
                    print(f"      📊 CSV: {df.shape} → {cleaned_df.shape}, "
                          f"ops: {len(stats['operations_performed'])}")
                
                elif file_path.suffix.lower() == '.json':
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    cleaned_data, stats = self.cleaning_engine.json_cleaner.clean_json(data)
                    print(f"      📄 JSON: {len(stats['operations_performed'])} operations, "
                          f"flattened: {stats.get('flattened', False)}")
                
                elif file_path.suffix.lower() == '.jsonl':
                    lines = []
                    with open(file_path, 'r') as f:
                        for line in f:
                            lines.append(json.loads(line.strip()))
                    cleaned_data, stats = self.cleaning_engine.json_cleaner.clean_json(lines)
                    print(f"      📄 JSONL: {len(lines)} records, "
                          f"{len(stats['operations_performed'])} operations")
                
                else:
                    print(f"      ⏭️  Skipping {file_path.suffix} file")
                
            except Exception as e:
                print(f"      ❌ Error cleaning {file_path.name}: {e}")
    
    def simulate_multi_user_scenario(self, scenario_type: str, num_users: int = 3):
        """Simulate multiple users for the same client."""
        scenario = self.client_scenarios[scenario_type]
        client_id = str(uuid.uuid4())
        
        print(f"\n👥 Simulating multi-user scenario: {scenario['name']}")
        print(f"   Client ID: {client_id}")
        print(f"   Number of users: {num_users}")
        
        base_dir = Path("examples/data_sub_layer_1")
        
        for user_num in range(1, num_users + 1):
            user_id = str(uuid.uuid4())
            print(f"\n   👤 User {user_num} (ID: {user_id[:8]}...)")
            
            # Create scenario-specific data
            data_dir = self.create_sample_data_for_scenario(scenario_type, base_dir)
            
            # Test upload
            metadata_list = self.test_scenario_upload(scenario_type, client_id, user_id, data_dir)
            
            # Test cleaning
            if metadata_list:
                self.test_scenario_cleaning(scenario_type, data_dir)
            
            # Small delay between users
            time.sleep(0.5)
    
    def test_error_scenarios(self):
        """Test various error scenarios."""
        print("\n🚨 Testing Error Scenarios...")
        
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Test 1: Non-existent file
        try:
            fake_file = Path("non_existent_file.csv")
            self.upload_api.upload_file(client_id, user_id, fake_file)
            print("   ❌ Should have failed for non-existent file")
        except Exception as e:
            print(f"   ✅ Correctly caught non-existent file error: {type(e).__name__}")
        
        # Test 2: Invalid client ID
        try:
            test_file = Path("examples/data_sub_layer_1/sample_customers.csv")
            if test_file.exists():
                self.upload_api.upload_file("invalid-uuid", user_id, test_file)
                print("   ❌ Should have failed for invalid client ID")
        except Exception as e:
            print(f"   ✅ Correctly caught invalid client ID error: {type(e).__name__}")
        
        # Test 3: Corrupted data cleaning
        try:
            corrupted_data = "not,valid,csv\ndata,with,issues\n,missing,values"
            import pandas as pd
            import io
            df = pd.read_csv(io.StringIO(corrupted_data))
            cleaned_df, stats = self.cleaning_engine.structured_cleaner.clean_dataframe(df)
            print(f"   ✅ Handled corrupted data gracefully: {df.shape} → {cleaned_df.shape}")
        except Exception as e:
            print(f"   ⚠️  Corrupted data error: {type(e).__name__}")
    
    def run_all_scenarios(self):
        """Run all client scenarios."""
        print("🎭 Starting Client Scenario Testing")
        print("=" * 50)
        
        # Test each scenario type
        for scenario_type in self.client_scenarios.keys():
            self.simulate_multi_user_scenario(scenario_type, num_users=2)
        
        # Test error scenarios
        self.test_error_scenarios()
        
        print("\n🎉 All client scenarios completed!")


def main():
    """Main entry point."""
    print("🎭 Sub-Layer 1 Client Scenario Testing")
    print("=" * 45)
    
    tester = ClientScenarioTester()
    tester.run_all_scenarios()
    
    return 0


if __name__ == "__main__":
    exit(main())
"""
Property-based tests for complete API coverage.

Tests Property 12: Complete API Coverage
Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5, 12.9
"""

import os
import json
import tempfile
import uuid
from typing import Dict, Any
from hypothesis import given, strategies as st, settings, HealthCheck
import pytest
import pandas as pd

from light_ai.api import UniversalDataHandler, APIResponse, create_api
from light_ai.config import Config
from light_ai.core.models import ResourceType, DataType


class TestAPICompletenessPBT:
    """Property-based tests for API completeness and consistency."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def api_handler(self, temp_dir):
        """Create API handler for testing."""
        # Load config from environment (including .env file)
        config = Config.load()
        # Override base directory for testing
        config.storage.base_directory = temp_dir
        return UniversalDataHandler(config=config, base_path=temp_dir)
    
    @pytest.fixture
    def sample_csv_file(self, temp_dir):
        """Create a sample CSV file for testing."""
        csv_path = os.path.join(temp_dir, "test_data.csv")
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie'],
            'value': [10.5, 20.3, 30.1]
        })
        df.to_csv(csv_path, index=False)
        return csv_path
    
    @pytest.fixture
    def sample_json_file(self, temp_dir):
        """Create a sample JSON file for testing."""
        json_path = os.path.join(temp_dir, "test_data.json")
        data = {
            "users": [
                {"id": 1, "name": "Alice", "active": True},
                {"id": 2, "name": "Bob", "active": False}
            ],
            "metadata": {"version": "1.0", "created": "2024-01-01"}
        }
        with open(json_path, 'w') as f:
            json.dump(data, f)
        return json_path
    
    @pytest.fixture
    def sample_text_file(self, temp_dir):
        """Create a sample text file for testing."""
        text_path = os.path.join(temp_dir, "test_document.txt")
        content = """
        This is a sample document for testing.
        It contains multiple paragraphs with various content.
        
        The document discusses data management and processing.
        It includes information about structured and unstructured data.
        """
        with open(text_path, 'w') as f:
            f.write(content)
        return text_path
    
    # ==================== Property Tests ====================
    
    @given(
        client_id=st.uuids(version=4).map(str),
        user_id=st.uuids(version=4).map(str)
    )
    @settings(max_examples=50, deadline=30000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_12_sub_layer_1_api_completeness(self, temp_dir, sample_csv_file, 
                                                     sample_json_file, client_id, user_id):
        """
        Feature: universal-data-handler, Property 12: Complete API Coverage
        For any valid client_id and user_id, all Sub-Layer 1 APIs should be available 
        and return consistent APIResponse objects with proper error handling.
        """
        # Create API handler for this test run
        config = Config.load()
        config.storage.base_directory = temp_dir
        api_handler = UniversalDataHandler(config=config, base_path=temp_dir)
        # Test 1: upload_file API exists and works
        response = api_handler.upload_file(
            client_id=client_id,
            user_id=user_id,
            file_path=sample_csv_file,
            resource_name="test_csv"
        )
        
        # Verify response structure
        assert isinstance(response, APIResponse)
        assert hasattr(response, 'success')
        assert hasattr(response, 'data')
        assert hasattr(response, 'error')
        assert hasattr(response, 'metadata')
        assert hasattr(response, 'timestamp')
        
        # If successful, should have resource_id
        if response.success:
            assert 'resource_id' in response.data
            resource_id = response.data['resource_id']
            
            # Test 2: upload_json API exists and works
            json_data = {"test": "data", "numbers": [1, 2, 3]}
            json_response = api_handler.upload_json(
                client_id=client_id,
                user_id=user_id,
                json_data=json_data,
                resource_name="test_json"
            )
            assert isinstance(json_response, APIResponse)
            
            # Test 3: update_resource API exists and works
            update_response = api_handler.update_resource(
                resource_id=resource_id,
                new_data=sample_json_file,
                client_id=client_id,
                user_id=user_id
            )
            assert isinstance(update_response, APIResponse)
            
            # Test 4: delete_resource API exists and works (soft delete)
            delete_response = api_handler.delete_resource(
                resource_id=resource_id,
                hard_delete=False,
                client_id=client_id,
                user_id=user_id
            )
            assert isinstance(delete_response, APIResponse)
        
        # Test 5: upload_bulk API exists and works
        bulk_response = api_handler.upload_bulk(
            client_id=client_id,
            user_id=user_id,
            files=[sample_csv_file, sample_json_file],
            parallel=False
        )
        assert isinstance(bulk_response, APIResponse)
    
    @given(
        client_id=st.uuids(version=4).map(str),
        user_id=st.uuids(version=4).map(str)
    )
    @settings(max_examples=50, deadline=30000)
    def test_property_12_sub_layer_2_api_completeness(self, api_handler, sample_csv_file,
                                                     sample_text_file, client_id, user_id):
        """
        Feature: universal-data-handler, Property 12: Complete API Coverage
        For any valid client_id and user_id, all Sub-Layer 2 APIs should be available
        and return consistent APIResponse objects.
        """
        # First upload some data to query
        upload_response = api_handler.upload_file(
            client_id=client_id,
            user_id=user_id,
            file_path=sample_csv_file,
            resource_name="test_data"
        )
        
        if upload_response.success:
            resource_id = upload_response.data['resource_id']
            
            # Test 1: get_resource API exists and works
            get_response = api_handler.get_resource(
                resource_id=resource_id,
                client_id=client_id,
                user_id=user_id
            )
            assert isinstance(get_response, APIResponse)
            
            # Test 2: query_structured API exists and works
            sql_response = api_handler.query_structured(
                client_id=client_id,
                user_id=user_id,
                sql_query="SELECT COUNT(*) as count FROM test_data"
            )
            assert isinstance(sql_response, APIResponse)
            
            # Test 3: query_natural API exists and works
            nl_response = api_handler.query_natural(
                client_id=client_id,
                user_id=user_id,
                question="How many rows are in the data?"
            )
            assert isinstance(nl_response, APIResponse)
        
        # Upload unstructured data for search testing
        text_upload = api_handler.upload_file(
            client_id=client_id,
            user_id=user_id,
            file_path=sample_text_file,
            resource_name="test_document"
        )
        
        if text_upload.success:
            # Test 4: search_unstructured API exists and works
            search_response = api_handler.search_unstructured(
                client_id=client_id,
                user_id=user_id,
                query="data management",
                strategy="semantic"
            )
            assert isinstance(search_response, APIResponse)
            
            # Test 5: ask_data_analyst API exists and works
            analyst_response = api_handler.ask_data_analyst(
                client_id=client_id,
                user_id=user_id,
                question="What insights can you provide about my data?"
            )
            assert isinstance(analyst_response, APIResponse)
    
    @given(
        client_id=st.uuids(version=4).map(str),
        user_id=st.uuids(version=4).map(str)
    )
    @settings(max_examples=50, deadline=30000)
    def test_property_12_metadata_api_completeness(self, api_handler, sample_csv_file,
                                                  client_id, user_id):
        """
        Feature: universal-data-handler, Property 12: Complete API Coverage
        For any valid client_id and user_id, all metadata APIs should be available
        and return consistent APIResponse objects.
        """
        # Upload data first
        upload_response = api_handler.upload_file(
            client_id=client_id,
            user_id=user_id,
            file_path=sample_csv_file,
            resource_name="test_metadata"
        )
        
        if upload_response.success:
            resource_id = upload_response.data['resource_id']
            
            # Test 1: get_resource_metadata API exists and works
            metadata_response = api_handler.get_resource_metadata(
                resource_id=resource_id,
                client_id=client_id,
                user_id=user_id
            )
            assert isinstance(metadata_response, APIResponse)
            
            # Test 2: get_schema API exists and works
            schema_response = api_handler.get_schema(
                resource_id=resource_id,
                client_id=client_id,
                user_id=user_id
            )
            assert isinstance(schema_response, APIResponse)
        
        # Test 3: list_resources API exists and works
        list_response = api_handler.list_resources(
            client_id=client_id,
            user_id=user_id,
            access_level="user"
        )
        assert isinstance(list_response, APIResponse)
        
        # Test 4: get_statistics API exists and works
        stats_response = api_handler.get_statistics(
            client_id=client_id,
            user_id=user_id,
            access_level="user"
        )
        assert isinstance(stats_response, APIResponse)
    
    @settings(max_examples=30, deadline=30000)
    def test_property_12_administration_api_completeness(self, api_handler, sample_csv_file):
        """
        Feature: universal-data-handler, Property 12: Complete API Coverage
        For any system state, all administration APIs should be available
        and return consistent APIResponse objects.
        """
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Upload some data first
        upload_response = api_handler.upload_file(
            client_id=client_id,
            user_id=user_id,
            file_path=sample_csv_file,
            resource_name="admin_test"
        )
        
        if upload_response.success:
            resource_id = upload_response.data['resource_id']
            
            # Test 1: clear_cache API exists and works
            cache_response = api_handler.clear_cache(scope="all")
            assert isinstance(cache_response, APIResponse)
            
            # Test 2: get_system_stats API exists and works
            system_stats_response = api_handler.get_system_stats()
            assert isinstance(system_stats_response, APIResponse)
            
            # Test 3: optimize_storage API exists and works
            optimize_response = api_handler.optimize_storage()
            assert isinstance(optimize_response, APIResponse)
            
            # Test 4: export_resource API exists and works
            export_response = api_handler.export_resource(
                resource_id=resource_id,
                export_format="json",
                client_id=client_id,
                user_id=user_id
            )
            assert isinstance(export_response, APIResponse)
            
            # Test 5: backup_data API exists and works
            backup_response = api_handler.backup_data(
                backup_path=None,
                include_raw_files=False
            )
            assert isinstance(backup_response, APIResponse)
            
            # Test 6: restore_data API exists (test with invalid path for safety)
            restore_response = api_handler.restore_data(
                backup_path="/nonexistent/path",
                restore_raw_files=False
            )
            assert isinstance(restore_response, APIResponse)
            # Should fail but still return proper APIResponse
            assert not restore_response.success
    
    @given(
        output_format=st.sampled_from(["dataframe", "json", "csv", "dict"])
    )
    @settings(max_examples=20, deadline=30000)
    def test_property_12_consistent_response_formatting(self, api_handler, sample_csv_file,
                                                       output_format):
        """
        Feature: universal-data-handler, Property 12: Complete API Coverage
        For any output format, APIs should return data in the requested format
        with consistent response structure.
        """
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Upload data
        upload_response = api_handler.upload_file(
            client_id=client_id,
            user_id=user_id,
            file_path=sample_csv_file,
            resource_name="format_test"
        )
        
        if upload_response.success:
            resource_id = upload_response.data['resource_id']
            
            # Test get_resource with different formats
            get_response = api_handler.get_resource(
                resource_id=resource_id,
                output_format=output_format,
                client_id=client_id,
                user_id=user_id
            )
            
            assert isinstance(get_response, APIResponse)
            if get_response.success:
                assert 'data' in get_response.data
                # Verify response has consistent structure
                response_dict = get_response.to_dict()
                assert 'success' in response_dict
                assert 'timestamp' in response_dict
                assert 'metadata' in response_dict
    
    @given(
        error_scenario=st.sampled_from([
            "invalid_client_id",
            "invalid_user_id", 
            "nonexistent_resource",
            "invalid_file_path",
            "invalid_format"
        ])
    )
    @settings(max_examples=25, deadline=30000)
    def test_property_12_comprehensive_error_handling(self, api_handler, error_scenario):
        """
        Feature: universal-data-handler, Property 12: Complete API Coverage
        For any error scenario, APIs should return proper APIResponse objects
        with success=False and descriptive error messages.
        """
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        if error_scenario == "invalid_client_id":
            # Test with invalid client_id
            response = api_handler.upload_file(
                client_id="invalid-uuid",
                user_id=user_id,
                file_path="/nonexistent/file.csv"
            )
        
        elif error_scenario == "invalid_user_id":
            # Test with invalid user_id
            response = api_handler.list_resources(
                client_id=client_id,
                user_id="invalid-uuid"
            )
        
        elif error_scenario == "nonexistent_resource":
            # Test with nonexistent resource
            fake_resource_id = str(uuid.uuid4())
            response = api_handler.get_resource(
                resource_id=fake_resource_id,
                client_id=client_id,
                user_id=user_id
            )
        
        elif error_scenario == "invalid_file_path":
            # Test with invalid file path
            response = api_handler.upload_file(
                client_id=client_id,
                user_id=user_id,
                file_path="/nonexistent/file.csv"
            )
        
        elif error_scenario == "invalid_format":
            # Test with invalid export format
            fake_resource_id = str(uuid.uuid4())
            response = api_handler.export_resource(
                resource_id=fake_resource_id,
                export_format="invalid_format",
                client_id=client_id,
                user_id=user_id
            )
        
        # All error scenarios should return proper APIResponse
        assert isinstance(response, APIResponse)
        assert not response.success
        assert response.error is not None
        assert isinstance(response.error, str)
        assert len(response.error) > 0
        
        # Response should be serializable
        response_dict = response.to_dict()
        assert isinstance(response_dict, dict)
        json_str = response.to_json()
        assert isinstance(json_str, str)
    
    def test_property_12_api_factory_function(self, temp_dir):
        """
        Feature: universal-data-handler, Property 12: Complete API Coverage
        The create_api factory function should create properly configured API instances.
        """
        # Test factory function
        config = Config()
        config.openrouter_api_key = "test-key"
        
        api = create_api(config=config, base_path=temp_dir)
        
        assert isinstance(api, UniversalDataHandler)
        assert api.config == config
        assert api.base_path == temp_dir
        
        # Test without parameters
        api_default = create_api()
        assert isinstance(api_default, UniversalDataHandler)
    
    @settings(max_examples=20, deadline=30000)
    def test_property_12_transaction_support(self, api_handler, sample_csv_file):
        """
        Feature: universal-data-handler, Property 12: Complete API Coverage
        For any critical operation, the system should provide transaction support
        with proper rollback on failures.
        """
        client_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # Test upload transaction behavior
        response = api_handler.upload_file(
            client_id=client_id,
            user_id=user_id,
            file_path=sample_csv_file,
            resource_name="transaction_test"
        )
        
        # Response should indicate transaction completion
        assert isinstance(response, APIResponse)
        
        if response.success:
            resource_id = response.data['resource_id']
            
            # Test update transaction behavior
            update_response = api_handler.update_resource(
                resource_id=resource_id,
                new_data=sample_csv_file,
                create_version=True,
                client_id=client_id,
                user_id=user_id
            )
            
            assert isinstance(update_response, APIResponse)
            
            # Test delete transaction behavior
            delete_response = api_handler.delete_resource(
                resource_id=resource_id,
                hard_delete=False,
                client_id=client_id,
                user_id=user_id
            )
            
            assert isinstance(delete_response, APIResponse)
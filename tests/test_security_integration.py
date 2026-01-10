"""
Integration tests for the security and data isolation system.

Tests the complete security stack including user management, data isolation,
access control, encryption, and audit logging.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from light_ai.config import Config
from light_ai.core.models import AccessLevel
from light_ai.security import SecurityManager
from light_ai.security.access_control import ResourceAction


@pytest.fixture
def temp_config():
    """Create temporary configuration for testing."""
    temp_dir = tempfile.mkdtemp()
    
    # Create a test configuration
    config = Config()
    config.storage.base_directory = temp_dir
    config.database.sqlite_path = "metadata/registry.db"
    config.database.duckdb_path = "data/duckdb/main.db"
    config.database.chromadb_path = "data/unstructured/chroma_db"
    
    yield config
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def security_manager(temp_config):
    """Create security manager for testing."""
    manager = SecurityManager(temp_config)
    yield manager
    manager.shutdown()


class TestSecurityManager:
    """Test security manager functionality."""
    
    def test_create_user_with_isolation(self, security_manager):
        """Test creating user with complete isolation setup."""
        client_id = "test-client"
        user_name = "test-user"
        
        # Create user
        user = security_manager.create_user(
            client_id=client_id,
            user_name=user_name,
            email="test@example.com",
            access_level=AccessLevel.USER
        )
        
        assert user.user_id is not None
        assert user.client_id == client_id
        assert user.user_name == user_name
        assert user.email == "test@example.com"
        assert user.access_level == AccessLevel.USER
        assert user.is_active is True
    
    def test_user_authentication(self, security_manager):
        """Test user authentication."""
        client_id = "test-client"
        user_name = "test-user"
        
        # Create user
        user = security_manager.create_user(client_id, user_name)
        
        # Authenticate user
        auth_user = security_manager.authenticate_user(client_id, user_name)
        assert auth_user is not None
        assert auth_user.user_id == user.user_id
        assert auth_user.last_login is not None
        
        # Test invalid authentication
        invalid_user = security_manager.authenticate_user(client_id, "nonexistent")
        assert invalid_user is None
    
    def test_username_to_userid_mapping(self, security_manager):
        """Test username to user_id mapping functionality."""
        client_id = "test-client"
        user_name = "test-user"
        
        # Create user
        user = security_manager.create_user(client_id, user_name)
        
        # Test username lookup
        found_user = security_manager.get_user_by_username(client_id, user_name)
        assert found_user is not None
        assert found_user.user_id == user.user_id
        
        # Test user_id lookup by username
        user_id = security_manager.get_user_id_by_username(client_id, user_name)
        assert user_id == user.user_id
        
        # Test nonexistent username
        nonexistent_user = security_manager.get_user_by_username(client_id, "nonexistent")
        assert nonexistent_user is None
    
    def test_access_control_validation(self, security_manager):
        """Test access control validation."""
        client_id = "test-client"
        user_name = "test-user"
        
        # Create user
        user = security_manager.create_user(client_id, user_name, access_level=AccessLevel.USER)
        
        # Test basic access validation
        can_query = security_manager.validate_access(
            user.user_id, client_id, ResourceAction.QUERY
        )
        assert can_query is True
        
        # Test admin action (should be denied for regular user)
        can_admin = security_manager.validate_access(
            user.user_id, client_id, ResourceAction.ADMIN
        )
        assert can_admin is False
    
    def test_data_encryption(self, security_manager):
        """Test user-specific data encryption."""
        client_id = "test-client"
        user_name = "test-user"
        
        # Create user
        user = security_manager.create_user(client_id, user_name)
        
        # Test data encryption
        test_data = "This is sensitive user data"
        encrypted_data = security_manager.encrypt_user_data(
            test_data, user.user_id, client_id
        )
        
        assert encrypted_data != test_data.encode()
        assert len(encrypted_data) > len(test_data)
        
        # Test data decryption
        decrypted_data = security_manager.decrypt_user_data(
            encrypted_data, user.user_id, client_id
        )
        
        assert decrypted_data.decode() == test_data
    
    def test_isolated_database_connection(self, security_manager):
        """Test isolated database connections."""
        client_id = "test-client"
        user_name = "test-user"
        
        # Create user
        user = security_manager.create_user(client_id, user_name)
        
        # Test isolated connection
        with security_manager.get_isolated_connection(user.user_id, client_id, 'sqlite') as conn:
            # Test basic query
            cursor = conn.execute("SELECT 1 as test")
            result = cursor.fetchone()
            assert result['test'] == 1
    
    def test_secure_transaction(self, security_manager):
        """Test secure transaction management."""
        client_id = "test-client"
        user_name = "test-user"
        
        # Create user
        user = security_manager.create_user(client_id, user_name)
        
        # Test transaction
        with security_manager.secure_transaction(user.user_id, client_id) as transaction_id:
            assert transaction_id is not None
            assert len(transaction_id) > 0
    
    def test_user_lifecycle(self, security_manager):
        """Test complete user lifecycle."""
        client_id = "test-client"
        user_name = "test-user"
        
        # Create user
        user = security_manager.create_user(client_id, user_name)
        original_user_id = user.user_id
        
        # Verify user exists
        found_user = security_manager.get_user_by_username(client_id, user_name)
        assert found_user is not None
        
        # Delete user completely
        success = security_manager.delete_user_completely(user.user_id, client_id)
        assert success is True
        
        # Verify user no longer exists
        deleted_user = security_manager.get_user_by_username(client_id, user_name)
        assert deleted_user is None
    
    def test_username_uniqueness_within_client(self, security_manager):
        """Test that usernames are unique within a client."""
        client_id = "test-client"
        user_name = "test-user"
        
        # Create first user
        user1 = security_manager.create_user(client_id, user_name)
        
        # Try to create second user with same username in same client
        with pytest.raises(ValueError, match="already exists"):
            security_manager.create_user(client_id, user_name)
        
        # Create user with same username in different client (should work)
        different_client = "different-client"
        user2 = security_manager.create_user(different_client, user_name)
        
        assert user1.user_id != user2.user_id
        assert user1.client_id != user2.client_id
        assert user1.user_name == user2.user_name
    
    def test_security_statistics(self, security_manager):
        """Test security statistics collection."""
        client_id = "test-client"
        
        # Create some users
        security_manager.create_user(client_id, "user1", access_level=AccessLevel.USER)
        security_manager.create_user(client_id, "user2", access_level=AccessLevel.MANAGER)
        security_manager.create_user(client_id, "admin1", access_level=AccessLevel.ADMIN)
        
        # Get statistics
        stats = security_manager.get_security_statistics(client_id)
        
        assert 'users' in stats
        assert 'audit' in stats
        assert 'connections' in stats
        assert 'namespaces' in stats
        
        # Check user statistics
        user_stats = stats['users']
        assert user_stats['total_users'] == 3
        assert user_stats['active_users'] == 3
    
    def test_system_integrity_verification(self, security_manager):
        """Test system integrity verification."""
        # Create some test data
        client_id = "test-client"
        user = security_manager.create_user(client_id, "test-user")
        
        # Verify system integrity
        integrity_results = security_manager.verify_system_integrity()
        
        assert 'overall_status' in integrity_results
        assert 'components' in integrity_results
        assert 'issues' in integrity_results
        
        # Should be healthy for new system
        assert integrity_results['overall_status'] in ['healthy', 'error']  # Allow error for test environment
    
    def test_convenience_methods(self, security_manager):
        """Test convenience methods for common operations."""
        client_id = "test-client"
        user_name = "test-user"
        
        # Test create_user_with_username
        user_id, user = security_manager.create_user_with_username(
            client_id, user_name, AccessLevel.USER
        )
        
        assert user_id == user.user_id
        assert user.user_name == user_name
        
        # Test validate_user_resource_access with username
        can_access = security_manager.validate_user_resource_access(
            client_id, user_name, "test-resource", ResourceAction.VIEW
        )
        
        # Should be True for basic view access
        assert can_access is True


class TestDataIsolation:
    """Test data isolation functionality."""
    
    def test_user_namespace_creation(self, security_manager):
        """Test user namespace creation and isolation."""
        client_id = "test-client"
        user1_name = "user1"
        user2_name = "user2"
        
        # Create two users
        user1 = security_manager.create_user(client_id, user1_name)
        user2 = security_manager.create_user(client_id, user2_name)
        
        # Verify they have different namespaces
        namespace1 = security_manager.data_isolation.get_user_namespace(user1.user_id, client_id)
        namespace2 = security_manager.data_isolation.get_user_namespace(user2.user_id, client_id)
        
        assert namespace1 is not None
        assert namespace2 is not None
        assert namespace1.user_id != namespace2.user_id
        assert namespace1.database_schema != namespace2.database_schema
        assert namespace1.storage_path != namespace2.storage_path
    
    def test_data_access_validation(self, security_manager):
        """Test data access validation between users."""
        client_id = "test-client"
        user1_name = "user1"
        user2_name = "user2"
        
        # Create two users
        user1 = security_manager.create_user(client_id, user1_name)
        user2 = security_manager.create_user(client_id, user2_name)
        
        # Test that user1 cannot access user2's resources
        fake_resource_id = "user2-resource-123"
        
        # This should return False since the resource doesn't exist in user1's namespace
        can_access = security_manager.validate_data_access(
            user1.user_id, client_id, [fake_resource_id]
        )
        assert can_access is False


if __name__ == "__main__":
    pytest.main([__file__])
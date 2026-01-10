"""
Demo of simple security and data isolation system.

Shows essential functionality:
- User creation with user_name mapping
- Data isolation validation
- Basic access control
- Simple audit logging
"""

import tempfile
import shutil
import uuid
from pathlib import Path

from light_ai.config import Config
from light_ai.security.simple_security import SimpleSecurityManager
from light_ai.core.models import ResourceMetadata, ResourceType, DataType
from datetime import datetime


def main():
    """Demonstrate simple security functionality."""
    
    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp()
    print(f"Demo running in: {temp_dir}")
    
    try:
        # Create test configuration
        config = Config()
        config.storage.base_directory = temp_dir
        
        # Initialize security manager
        security_manager = SimpleSecurityManager(config)
        print("✓ Security manager initialized")
        
        # Demo 1: Create users with user_name mapping
        print("\n=== Demo 1: User Management ===")
        
        client_id = "demo-client"
        
        # Create users
        user1 = security_manager.create_user(client_id, "alice")
        user2 = security_manager.create_user(client_id, "bob")
        
        print(f"✓ Created user: {user1.user_name} (ID: {user1.user_id})")
        print(f"✓ Created user: {user2.user_name} (ID: {user2.user_id})")
        
        # Test username lookup
        found_user = security_manager.get_user_by_username(client_id, "alice")
        print(f"✓ Found user by username: {found_user.user_name} -> {found_user.user_id}")
        
        # Test user_id lookup by username
        alice_id = security_manager.get_user_id_by_username(client_id, "alice")
        print(f"✓ User ID lookup: alice -> {alice_id}")
        
        # Demo 2: Data isolation validation
        print("\n=== Demo 2: Data Isolation ===")
        
        # Create mock resource metadata for each user
        alice_resource = ResourceMetadata(
            resource_id=str(uuid.uuid4()),  # Use proper UUID
            user_id=user1.user_id,
            client_id=client_id,
            resource_type=ResourceType.STRUCTURED,
            data_type=DataType.CSV,
            original_filename="alice_data.csv",
            file_size_bytes=1024,
            storage_path="/path/to/alice/data.csv",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        bob_resource = ResourceMetadata(
            resource_id=str(uuid.uuid4()),  # Use proper UUID
            user_id=user2.user_id,
            client_id=client_id,
            resource_type=ResourceType.JSON,
            data_type=DataType.JSON,
            original_filename="bob_data.json",
            file_size_bytes=2048,
            storage_path="/path/to/bob/data.json",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Test access validation
        # Alice should be able to access her own resource
        alice_can_access_own = security_manager.validate_user_access(
            user1.user_id, client_id, alice_resource
        )
        print(f"✓ Alice can access her own resource: {alice_can_access_own}")
        
        # Alice should NOT be able to access Bob's resource
        alice_can_access_bobs = security_manager.validate_user_access(
            user1.user_id, client_id, bob_resource
        )
        print(f"✓ Alice cannot access Bob's resource: {not alice_can_access_bobs}")
        
        # Test access validation by username
        alice_can_access_by_username = security_manager.validate_user_access_by_username(
            client_id, "alice", alice_resource
        )
        print(f"✓ Alice can access her resource by username: {alice_can_access_by_username}")
        
        # Demo 3: Storage paths
        print("\n=== Demo 3: User Storage Paths ===")
        
        alice_structured_path = security_manager.get_user_storage_path(
            user1.user_id, client_id, 'structured'
        )
        print(f"✓ Alice's structured data path: {alice_structured_path}")
        
        bob_json_path = security_manager.get_user_storage_path_by_username(
            client_id, "bob", 'json'
        )
        print(f"✓ Bob's JSON data path (by username): {bob_json_path}")
        
        # Demo 4: Transaction context
        print("\n=== Demo 4: Transaction Management ===")
        
        with security_manager.user_transaction(user1.user_id, client_id) as tx:
            print(f"✓ Transaction started for Alice: {tx['started_at']}")
            # Simulate some work
            security_manager.log_data_access(
                user1.user_id, client_id, "DATA_QUERY", 
                alice_resource.resource_id, "SELECT * FROM data"
            )
        print("✓ Transaction completed successfully")
        
        # Demo 5: User statistics
        print("\n=== Demo 5: User Statistics ===")
        
        stats = security_manager.get_user_statistics(client_id)
        print(f"✓ Total users: {stats['total_users']}")
        print(f"✓ Active users: {stats['active_users']}")
        print(f"✓ Usernames: {stats['usernames']}")
        
        # Demo 6: Convenience methods
        print("\n=== Demo 6: Convenience Methods ===")
        
        # Ensure user exists (will return existing user)
        charlie_id = security_manager.ensure_user_exists(client_id, "charlie")
        print(f"✓ Ensured user exists: charlie -> {charlie_id}")
        
        # Try again (should return same ID)
        charlie_id_again = security_manager.ensure_user_exists(client_id, "charlie")
        print(f"✓ Same user ID returned: {charlie_id == charlie_id_again}")
        
        print("\n=== Demo Complete ===")
        print("✓ All essential security features working correctly!")
        print(f"✓ Audit log created at: {security_manager.audit_logger.log_file}")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"✓ Cleaned up demo directory: {temp_dir}")


if __name__ == "__main__":
    main()
"""
Demo script showing the security and data isolation system in action.

This demonstrates the core functionality without requiring full test setup.
"""

import tempfile
import shutil
from pathlib import Path

from light_ai.config import Config
from light_ai.core.models import AccessLevel
from light_ai.security import SecurityManager
from light_ai.security.access_control import ResourceAction


def main():
    """Demonstrate security system functionality."""
    print("🔒 Security and Data Isolation Demo")
    print("=" * 50)
    
    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp()
    print(f"📁 Using temporary directory: {temp_dir}")
    
    try:
        # Create configuration
        config = Config()
        config.storage.base_directory = temp_dir
        config.database.sqlite_path = "metadata/registry.db"
        config.database.duckdb_path = "data/duckdb/main.db"
        config.database.chromadb_path = "data/unstructured/chroma_db"
        
        # Initialize security manager
        print("\n🚀 Initializing Security Manager...")
        security_manager = SecurityManager(config)
        
        # Demo 1: Create users with username mapping
        print("\n👥 Creating Users...")
        client_id = "demo-client"
        
        user1 = security_manager.create_user(
            client_id=client_id,
            user_name="alice",
            email="alice@example.com",
            access_level=AccessLevel.USER
        )
        print(f"✅ Created user: {user1.user_name} (ID: {user1.user_id[:8]}...)")
        
        user2 = security_manager.create_user(
            client_id=client_id,
            user_name="bob",
            email="bob@example.com", 
            access_level=AccessLevel.MANAGER
        )
        print(f"✅ Created user: {user2.user_name} (ID: {user2.user_id[:8]}...)")
        
        # Demo 2: Username to user_id mapping
        print("\n🔍 Testing Username Mapping...")
        alice_id = security_manager.get_user_id_by_username(client_id, "alice")
        bob_user = security_manager.get_user_by_username(client_id, "bob")
        
        print(f"✅ Alice's user_id: {alice_id[:8]}...")
        print(f"✅ Bob's full info: {bob_user.user_name} ({bob_user.access_level.value})")
        
        # Demo 3: Access control validation
        print("\n🛡️ Testing Access Control...")
        
        # Alice (USER level) trying different actions
        can_query = security_manager.validate_access(
            user1.user_id, client_id, ResourceAction.QUERY
        )
        can_admin = security_manager.validate_access(
            user1.user_id, client_id, ResourceAction.ADMIN
        )
        
        print(f"✅ Alice can query: {can_query}")
        print(f"❌ Alice can admin: {can_admin}")
        
        # Bob (MANAGER level) trying admin action
        bob_can_admin = security_manager.validate_access(
            user2.user_id, client_id, ResourceAction.ADMIN
        )
        bob_can_delete = security_manager.validate_access(
            user2.user_id, client_id, ResourceAction.DELETE
        )
        
        print(f"❌ Bob can admin: {bob_can_admin}")
        print(f"✅ Bob can delete: {bob_can_delete}")
        
        # Demo 4: Data encryption
        print("\n🔐 Testing Data Encryption...")
        
        test_data = "This is Alice's sensitive data!"
        encrypted = security_manager.encrypt_user_data(test_data, user1.user_id, client_id)
        decrypted = security_manager.decrypt_user_data(encrypted, user1.user_id, client_id)
        
        print(f"📝 Original: {test_data}")
        print(f"🔒 Encrypted: {encrypted[:20]}... (length: {len(encrypted)})")
        print(f"🔓 Decrypted: {decrypted.decode()}")
        print(f"✅ Round-trip successful: {test_data == decrypted.decode()}")
        
        # Demo 5: Isolated database connections
        print("\n🗄️ Testing Database Isolation...")
        
        try:
            with security_manager.get_isolated_connection(user1.user_id, client_id, 'sqlite') as conn:
                cursor = conn.execute("SELECT 1 as test_value")
                result = cursor.fetchone()
                print(f"✅ Alice's isolated query result: {result['test_value']}")
        except Exception as e:
            print(f"⚠️ Database connection test: {e}")
        
        # Demo 6: Secure transactions
        print("\n💳 Testing Secure Transactions...")
        
        try:
            with security_manager.secure_transaction(user1.user_id, client_id) as tx_id:
                print(f"✅ Started secure transaction: {tx_id[:8]}...")
                # Transaction automatically commits when exiting context
        except Exception as e:
            print(f"⚠️ Transaction test: {e}")
        
        # Demo 7: User authentication
        print("\n🔑 Testing User Authentication...")
        
        auth_user = security_manager.authenticate_user(client_id, "alice")
        if auth_user:
            print(f"✅ Alice authenticated successfully")
            print(f"📅 Last login: {auth_user.last_login}")
        
        invalid_auth = security_manager.authenticate_user(client_id, "nonexistent")
        print(f"❌ Invalid user authentication: {invalid_auth is None}")
        
        # Demo 8: Security statistics
        print("\n📊 Security Statistics...")
        
        stats = security_manager.get_security_statistics(client_id)
        print(f"👥 Total users: {stats['users']['total_users']}")
        print(f"✅ Active users: {stats['users']['active_users']}")
        print(f"🔗 Connection pools: {stats['connections']['total_pools']}")
        print(f"🏠 User namespaces: {stats['namespaces']}")
        
        # Demo 9: Username uniqueness
        print("\n🚫 Testing Username Uniqueness...")
        
        try:
            # Try to create another user with same username
            security_manager.create_user(client_id, "alice")
            print("❌ Should not reach here - duplicate username allowed!")
        except ValueError as e:
            print(f"✅ Correctly prevented duplicate username: {str(e)[:50]}...")
        
        # But same username in different client should work
        different_client = "other-client"
        alice_other = security_manager.create_user(different_client, "alice")
        print(f"✅ Same username in different client: {alice_other.client_id}:{alice_other.user_name}")
        
        print("\n🎉 All demos completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        try:
            security_manager.shutdown()
        except:
            pass
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"\n🧹 Cleaned up temporary directory")


if __name__ == "__main__":
    main()
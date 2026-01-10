"""
Simple security manager for essential data isolation.

Provides core security features without complex infrastructure:
- User management with user_name mapping
- Basic data isolation 
- Simple access validation
- Essential audit logging
"""

from typing import Dict, Any, List, Optional
from contextlib import contextmanager
from datetime import datetime

from ..core.models import ResourceMetadata
from ..config import Config, get_config
from ..logger import get_logger
from .simple_isolation import SimpleDataIsolation, SimpleUser, SimpleTransactionManager, SimpleAuditLogger

logger = get_logger(__name__)


class SimpleSecurityManager:
    """
    Simple security manager focusing on essential features.
    
    Provides user management, data isolation, and access control
    without complex encryption or heavy infrastructure.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize simple security manager."""
        self.config = config or get_config()
        self.data_isolation = SimpleDataIsolation(config)
        self.transaction_manager = SimpleTransactionManager(config)
        self.audit_logger = SimpleAuditLogger(config)
        
        logger.info("Simple security manager initialized")
    
    # User Management
    
    def create_user(self, client_id: str, user_name: str) -> SimpleUser:
        """
        Create a new user with basic isolation.
        
        Args:
            client_id: Client identifier
            user_name: Human-readable username (unique within client)
            
        Returns:
            Created SimpleUser object
        """
        user = self.data_isolation.create_user(client_id, user_name)
        
        # Log user creation
        self.audit_logger.log_access(
            user.user_id, client_id, "USER_CREATED", 
            details=f"username:{user_name}"
        )
        
        return user
    
    def get_user_by_username(self, client_id: str, user_name: str) -> Optional[SimpleUser]:
        """
        Get user by username (for simplified access).
        
        Args:
            client_id: Client identifier
            user_name: Username to look up
            
        Returns:
            SimpleUser object or None if not found
        """
        return self.data_isolation.get_user_by_username(client_id, user_name)
    
    def get_user_id_by_username(self, client_id: str, user_name: str) -> Optional[str]:
        """
        Get user_id by username (for simplified access).
        
        Args:
            client_id: Client identifier
            user_name: Username to look up
            
        Returns:
            User ID or None if not found
        """
        return self.data_isolation.get_user_id_by_username(client_id, user_name)
    
    def list_users(self, client_id: str) -> List[SimpleUser]:
        """
        List all users for a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            List of SimpleUser objects
        """
        return self.data_isolation.list_users(client_id)
    
    # Access Control
    
    def validate_user_access(self, user_id: str, client_id: str, 
                           resource_metadata: ResourceMetadata) -> bool:
        """
        Validate that user can access a resource.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            resource_metadata: Resource metadata to validate
            
        Returns:
            True if user can access the resource
        """
        can_access = self.data_isolation.validate_user_access(user_id, client_id, resource_metadata)
        
        # Log access attempt
        self.audit_logger.log_access(
            user_id, client_id, 
            "ACCESS_CHECK", 
            resource_metadata.resource_id,
            f"result:{can_access}"
        )
        
        return can_access
    
    def validate_user_access_by_username(self, client_id: str, user_name: str,
                                       resource_metadata: ResourceMetadata) -> bool:
        """
        Validate access using username instead of user_id.
        
        Args:
            client_id: Client identifier
            user_name: Username
            resource_metadata: Resource metadata to validate
            
        Returns:
            True if user can access the resource
        """
        user_id = self.get_user_id_by_username(client_id, user_name)
        if not user_id:
            return False
        
        return self.validate_user_access(user_id, client_id, resource_metadata)
    
    # Data Operations
    
    def get_user_storage_path(self, user_id: str, client_id: str, data_type: str = 'structured'):
        """
        Get storage path for user data.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            data_type: Type of data ('structured', 'json', 'unstructured')
            
        Returns:
            Path to user's data directory
        """
        return self.data_isolation.get_user_storage_path(user_id, client_id, data_type)
    
    def get_user_storage_path_by_username(self, client_id: str, user_name: str, 
                                        data_type: str = 'structured'):
        """
        Get storage path using username.
        
        Args:
            client_id: Client identifier
            user_name: Username
            data_type: Type of data
            
        Returns:
            Path to user's data directory or None if user not found
        """
        user_id = self.get_user_id_by_username(client_id, user_name)
        if not user_id:
            return None
        
        return self.get_user_storage_path(user_id, client_id, data_type)
    
    @contextmanager
    def user_transaction(self, user_id: str, client_id: str):
        """
        Create transaction context for user operations.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            
        Yields:
            Transaction context
        """
        with self.transaction_manager.transaction(user_id, client_id) as context:
            # Log transaction start
            self.audit_logger.log_access(
                user_id, client_id, "TRANSACTION_START"
            )
            
            try:
                yield context
                
                # Log transaction success
                self.audit_logger.log_access(
                    user_id, client_id, "TRANSACTION_COMMIT"
                )
                
            except Exception as e:
                # Log transaction failure
                self.audit_logger.log_access(
                    user_id, client_id, "TRANSACTION_ROLLBACK",
                    details=f"error:{str(e)}"
                )
                raise
    
    # Convenience Methods
    
    def create_user_and_get_id(self, client_id: str, user_name: str) -> str:
        """
        Create user and return user_id.
        
        Args:
            client_id: Client identifier
            user_name: Username
            
        Returns:
            User ID of created user
        """
        user = self.create_user(client_id, user_name)
        return user.user_id
    
    def ensure_user_exists(self, client_id: str, user_name: str) -> str:
        """
        Ensure user exists, create if not found.
        
        Args:
            client_id: Client identifier
            user_name: Username
            
        Returns:
            User ID (existing or newly created)
        """
        user_id = self.get_user_id_by_username(client_id, user_name)
        
        if user_id:
            return user_id
        
        # User doesn't exist, create it
        user = self.create_user(client_id, user_name)
        return user.user_id
    
    def log_data_access(self, user_id: str, client_id: str, action: str,
                       resource_id: Optional[str] = None, details: Optional[str] = None) -> None:
        """
        Log data access event.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            action: Action performed
            resource_id: Optional resource identifier
            details: Optional additional details
        """
        self.audit_logger.log_access(user_id, client_id, action, resource_id, details)
    
    # System Operations
    
    def get_user_statistics(self, client_id: str) -> Dict[str, Any]:
        """
        Get user statistics for a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            User statistics
        """
        users = self.list_users(client_id)
        
        return {
            'total_users': len(users),
            'active_users': len([u for u in users if u.is_active]),
            'usernames': [u.user_name for u in users]
        }
    
    def delete_user(self, user_id: str, client_id: str) -> bool:
        """
        Delete user and their data.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            
        Returns:
            True if deletion was successful
        """
        success = self.data_isolation.delete_user(user_id, client_id)
        
        if success:
            self.audit_logger.log_access(
                user_id, client_id, "USER_DELETED"
            )
        
        return success
    
    def delete_user_by_username(self, client_id: str, user_name: str) -> bool:
        """
        Delete user by username.
        
        Args:
            client_id: Client identifier
            user_name: Username
            
        Returns:
            True if deletion was successful
        """
        user_id = self.get_user_id_by_username(client_id, user_name)
        if not user_id:
            return False
        
        return self.delete_user(user_id, client_id)
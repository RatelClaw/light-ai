"""
Access Control Manager for API Layer.

Provides simplified access control interface for the comprehensive API layer.
"""

from typing import Dict, Any, Optional
from ..core.models import AccessLevel
from ..config import Config
from .access_control import AccessControlLayer, ResourceAction
from .user_manager import UserManager


class AccessControlManager:
    """
    Simplified access control manager for API layer.
    
    Provides easy-to-use methods for validating user access in API endpoints.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize access control manager."""
        self.config = config
        self.access_control = AccessControlLayer(config)
        self.user_manager = UserManager(config)
    
    def validate_user_access(self, client_id: str, user_id: str, 
                           access_level: AccessLevel = AccessLevel.USER) -> bool:
        """
        Validate basic user access.
        
        Args:
            client_id: Client identifier
            user_id: User identifier
            access_level: Required access level
            
        Returns:
            True if user has valid access
        """
        try:
            # Check if user exists and is active
            user = self.user_manager.get_user(user_id, client_id)
            if not user or not user.is_active:
                return False
            
            # Check if user has required access level
            user_permissions = self.access_control.get_user_permissions(user_id, client_id)
            if not user_permissions or not user_permissions.is_active:
                return False
            
            # Check access level hierarchy
            access_levels = {
                AccessLevel.USER: 1,
                AccessLevel.MANAGER: 2,
                AccessLevel.ADMIN: 3
            }
            
            required_level = access_levels.get(access_level, 1)
            user_level = access_levels.get(user_permissions.access_level, 1)
            
            return user_level >= required_level
            
        except Exception:
            return False
    
    def validate_resource_access(self, client_id: str, user_id: str, 
                               resource_id: str, action: str = "view") -> bool:
        """
        Validate user access to a specific resource.
        
        Args:
            client_id: Client identifier
            user_id: User identifier
            resource_id: Resource identifier
            action: Action being performed
            
        Returns:
            True if user can access the resource
        """
        try:
            # Map string actions to ResourceAction enum
            action_mapping = {
                "view": ResourceAction.VIEW,
                "query": ResourceAction.QUERY,
                "update": ResourceAction.UPDATE,
                "delete": ResourceAction.DELETE,
                "export": ResourceAction.EXPORT,
                "share": ResourceAction.SHARE,
                "admin": ResourceAction.ADMIN
            }
            
            resource_action = action_mapping.get(action.lower(), ResourceAction.VIEW)
            
            # Create access request
            from .access_control import AccessRequest
            request = AccessRequest(
                user_id=user_id,
                client_id=client_id,
                resource_id=resource_id,
                action=resource_action
            )
            
            # Validate access
            result = self.access_control.validate_access(request)
            return result.granted
            
        except Exception:
            return False
    
    def create_user_permissions(self, client_id: str, user_id: str, 
                              access_level: AccessLevel = AccessLevel.USER) -> bool:
        """
        Create permissions for a new user.
        
        Args:
            client_id: Client identifier
            user_id: User identifier
            access_level: User access level
            
        Returns:
            True if permissions were created successfully
        """
        try:
            self.access_control.create_user_permissions(
                user_id=user_id,
                client_id=client_id,
                access_level=access_level
            )
            return True
        except Exception:
            return False
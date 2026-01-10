"""
Access control layer for user permission validation.

Provides comprehensive access control with role-based permissions,
resource-level authorization, and audit logging.
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
from pathlib import Path

from ..core.models import DataHierarchy, ResourceMetadata, AccessLevel
from ..config import Config, get_config
from ..logger import get_logger

logger = get_logger(__name__)


class Permission(Enum):
    """Available permissions."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    EXECUTE = "execute"
    SHARE = "share"


class ResourceAction(Enum):
    """Resource actions that require permission checks."""
    VIEW = "view"
    QUERY = "query"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    SHARE = "share"
    ADMIN = "admin"


@dataclass
class UserPermissions:
    """User permission configuration."""
    user_id: str
    client_id: str
    user_name: Optional[str]
    access_level: AccessLevel
    permissions: Set[Permission]
    resource_permissions: Dict[str, Set[Permission]]  # resource_id -> permissions
    created_at: datetime
    updated_at: datetime
    is_active: bool = True


@dataclass
class AccessRequest:
    """Access request for validation."""
    user_id: str
    client_id: str
    resource_id: Optional[str]
    action: ResourceAction
    additional_context: Optional[Dict[str, Any]] = None


@dataclass
class AccessResult:
    """Result of access validation."""
    granted: bool
    reason: str
    required_permissions: Set[Permission]
    user_permissions: Set[Permission]
    additional_info: Optional[Dict[str, Any]] = None


class AccessControlLayer:
    """
    Comprehensive access control system.
    
    Provides role-based access control (RBAC) with resource-level permissions,
    hierarchical access levels, and comprehensive audit logging.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize access control layer."""
        self.config = config or get_config()
        self._user_permissions: Dict[str, UserPermissions] = {}
        self._permission_cache_ttl = 3600  # 1 hour
        
        # Default permission mappings for actions
        self._action_permissions = {
            ResourceAction.VIEW: {Permission.READ},
            ResourceAction.QUERY: {Permission.READ},
            ResourceAction.UPDATE: {Permission.WRITE},
            ResourceAction.DELETE: {Permission.DELETE},
            ResourceAction.EXPORT: {Permission.READ},
            ResourceAction.SHARE: {Permission.SHARE},
            ResourceAction.ADMIN: {Permission.ADMIN}
        }
        
        # Default permissions for access levels
        self._access_level_permissions = {
            AccessLevel.USER: {Permission.READ, Permission.WRITE},
            AccessLevel.MANAGER: {Permission.READ, Permission.WRITE, Permission.DELETE, Permission.SHARE},
            AccessLevel.ADMIN: {Permission.READ, Permission.WRITE, Permission.DELETE, Permission.ADMIN, Permission.SHARE, Permission.EXECUTE}
        }
    
    def create_user_permissions(self, user_id: str, client_id: str, 
                               user_name: Optional[str] = None,
                               access_level: AccessLevel = AccessLevel.USER,
                               additional_permissions: Optional[Set[Permission]] = None) -> UserPermissions:
        """
        Create user permissions configuration.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            user_name: Optional human-readable username
            access_level: User access level
            additional_permissions: Additional permissions beyond access level defaults
            
        Returns:
            UserPermissions object
        """
        # Get default permissions for access level
        base_permissions = self._access_level_permissions.get(access_level, set())
        
        # Add any additional permissions
        if additional_permissions:
            base_permissions = base_permissions.union(additional_permissions)
        
        user_permissions = UserPermissions(
            user_id=user_id,
            client_id=client_id,
            user_name=user_name,
            access_level=access_level,
            permissions=base_permissions,
            resource_permissions={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True
        )
        
        # Cache permissions
        cache_key = f"{client_id}:{user_id}"
        self._user_permissions[cache_key] = user_permissions
        
        # Save to storage
        self._save_user_permissions(user_permissions)
        
        logger.info(f"Created permissions for user {client_id}:{user_id} with access level {access_level.value}")
        return user_permissions
    
    def get_user_permissions(self, user_id: str, client_id: str) -> Optional[UserPermissions]:
        """
        Get user permissions.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            
        Returns:
            UserPermissions object or None if not found
        """
        cache_key = f"{client_id}:{user_id}"
        
        # Check cache first
        if cache_key in self._user_permissions:
            return self._user_permissions[cache_key]
        
        # Load from storage
        user_permissions = self._load_user_permissions(user_id, client_id)
        if user_permissions:
            self._user_permissions[cache_key] = user_permissions
        
        return user_permissions
    
    def validate_access(self, request: AccessRequest) -> AccessResult:
        """
        Validate access request.
        
        Args:
            request: Access request to validate
            
        Returns:
            AccessResult with validation outcome
        """
        # Get user permissions
        user_permissions = self.get_user_permissions(request.user_id, request.client_id)
        
        if not user_permissions or not user_permissions.is_active:
            return AccessResult(
                granted=False,
                reason="User permissions not found or inactive",
                required_permissions=set(),
                user_permissions=set()
            )
        
        # Get required permissions for action
        required_permissions = self._action_permissions.get(request.action, set())
        
        # Check if user has required permissions
        user_perms = user_permissions.permissions.copy()
        
        # Add resource-specific permissions if applicable
        if request.resource_id and request.resource_id in user_permissions.resource_permissions:
            user_perms.update(user_permissions.resource_permissions[request.resource_id])
        
        # Check if user has all required permissions
        if required_permissions.issubset(user_perms):
            # Additional validation for resource ownership
            if request.resource_id:
                ownership_valid = self._validate_resource_ownership(
                    request.user_id, request.client_id, request.resource_id
                )
                
                if not ownership_valid and Permission.ADMIN not in user_perms:
                    return AccessResult(
                        granted=False,
                        reason="User does not own resource and lacks admin permissions",
                        required_permissions=required_permissions,
                        user_permissions=user_perms
                    )
            
            return AccessResult(
                granted=True,
                reason="Access granted",
                required_permissions=required_permissions,
                user_permissions=user_perms
            )
        else:
            missing_permissions = required_permissions - user_perms
            return AccessResult(
                granted=False,
                reason=f"Missing permissions: {[p.value for p in missing_permissions]}",
                required_permissions=required_permissions,
                user_permissions=user_perms
            )
    
    def _validate_resource_ownership(self, user_id: str, client_id: str, resource_id: str) -> bool:
        """
        Validate that user owns the resource.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            resource_id: Resource identifier
            
        Returns:
            True if user owns the resource
        """
        try:
            # Load resource metadata to check ownership
            from ..storage.metadata_registry import MetadataRegistry
            
            metadata_registry = MetadataRegistry(self.config)
            resource_metadata = metadata_registry.get_resource_metadata(resource_id)
            
            if not resource_metadata:
                return False
            
            return (resource_metadata.user_id == user_id and 
                   resource_metadata.client_id == client_id and
                   not resource_metadata.is_deleted)
        except Exception as e:
            logger.error(f"Error validating resource ownership: {e}")
            return False
    
    def grant_resource_permission(self, user_id: str, client_id: str, 
                                 resource_id: str, permission: Permission) -> bool:
        """
        Grant specific permission for a resource.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            resource_id: Resource identifier
            permission: Permission to grant
            
        Returns:
            True if permission was granted successfully
        """
        user_permissions = self.get_user_permissions(user_id, client_id)
        if not user_permissions:
            return False
        
        if resource_id not in user_permissions.resource_permissions:
            user_permissions.resource_permissions[resource_id] = set()
        
        user_permissions.resource_permissions[resource_id].add(permission)
        user_permissions.updated_at = datetime.utcnow()
        
        # Save updated permissions
        self._save_user_permissions(user_permissions)
        
        logger.info(f"Granted {permission.value} permission on resource {resource_id} to user {client_id}:{user_id}")
        return True
    
    def revoke_resource_permission(self, user_id: str, client_id: str, 
                                  resource_id: str, permission: Permission) -> bool:
        """
        Revoke specific permission for a resource.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            resource_id: Resource identifier
            permission: Permission to revoke
            
        Returns:
            True if permission was revoked successfully
        """
        user_permissions = self.get_user_permissions(user_id, client_id)
        if not user_permissions:
            return False
        
        if resource_id in user_permissions.resource_permissions:
            user_permissions.resource_permissions[resource_id].discard(permission)
            
            # Remove empty permission sets
            if not user_permissions.resource_permissions[resource_id]:
                del user_permissions.resource_permissions[resource_id]
            
            user_permissions.updated_at = datetime.utcnow()
            
            # Save updated permissions
            self._save_user_permissions(user_permissions)
            
            logger.info(f"Revoked {permission.value} permission on resource {resource_id} from user {client_id}:{user_id}")
            return True
        
        return False
    
    def update_user_access_level(self, user_id: str, client_id: str, 
                                new_access_level: AccessLevel) -> bool:
        """
        Update user's access level.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            new_access_level: New access level
            
        Returns:
            True if access level was updated successfully
        """
        user_permissions = self.get_user_permissions(user_id, client_id)
        if not user_permissions:
            return False
        
        # Update access level and base permissions
        user_permissions.access_level = new_access_level
        user_permissions.permissions = self._access_level_permissions.get(new_access_level, set())
        user_permissions.updated_at = datetime.utcnow()
        
        # Save updated permissions
        self._save_user_permissions(user_permissions)
        
        logger.info(f"Updated access level for user {client_id}:{user_id} to {new_access_level.value}")
        return True
    
    def deactivate_user(self, user_id: str, client_id: str) -> bool:
        """
        Deactivate user permissions.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            
        Returns:
            True if user was deactivated successfully
        """
        user_permissions = self.get_user_permissions(user_id, client_id)
        if not user_permissions:
            return False
        
        user_permissions.is_active = False
        user_permissions.updated_at = datetime.utcnow()
        
        # Save updated permissions
        self._save_user_permissions(user_permissions)
        
        # Remove from cache
        cache_key = f"{client_id}:{user_id}"
        if cache_key in self._user_permissions:
            del self._user_permissions[cache_key]
        
        logger.info(f"Deactivated user permissions for {client_id}:{user_id}")
        return True
    
    def list_user_permissions(self, client_id: str) -> List[UserPermissions]:
        """
        List all user permissions for a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            List of UserPermissions objects
        """
        permissions_dir = self.config.get_full_path(f"security/permissions/{client_id}")
        
        if not permissions_dir.exists():
            return []
        
        user_permissions_list = []
        for perm_file in permissions_dir.glob("*.json"):
            try:
                user_permissions = self._load_user_permissions_from_file(perm_file)
                if user_permissions:
                    user_permissions_list.append(user_permissions)
            except Exception as e:
                logger.warning(f"Failed to load permissions from {perm_file}: {e}")
        
        return user_permissions_list
    
    def _save_user_permissions(self, user_permissions: UserPermissions) -> None:
        """Save user permissions to storage."""
        permissions_dir = self.config.get_full_path(f"security/permissions/{user_permissions.client_id}")
        permissions_dir.mkdir(parents=True, exist_ok=True)
        
        permissions_file = permissions_dir / f"{user_permissions.user_id}.json"
        
        permissions_data = {
            'user_id': user_permissions.user_id,
            'client_id': user_permissions.client_id,
            'user_name': user_permissions.user_name,
            'access_level': user_permissions.access_level.value,
            'permissions': [p.value for p in user_permissions.permissions],
            'resource_permissions': {
                resource_id: [p.value for p in perms]
                for resource_id, perms in user_permissions.resource_permissions.items()
            },
            'created_at': user_permissions.created_at.isoformat(),
            'updated_at': user_permissions.updated_at.isoformat(),
            'is_active': user_permissions.is_active
        }
        
        with open(permissions_file, 'w') as f:
            json.dump(permissions_data, f, indent=2)
        
        # Set restrictive permissions
        import os
        os.chmod(permissions_file, 0o600)
    
    def _load_user_permissions(self, user_id: str, client_id: str) -> Optional[UserPermissions]:
        """Load user permissions from storage."""
        permissions_file = self.config.get_full_path(f"security/permissions/{client_id}/{user_id}.json")
        
        if not permissions_file.exists():
            return None
        
        return self._load_user_permissions_from_file(permissions_file)
    
    def _load_user_permissions_from_file(self, permissions_file: Path) -> Optional[UserPermissions]:
        """Load user permissions from a specific file."""
        try:
            with open(permissions_file, 'r') as f:
                permissions_data = json.load(f)
            
            # Convert string permissions back to enums
            permissions = {Permission(p) for p in permissions_data['permissions']}
            resource_permissions = {
                resource_id: {Permission(p) for p in perms}
                for resource_id, perms in permissions_data['resource_permissions'].items()
            }
            
            return UserPermissions(
                user_id=permissions_data['user_id'],
                client_id=permissions_data['client_id'],
                user_name=permissions_data.get('user_name'),
                access_level=AccessLevel(permissions_data['access_level']),
                permissions=permissions,
                resource_permissions=resource_permissions,
                created_at=datetime.fromisoformat(permissions_data['created_at']),
                updated_at=datetime.fromisoformat(permissions_data['updated_at']),
                is_active=permissions_data.get('is_active', True)
            )
        except Exception as e:
            logger.error(f"Failed to load user permissions from {permissions_file}: {e}")
            return None
    
    def delete_user_permissions(self, user_id: str, client_id: str) -> bool:
        """
        Delete user permissions.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            
        Returns:
            True if permissions were deleted successfully
        """
        try:
            # Remove from cache
            cache_key = f"{client_id}:{user_id}"
            if cache_key in self._user_permissions:
                del self._user_permissions[cache_key]
            
            # Delete permissions file
            permissions_file = self.config.get_full_path(f"security/permissions/{client_id}/{user_id}.json")
            if permissions_file.exists():
                permissions_file.unlink()
            
            logger.info(f"Deleted permissions for user {client_id}:{user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete user permissions for {client_id}:{user_id}: {e}")
            return False
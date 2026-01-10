"""
Comprehensive security manager integrating all security components.

Provides a unified interface for all security operations including user management,
data isolation, access control, encryption, and audit logging.
"""

from typing import Dict, Any, List, Optional, Union, Tuple
from contextlib import contextmanager
from datetime import datetime

from ..core.models import AccessLevel, ResourceMetadata
from ..config import Config, get_config
from ..logger import get_logger
from .user_manager import UserManager, User
from .isolation import DataIsolationLayer, UserNamespace
from .access_control import AccessControlLayer, AccessRequest, ResourceAction
from .encryption import UserEncryptionManager
from .transaction_manager import TransactionManager
from .audit_logger import AuditLogger, AuditEventType, AuditSeverity
from .connection_pool import IsolatedConnectionManager

logger = get_logger(__name__)


class SecurityManager:
    """
    Unified security manager for the Intelligent AI Data Analyst System.
    
    Integrates all security components to provide comprehensive data protection,
    user management, access control, and audit logging.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize security manager with all components."""
        self.config = config or get_config()
        
        # Initialize all security components
        self.user_manager = UserManager(config)
        self.data_isolation = DataIsolationLayer(config)
        self.access_control = AccessControlLayer(config)
        self.encryption_manager = UserEncryptionManager(config)
        self.transaction_manager = TransactionManager(config)
        self.audit_logger = AuditLogger(config)
        self.connection_manager = IsolatedConnectionManager(config)
        
        logger.info("Security manager initialized with all components")
    
    # User Management Operations
    
    def create_user(self, client_id: str, user_name: str, 
                   email: Optional[str] = None, full_name: Optional[str] = None,
                   access_level: AccessLevel = AccessLevel.USER,
                   metadata: Optional[Dict[str, Any]] = None) -> User:
        """
        Create a new user with complete security setup.
        
        Args:
            client_id: Client identifier
            user_name: Human-readable username (unique within client)
            email: Optional email address
            full_name: Optional full name
            access_level: User access level
            metadata: Optional additional metadata
            
        Returns:
            Created User object
        """
        # Create user through user manager (handles all setup)
        user = self.user_manager.create_user(
            client_id=client_id,
            user_name=user_name,
            email=email,
            full_name=full_name,
            access_level=access_level,
            metadata=metadata
        )
        
        logger.info(f"Created secure user: {client_id}:{user_name}")
        return user
    
    def authenticate_user(self, client_id: str, user_name: str, 
                         password: Optional[str] = None) -> Optional[User]:
        """
        Authenticate user and return user object if successful.
        
        Args:
            client_id: Client identifier
            user_name: Username
            password: Optional password (for future use)
            
        Returns:
            User object if authentication successful, None otherwise
        """
        return self.user_manager.authenticate_user(client_id, user_name, password)
    
    def get_user_by_username(self, client_id: str, user_name: str) -> Optional[User]:
        """
        Get user by username (for simplified access).
        
        Args:
            client_id: Client identifier
            user_name: Username to look up
            
        Returns:
            User object or None if not found
        """
        return self.user_manager.get_user_by_username(client_id, user_name)
    
    def get_user_id_by_username(self, client_id: str, user_name: str) -> Optional[str]:
        """
        Get user_id by username (for simplified access).
        
        Args:
            client_id: Client identifier
            user_name: Username to look up
            
        Returns:
            User ID or None if not found
        """
        return self.user_manager.get_user_id_by_username(client_id, user_name)
    
    # Access Control Operations
    
    def validate_access(self, user_id: str, client_id: str, 
                       action: ResourceAction, resource_id: Optional[str] = None,
                       additional_context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Validate user access for a specific action.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            action: Action being performed
            resource_id: Optional resource identifier
            additional_context: Optional additional context
            
        Returns:
            True if access is granted
        """
        request = AccessRequest(
            user_id=user_id,
            client_id=client_id,
            resource_id=resource_id,
            action=action,
            additional_context=additional_context
        )
        
        result = self.access_control.validate_access(request)
        
        # Log access attempt
        if result.granted:
            self.audit_logger.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                action=f"Access granted for {action.value}",
                severity=AuditSeverity.INFO,
                user_id=user_id,
                client_id=client_id,
                resource_id=resource_id,
                details={'action': action.value}
            )
        else:
            self.audit_logger.log_event(
                event_type=AuditEventType.ACCESS_DENIED,
                action=f"Access denied for {action.value}: {result.reason}",
                severity=AuditSeverity.WARNING,
                user_id=user_id,
                client_id=client_id,
                resource_id=resource_id,
                details={'action': action.value, 'reason': result.reason}
            )
        
        return result.granted
    
    def validate_data_access(self, user_id: str, client_id: str, 
                           resource_ids: List[str]) -> bool:
        """
        Validate that user can access specified resources.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            resource_ids: List of resource IDs to validate
            
        Returns:
            True if user can access all resources
        """
        return self.data_isolation.validate_data_access(user_id, client_id, resource_ids)
    
    # Data Isolation Operations
    
    @contextmanager
    def get_isolated_connection(self, user_id: str, client_id: str, db_type: str = 'duckdb'):
        """
        Get isolated database connection for a user.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            db_type: Database type ('duckdb' or 'sqlite')
            
        Yields:
            Database connection within user's isolated environment
        """
        # Validate user exists and is active
        user = self.user_manager.get_user(user_id, client_id)
        if not user or not user.is_active:
            raise ValueError(f"User {client_id}:{user_id} not found or inactive")
        
        # Get isolated connection
        with self.data_isolation.get_isolated_connection(user_id, client_id, db_type) as conn:
            yield conn
    
    def execute_isolated_query(self, user_id: str, client_id: str, 
                              query: str, parameters: Optional[List] = None,
                              db_type: str = 'duckdb') -> List[Dict[str, Any]]:
        """
        Execute query within user's isolated environment with access validation.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            query: SQL query to execute
            parameters: Optional query parameters
            db_type: Database type ('duckdb' or 'sqlite')
            
        Returns:
            Query results
        """
        # Validate query access
        if not self.validate_access(user_id, client_id, ResourceAction.QUERY):
            raise PermissionError(f"User {client_id}:{user_id} does not have query permissions")
        
        # Execute query in isolated environment
        results = self.data_isolation.execute_isolated_query(
            user_id, client_id, query, parameters, db_type
        )
        
        # Log query execution
        self.audit_logger.log_data_access(
            user_id=user_id,
            client_id=client_id,
            resource_id=None,
            action="Query executed",
            details={
                'query': query[:100] + '...' if len(query) > 100 else query,
                'db_type': db_type,
                'result_count': len(results)
            }
        )
        
        return results
    
    # Transaction Management
    
    @contextmanager
    def secure_transaction(self, user_id: str, client_id: str, 
                          isolation_level: str = "READ_COMMITTED"):
        """
        Create secure transaction with user validation and audit logging.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            isolation_level: Transaction isolation level
            
        Yields:
            Transaction ID
        """
        # Validate user
        user = self.user_manager.get_user(user_id, client_id)
        if not user or not user.is_active:
            raise ValueError(f"User {client_id}:{user_id} not found or inactive")
        
        # Start transaction
        with self.transaction_manager.transaction(user_id, client_id, isolation_level) as transaction_id:
            # Log transaction start
            self.audit_logger.log_transaction_event(
                transaction_id=transaction_id,
                event_type=AuditEventType.TRANSACTION_START,
                action="Transaction started",
                user_id=user_id,
                client_id=client_id,
                details={'isolation_level': isolation_level}
            )
            
            try:
                yield transaction_id
                
                # Log transaction commit
                self.audit_logger.log_transaction_event(
                    transaction_id=transaction_id,
                    event_type=AuditEventType.TRANSACTION_COMMIT,
                    action="Transaction committed",
                    user_id=user_id,
                    client_id=client_id
                )
                
            except Exception as e:
                # Log transaction rollback
                self.audit_logger.log_transaction_event(
                    transaction_id=transaction_id,
                    event_type=AuditEventType.TRANSACTION_ROLLBACK,
                    action=f"Transaction rolled back: {str(e)}",
                    user_id=user_id,
                    client_id=client_id,
                    details={'error': str(e)}
                )
                raise
    
    # Encryption Operations
    
    def encrypt_user_data(self, data: Union[str, bytes], user_id: str, client_id: str) -> bytes:
        """
        Encrypt data for a specific user.
        
        Args:
            data: Data to encrypt
            user_id: User identifier
            client_id: Client identifier
            
        Returns:
            Encrypted data
        """
        # Validate user
        user = self.user_manager.get_user(user_id, client_id)
        if not user or not user.is_active:
            raise ValueError(f"User {client_id}:{user_id} not found or inactive")
        
        encrypted_data = self.encryption_manager.encryption_engine.encrypt_data(
            data, user_id, client_id
        )
        
        # Log encryption
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            action="Data encrypted",
            severity=AuditSeverity.INFO,
            user_id=user_id,
            client_id=client_id,
            details={'data_size': len(data) if isinstance(data, (str, bytes)) else 0}
        )
        
        return encrypted_data
    
    def decrypt_user_data(self, encrypted_data: bytes, user_id: str, client_id: str) -> bytes:
        """
        Decrypt data for a specific user.
        
        Args:
            encrypted_data: Encrypted data
            user_id: User identifier
            client_id: Client identifier
            
        Returns:
            Decrypted data
        """
        # Validate user
        user = self.user_manager.get_user(user_id, client_id)
        if not user or not user.is_active:
            raise ValueError(f"User {client_id}:{user_id} not found or inactive")
        
        decrypted_data = self.encryption_manager.encryption_engine.decrypt_data(
            encrypted_data, user_id, client_id
        )
        
        # Log decryption
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            action="Data decrypted",
            severity=AuditSeverity.INFO,
            user_id=user_id,
            client_id=client_id,
            details={'data_size': len(decrypted_data)}
        )
        
        return decrypted_data
    
    # User Lifecycle Management
    
    def delete_user_completely(self, user_id: str, client_id: str) -> bool:
        """
        Completely delete user and all associated data.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            
        Returns:
            True if deletion was successful
        """
        try:
            # Close connection pools for user
            self.connection_manager.close_user_pools(user_id, client_id)
            
            # Delete user through user manager (handles all cleanup)
            success = self.user_manager.delete_user(user_id, client_id, hard_delete=True)
            
            if success:
                logger.info(f"Completely deleted user and all data: {client_id}:{user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to completely delete user {client_id}:{user_id}: {e}")
            return False
    
    # System Operations
    
    def get_security_statistics(self, client_id: str) -> Dict[str, Any]:
        """
        Get comprehensive security statistics for a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Security statistics
        """
        return {
            'users': self.user_manager.get_user_statistics(client_id),
            'audit': self.audit_logger.get_audit_statistics(days=30),
            'connections': self.connection_manager.get_pool_statistics(),
            'namespaces': len(self.data_isolation.list_user_namespaces(client_id))
        }
    
    def verify_system_integrity(self) -> Dict[str, Any]:
        """
        Verify system integrity across all security components.
        
        Returns:
            Integrity verification results
        """
        results = {
            'overall_status': 'healthy',
            'components': {},
            'issues': []
        }
        
        try:
            # Verify audit log integrity
            audit_results = self.audit_logger.verify_integrity()
            results['components']['audit_logs'] = audit_results
            
            if not audit_results['verified']:
                results['overall_status'] = 'compromised'
                results['issues'].extend(audit_results['errors'])
            
            # Add other integrity checks as needed
            
        except Exception as e:
            results['overall_status'] = 'error'
            results['issues'].append(f"Integrity check failed: {str(e)}")
        
        return results
    
    def cleanup_system(self, max_age_days: int = 30) -> Dict[str, Any]:
        """
        Perform system cleanup operations.
        
        Args:
            max_age_days: Maximum age for cleanup operations
            
        Returns:
            Cleanup results
        """
        results = {
            'transactions_cleaned': 0,
            'connections_optimized': 0,
            'audit_records_processed': 0
        }
        
        try:
            # Cleanup stale transactions
            results['transactions_cleaned'] = self.transaction_manager.cleanup_stale_transactions(
                max_age_hours=max_age_days * 24
            )
            
            # Force audit log flush
            self.audit_logger.flush()
            
            logger.info(f"System cleanup completed: {results}")
            
        except Exception as e:
            logger.error(f"System cleanup failed: {e}")
            results['error'] = str(e)
        
        return results
    
    def shutdown(self) -> None:
        """Shutdown security manager and all components."""
        try:
            # Flush audit logs
            self.audit_logger.flush()
            
            # Close all connection pools
            self.connection_manager.close_all_pools()
            
            logger.info("Security manager shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during security manager shutdown: {e}")
    
    # Convenience methods for common operations
    
    def create_user_with_username(self, client_id: str, user_name: str, 
                                 access_level: AccessLevel = AccessLevel.USER) -> Tuple[str, User]:
        """
        Create user and return both user_id and User object.
        
        Args:
            client_id: Client identifier
            user_name: Human-readable username
            access_level: User access level
            
        Returns:
            Tuple of (user_id, User object)
        """
        user = self.create_user(client_id, user_name, access_level=access_level)
        return user.user_id, user
    
    def validate_user_resource_access(self, client_id: str, user_name: str, 
                                    resource_id: str, action: ResourceAction) -> bool:
        """
        Validate access using username instead of user_id.
        
        Args:
            client_id: Client identifier
            user_name: Username
            resource_id: Resource identifier
            action: Action being performed
            
        Returns:
            True if access is granted
        """
        user_id = self.get_user_id_by_username(client_id, user_name)
        if not user_id:
            return False
        
        return self.validate_access(user_id, client_id, action, resource_id)
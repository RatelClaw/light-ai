"""
Encryption engine for user-specific data protection.

Provides per-user encryption keys, secure storage, and data encryption/decryption
with support for key rotation and secure key management.
"""

import os
import secrets
import hashlib
from pathlib import Path
from typing import Dict, Optional, Any, Union, List
from dataclasses import dataclass
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import json

from ..config import Config, get_config
from ..logger import get_logger

logger = get_logger(__name__)


@dataclass
class UserEncryptionKey:
    """User-specific encryption key information."""
    user_id: str
    client_id: str
    key_id: str
    encrypted_key: bytes
    salt: bytes
    created_at: datetime
    last_used: datetime
    is_active: bool = True


class EncryptionEngine:
    """
    Core encryption engine for data protection.
    
    Provides symmetric encryption using Fernet (AES 128 in CBC mode with HMAC SHA256).
    Each user gets their own encryption key derived from a master key and user-specific salt.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize encryption engine.
        
        Args:
            config: Optional configuration instance
        """
        self.config = config or get_config()
        self._master_key = self._get_or_create_master_key()
        self._user_keys: Dict[str, Fernet] = {}
        self._key_cache_ttl = 3600  # 1 hour cache TTL
        
    def _get_or_create_master_key(self) -> bytes:
        """Get or create the master encryption key."""
        key_file = self.config.get_full_path("security/master.key")
        key_file.parent.mkdir(parents=True, exist_ok=True)
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                master_key = f.read()
            logger.info("Loaded existing master encryption key")
        else:
            # Generate new master key
            master_key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(master_key)
            # Set restrictive permissions
            os.chmod(key_file, 0o600)
            logger.info("Generated new master encryption key")
            
        return master_key
    
    def _derive_user_key(self, user_id: str, client_id: str, salt: bytes) -> bytes:
        """
        Derive a user-specific encryption key from master key and salt.
        
        Args:
            user_id: User identifier
            client_id: Client identifier  
            salt: Random salt for key derivation
            
        Returns:
            Derived encryption key
        """
        # Combine user_id and client_id for key derivation
        user_data = f"{client_id}:{user_id}".encode('utf-8')
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        # Derive key from master key + user data
        derived_key = kdf.derive(self._master_key + user_data)
        return base64.urlsafe_b64encode(derived_key)
    
    def get_user_fernet(self, user_id: str, client_id: str) -> Fernet:
        """
        Get Fernet instance for a specific user.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            
        Returns:
            Fernet instance for user encryption/decryption
        """
        cache_key = f"{client_id}:{user_id}"
        
        if cache_key in self._user_keys:
            return self._user_keys[cache_key]
        
        # Load or create user key
        user_key_info = self._load_user_key(user_id, client_id)
        if not user_key_info:
            user_key_info = self._create_user_key(user_id, client_id)
        
        # Derive the actual encryption key
        derived_key = self._derive_user_key(user_id, client_id, user_key_info.salt)
        fernet = Fernet(derived_key)
        
        # Cache the Fernet instance
        self._user_keys[cache_key] = fernet
        
        return fernet
    
    def _load_user_key(self, user_id: str, client_id: str) -> Optional[UserEncryptionKey]:
        """Load user encryption key from storage."""
        key_file = self.config.get_full_path(f"security/users/{client_id}/{user_id}.key")
        
        if not key_file.exists():
            return None
        
        try:
            with open(key_file, 'r') as f:
                key_data = json.load(f)
            
            return UserEncryptionKey(
                user_id=key_data['user_id'],
                client_id=key_data['client_id'],
                key_id=key_data['key_id'],
                encrypted_key=base64.b64decode(key_data['encrypted_key']),
                salt=base64.b64decode(key_data['salt']),
                created_at=datetime.fromisoformat(key_data['created_at']),
                last_used=datetime.fromisoformat(key_data['last_used']),
                is_active=key_data.get('is_active', True)
            )
        except Exception as e:
            logger.error(f"Failed to load user key for {client_id}:{user_id}: {e}")
            return None
    
    def _create_user_key(self, user_id: str, client_id: str) -> UserEncryptionKey:
        """Create new user encryption key."""
        key_file = self.config.get_full_path(f"security/users/{client_id}/{user_id}.key")
        key_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate random salt for this user
        salt = os.urandom(32)
        key_id = secrets.token_hex(16)
        
        # Create user key info
        user_key_info = UserEncryptionKey(
            user_id=user_id,
            client_id=client_id,
            key_id=key_id,
            encrypted_key=b'',  # Not used in current implementation
            salt=salt,
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow(),
            is_active=True
        )
        
        # Save to file
        key_data = {
            'user_id': user_id,
            'client_id': client_id,
            'key_id': key_id,
            'encrypted_key': base64.b64encode(b'').decode('utf-8'),
            'salt': base64.b64encode(salt).decode('utf-8'),
            'created_at': user_key_info.created_at.isoformat(),
            'last_used': user_key_info.last_used.isoformat(),
            'is_active': user_key_info.is_active
        }
        
        with open(key_file, 'w') as f:
            json.dump(key_data, f, indent=2)
        
        # Set restrictive permissions
        os.chmod(key_file, 0o600)
        
        logger.info(f"Created new encryption key for user {client_id}:{user_id}")
        return user_key_info
    
    def encrypt_data(self, data: Union[str, bytes], user_id: str, client_id: str) -> bytes:
        """
        Encrypt data for a specific user.
        
        Args:
            data: Data to encrypt (string or bytes)
            user_id: User identifier
            client_id: Client identifier
            
        Returns:
            Encrypted data as bytes
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        fernet = self.get_user_fernet(user_id, client_id)
        encrypted_data = fernet.encrypt(data)
        
        # Update last used timestamp
        self._update_key_usage(user_id, client_id)
        
        return encrypted_data
    
    def decrypt_data(self, encrypted_data: bytes, user_id: str, client_id: str) -> bytes:
        """
        Decrypt data for a specific user.
        
        Args:
            encrypted_data: Encrypted data as bytes
            user_id: User identifier
            client_id: Client identifier
            
        Returns:
            Decrypted data as bytes
        """
        fernet = self.get_user_fernet(user_id, client_id)
        decrypted_data = fernet.decrypt(encrypted_data)
        
        # Update last used timestamp
        self._update_key_usage(user_id, client_id)
        
        return decrypted_data
    
    def encrypt_file(self, file_path: Union[str, Path], user_id: str, client_id: str) -> Path:
        """
        Encrypt a file for a specific user.
        
        Args:
            file_path: Path to file to encrypt
            user_id: User identifier
            client_id: Client identifier
            
        Returns:
            Path to encrypted file
        """
        file_path = Path(file_path)
        encrypted_path = file_path.with_suffix(file_path.suffix + '.enc')
        
        with open(file_path, 'rb') as infile:
            data = infile.read()
        
        encrypted_data = self.encrypt_data(data, user_id, client_id)
        
        with open(encrypted_path, 'wb') as outfile:
            outfile.write(encrypted_data)
        
        logger.info(f"Encrypted file: {file_path} -> {encrypted_path}")
        return encrypted_path
    
    def decrypt_file(self, encrypted_file_path: Union[str, Path], 
                    user_id: str, client_id: str, output_path: Optional[Path] = None) -> Path:
        """
        Decrypt a file for a specific user.
        
        Args:
            encrypted_file_path: Path to encrypted file
            user_id: User identifier
            client_id: Client identifier
            output_path: Optional output path (defaults to removing .enc extension)
            
        Returns:
            Path to decrypted file
        """
        encrypted_file_path = Path(encrypted_file_path)
        
        if output_path is None:
            if encrypted_file_path.suffix == '.enc':
                output_path = encrypted_file_path.with_suffix('')
            else:
                output_path = encrypted_file_path.with_suffix('.dec')
        
        with open(encrypted_file_path, 'rb') as infile:
            encrypted_data = infile.read()
        
        decrypted_data = self.decrypt_data(encrypted_data, user_id, client_id)
        
        with open(output_path, 'wb') as outfile:
            outfile.write(decrypted_data)
        
        logger.info(f"Decrypted file: {encrypted_file_path} -> {output_path}")
        return output_path
    
    def _update_key_usage(self, user_id: str, client_id: str) -> None:
        """Update the last used timestamp for a user key."""
        try:
            key_file = self.config.get_full_path(f"security/users/{client_id}/{user_id}.key")
            if key_file.exists():
                with open(key_file, 'r') as f:
                    key_data = json.load(f)
                
                key_data['last_used'] = datetime.utcnow().isoformat()
                
                with open(key_file, 'w') as f:
                    json.dump(key_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to update key usage for {client_id}:{user_id}: {e}")
    
    def rotate_user_key(self, user_id: str, client_id: str) -> str:
        """
        Rotate encryption key for a user.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            
        Returns:
            New key ID
        """
        # Remove from cache
        cache_key = f"{client_id}:{user_id}"
        if cache_key in self._user_keys:
            del self._user_keys[cache_key]
        
        # Create new key
        new_key_info = self._create_user_key(user_id, client_id)
        
        logger.info(f"Rotated encryption key for user {client_id}:{user_id}")
        return new_key_info.key_id
    
    def delete_user_key(self, user_id: str, client_id: str) -> bool:
        """
        Delete encryption key for a user.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            
        Returns:
            True if key was deleted successfully
        """
        try:
            # Remove from cache
            cache_key = f"{client_id}:{user_id}"
            if cache_key in self._user_keys:
                del self._user_keys[cache_key]
            
            # Delete key file
            key_file = self.config.get_full_path(f"security/users/{client_id}/{user_id}.key")
            if key_file.exists():
                key_file.unlink()
                logger.info(f"Deleted encryption key for user {client_id}:{user_id}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Failed to delete user key for {client_id}:{user_id}: {e}")
            return False


class UserEncryptionManager:
    """
    High-level manager for user encryption operations.
    
    Provides user lifecycle management including key creation, rotation, and deletion.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize user encryption manager."""
        self.config = config or get_config()
        self.encryption_engine = EncryptionEngine(config)
    
    def create_user_namespace(self, user_id: str, client_id: str, user_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create encrypted namespace for a new user.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            user_name: Optional human-readable username
            
        Returns:
            Dictionary with namespace information
        """
        # Create encryption key
        user_key_info = self.encryption_engine._create_user_key(user_id, client_id)
        
        # Create user directory structure
        user_dir = self.config.get_full_path(f"data/users/{client_id}/{user_id}")
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different data types
        subdirs = ['structured', 'json', 'unstructured', 'temp']
        for subdir in subdirs:
            (user_dir / subdir).mkdir(exist_ok=True)
        
        # Store user metadata
        user_metadata = {
            'user_id': user_id,
            'client_id': client_id,
            'user_name': user_name,
            'key_id': user_key_info.key_id,
            'created_at': user_key_info.created_at.isoformat(),
            'namespace_path': str(user_dir),
            'encryption_enabled': True
        }
        
        metadata_file = user_dir / 'user_metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(user_metadata, f, indent=2)
        
        logger.info(f"Created encrypted namespace for user {client_id}:{user_id}")
        return user_metadata
    
    def get_user_namespace_info(self, user_id: str, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user namespace information.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            
        Returns:
            User namespace information or None if not found
        """
        metadata_file = self.config.get_full_path(f"data/users/{client_id}/{user_id}/user_metadata.json")
        
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load user namespace info for {client_id}:{user_id}: {e}")
            return None
    
    def delete_user_namespace(self, user_id: str, client_id: str) -> bool:
        """
        Delete user namespace and all associated data.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            
        Returns:
            True if deletion was successful
        """
        try:
            import shutil
            
            # Delete encryption key
            self.encryption_engine.delete_user_key(user_id, client_id)
            
            # Delete user directory
            user_dir = self.config.get_full_path(f"data/users/{client_id}/{user_id}")
            if user_dir.exists():
                shutil.rmtree(user_dir)
            
            logger.info(f"Deleted user namespace for {client_id}:{user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete user namespace for {client_id}:{user_id}: {e}")
            return False
    
    def list_user_namespaces(self, client_id: str) -> List[Dict[str, Any]]:
        """
        List all user namespaces for a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            List of user namespace information
        """
        client_dir = self.config.get_full_path(f"data/users/{client_id}")
        
        if not client_dir.exists():
            return []
        
        namespaces = []
        for user_dir in client_dir.iterdir():
            if user_dir.is_dir():
                metadata_file = user_dir / 'user_metadata.json'
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            namespace_info = json.load(f)
                        namespaces.append(namespace_info)
                    except Exception as e:
                        logger.warning(f"Failed to load namespace info from {metadata_file}: {e}")
        
        return namespaces
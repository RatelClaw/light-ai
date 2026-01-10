"""
Audit logging system for comprehensive data access tracking.

Provides detailed audit trails for all data operations, security events,
and user activities with tamper-resistant logging and compliance features.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import threading
import uuid

from ..config import Config, get_config
from ..logger import get_logger

logger = get_logger(__name__)


class AuditEventType(Enum):
    """Types of audit events."""
    # Data operations
    DATA_ACCESS = "data_access"
    DATA_QUERY = "data_query"
    DATA_UPLOAD = "data_upload"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"
    
    # Security events
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    ACCESS_DENIED = "access_denied"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    
    # System events
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    
    # Transaction events
    TRANSACTION_START = "transaction_start"
    TRANSACTION_COMMIT = "transaction_commit"
    TRANSACTION_ROLLBACK = "transaction_rollback"
    
    # Administrative events
    USER_CREATED = "user_created"
    USER_DELETED = "user_deleted"
    SCHEMA_CREATED = "schema_created"
    SCHEMA_DELETED = "schema_deleted"


class AuditSeverity(Enum):
    """Audit event severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event record."""
    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: datetime
    user_id: Optional[str]
    client_id: Optional[str]
    resource_id: Optional[str]
    action: str
    details: Dict[str, Any]
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    transaction_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditEvent':
        """Create from dictionary."""
        data = data.copy()
        data['event_type'] = AuditEventType(data['event_type'])
        data['severity'] = AuditSeverity(data['severity'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class AuditLogger:
    """
    Comprehensive audit logging system.
    
    Provides tamper-resistant audit trails with integrity verification,
    structured logging, and compliance features.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize audit logger."""
        self.config = config or get_config()
        self._audit_lock = threading.Lock()
        self._log_buffer: List[AuditEvent] = []
        self._buffer_size = 100
        self._integrity_chain: List[str] = []
        
        # Ensure audit directory exists
        self.audit_dir = self.config.get_full_path("audit")
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize integrity chain
        self._load_integrity_chain()
    
    def log_event(self, event_type: AuditEventType, action: str, 
                  severity: AuditSeverity = AuditSeverity.INFO,
                  user_id: Optional[str] = None, client_id: Optional[str] = None,
                  resource_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None,
                  source_ip: Optional[str] = None, user_agent: Optional[str] = None,
                  session_id: Optional[str] = None, transaction_id: Optional[str] = None) -> str:
        """
        Log an audit event.
        
        Args:
            event_type: Type of audit event
            action: Description of the action performed
            severity: Event severity level
            user_id: Optional user identifier
            client_id: Optional client identifier
            resource_id: Optional resource identifier
            details: Optional additional details
            source_ip: Optional source IP address
            user_agent: Optional user agent string
            session_id: Optional session identifier
            transaction_id: Optional transaction identifier
            
        Returns:
            Event ID of the logged event
        """
        event_id = str(uuid.uuid4())
        
        audit_event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            severity=severity,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            client_id=client_id,
            resource_id=resource_id,
            action=action,
            details=details or {},
            source_ip=source_ip,
            user_agent=user_agent,
            session_id=session_id,
            transaction_id=transaction_id
        )
        
        with self._audit_lock:
            self._log_buffer.append(audit_event)
            
            # Flush buffer if it's full
            if len(self._log_buffer) >= self._buffer_size:
                self._flush_buffer()
        
        # Log critical events immediately
        if severity == AuditSeverity.CRITICAL:
            with self._audit_lock:
                self._flush_buffer()
        
        logger.debug(f"Logged audit event: {event_type.value} - {action}")
        return event_id
    
    def log_data_access(self, user_id: str, client_id: str, resource_id: str,
                       action: str, details: Optional[Dict[str, Any]] = None,
                       **kwargs) -> str:
        """
        Log data access event.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            resource_id: Resource identifier
            action: Action performed
            details: Optional additional details
            **kwargs: Additional audit parameters
            
        Returns:
            Event ID
        """
        return self.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            action=action,
            severity=AuditSeverity.INFO,
            user_id=user_id,
            client_id=client_id,
            resource_id=resource_id,
            details=details,
            **kwargs
        )
    
    def log_security_event(self, event_type: AuditEventType, action: str,
                          severity: AuditSeverity = AuditSeverity.WARNING,
                          user_id: Optional[str] = None, client_id: Optional[str] = None,
                          details: Optional[Dict[str, Any]] = None, **kwargs) -> str:
        """
        Log security event.
        
        Args:
            event_type: Security event type
            action: Action description
            severity: Event severity
            user_id: Optional user identifier
            client_id: Optional client identifier
            details: Optional additional details
            **kwargs: Additional audit parameters
            
        Returns:
            Event ID
        """
        return self.log_event(
            event_type=event_type,
            action=action,
            severity=severity,
            user_id=user_id,
            client_id=client_id,
            details=details,
            **kwargs
        )
    
    def log_transaction_event(self, transaction_id: str, event_type: AuditEventType,
                             action: str, user_id: str, client_id: str,
                             details: Optional[Dict[str, Any]] = None, **kwargs) -> str:
        """
        Log transaction event.
        
        Args:
            transaction_id: Transaction identifier
            event_type: Transaction event type
            action: Action description
            user_id: User identifier
            client_id: Client identifier
            details: Optional additional details
            **kwargs: Additional audit parameters
            
        Returns:
            Event ID
        """
        return self.log_event(
            event_type=event_type,
            action=action,
            severity=AuditSeverity.INFO,
            user_id=user_id,
            client_id=client_id,
            transaction_id=transaction_id,
            details=details,
            **kwargs
        )
    
    def _flush_buffer(self) -> None:
        """Flush audit buffer to persistent storage."""
        if not self._log_buffer:
            return
        
        # Create daily log file
        today = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = self.audit_dir / f"audit_{today}.jsonl"
        
        # Write events to file
        with open(log_file, 'a') as f:
            for event in self._log_buffer:
                event_data = event.to_dict()
                
                # Add integrity hash
                event_hash = self._calculate_event_hash(event_data)
                event_data['integrity_hash'] = event_hash
                
                # Write to file
                f.write(json.dumps(event_data) + '\n')
                
                # Update integrity chain
                self._integrity_chain.append(event_hash)
        
        # Clear buffer
        self._log_buffer.clear()
        
        # Save integrity chain
        self._save_integrity_chain()
        
        logger.debug(f"Flushed {len(self._log_buffer)} audit events to {log_file}")
    
    def _calculate_event_hash(self, event_data: Dict[str, Any]) -> str:
        """Calculate integrity hash for an event."""
        # Create deterministic string representation
        event_str = json.dumps(event_data, sort_keys=True, separators=(',', ':'))
        
        # Include previous hash in chain for tamper detection
        if self._integrity_chain:
            event_str += self._integrity_chain[-1]
        
        # Calculate SHA-256 hash
        return hashlib.sha256(event_str.encode('utf-8')).hexdigest()
    
    def _load_integrity_chain(self) -> None:
        """Load integrity chain from storage."""
        chain_file = self.audit_dir / "integrity_chain.json"
        
        if chain_file.exists():
            try:
                with open(chain_file, 'r') as f:
                    self._integrity_chain = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load integrity chain: {e}")
                self._integrity_chain = []
        else:
            self._integrity_chain = []
    
    def _save_integrity_chain(self) -> None:
        """Save integrity chain to storage."""
        chain_file = self.audit_dir / "integrity_chain.json"
        
        try:
            with open(chain_file, 'w') as f:
                json.dump(self._integrity_chain, f)
        except Exception as e:
            logger.error(f"Failed to save integrity chain: {e}")
    
    def query_events(self, start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None,
                    event_type: Optional[AuditEventType] = None,
                    user_id: Optional[str] = None,
                    client_id: Optional[str] = None,
                    resource_id: Optional[str] = None,
                    severity: Optional[AuditSeverity] = None,
                    limit: int = 1000) -> List[AuditEvent]:
        """
        Query audit events with filters.
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            event_type: Optional event type filter
            user_id: Optional user ID filter
            client_id: Optional client ID filter
            resource_id: Optional resource ID filter
            severity: Optional severity filter
            limit: Maximum number of events to return
            
        Returns:
            List of matching audit events
        """
        events = []
        
        # Determine date range for file scanning
        if start_date:
            start_str = start_date.strftime("%Y-%m-%d")
        else:
            start_str = "2020-01-01"  # Default start
        
        if end_date:
            end_str = end_date.strftime("%Y-%m-%d")
        else:
            end_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        # Scan log files in date range
        for log_file in self.audit_dir.glob("audit_*.jsonl"):
            file_date = log_file.stem.replace("audit_", "")
            
            if start_str <= file_date <= end_str:
                events.extend(self._read_log_file(log_file))
        
        # Apply filters
        filtered_events = []
        for event in events:
            if len(filtered_events) >= limit:
                break
            
            # Apply filters
            if start_date and event.timestamp < start_date:
                continue
            if end_date and event.timestamp > end_date:
                continue
            if event_type and event.event_type != event_type:
                continue
            if user_id and event.user_id != user_id:
                continue
            if client_id and event.client_id != client_id:
                continue
            if resource_id and event.resource_id != resource_id:
                continue
            if severity and event.severity != severity:
                continue
            
            filtered_events.append(event)
        
        # Sort by timestamp (newest first)
        filtered_events.sort(key=lambda e: e.timestamp, reverse=True)
        
        return filtered_events[:limit]
    
    def _read_log_file(self, log_file: Path) -> List[AuditEvent]:
        """Read audit events from a log file."""
        events = []
        
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            event_data = json.loads(line)
                            # Remove integrity hash before creating event
                            event_data.pop('integrity_hash', None)
                            event = AuditEvent.from_dict(event_data)
                            events.append(event)
                        except Exception as e:
                            logger.warning(f"Failed to parse audit event: {e}")
        except Exception as e:
            logger.error(f"Failed to read audit log file {log_file}: {e}")
        
        return events
    
    def verify_integrity(self, start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Verify audit log integrity.
        
        Args:
            start_date: Optional start date for verification
            end_date: Optional end date for verification
            
        Returns:
            Integrity verification results
        """
        results = {
            'verified': True,
            'total_events': 0,
            'verified_events': 0,
            'failed_events': 0,
            'errors': []
        }
        
        # Determine date range
        if start_date:
            start_str = start_date.strftime("%Y-%m-%d")
        else:
            start_str = "2020-01-01"
        
        if end_date:
            end_str = end_date.strftime("%Y-%m-%d")
        else:
            end_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        # Verify each log file
        for log_file in sorted(self.audit_dir.glob("audit_*.jsonl")):
            file_date = log_file.stem.replace("audit_", "")
            
            if start_str <= file_date <= end_str:
                file_results = self._verify_log_file(log_file)
                results['total_events'] += file_results['total_events']
                results['verified_events'] += file_results['verified_events']
                results['failed_events'] += file_results['failed_events']
                results['errors'].extend(file_results['errors'])
                
                if not file_results['verified']:
                    results['verified'] = False
        
        return results
    
    def _verify_log_file(self, log_file: Path) -> Dict[str, Any]:
        """Verify integrity of a single log file."""
        results = {
            'verified': True,
            'total_events': 0,
            'verified_events': 0,
            'failed_events': 0,
            'errors': []
        }
        
        try:
            with open(log_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    results['total_events'] += 1
                    
                    try:
                        event_data = json.loads(line)
                        stored_hash = event_data.pop('integrity_hash', None)
                        
                        if stored_hash:
                            calculated_hash = self._calculate_event_hash(event_data)
                            
                            if stored_hash == calculated_hash:
                                results['verified_events'] += 1
                            else:
                                results['failed_events'] += 1
                                results['verified'] = False
                                results['errors'].append(
                                    f"Integrity check failed for event at line {line_num} in {log_file.name}"
                                )
                        else:
                            results['errors'].append(
                                f"Missing integrity hash for event at line {line_num} in {log_file.name}"
                            )
                    except Exception as e:
                        results['errors'].append(
                            f"Failed to verify event at line {line_num} in {log_file.name}: {e}"
                        )
        except Exception as e:
            results['verified'] = False
            results['errors'].append(f"Failed to read log file {log_file}: {e}")
        
        return results
    
    def flush(self) -> None:
        """Force flush of audit buffer."""
        with self._audit_lock:
            self._flush_buffer()
    
    def get_audit_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get audit statistics for the specified number of days.
        
        Args:
            days: Number of days to include in statistics
            
        Returns:
            Audit statistics
        """
        end_date = datetime.utcnow()
        start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = start_date.replace(day=start_date.day - days + 1)
        
        events = self.query_events(start_date=start_date, end_date=end_date, limit=10000)
        
        stats = {
            'total_events': len(events),
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'events_by_type': {},
            'events_by_severity': {},
            'events_by_user': {},
            'events_by_client': {},
            'daily_counts': {}
        }
        
        for event in events:
            # Count by type
            event_type = event.event_type.value
            stats['events_by_type'][event_type] = stats['events_by_type'].get(event_type, 0) + 1
            
            # Count by severity
            severity = event.severity.value
            stats['events_by_severity'][severity] = stats['events_by_severity'].get(severity, 0) + 1
            
            # Count by user
            if event.user_id:
                user_key = f"{event.client_id}:{event.user_id}"
                stats['events_by_user'][user_key] = stats['events_by_user'].get(user_key, 0) + 1
            
            # Count by client
            if event.client_id:
                stats['events_by_client'][event.client_id] = stats['events_by_client'].get(event.client_id, 0) + 1
            
            # Count by day
            day_key = event.timestamp.strftime("%Y-%m-%d")
            stats['daily_counts'][day_key] = stats['daily_counts'].get(day_key, 0) + 1
        
        return stats
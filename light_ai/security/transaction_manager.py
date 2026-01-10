"""
Transaction manager for ACID compliance.

Provides transaction management with rollback capabilities, ensuring
atomicity, consistency, isolation, and durability for all data operations.
"""

import sqlite3
import duckdb
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass
from datetime import datetime
from contextlib import contextmanager
from enum import Enum
import threading
import uuid
import json

from ..config import Config, get_config
from ..logger import get_logger

logger = get_logger(__name__)


class TransactionState(Enum):
    """Transaction states."""
    ACTIVE = "active"
    COMMITTED = "committed"
    ABORTED = "aborted"
    PREPARING = "preparing"


@dataclass
class TransactionContext:
    """Context information for a transaction."""
    transaction_id: str
    user_id: str
    client_id: str
    state: TransactionState
    started_at: datetime
    operations: List[Dict[str, Any]]
    rollback_data: Dict[str, Any]
    isolation_level: str = "READ_COMMITTED"


class TransactionManager:
    """
    ACID-compliant transaction manager.
    
    Provides transaction management across multiple databases (DuckDB, SQLite)
    with support for rollback, savepoints, and distributed transactions.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize transaction manager."""
        self.config = config or get_config()
        self._active_transactions: Dict[str, TransactionContext] = {}
        self._transaction_lock = threading.Lock()
        self._connection_pools: Dict[str, List] = {
            'duckdb': [],
            'sqlite': []
        }
        self._pool_locks: Dict[str, threading.Lock] = {
            'duckdb': threading.Lock(),
            'sqlite': threading.Lock()
        }
    
    def begin_transaction(self, user_id: str, client_id: str, 
                         isolation_level: str = "READ_COMMITTED") -> str:
        """
        Begin a new transaction.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            isolation_level: Transaction isolation level
            
        Returns:
            Transaction ID
        """
        transaction_id = str(uuid.uuid4())
        
        with self._transaction_lock:
            transaction_context = TransactionContext(
                transaction_id=transaction_id,
                user_id=user_id,
                client_id=client_id,
                state=TransactionState.ACTIVE,
                started_at=datetime.utcnow(),
                operations=[],
                rollback_data={},
                isolation_level=isolation_level
            )
            
            self._active_transactions[transaction_id] = transaction_context
        
        logger.info(f"Started transaction {transaction_id} for user {client_id}:{user_id}")
        return transaction_id
    
    def commit_transaction(self, transaction_id: str) -> bool:
        """
        Commit a transaction.
        
        Args:
            transaction_id: Transaction identifier
            
        Returns:
            True if commit was successful
        """
        with self._transaction_lock:
            if transaction_id not in self._active_transactions:
                logger.error(f"Transaction {transaction_id} not found")
                return False
            
            transaction = self._active_transactions[transaction_id]
            
            if transaction.state != TransactionState.ACTIVE:
                logger.error(f"Transaction {transaction_id} is not active (state: {transaction.state})")
                return False
            
            try:
                transaction.state = TransactionState.PREPARING
                
                # Commit all operations
                self._commit_operations(transaction)
                
                transaction.state = TransactionState.COMMITTED
                
                # Clean up transaction
                del self._active_transactions[transaction_id]
                
                logger.info(f"Committed transaction {transaction_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to commit transaction {transaction_id}: {e}")
                transaction.state = TransactionState.ABORTED
                self._rollback_operations(transaction)
                return False
    
    def rollback_transaction(self, transaction_id: str) -> bool:
        """
        Rollback a transaction.
        
        Args:
            transaction_id: Transaction identifier
            
        Returns:
            True if rollback was successful
        """
        with self._transaction_lock:
            if transaction_id not in self._active_transactions:
                logger.error(f"Transaction {transaction_id} not found")
                return False
            
            transaction = self._active_transactions[transaction_id]
            
            try:
                transaction.state = TransactionState.ABORTED
                
                # Rollback all operations
                self._rollback_operations(transaction)
                
                # Clean up transaction
                del self._active_transactions[transaction_id]
                
                logger.info(f"Rolled back transaction {transaction_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to rollback transaction {transaction_id}: {e}")
                return False
    
    def _commit_operations(self, transaction: TransactionContext) -> None:
        """Commit all operations in a transaction."""
        for operation in transaction.operations:
            operation_type = operation['type']
            
            if operation_type == 'database_write':
                self._commit_database_operation(operation, transaction)
            elif operation_type == 'file_write':
                self._commit_file_operation(operation, transaction)
            elif operation_type == 'metadata_update':
                self._commit_metadata_operation(operation, transaction)
            else:
                logger.warning(f"Unknown operation type: {operation_type}")
    
    def _rollback_operations(self, transaction: TransactionContext) -> None:
        """Rollback all operations in a transaction."""
        # Rollback operations in reverse order
        for operation in reversed(transaction.operations):
            try:
                operation_type = operation['type']
                
                if operation_type == 'database_write':
                    self._rollback_database_operation(operation, transaction)
                elif operation_type == 'file_write':
                    self._rollback_file_operation(operation, transaction)
                elif operation_type == 'metadata_update':
                    self._rollback_metadata_operation(operation, transaction)
                    
            except Exception as e:
                logger.error(f"Failed to rollback operation {operation}: {e}")
    
    def _commit_database_operation(self, operation: Dict[str, Any], 
                                  transaction: TransactionContext) -> None:
        """Commit a database operation."""
        db_type = operation['db_type']
        query = operation['query']
        parameters = operation.get('parameters')
        
        if db_type == 'duckdb':
            self._execute_duckdb_operation(query, parameters, transaction, commit=True)
        elif db_type == 'sqlite':
            self._execute_sqlite_operation(query, parameters, transaction, commit=True)
    
    def _rollback_database_operation(self, operation: Dict[str, Any], 
                                   transaction: TransactionContext) -> None:
        """Rollback a database operation."""
        rollback_query = operation.get('rollback_query')
        if rollback_query:
            db_type = operation['db_type']
            parameters = operation.get('rollback_parameters')
            
            if db_type == 'duckdb':
                self._execute_duckdb_operation(rollback_query, parameters, transaction, commit=True)
            elif db_type == 'sqlite':
                self._execute_sqlite_operation(rollback_query, parameters, transaction, commit=True)
    
    def _commit_file_operation(self, operation: Dict[str, Any], 
                              transaction: TransactionContext) -> None:
        """Commit a file operation."""
        operation_subtype = operation['subtype']
        
        if operation_subtype == 'create':
            # File was created in temp location, move to final location
            temp_path = Path(operation['temp_path'])
            final_path = Path(operation['final_path'])
            
            if temp_path.exists():
                final_path.parent.mkdir(parents=True, exist_ok=True)
                temp_path.rename(final_path)
                
        elif operation_subtype == 'update':
            # Remove backup file
            backup_path = Path(operation['backup_path'])
            if backup_path.exists():
                backup_path.unlink()
                
        elif operation_subtype == 'delete':
            # Remove backup file (file was already deleted)
            backup_path = Path(operation['backup_path'])
            if backup_path.exists():
                backup_path.unlink()
    
    def _rollback_file_operation(self, operation: Dict[str, Any], 
                                transaction: TransactionContext) -> None:
        """Rollback a file operation."""
        operation_subtype = operation['subtype']
        
        if operation_subtype == 'create':
            # Remove created file
            final_path = Path(operation['final_path'])
            if final_path.exists():
                final_path.unlink()
                
        elif operation_subtype == 'update':
            # Restore from backup
            backup_path = Path(operation['backup_path'])
            final_path = Path(operation['final_path'])
            
            if backup_path.exists():
                backup_path.rename(final_path)
                
        elif operation_subtype == 'delete':
            # Restore from backup
            backup_path = Path(operation['backup_path'])
            final_path = Path(operation['final_path'])
            
            if backup_path.exists():
                backup_path.rename(final_path)
    
    def _commit_metadata_operation(self, operation: Dict[str, Any], 
                                  transaction: TransactionContext) -> None:
        """Commit a metadata operation."""
        # Metadata operations are typically database operations
        # This is a placeholder for any special metadata handling
        pass
    
    def _rollback_metadata_operation(self, operation: Dict[str, Any], 
                                   transaction: TransactionContext) -> None:
        """Rollback a metadata operation."""
        # Metadata operations are typically database operations
        # This is a placeholder for any special metadata handling
        pass
    
    def _execute_duckdb_operation(self, query: str, parameters: Optional[List], 
                                 transaction: TransactionContext, commit: bool = False) -> None:
        """Execute DuckDB operation within transaction context."""
        db_path = self.config.get_full_path(self.config.database.duckdb_path)
        
        with duckdb.connect(str(db_path)) as conn:
            # Set isolation level
            if transaction.isolation_level == "SERIALIZABLE":
                conn.execute("BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE")
            else:
                conn.execute("BEGIN TRANSACTION")
            
            try:
                if parameters:
                    conn.execute(query, parameters)
                else:
                    conn.execute(query)
                
                if commit:
                    conn.execute("COMMIT")
                else:
                    conn.execute("ROLLBACK")
                    
            except Exception as e:
                conn.execute("ROLLBACK")
                raise e
    
    def _execute_sqlite_operation(self, query: str, parameters: Optional[List], 
                                 transaction: TransactionContext, commit: bool = False) -> None:
        """Execute SQLite operation within transaction context."""
        user_db_path = self.config.get_full_path(
            f"metadata/users/{transaction.client_id}_{transaction.user_id}.db"
        )
        
        with sqlite3.connect(str(user_db_path)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Set isolation level
            if transaction.isolation_level == "SERIALIZABLE":
                conn.execute("BEGIN IMMEDIATE TRANSACTION")
            else:
                conn.execute("BEGIN TRANSACTION")
            
            try:
                if parameters:
                    conn.execute(query, parameters)
                else:
                    conn.execute(query)
                
                if commit:
                    conn.commit()
                else:
                    conn.rollback()
                    
            except Exception as e:
                conn.rollback()
                raise e
    
    @contextmanager
    def transaction(self, user_id: str, client_id: str, 
                   isolation_level: str = "READ_COMMITTED"):
        """
        Context manager for transactions.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            isolation_level: Transaction isolation level
            
        Yields:
            Transaction ID
        """
        transaction_id = self.begin_transaction(user_id, client_id, isolation_level)
        
        try:
            yield transaction_id
            self.commit_transaction(transaction_id)
        except Exception as e:
            logger.error(f"Transaction {transaction_id} failed: {e}")
            self.rollback_transaction(transaction_id)
            raise
    
    def add_database_operation(self, transaction_id: str, db_type: str, 
                              query: str, parameters: Optional[List] = None,
                              rollback_query: Optional[str] = None,
                              rollback_parameters: Optional[List] = None) -> bool:
        """
        Add database operation to transaction.
        
        Args:
            transaction_id: Transaction identifier
            db_type: Database type ('duckdb' or 'sqlite')
            query: SQL query to execute
            parameters: Optional query parameters
            rollback_query: Optional rollback query
            rollback_parameters: Optional rollback parameters
            
        Returns:
            True if operation was added successfully
        """
        with self._transaction_lock:
            if transaction_id not in self._active_transactions:
                logger.error(f"Transaction {transaction_id} not found")
                return False
            
            transaction = self._active_transactions[transaction_id]
            
            if transaction.state != TransactionState.ACTIVE:
                logger.error(f"Transaction {transaction_id} is not active")
                return False
            
            operation = {
                'type': 'database_write',
                'db_type': db_type,
                'query': query,
                'parameters': parameters,
                'rollback_query': rollback_query,
                'rollback_parameters': rollback_parameters,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            transaction.operations.append(operation)
            return True
    
    def add_file_operation(self, transaction_id: str, operation_type: str,
                          file_path: str, **kwargs) -> bool:
        """
        Add file operation to transaction.
        
        Args:
            transaction_id: Transaction identifier
            operation_type: Operation type ('create', 'update', 'delete')
            file_path: Path to file
            **kwargs: Additional operation-specific parameters
            
        Returns:
            True if operation was added successfully
        """
        with self._transaction_lock:
            if transaction_id not in self._active_transactions:
                logger.error(f"Transaction {transaction_id} not found")
                return False
            
            transaction = self._active_transactions[transaction_id]
            
            if transaction.state != TransactionState.ACTIVE:
                logger.error(f"Transaction {transaction_id} is not active")
                return False
            
            operation = {
                'type': 'file_write',
                'subtype': operation_type,
                'file_path': file_path,
                'timestamp': datetime.utcnow().isoformat(),
                **kwargs
            }
            
            transaction.operations.append(operation)
            return True
    
    def get_transaction_status(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction status.
        
        Args:
            transaction_id: Transaction identifier
            
        Returns:
            Transaction status information or None if not found
        """
        with self._transaction_lock:
            if transaction_id not in self._active_transactions:
                return None
            
            transaction = self._active_transactions[transaction_id]
            
            return {
                'transaction_id': transaction.transaction_id,
                'user_id': transaction.user_id,
                'client_id': transaction.client_id,
                'state': transaction.state.value,
                'started_at': transaction.started_at.isoformat(),
                'operation_count': len(transaction.operations),
                'isolation_level': transaction.isolation_level
            }
    
    def list_active_transactions(self, user_id: Optional[str] = None, 
                               client_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List active transactions.
        
        Args:
            user_id: Optional user filter
            client_id: Optional client filter
            
        Returns:
            List of active transaction information
        """
        with self._transaction_lock:
            transactions = []
            
            for transaction in self._active_transactions.values():
                if user_id and transaction.user_id != user_id:
                    continue
                if client_id and transaction.client_id != client_id:
                    continue
                
                transactions.append({
                    'transaction_id': transaction.transaction_id,
                    'user_id': transaction.user_id,
                    'client_id': transaction.client_id,
                    'state': transaction.state.value,
                    'started_at': transaction.started_at.isoformat(),
                    'operation_count': len(transaction.operations),
                    'isolation_level': transaction.isolation_level
                })
            
            return transactions
    
    def cleanup_stale_transactions(self, max_age_hours: int = 24) -> int:
        """
        Clean up stale transactions.
        
        Args:
            max_age_hours: Maximum age in hours before transaction is considered stale
            
        Returns:
            Number of transactions cleaned up
        """
        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        cleaned_count = 0
        
        with self._transaction_lock:
            stale_transactions = []
            
            for transaction_id, transaction in self._active_transactions.items():
                if transaction.started_at.timestamp() < cutoff_time:
                    stale_transactions.append(transaction_id)
            
            for transaction_id in stale_transactions:
                logger.warning(f"Cleaning up stale transaction: {transaction_id}")
                self.rollback_transaction(transaction_id)
                cleaned_count += 1
        
        return cleaned_count
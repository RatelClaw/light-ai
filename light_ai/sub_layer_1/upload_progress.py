"""
Upload progress tracking system for large file uploads.

Provides real-time progress updates and status monitoring for file upload operations.
"""

import threading
import time
from typing import Dict, Optional, Callable, Any
from datetime import datetime, timedelta

from ..core.models import UploadProgress
from ..logger import get_logger

logger = get_logger(__name__)


class UploadProgressTracker:
    """
    Tracks upload progress for multiple files with thread-safe operations.
    """
    
    def __init__(self):
        """Initialize progress tracker."""
        self._progress_data: Dict[str, UploadProgress] = {}
        self._lock = threading.RLock()
        self._callbacks: Dict[str, Callable[[UploadProgress], None]] = {}
    
    def start_upload(self, resource_id: str, filename: str, total_bytes: int) -> UploadProgress:
        """
        Start tracking progress for a new upload.
        
        Args:
            resource_id: Unique identifier for the resource
            filename: Name of the file being uploaded
            total_bytes: Total size of the file in bytes
            
        Returns:
            UploadProgress instance for tracking
        """
        with self._lock:
            progress = UploadProgress(
                resource_id=resource_id,
                filename=filename,
                total_bytes=total_bytes,
                status="uploading",
                stage="validation",
                message="Starting upload..."
            )
            
            self._progress_data[resource_id] = progress
            
            logger.info(f"Started tracking upload progress for {filename} ({resource_id})")
            
            return progress
    
    def update_progress(self, resource_id: str, uploaded_bytes: int, 
                       stage: Optional[str] = None, message: Optional[str] = None) -> None:
        """
        Update progress for an ongoing upload.
        
        Args:
            resource_id: Resource identifier
            uploaded_bytes: Number of bytes uploaded so far
            stage: Current processing stage
            message: Status message
        """
        with self._lock:
            if resource_id not in self._progress_data:
                logger.warning(f"No progress tracking found for resource_id: {resource_id}")
                return
            
            progress = self._progress_data[resource_id]
            progress.update_progress(uploaded_bytes, stage, message)
            
            # Call callback if registered
            if resource_id in self._callbacks:
                try:
                    self._callbacks[resource_id](progress)
                except Exception as e:
                    logger.error(f"Error in progress callback for {resource_id}: {e}")
    
    def complete_upload(self, resource_id: str, 
                       message: str = "Upload completed successfully") -> None:
        """
        Mark an upload as completed.
        
        Args:
            resource_id: Resource identifier
            message: Completion message
        """
        with self._lock:
            if resource_id not in self._progress_data:
                logger.warning(f"No progress tracking found for resource_id: {resource_id}")
                return
            
            progress = self._progress_data[resource_id]
            progress.mark_completed(message)
            
            # Call callback if registered
            if resource_id in self._callbacks:
                try:
                    self._callbacks[resource_id](progress)
                except Exception as e:
                    logger.error(f"Error in completion callback for {resource_id}: {e}")
            
            logger.info(f"Upload completed for {progress.filename} ({resource_id})")
    
    def fail_upload(self, resource_id: str, error_message: str) -> None:
        """
        Mark an upload as failed.
        
        Args:
            resource_id: Resource identifier
            error_message: Error description
        """
        with self._lock:
            if resource_id not in self._progress_data:
                logger.warning(f"No progress tracking found for resource_id: {resource_id}")
                return
            
            progress = self._progress_data[resource_id]
            progress.mark_failed(error_message)
            
            # Call callback if registered
            if resource_id in self._callbacks:
                try:
                    self._callbacks[resource_id](progress)
                except Exception as e:
                    logger.error(f"Error in failure callback for {resource_id}: {e}")
            
            logger.error(f"Upload failed for {progress.filename} ({resource_id}): {error_message}")
    
    def get_progress(self, resource_id: str) -> Optional[UploadProgress]:
        """
        Get current progress for a resource.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            UploadProgress instance or None if not found
        """
        with self._lock:
            return self._progress_data.get(resource_id)
    
    def get_all_progress(self) -> Dict[str, UploadProgress]:
        """
        Get progress for all tracked uploads.
        
        Returns:
            Dictionary mapping resource_ids to UploadProgress instances
        """
        with self._lock:
            return self._progress_data.copy()
    
    def register_callback(self, resource_id: str, 
                         callback: Callable[[UploadProgress], None]) -> None:
        """
        Register a callback function to be called on progress updates.
        
        Args:
            resource_id: Resource identifier
            callback: Function to call with UploadProgress instance
        """
        with self._lock:
            self._callbacks[resource_id] = callback
            logger.debug(f"Registered progress callback for {resource_id}")
    
    def unregister_callback(self, resource_id: str) -> None:
        """
        Unregister progress callback for a resource.
        
        Args:
            resource_id: Resource identifier
        """
        with self._lock:
            if resource_id in self._callbacks:
                del self._callbacks[resource_id]
                logger.debug(f"Unregistered progress callback for {resource_id}")
    
    def cleanup_completed(self, max_age_hours: int = 24) -> int:
        """
        Clean up completed/failed uploads older than specified age.
        
        Args:
            max_age_hours: Maximum age in hours for keeping completed uploads
            
        Returns:
            Number of entries cleaned up
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        cleaned_count = 0
        
        with self._lock:
            to_remove = []
            
            for resource_id, progress in self._progress_data.items():
                if (progress.is_complete and 
                    progress.updated_at < cutoff_time):
                    to_remove.append(resource_id)
            
            for resource_id in to_remove:
                del self._progress_data[resource_id]
                if resource_id in self._callbacks:
                    del self._callbacks[resource_id]
                cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old upload progress entries")
        
        return cleaned_count
    
    def get_active_uploads(self) -> Dict[str, UploadProgress]:
        """
        Get only active (non-completed) uploads.
        
        Returns:
            Dictionary of active uploads
        """
        with self._lock:
            return {
                resource_id: progress 
                for resource_id, progress in self._progress_data.items()
                if not progress.is_complete
            }
    
    def get_upload_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about tracked uploads.
        
        Returns:
            Dictionary with upload statistics
        """
        with self._lock:
            total_uploads = len(self._progress_data)
            active_uploads = len(self.get_active_uploads())
            completed_uploads = sum(
                1 for p in self._progress_data.values() 
                if p.status == "completed"
            )
            failed_uploads = sum(
                1 for p in self._progress_data.values() 
                if p.status == "failed"
            )
            
            total_bytes = sum(p.total_bytes for p in self._progress_data.values())
            uploaded_bytes = sum(p.uploaded_bytes for p in self._progress_data.values())
            
            return {
                "total_uploads": total_uploads,
                "active_uploads": active_uploads,
                "completed_uploads": completed_uploads,
                "failed_uploads": failed_uploads,
                "total_bytes": total_bytes,
                "uploaded_bytes": uploaded_bytes,
                "overall_progress_percentage": (
                    (uploaded_bytes / total_bytes * 100) if total_bytes > 0 else 0
                )
            }


# Global progress tracker instance
_global_tracker: Optional[UploadProgressTracker] = None


def get_progress_tracker() -> UploadProgressTracker:
    """Get the global upload progress tracker instance."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = UploadProgressTracker()
    return _global_tracker


def set_progress_tracker(tracker: UploadProgressTracker) -> None:
    """Set the global upload progress tracker instance."""
    global _global_tracker
    _global_tracker = tracker
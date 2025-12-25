"""
Model Download Manager Module.

This module provides the ModelDownloadManager class for handling model download
state management, including partial download detection, resumption, and logging.

Classes:
    ModelDownloadManager: Class for managing model download states.
"""

import os
import json
import time
import threading
from pathlib import Path
from typing import Optional, Dict, List, Callable, Any
import logging
from datetime import datetime

from .config import get_model_folder_path, get_model_blob_path
from .file_manager import FileManager


class ModelDownloadManager:
    """
    Manager class for model download state management.
    
    Handles partial download detection, resumption, and logging for model downloads.
    
    Attributes:
        file_manager: FileManager instance for file operations.
        logger: Logger instance for logging operations.
        download_states: Dictionary to track download states.
        _lock: Thread lock for state management.
    """
    
    def __init__(self, file_manager: FileManager):
        """
        Initialize ModelDownloadManager.
        
        Args:
            file_manager: FileManager instance.
        """
        self.file_manager = file_manager
        self.logger = logging.getLogger(__name__)
        self.download_states = {}
        self._lock = threading.Lock()
        
        # State file path
        self.state_file = Path(self.file_manager.get_temp_path("model_download_states.json"))
        
        # Load existing states
        self._load_states()
    
    def _load_states(self):
        """Load download states from file."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.download_states = data.get('states', {})
                    self.logger.info(f"Loaded {len(self.download_states)} download states")
            else:
                self.download_states = {}
        except Exception as e:
            self.logger.error(f"Error loading download states: {e}")
            self.download_states = {}
    
    def _save_states(self):
        """Save download states to file."""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump({'states': self.download_states}, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving download states: {e}")
    
    def get_download_state(self, model_name: str) -> Dict[str, Any]:
        """
        Get download state for a model.
        
        Args:
            model_name: Name of the model.
            
        Returns:
            Dictionary containing download state information.
        """
        with self._lock:
            if model_name not in self.download_states:
                self.download_states[model_name] = {
                    'model_name': model_name,
                    'status': 'idle',
                    'downloaded_bytes': 0,
                    'total_bytes': 0,
                    'start_time': None,
                    'last_activity': None,
                    'partial_files': [],
                    'error_message': None,
                    'resume_supported': False,
                    'manifest_pulled': False
                }
            
            return self.download_states[model_name].copy()
    
    def update_download_state(self, model_name: str, updates: Dict[str, Any]):
        """
        Update download state for a model.
        
        Args:
            model_name: Name of the model.
            updates: Dictionary of updates to apply.
        """
        with self._lock:
            if model_name not in self.download_states:
                self.download_states[model_name] = {
                    'model_name': model_name,
                    'status': 'idle',
                    'downloaded_bytes': 0,
                    'total_bytes': 0,
                    'start_time': None,
                    'last_activity': None,
                    'partial_files': [],
                    'error_message': None,
                    'resume_supported': False,
                    'manifest_pulled': False
                }
            
            # Update state
            current_time = datetime.now().isoformat()
            self.download_states[model_name].update(updates)
            self.download_states[model_name]['last_activity'] = current_time
            
            # Log state changes
            if 'status' in updates:
                status = updates['status']
                self.logger.info(f"Model {model_name} download status: {status}")
            
            # Save to file
            self._save_states()
    
    def check_partial_download(self, model_name: str) -> Dict[str, Any]:
        """
        Check for partial downloads and return recovery information.
        
        Args:
            model_name: Name of the model.
            
        Returns:
            Dictionary with recovery information.
        """
        recovery_info = {
            'has_partial': False,
            'can_resume': False,
            'partial_size': 0,
            'total_size': 0,
            'partial_files': [],
            'manifest_available': False
        }
        
        try:
            model_folder = get_model_folder_path(model_name)
            blob_path = get_model_blob_path(model_name)
            
            if not blob_path.exists():
                return recovery_info
            
            # Check for partial files
            partial_files = []
            total_partial_size = 0
            
            for file_path in blob_path.iterdir():
                if file_path.is_file():
                    file_size = file_path.stat().st_size
                    total_partial_size += file_size
                    partial_files.append({
                        'name': file_path.name,
                        'size': file_size,
                        'path': str(file_path)
                    })
            
            if partial_files:
                recovery_info['has_partial'] = True
                recovery_info['partial_files'] = partial_files
                recovery_info['partial_size'] = total_partial_size
                
                # Check if we can resume (if we have some data but not complete)
                state = self.get_download_state(model_name)
                if state['total_bytes'] > 0 and total_partial_size < state['total_bytes']:
                    recovery_info['can_resume'] = True
                    recovery_info['total_size'] = state['total_bytes']
            
            # Check for manifest
            manifest_path = model_folder / "manifest.json"
            if manifest_path.exists():
                recovery_info['manifest_available'] = True
            
        except Exception as e:
            self.logger.error(f"Error checking partial download for {model_name}: {e}")
        
        return recovery_info
    
    def cleanup_partial_download(self, model_name: str):
        """
        Clean up partial download files.
        
        Args:
            model_name: Name of the model.
        """
        try:
            blob_path = Path(get_model_blob_path(model_name))
            if blob_path.exists():
                for file_path in blob_path.iterdir():
                    if file_path.is_file():
                        try:
                            file_path.unlink()
                            self.logger.debug(f"Removed partial file: {file_path}")
                        except Exception as e:
                            self.logger.warning(f"Failed to remove partial file {file_path}: {e}")
                
                # Remove empty blob directory
                try:
                    blob_path.rmdir()
                except OSError:
                    pass  # Directory not empty
            
            # Reset state
            self.update_download_state(model_name, {
                'status': 'idle',
                'downloaded_bytes': 0,
                'total_bytes': 0,
                'partial_files': [],
                'error_message': None,
                'resume_supported': False
            })
            
            self.logger.info(f"Cleaned up partial download for model {model_name}")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up partial download for {model_name}: {e}")
    
    def mark_download_complete(self, model_name: str):
        """
        Mark download as complete and clean up state.
        
        Args:
            model_name: Name of the model.
        """
        try:
            self.update_download_state(model_name, {
                'status': 'completed',
                'downloaded_bytes': 0,
                'total_bytes': 0,
                'partial_files': [],
                'error_message': None,
                'resume_supported': False
            })
            
            self.logger.info(f"Download completed for model {model_name}")
            
        except Exception as e:
            self.logger.error(f"Error marking download complete for {model_name}: {e}")
    
    def get_download_progress(self, model_name: str) -> Dict[str, Any]:
        """
        Get download progress information.
        
        Args:
            model_name: Name of the model.
            
        Returns:
            Dictionary with progress information.
        """
        state = self.get_download_state(model_name)
        recovery_info = self.check_partial_download(model_name)
        
        progress = {
            'model_name': model_name,
            'status': state['status'],
            'downloaded_bytes': state['downloaded_bytes'],
            'total_bytes': state['total_bytes'],
            'progress_percent': 0,
            'has_partial': recovery_info['has_partial'],
            'can_resume': recovery_info['can_resume'],
            'partial_size': recovery_info['partial_size'],
            'manifest_available': recovery_info['manifest_available']
        }
        
        if progress['total_bytes'] > 0:
            progress['progress_percent'] = min(100, (progress['downloaded_bytes'] / progress['total_bytes']) * 100)
        
        return progress
    
    def log_download_event(self, model_name: str, event_type: str, message: str, details: Optional[Dict] = None):
        """
        Log download event with structured information.
        
        Args:
            model_name: Name of the model.
            event_type: Type of event (start, progress, resume, complete, error).
            message: Event message.
            details: Optional additional details.
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'model_name': model_name,
            'event_type': event_type,
            'message': message,
            'details': details or {}
        }
        
        # Log to file with structured format
        log_file = Path(self.file_manager.get_temp_path(f"model_download_{model_name}.log"))
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, indent=2) + '\n')
        except Exception as e:
            self.logger.error(f"Error writing download log: {e}")
        
        # Also log to console/logger
        self.logger.info(f"[{model_name}] {event_type.upper()}: {message}")
    
    def handle_manifest_pull(self, model_name: str, manifest_data: Dict):
        """
        Handle manifest pull event and update state.
        
        Args:
            model_name: Name of the model.
            manifest_data: Manifest data from Ollama.
        """
        try:
            # Extract total size from manifest if available
            total_size = 0
            layers = manifest_data.get('layers', [])
            for layer in layers:
                total_size += layer.get('size', 0)
            
            self.update_download_state(model_name, {
                'status': 'pulling_manifest',
                'total_bytes': total_size,
                'manifest_pulled': True,
                'resume_supported': total_size > 0
            })
            
            self.log_download_event(
                model_name, 
                'manifest_pulled', 
                f"Manifest pulled, total size: {total_size} bytes",
                {'layers': len(layers), 'total_size': total_size}
            )
            
        except Exception as e:
            self.logger.error(f"Error handling manifest pull for {model_name}: {e}")
    
    def handle_download_reset(self, model_name: str, reason: str):
        """
        Handle download reset due to various reasons.
        
        Args:
            model_name: Name of the model.
            reason: Reason for reset.
        """
        self.log_download_event(
            model_name, 
            'reset', 
            f"Download reset: {reason}",
            {'reason': reason}
        )
        
        # Clean up partial files
        self.cleanup_partial_download(model_name)
        
        # Update state
        self.update_download_state(model_name, {
            'status': 'reset',
            'error_message': reason
        })
    
    def get_active_downloads(self) -> List[str]:
        """Get list of models currently being downloaded."""
        active_states = ['downloading', 'pulling_manifest', 'resuming']
        active_models = []
        
        for model_name, state in self.download_states.items():
            if state.get('status') in active_states:
                active_models.append(model_name)
        
        return active_models
    
    def cleanup_old_logs(self, max_age_days: int = 7):
        """
        Clean up old download log files.
        
        Args:
            max_age_days: Maximum age of log files in days.
        """
        try:
            import glob
            from datetime import datetime, timedelta
            
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            log_pattern = str(self.file_manager.get_temp_path("model_download_*.log"))
            
            for log_file in glob.glob(log_pattern):
                try:
                    file_time = datetime.fromtimestamp(os.path.getmtime(log_file))
                    if file_time < cutoff_date:
                        os.remove(log_file)
                        self.logger.debug(f"Removed old log file: {log_file}")
                except Exception as e:
                    self.logger.warning(f"Failed to remove old log file {log_file}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up old logs: {e}")
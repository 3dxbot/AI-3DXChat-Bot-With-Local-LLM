"""
Status Manager Module.

This module provides the StatusManager class for tracking and managing
the status of Ollama, models, and operations.

Classes:
    StatusManager: Class for managing application status.
"""

import threading
import time
from typing import Dict, Optional, Callable
import logging


class StatusManager:
    """
    Manager class for application status tracking.
    
    Handles status updates for Ollama, models, and operations with callbacks.
    
    Attributes:
        logger: Logger instance for logging operations.
        _ollama_status: Current Ollama status.
        _active_model: Currently active model.
        _model_status: Dictionary of model statuses.
        _callbacks: Dictionary of status change callbacks.
        _monitoring: Flag indicating if monitoring is active.
        _monitor_thread: Thread for status monitoring.
    """
    
    def __init__(self):
        """Initialize StatusManager."""
        self.logger = logging.getLogger(__name__)
        
        # Status tracking
        self._ollama_status = "Checking"
        self._active_model = None
        self._active_character = None
        self._is_character_synced = False
        self._model_status = {}
        
        # Callbacks
        self._callbacks = {
            'ollama_status': [],
            'model_status': [],
            'active_model': [],
            'active_character': [],
            'character_sync': []
        }
        
        # Monitoring
        self._monitoring = False
        self._monitor_thread = None
        self._stop_monitoring = threading.Event()
    
    def set_ollama_status(self, status: str):
        """
        Set Ollama status.
        
        Args:
            status: New status string.
        """
        old_status = self._ollama_status
        self._ollama_status = status
        
        self.logger.info(f"Ollama status changed: {old_status} -> {status}")
        
        # Notify callbacks
        for callback in self._callbacks['ollama_status']:
            try:
                callback(status, old_status)
            except Exception as e:
                self.logger.error(f"Error in ollama status callback: {e}")
    
    def get_ollama_status(self) -> str:
        """Get current Ollama status."""
        return self._ollama_status
    
    def set_active_model(self, model_name: Optional[str]):
        """
        Set active model.
        
        Args:
            model_name: Name of the active model, or None.
        """
        old_model = self._active_model
        self._active_model = model_name
        
        # Reset sync status when model changes
        if model_name != old_model:
            self.set_character_synced(False)
            
        self.logger.info(f"Active model changed: {old_model} -> {model_name}")
        
        # Notify callbacks
        for callback in self._callbacks['active_model']:
            try:
                callback(model_name, old_model)
            except Exception as e:
                self.logger.error(f"Error in active model callback: {e}")
    
    def get_active_model(self) -> Optional[str]:
        """Get currently active model."""
        return self._active_model
    
    def set_active_character(self, char_name: Optional[str]):
        """
        Set active character profile name.
        
        Args:
            char_name: Name of the active character, or None.
        """
        old_char = self._active_character
        self._active_character = char_name
        
        self.logger.info(f"Active character changed: {old_char} -> {char_name}")
        
        # Notify callbacks
        for callback in self._callbacks['active_character']:
            try:
                callback(char_name, old_char)
            except Exception as e:
                self.logger.error(f"Error in active character callback: {e}")
                
    def get_active_character(self) -> Optional[str]:
        """Get currently active character profile name."""
        return self._active_character

    def set_character_synced(self, synced: bool):
        """
        Set if the active character is synced with the current model.
        
        Args:
            synced: True if synced, False otherwise.
        """
        old_synced = self._is_character_synced
        self._is_character_synced = synced
        
        # Notify callbacks
        for callback in self._callbacks['character_sync']:
            try:
                callback(synced, old_synced)
            except Exception as e:
                self.logger.error(f"Error in character sync callback: {e}")

    def is_character_synced(self) -> bool:
        """Check if character is synced."""
        return self._is_character_synced
    
    def set_model_status(self, model_name: str, status: str):
        """
        Set model status.
        
        Args:
            model_name: Name of the model.
            status: New status string.
        """
        old_status = self._model_status.get(model_name)
        self._model_status[model_name] = status
        
        self.logger.info(f"Model {model_name} status changed: {old_status} -> {status}")
        
        # Notify callbacks
        for callback in self._callbacks['model_status']:
            try:
                callback(model_name, status, old_status)
            except Exception as e:
                self.logger.error(f"Error in model status callback: {e}")
    
    def get_model_status(self, model_name: str) -> Optional[str]:
        """
        Get model status.
        
        Args:
            model_name: Name of the model.
            
        Returns:
            Status string or None if model not found.
        """
        return self._model_status.get(model_name)
    
    def list_models(self) -> Dict[str, str]:
        """Get dictionary of all model statuses."""
        return self._model_status.copy()
    
    def remove_model(self, model_name: str):
        """
        Remove model from tracking.
        
        Args:
            model_name: Name of the model to remove.
        """
        if model_name in self._model_status:
            del self._model_status[model_name]
            if self._active_model == model_name:
                self.set_active_model(None)
    
    def add_callback(self, event_type: str, callback: Callable):
        """
        Add status change callback.
        
        Args:
            event_type: Type of event ('ollama_status', 'model_status', 'active_model').
            callback: Callback function to call on status change.
        """
        if event_type in self._callbacks:
            self._callbacks[event_type].append(callback)
    
    def remove_callback(self, event_type: str, callback: Callable):
        """
        Remove status change callback.
        
        Args:
            event_type: Type of event.
            callback: Callback function to remove.
        """
        if event_type in self._callbacks:
            if callback in self._callbacks[event_type]:
                self._callbacks[event_type].remove(callback)
    
    def start_monitoring(self):
        """Start background status monitoring."""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._stop_monitoring.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop background status monitoring."""
        self._monitoring = False
        self._stop_monitoring.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
    
    def _monitor_loop(self):
        """Background monitoring loop."""
        while self._monitoring and not self._stop_monitoring.is_set():
            try:
                # Update status every 5 seconds
                time.sleep(5)
                
                # This would be called by the OllamaManager
                # when status changes occur
                
            except Exception as e:
                self.logger.error(f"Error in status monitoring: {e}")
                time.sleep(1)
"""
File Manager Module.

This module provides the FileManager class for handling file operations
related to Ollama and model storage.

Classes:
    FileManager: Class for managing file operations.
"""

import os
import shutil
from pathlib import Path
from typing import Optional
import logging
from .config import OLLAMA_DIR, OLLAMA_EXE_PATH, OLLAMA_MODELS_DIR, OLLAMA_TEMP_DIR


class FileManager:
    """
    Manager class for file operations.
    
    Handles file operations for Ollama and model storage.
    
    Attributes:
        logger: Logger instance for logging operations.
        base_dir: Base directory for Ollama files.
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize FileManager.
        
        Args:
            base_dir: Base directory for Ollama files. If None, uses default.
        """
        self.logger = logging.getLogger(__name__)
        
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            # Use application base directory
            import sys
            if getattr(sys, 'frozen', False):
                self.base_dir = Path(sys.executable).parent
            else:
                self.base_dir = Path(__file__).parent.parent
        
        # Use config paths
        self.ollama_dir = Path(OLLAMA_DIR)
        self.models_dir = Path(OLLAMA_MODELS_DIR)
        self.temp_dir = Path(OLLAMA_TEMP_DIR)
    
    def create_ollama_directories(self):
        """Create necessary directories for Ollama."""
        try:
            self.ollama_dir.mkdir(parents=True, exist_ok=True)
            self.models_dir.mkdir(parents=True, exist_ok=True)
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Created Ollama directories: {self.ollama_dir}")
        except Exception as e:
            self.logger.error(f"Error creating directories: {e}")
            raise
    
    def get_ollama_path(self) -> Path:
        """Get path to Ollama executable."""
        return Path(OLLAMA_EXE_PATH)
    
    def get_models_path(self) -> Path:
        """Get path to models directory."""
        return Path(OLLAMA_MODELS_DIR)
    
    def get_temp_path(self, filename: str) -> Path:
        """Get path to temporary file."""
        return Path(OLLAMA_TEMP_DIR) / filename
    
    def ollama_exists(self) -> bool:
        """Check if Ollama executable exists."""
        return self.get_ollama_path().exists()
    
    def list_models(self) -> list:
        """List available models."""
        if not self.models_dir.exists():
            return []
        
        return [d.name for d in self.models_dir.iterdir() if d.is_dir()]
    
    def delete_ollama(self) -> bool:
        """
        Delete Ollama installation.
        
        Returns:
            bool: True if deletion successful, False otherwise.
        """
        try:
            if self.ollama_dir.exists():
                shutil.rmtree(self.ollama_dir)
                self.logger.info("Ollama installation deleted")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting Ollama: {e}")
            return False
    
    def cleanup_temp_files(self):
        """Clean up temporary files."""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.temp_dir.mkdir()
        except Exception as e:
            self.logger.error(f"Error cleaning up temp files: {e}")
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

class FileManager:
    """
    Manager class for file operations.
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize FileManager.
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
    
    def create_ollama_directories(self):
        """No longer used."""
        pass
    
    def cleanup_temp_files(self):
        """Clean up temporary files."""
        # No-op for now as Ollama temp is gone
        pass

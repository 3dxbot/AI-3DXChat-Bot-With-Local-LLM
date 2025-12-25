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
            
            # Run migration after creating directories
            self.migrate_existing_models()
            
        except Exception as e:
            self.logger.error(f"Error creating directories: {e}")
            raise
    
    def migrate_existing_models(self):
        """
        Migrate existing models from old structure to new separate folder structure.
        
        This ensures compatibility with existing installations.
        """
        try:
            # Import model path functions from config
            from .config import get_model_folder_path
            
            if not self.models_dir.exists():
                self.logger.info("No existing models directory found, skipping migration")
                return
            
            # Check if we're already using the new structure
            existing_folders = [d for d in self.models_dir.iterdir() if d.is_dir()]
            if existing_folders and any(d.name in ['blobs', 'config'] for d in existing_folders):
                self.logger.info("Found old model structure, starting migration...")
                
                # Find models in the old structure (blobs directory)
                blobs_dir = self.models_dir / "blobs"
                if blobs_dir.exists():
                    # List all model files in blobs
                    model_files = [f for f in blobs_dir.iterdir() if f.is_file() and f.name.startswith('sha256-')]
                    
                    if model_files:
                        self.logger.info(f"Found {len(model_files)} model files to migrate")
                        
                        # Create a default model folder for old models
                        default_model_folder = get_model_folder_path("default")
                        default_model_folder.mkdir(parents=True, exist_ok=True)
                        
                        # Move blobs to the default model folder
                        default_blobs = default_model_folder / "blobs"
                        default_blobs.mkdir(exist_ok=True)
                        
                        for model_file in model_files:
                            try:
                                target_path = default_blobs / model_file.name
                                model_file.rename(target_path)
                                self.logger.debug(f"Migrated {model_file.name} to {target_path}")
                            except Exception as e:
                                self.logger.warning(f"Failed to migrate {model_file.name}: {e}")
                        
                        self.logger.info("Migration completed. Old models are now in 'default' folder.")
                    else:
                        self.logger.info("No model files found in old structure")
                else:
                    self.logger.info("No old blobs directory found")
            else:
                self.logger.info("Already using new model folder structure")
                
        except Exception as e:
            self.logger.error(f"Error during model migration: {e}")
    
    def get_ollama_path(self) -> Path:
        """Get path to Ollama executable."""
        return Path(os.path.abspath(OLLAMA_EXE_PATH))
    
    def get_models_path(self) -> Path:
        """Get path to models directory."""
        return Path(os.path.abspath(OLLAMA_MODELS_DIR))
    
    def get_temp_path(self, filename: str) -> Path:
        """Get path to temporary file."""
        return Path(os.path.abspath(os.path.join(OLLAMA_TEMP_DIR, filename)))
    
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
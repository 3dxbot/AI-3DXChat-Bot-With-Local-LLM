"""
GGUF Manager Module.

This module provides the GGUFManager class for handling GGUF model operations
including registration, Modelfile generation, and character integration.

Classes:
    GGUFManager: Main class for GGUF model operations management.
"""

import os
import json
import hashlib
import requests
from pathlib import Path
from typing import Optional, Dict, List, Any
import logging
import shutil

from .config import get_model_folder_path, get_model_blob_path, OLLAMA_API_URL
from .file_manager import FileManager


class GGUFManager:
    """
    Manager class for GGUF model operations.
    
    Handles GGUF model registration, Modelfile generation, and character integration.
    
    Attributes:
        file_manager: FileManager instance for file operations.
        logger: Logger instance for logging operations.
        api_base_url: Base URL for Ollama API.
    """
    
    def __init__(self, file_manager: FileManager):
        """
        Initialize GGUFManager.
        
        Args:
            file_manager: FileManager instance.
        """
        self.file_manager = file_manager
        self.logger = logging.getLogger(__name__)
        self.api_base_url = OLLAMA_API_URL
        
    def is_gguf_file(self, file_path: str) -> bool:
        """
        Check if file is a GGUF model file.
        
        Args:
            file_path: Path to the file to check.
            
        Returns:
            bool: True if file is GGUF, False otherwise.
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return False
            
            # Check file extension
            if file_path.suffix.lower() != '.gguf':
                return False
            
            # Check GGUF magic bytes (first 4 bytes should be "GGUF")
            with open(file_path, 'rb') as f:
                magic = f.read(4)
                return magic == b'GGUF'
                
        except Exception as e:
            self.logger.error(f"Error checking GGUF file {file_path}: {e}")
            return False
    
    def calculate_file_hash(self, file_path: str) -> str:
        """
        Calculate SHA256 hash of a file.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            str: SHA256 hash of the file.
        """
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""
    
    def create_model_from_gguf(self, gguf_path: str, model_name: str, 
                              system_prompt: str = "", manifest: str = "") -> bool:
        """
        Create a new model from GGUF file with character integration.
        
        Args:
            gguf_path: Path to the GGUF file.
            model_name: Name for the new model.
            system_prompt: System prompt from character.
            manifest: Character manifest info.
            
        Returns:
            bool: True if model creation successful, False otherwise.
        """
        try:
            self.logger.info(f"Creating model {model_name} from GGUF file: {gguf_path}")
            
            # Validate GGUF file
            if not self.is_gguf_file(gguf_path):
                self.logger.error(f"Invalid GGUF file: {gguf_path}")
                return False
            
            # Prepare model directory
            model_folder = Path(get_model_folder_path(model_name))
            model_folder.mkdir(parents=True, exist_ok=True)
            
            # Copy GGUF file to model directory
            gguf_dest = model_folder / f"{model_name}.gguf"
            shutil.copy2(gguf_path, gguf_dest)
            self.logger.info(f"Copied GGUF file to: {gguf_dest}")
            
            # Create Modelfile
            modelfile_content = self._generate_modelfile(
                model_name, gguf_dest, system_prompt, manifest
            )
            
            modelfile_path = model_folder / "Modelfile"
            with open(modelfile_path, 'w', encoding='utf-8') as f:
                f.write(modelfile_content)
            
            self.logger.info(f"Created Modelfile: {modelfile_path}")
            
            # Register model with Ollama
            if self._register_model_with_ollama(model_name, modelfile_path):
                self.logger.info(f"Successfully registered model: {model_name}")
                return True
            else:
                self.logger.error(f"Failed to register model: {model_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating model from GGUF: {e}")
            return False
    
    def _generate_modelfile(self, model_name: str, gguf_path: str, 
                           system_prompt: str = "", manifest: str = "") -> str:
        """
        Generate Modelfile content for GGUF model with character integration.
        
        Args:
            model_name: Name of the model.
            gguf_path: Path to the GGUF file.
            system_prompt: System prompt from character.
            manifest: Character manifest info.
            
        Returns:
            str: Generated Modelfile content.
        """
        # Base GGUF model configuration
        modelfile_lines = [
            f"# Modelfile for {model_name}",
            f"# Generated from GGUF file: {gguf_path}",
            "",
            f"FROM {gguf_path}",
            "",
            "# Model parameters",
            "PARAMETER num_ctx 4096",
            "PARAMETER num_threads 4",
            "PARAMETER num_gpu 1",
            "",
        ]
        
        # Add system prompt if provided
        if system_prompt.strip():
            modelfile_lines.extend([
                "# System prompt from character",
                f"SYSTEM \"\"\"",
                system_prompt,
                "\"\"\"",
                "",
            ])
        
        # Add character context if provided
        if manifest.strip():
            modelfile_lines.extend([
                "# Character context",
                f"TEMPLATE \"\"\"",
                "{{ if .System }}{{ .System }}\\n\\n{{ end }}",
                "Character Context:",
                manifest,
                "",
                "Conversation:",
                "{{ .Prompt }}",
                "{{ .Response }}",
                "\"\"\"",
                "",
            ])
        else:
            # Default template if no character context
            modelfile_lines.extend([
                "# Default template",
                f"TEMPLATE \"\"\"",
                "{{ if .System }}{{ .System }}\\n\\n{{ end }}",
                "{{ .Prompt }}",
                "{{ .Response }}",
                "\"\"\"",
                "",
            ])
        
        return "\n".join(modelfile_lines)
    
    def _register_model_with_ollama(self, model_name: str, modelfile_path: str) -> bool:
        """
        Register model with Ollama using Modelfile.
        
        Args:
            model_name: Name of the model.
            modelfile_path: Path to the Modelfile.
            
        Returns:
            bool: True if registration successful, False otherwise.
        """
        try:
            self.logger.info(f"Registering model {model_name} with Ollama...")
            
            # Read Modelfile content
            with open(modelfile_path, 'r', encoding='utf-8') as f:
                modelfile_content = f.read()
            
            # Send create request to Ollama API
            response = requests.post(
                f"{self.api_base_url}/api/create",
                json={
                    "name": model_name,
                    "modelfile": modelfile_content
                },
                timeout=300  # 5 minutes timeout for model creation
            )
            
            if response.status_code == 200:
                self.logger.info(f"Model {model_name} registered successfully")
                return True
            else:
                self.logger.error(f"Failed to register model {model_name}: HTTP {response.status_code}")
                self.logger.error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error registering model with Ollama: {e}")
            return False
    
    def update_model_character(self, model_name: str, system_prompt: str = "", 
                              manifest: str = "") -> bool:
        """
        Update character information for an existing model.
        
        Args:
            model_name: Name of the model.
            system_prompt: System prompt from character.
            manifest: Character manifest info.
            
        Returns:
            bool: True if update successful, False otherwise.
        """
        try:
            self.logger.info(f"Updating character for model: {model_name}")
            
            # Check if model exists
            model_folder = Path(get_model_folder_path(model_name))
            if not model_folder.exists():
                self.logger.error(f"Model folder not found: {model_folder}")
                return False
            
            # Find GGUF file
            gguf_files = list(model_folder.glob("*.gguf"))
            if not gguf_files:
                self.logger.error(f"No GGUF file found in model folder: {model_folder}")
                return False
            
            gguf_path = gguf_files[0]
            
            # Generate new Modelfile
            modelfile_content = self._generate_modelfile(
                model_name, str(gguf_path), system_prompt, manifest
            )
            
            # Update Modelfile
            modelfile_path = model_folder / "Modelfile"
            with open(modelfile_path, 'w', encoding='utf-8') as f:
                f.write(modelfile_content)
            
            self.logger.info(f"Updated Modelfile for model: {model_name}")
            
            # Re-register model with Ollama
            return self._register_model_with_ollama(model_name, modelfile_path)
            
        except Exception as e:
            self.logger.error(f"Error updating model character: {e}")
            return False
    
    def list_gguf_models(self) -> List[Dict[str, Any]]:
        """
        List all GGUF models registered in the system.
        
        Returns:
            List[Dict[str, Any]]: List of GGUF model information.
        """
        models = []
        
        try:
            # Check all model folders
            ollama_models_dir = Path(self.file_manager.get_models_path())
            if not ollama_models_dir.exists():
                return models
            
            for model_folder in ollama_models_dir.iterdir():
                if model_folder.is_dir():
                    model_info = self._get_model_info(model_folder)
                    if model_info:
                        models.append(model_info)
                        
        except Exception as e:
            self.logger.error(f"Error listing GGUF models: {e}")
        
        return models
    
    def _get_model_info(self, model_folder: Path) -> Optional[Dict[str, Any]]:
        """
        Get information about a model from its folder.
        
        Args:
            model_folder: Path to the model folder.
            
        Returns:
            Optional[Dict[str, Any]]: Model information or None if not GGUF model.
        """
        try:
            model_name = model_folder.name
            
            # Check for GGUF file
            gguf_files = list(model_folder.glob("*.gguf"))
            if not gguf_files:
                return None
            
            gguf_file = gguf_files[0]
            
            # Check for Modelfile
            modelfile_path = model_folder / "Modelfile"
            has_modelfile = modelfile_path.exists()
            
            # Get file size
            file_size = gguf_file.stat().st_size
            
            return {
                "name": model_name,
                "type": "gguf",
                "gguf_file": str(gguf_file),
                "modelfile_exists": has_modelfile,
                "file_size": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "path": str(model_folder)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting model info for {model_folder}: {e}")
            return None
    
    def delete_gguf_model(self, model_name: str) -> bool:
        """
        Delete a GGUF model and its files.
        
        Args:
            model_name: Name of the model to delete.
            
        Returns:
            bool: True if deletion successful, False otherwise.
        """
        try:
            self.logger.info(f"Deleting GGUF model: {model_name}")
            
            # Delete from Ollama
            response = requests.delete(
                f"{self.api_base_url}/api/delete",
                json={"name": model_name}
            )
            
            if response.status_code != 200:
                self.logger.warning(f"Failed to delete model from Ollama: HTTP {response.status_code}")
            
            # Delete local files
            model_folder = Path(get_model_folder_path(model_name))
            if model_folder.exists():
                shutil.rmtree(model_folder)
                self.logger.info(f"Deleted model folder: {model_folder}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting GGUF model: {e}")
            return False
    
    def is_model_registered(self, model_name: str) -> bool:
        """
        Check if a model is registered with Ollama.
        
        Args:
            model_name: Name of the model.
            
        Returns:
            bool: True if model is registered, False otherwise.
        """
        try:
            response = requests.get(f"{self.api_base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                return any(model.get("name") == model_name for model in models)
            return False
        except Exception as e:
            self.logger.error(f"Error checking model registration: {e}")
            return False
"""
Ollama Manager Module.

This module provides the OllamaManager class for handling all Ollama-related
operations including detection, installation, service management, and model
operations.

Classes:
    OllamaManager: Main class for Ollama operations management.
"""

import os
import subprocess
import time
import requests
import json
from pathlib import Path
from typing import Optional, Dict, List, Callable
import threading
import logging

from .file_manager import FileManager
from .download_manager import DownloadManager
from .status_manager import StatusManager
from .config import OLLAMA_API_URL, OLLAMA_DOWNLOAD_URL


class OllamaManager:
    """
    Manager class for Ollama operations.
    
    Handles Ollama detection, installation, service management, and model operations.
    
    Attributes:
        file_manager: FileManager instance for file operations.
        download_manager: DownloadManager instance for downloads.
        status_manager: StatusManager instance for status tracking.
        logger: Logger instance for logging operations.
        ollama_path: Path to Ollama executable.
        api_base_url: Base URL for Ollama API.
    """
    
    def __init__(self, file_manager: FileManager, download_manager: DownloadManager, status_manager: StatusManager):
        """
        Initialize OllamaManager.
        
        Args:
            file_manager: FileManager instance.
            download_manager: DownloadManager instance.
            status_manager: StatusManager instance.
        """
        self.file_manager = file_manager
        self.download_manager = download_manager
        self.status_manager = status_manager
        self.logger = logging.getLogger(__name__)
        
        self.ollama_path = self.file_manager.get_ollama_path()
        self.api_base_url = OLLAMA_API_URL
        
        # Threading for async operations
        self._service_thread = None
        self._stop_service_event = threading.Event()
    
    def detect_ollama(self) -> bool:
        """
        Detect if Ollama is installed and accessible.
        
        Returns:
            bool: True if Ollama is detected, False otherwise.
        """
        try:
            self.status_manager.set_ollama_status("Checking")
            
            # Check if executable exists
            if not self.file_manager.ollama_exists():
                self.status_manager.set_ollama_status("Not Installed")
                return False
            
            # Check if service is running
            if self.is_service_running():
                self.status_manager.set_ollama_status("Running")
                return True
            
            # Try to start service
            if self.start_service():
                self.status_manager.set_ollama_status("Running")
                return True
            else:
                self.status_manager.set_ollama_status("Error")
                return False
                
        except Exception as e:
            self.logger.error(f"Error detecting Ollama: {e}")
            self.status_manager.set_ollama_status("Error")
            return False
    
    def download_ollama(self, progress_callback: Optional[Callable] = None, complete_callback: Optional[Callable] = None):
        """
        Download Ollama executable.
        
        Args:
            progress_callback: Optional callback for progress updates.
            complete_callback: Optional callback for completion.
        """
        try:
            self.status_manager.set_ollama_status("Downloading")
            
            download_url = OLLAMA_DOWNLOAD_URL
            temp_path = self.file_manager.get_temp_path("ollama.zip")
            
            # Ensure temp directory exists
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            
            def on_progress(progress, total, status_text):
                if progress_callback:
                    progress_callback(progress, total, status_text)
            
            def on_complete(success, error_message=None):
                if success:
                    try:
                        import zipfile
                        self.logger.info("Extracting Ollama...")
                        with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                            # Extract all to the ollama directory
                            extract_path = os.path.dirname(self.file_manager.get_ollama_path())
                            zip_ref.extractall(extract_path)
                            
                        self.status_manager.set_ollama_status("Not Installed") # Trigger detection
                        self.logger.info("Ollama downloaded and extracted successfully")
                        
                        # Cleanup zip
                        try:
                            os.remove(temp_path)
                        except:
                            pass
                            
                        # Trigger detection explicitly
                        self.detect_ollama()
                        
                    except Exception as e:
                        self.logger.error(f"Failed to extract Ollama: {e}")
                        self.status_manager.set_ollama_status("Error")
                        if complete_callback:
                            complete_callback(False, f"Failed to extract file: {e}")
                        return
                else:
                    self.status_manager.set_ollama_status("Error")
                    self.logger.error(f"Failed to download Ollama: {error_message}")

                if complete_callback:
                    complete_callback(success, error_message)
            
            self.download_manager.download_file(
                download_url,
                temp_path,
                on_progress,
                on_complete
            )
            
        except Exception as e:
            self.logger.error(f"Error downloading Ollama: {e}")
            self.status_manager.set_ollama_status("Error")
    
    def start_service(self) -> bool:
        """
        Start Ollama service.
        
        Returns:
            bool: True if service started successfully, False otherwise.
        """
        try:
            if not self.file_manager.ollama_exists():
                self.logger.error("Ollama executable not found")
                return False
            
            # Kill any existing Ollama processes
            self._kill_existing_processes()
            
            # Start Ollama service
            self._service_thread = threading.Thread(target=self._run_service)
            self._service_thread.daemon = True
            self._service_thread.start()
            
            # Wait for service to be ready
            timeout = 30
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if self.is_service_running():
                    self.logger.info("Ollama service started successfully")
                    return True
                time.sleep(1)
            
            self.logger.error("Timeout waiting for Ollama service to start")
            return False
            
        except Exception as e:
            self.logger.error(f"Error starting Ollama service: {e}")
            return False
    
    def stop_service(self) -> bool:
        """
        Stop Ollama service.
        
        Returns:
            bool: True if service stopped successfully, False otherwise.
        """
        try:
            self._stop_service_event.set()
            
            # Kill Ollama processes
            self._kill_existing_processes()
            
            self.logger.info("Ollama service stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping Ollama service: {e}")
            return False
    
    def restart_service(self) -> bool:
        """
        Restart Ollama service.
        
        Returns:
            bool: True if service restarted successfully, False otherwise.
        """
        try:
            self.stop_service()
            time.sleep(2)  # Wait for service to stop
            return self.start_service()
        except Exception as e:
            self.logger.error(f"Error restarting Ollama service: {e}")
            return False
    
    def delete_ollama(self) -> bool:
        """
        Delete Ollama installation.
        
        Returns:
            bool: True if deletion successful, False otherwise.
        """
        try:
            self.stop_service()
            return self.file_manager.delete_ollama()
        except Exception as e:
            self.logger.error(f"Error deleting Ollama: {e}")
            return False
    
    def is_service_running(self) -> bool:
        """
        Check if Ollama service is running.
        
        Returns:
            bool: True if service is running, False otherwise.
        """
        try:
            response = requests.get(f"{self.api_base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_models(self) -> List[Dict]:
        """
        List available models.
        
        Returns:
            List[Dict]: List of available models.
        """
        try:
            response = requests.get(f"{self.api_base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("models", [])
            return []
        except Exception as e:
            self.logger.error(f"Error listing models: {e}")
            return []
    
    def download_model(self, model_name: str, progress_callback: Optional[Callable] = None, complete_callback: Optional[Callable] = None):
        """
        Download a model.
        
        Args:
            model_name: Name of the model to download.
            progress_callback: Optional callback for progress updates.
            complete_callback: Optional callback for completion.
        """
        try:
            self.status_manager.set_model_status(model_name, "Downloading")
            
            def on_progress(response):
                try:
                    for line in response.iter_lines():
                        if line:
                            data = json.loads(line.decode('utf-8'))
                            if 'status' in data:
                                status = data['status']
                                if progress_callback:
                                    progress_callback(status, data.get('total', 0), data.get('completed', 0))
                except Exception as e:
                    self.logger.error(f"Error processing model download progress: {e}")
            
            def on_complete(success, error_message=None):
                if success:
                    self.status_manager.set_model_status(model_name, "Available")
                    self.status_manager.set_active_model(model_name)
                else:
                    self.status_manager.set_model_status(model_name, "Error")
                
                if complete_callback:
                    complete_callback(success, error_message)
            
            # Start model download
            response = requests.post(
                f"{self.api_base_url}/api/pull",
                json={"name": model_name},
                stream=True,
                timeout=3600  # Increased timeout for large models
            )
            
            if response.status_code == 200:
                on_progress(response)
                on_complete(True)
            else:
                try:
                   error_text = response.text
                except:
                   error_text = "Unknown error"
                self.logger.error(f"Failed to download model. Status: {response.status_code}, Response: {error_text}")
                on_complete(False, f"HTTP {response.status_code}: {error_text}")
                
        except Exception as e:
            self.logger.error(f"Error downloading model {model_name}: {e}")
            self.status_manager.set_model_status(model_name, "Error")
            if complete_callback:
                complete_callback(False, str(e))
    
    def delete_model(self, model_name: str) -> bool:
        """
        Delete a model.
        
        Args:
            model_name: Name of the model to delete.
            
        Returns:
            bool: True if deletion successful, False otherwise.
        """
        try:
            response = requests.delete(f"{self.api_base_url}/api/delete", json={"name": model_name})
            if response.status_code == 200:
                self.status_manager.remove_model(model_name)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting model {model_name}: {e}")
            return False
    
    def activate_model(self, model_name: str) -> bool:
        """
        Activate a model.
        
        Args:
            model_name: Name of the model to activate.
            
        Returns:
            bool: True if activation successful, False otherwise.
        """
        try:
            self.status_manager.set_active_model(model_name)
            return True
        except Exception as e:
            self.logger.error(f"Error activating model {model_name}: {e}")
            return False
    
    def _run_service(self):
        """Run Ollama service in background thread."""
        try:
            subprocess.run([str(self.ollama_path)], capture_output=True, text=True)
        except Exception as e:
            self.logger.error(f"Service thread error: {e}")
    
    def _kill_existing_processes(self):
        """Kill any existing Ollama processes."""
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name']):
                if 'ollama' in proc.info['name'].lower():
                    try:
                        proc.kill()
                    except psutil.NoSuchProcess:
                        pass
        except ImportError:
            # Fallback for systems without psutil
            try:
                subprocess.run(['taskkill', '/F', '/IM', 'ollama.exe'], capture_output=True)
            except:
                pass
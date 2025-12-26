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
import asyncio
import requests
import json
from pathlib import Path
from typing import Optional, Dict, List, Callable, Any
import threading
import logging
import zipfile
import shutil
from datetime import datetime

from .file_manager import FileManager
from .download_manager import DownloadManager
from .status_manager import StatusManager
from .model_download_manager import ModelDownloadManager
from .gguf_manager import GGUFManager
from .modelfile_generator import ModelfileGenerator
from .config import OLLAMA_API_URL, OLLAMA_DOWNLOAD_URL, OLLAMA_HOST, OLLAMA_PORT


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
        self.model_download_manager = ModelDownloadManager(file_manager)
        self.gguf_manager = GGUFManager(file_manager)
        self.modelfile_generator = ModelfileGenerator()
        self.logger = logging.getLogger(__name__)
        
        self.ollama_path = self.file_manager.get_ollama_path()
        self.api_base_url = OLLAMA_API_URL
        
        # Threading for async operations
        self._service_thread = None
        self._stop_service_event = threading.Event()
        
        # Chat context history
        self.chat_history = []
    
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
                # For diagnostic purposes: if we are on the isolated port but didn't open logs yet,
                # we might want to suggest a restart or just log it.
                if not hasattr(self, 'server_log_file') or not self.server_log_file:
                    self.logger.info("Ollama is already running on port 11435. Diagnostic logs (ollama_server.log) will not be available until service is restarted via the UI.")
                
                self.status_manager.set_ollama_status("Running")
                return True
            else:
                # If not running but exists, it's "Stopped"
                self.status_manager.set_ollama_status("Stopped")
                return False
                
        except Exception as e:
            self.logger.error(f"Error detecting Ollama: {e}")
            self.status_manager.set_ollama_status("Error")
            return False
    
    def check_partial_model_downloads(self):
        """
        Check for partial model downloads and handle them appropriately.
        This method should be called during startup to clean up or resume interrupted downloads.
        """
        try:
            self.logger.info("Checking for partial model downloads...")
            
            # Get list of models that might have partial downloads
            # We check all model folders for partial files
            models_path = self.file_manager.get_models_path()
            if not models_path.exists():
                return
            
            for model_folder in models_path.iterdir():
                if model_folder.is_dir():
                    model_name = model_folder.name
                    
                    # Check for partial download
                    recovery_info = self.model_download_manager.check_partial_download(model_name)
                    
                    if recovery_info['has_partial']:
                        self.logger.warning(f"Found partial download for model: {model_name}")
                        self.logger.info(f"Partial size: {recovery_info['partial_size']} bytes")
                        self.logger.info(f"Can resume: {recovery_info['can_resume']}")
                        
                        # Clean up partial download to prevent issues
                        # In a production system, you might want to offer resume option
                        self.model_download_manager.cleanup_partial_download(model_name)
                        self.logger.info(f"Cleaned up partial download for: {model_name}")
                        
                        # Update status to reflect cleanup
                        self.status_manager.set_model_status(model_name, "Available")
                    else:
                        # Model appears complete, mark as available
                        self.status_manager.set_model_status(model_name, "Available")
                        
        except Exception as e:
            self.logger.error(f"Error checking partial model downloads: {e}")
    
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
            
            # Simplified: Always delete existing zip to avoid corrupted/partial downloads
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    self.logger.info(f"Deleted existing archive at {temp_path} for clean download")
                except Exception as e:
                    self.logger.warning(f"Failed to delete existing zip: {e}")

            def on_progress(progress, total, status_text):
                if progress_callback:
                    progress_callback(progress, total, status_text)
            
            def on_complete(success, error_message=None):
                if success:
                    try:
                        self.status_manager.set_ollama_status("Installing")
                        self.logger.info("Extracting Ollama...")
                        with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                            # Extract all to the ollama directory
                            extract_path = os.path.dirname(self.file_manager.get_ollama_path())
                            zip_ref.extractall(extract_path)
                            
                        self.logger.info("Ollama downloaded and extracted successfully")
                        self.status_manager.set_ollama_status("Stopped") # Trigger detection
                        
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
            time.sleep(2)  # Give system time to release ports
            
            # Start Ollama service
            executable = os.path.abspath(str(self.ollama_path))
            models_path = os.path.abspath(str(self.file_manager.get_models_path()))
            self.logger.info(f"Starting Ollama service: {executable}")
            self.logger.info(f"Ollama Models Path: {models_path}")
            
            # Set environment variables for local operation
            env = os.environ.copy()
            env["OLLAMA_MODELS"] = models_path
            env["OLLAMA_HOST"] = f"{OLLAMA_HOST}:{OLLAMA_PORT}"
            
            self.logger.info(f"Ollama environment configured:")
            self.logger.info(f"  OLLAMA_MODELS: {models_path}")
            self.logger.info(f"  OLLAMA_HOST: {env['OLLAMA_HOST']}")
            
            # Prepare log file for Ollama output
            log_dir = os.path.dirname(executable)
            self.server_log_path = os.path.join(log_dir, "ollama_server.log")
            
            # Close previous log file if already open
            if hasattr(self, 'server_log_file') and self.server_log_file:
                try:
                    self.server_log_file.close()
                except:
                    pass

            try:
                self.server_log_file = open(self.server_log_path, "a", encoding="utf-8")
                self.logger.info(f"Ollama server logs redirected to: {self.server_log_path}")
            except Exception as e:
                self.logger.error(f"Failed to open Ollama server log file: {e}")
                self.server_log_file = None

            # Use subprocess.Popen to start it as a detached process on Windows
            if os.name == 'nt':
                self.process = subprocess.Popen(
                    [executable, "serve"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    stdout=self.server_log_file,
                    stderr=self.server_log_file,
                    close_fds=True,
                    env=env
                )
            else:
                self.process = subprocess.Popen(
                    [executable, "serve"], 
                    start_new_session=True, 
                    stdout=self.server_log_file,
                    stderr=self.server_log_file,
                    env=env
                )
            
            # Wait for service to be ready
            sanity_timeout = 600 # 10 minute sanity limit to prevent infinite loops
            start_time = time.time()
            self.logger.info("Waiting for Ollama API to initialize. This may take a while depending on machine speed...")
            
            while time.time() - start_time < sanity_timeout:
                # Check 1: API response
                if self.is_service_running():
                    self.logger.info("Ollama service started and API is responsive")
                    self.status_manager.set_ollama_status("Running")
                    return True
                
                # Check 2: Process presence verification
                process_name = "ollama.exe" if os.name == 'nt' else "ollama"
                if not self._is_process_running(process_name):
                    self.logger.error("Ollama process died during initialization")
                    self.status_manager.set_ollama_status("Error")
                    return False
                
                # Progress heartbeat
                wait_duration = int(time.time() - start_time)
                if wait_duration % 15 == 0:
                    self.logger.info(f"Ollama process is active, still waiting for API response... ({wait_duration}s elapsed)")
                
                time.sleep(2)
            
            self.logger.error(f"Sanity timeout reached ({sanity_timeout}s) waiting for Ollama service")
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
            self.status_manager.set_ollama_status("Stopping")
            
            # Kill Ollama processes
            self._kill_existing_processes()
            
            self.logger.info("Ollama service stopped")
            self.status_manager.set_ollama_status("Stopped") 
            self.detect_ollama()
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
        Download a model with enhanced state management and resume support.

        Args:
            model_name: Name of the model to download.
            progress_callback: Optional callback for progress updates.
            complete_callback: Optional callback for completion.
        """
        try:
            # Validate model exists before starting download
            self.logger.info(f"Validating model '{model_name}' exists in Ollama registry...")
            try:
                show_response = requests.post(
                    f"{self.api_base_url}/api/show",
                    json={"name": model_name},
                    timeout=10
                )

                if show_response.status_code != 200:
                    error_msg = f"Model '{model_name}' not found in Ollama registry (HTTP {show_response.status_code})"
                    self.logger.warning(error_msg)
                    # Continue anyway - Ollama might be able to download it despite API validation failure
                    self.logger.info(f"Attempting download anyway despite validation failure...")
                else:
                    show_data = show_response.json()
                    if 'error' in show_data:
                        error_msg = f"Model '{model_name}' not found: {show_data['error']}"
                        self.logger.warning(error_msg)
                        # Continue anyway - the API might be having connectivity issues
                        self.logger.info(f"Attempting download anyway despite API error...")
                    else:
                        self.logger.info(f"Model '{model_name}' found in registry, proceeding with download...")

            except requests.exceptions.RequestException as e:
                error_msg = f"Failed to validate model '{model_name}': {e}"
                self.logger.warning(error_msg)
                # Continue anyway - network issues shouldn't prevent download attempts
                self.logger.info(f"Attempting download despite validation failure...")

            # Initialize download state
            self.model_download_manager.update_download_state(model_name, {
                'status': 'starting',
                'start_time': datetime.now().isoformat(),
                'error_message': None
            })

            self.status_manager.set_model_status(model_name, "Downloading")
            self.logger.info(f"Starting download of model: {model_name}")

            # Check for partial download and handle appropriately
            recovery_info = self.model_download_manager.check_partial_download(model_name)
            if recovery_info['has_partial']:
                self.logger.info(f"Found partial download for {model_name}, cleaning up...")
                self.model_download_manager.cleanup_partial_download(model_name)
            
            def on_progress(response):
                try:
                    for line in response.iter_lines():
                        if line:
                            data = json.loads(line.decode('utf-8'))

                            # Handle different types of progress events
                            if 'status' in data:
                                status = data['status']

                                # Handle manifest pulling
                                if status == 'pulling manifest':
                                    self.model_download_manager.handle_manifest_pull(model_name, data)
                                    self.model_download_manager.log_download_event(
                                        model_name, 'manifest_pulled', 'Manifest pulled successfully'
                                    )

                                # Handle downloading layers
                                elif status == 'downloading':
                                    downloaded = data.get('completed', 0)
                                    total = data.get('total', 0)

                                    self.model_download_manager.update_download_state(model_name, {
                                        'status': 'downloading',
                                        'downloaded_bytes': downloaded,
                                        'total_bytes': total
                                    })

                                    # Log progress
                                    if total > 0:
                                        progress_percent = (downloaded / total) * 100
                                        self.model_download_manager.log_download_event(
                                            model_name, 'progress',
                                            f'Downloading: {progress_percent:.1f}%',
                                            {'downloaded': downloaded, 'total': total}
                                        )

                                # Handle writing manifest
                                elif status == 'writing manifest':
                                    self.model_download_manager.log_download_event(
                                        model_name, 'writing_manifest', 'Writing manifest...'
                                    )

                                # Handle verification
                                elif status == 'verifying sha256 digest':
                                    self.model_download_manager.log_download_event(
                                        model_name, 'verifying', 'Verifying download...'
                                    )

                                # Call progress callback with correct signature
                                if progress_callback:
                                    total = data.get('total', 0)
                                    completed = data.get('completed', 0)
                                    progress_callback(status, total, completed)

                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON decode error in model download progress: {e}")
                    self.model_download_manager.log_download_event(
                        model_name, 'error', f'JSON decode error: {e}'
                    )
                except Exception as e:
                    self.logger.error(f"Error processing model download progress: {e}")
                    self.model_download_manager.log_download_event(
                        model_name, 'error', f'Progress processing error: {e}'
                    )
            
            def on_complete(success, error_message=None):
                if success:
                    self.model_download_manager.mark_download_complete(model_name)
                    self.model_download_manager.log_download_event(
                        model_name, 'completed', 'Model download completed successfully'
                    )
                    self.status_manager.set_model_status(model_name, "Available")
                    self.status_manager.set_active_model(model_name)
                    self.logger.info(f"Model {model_name} downloaded successfully")
                else:
                    self.model_download_manager.update_download_state(model_name, {
                        'status': 'error',
                        'error_message': error_message
                    })
                    self.model_download_manager.log_download_event(
                        model_name, 'error', f'Download failed: {error_message}'
                    )
                    self.status_manager.set_model_status(model_name, "Error")
                    self.logger.error(f"Model {model_name} download failed: {error_message}")
                
                if complete_callback:
                    complete_callback(success, error_message)
            
            # Start model download
            self.logger.info(f"Sending pull request to Ollama API for model: {model_name}")
            self.model_download_manager.log_download_event(
                model_name, 'started', f'Starting download via Ollama API'
            )
            
            response = requests.post(
                f"{self.api_base_url}/api/pull",
                json={"name": model_name},
                stream=True,
                timeout=3600  # Increased timeout for large models
            )
            
            self.logger.info(f"Ollama API response status: {response.status_code}")
            
            if response.status_code == 200:
                on_progress(response)
                on_complete(True)
            else:
                try:
                   error_text = response.text
                except:
                   error_text = "Unknown error"
                self.logger.error(f"Failed to download model. Status: {response.status_code}, Response: {error_text}")
                self.model_download_manager.handle_download_reset(
                    model_name, f"HTTP {response.status_code}: {error_text}"
                )
                on_complete(False, f"HTTP {response.status_code}: {error_text}")
                
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error downloading model {model_name}: {e}")
            self.logger.error("Ollama service may not be running or accessible")
            self.model_download_manager.handle_download_reset(model_name, f"Connection failed: {e}")
            self.status_manager.set_model_status(model_name, "Error")
            if complete_callback:
                complete_callback(False, f"Connection failed: {e}")
        except requests.exceptions.Timeout as e:
            self.logger.error(f"Timeout error downloading model {model_name}: {e}")
            self.model_download_manager.handle_download_reset(model_name, f"Request timeout: {e}")
            self.status_manager.set_model_status(model_name, "Error")
            if complete_callback:
                complete_callback(False, f"Request timeout: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error downloading model {model_name}: {e}")
            self.model_download_manager.handle_download_reset(model_name, f"Unexpected error: {e}")
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
            # First check if model exists in Ollama
            models = self.list_models()
            model_names = [m.get('name') for m in models]

            if model_name not in model_names:
                self.logger.warning(f"Model '{model_name}' not found in Ollama, removing from status tracking only")
                # Remove from status tracking even if not in Ollama
                self.status_manager.remove_model(model_name)
                return True

            # Model exists, try to delete it
            response = requests.delete(f"{self.api_base_url}/api/delete", json={"name": model_name})
            if response.status_code == 200:
                self.status_manager.remove_model(model_name)

                # Clean up the model's folder
                from .config import get_model_folder_path
                model_folder = get_model_folder_path(model_name)
                if model_folder.exists():
                    shutil.rmtree(model_folder)
                    self.logger.info(f"Cleaned up model folder for {model_name}")

                return True
            else:
                self.logger.error(f"Failed to delete model {model_name}: HTTP {response.status_code}")
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
            # Verify model existence
            models = self.list_models()
            model_names = [m.get('name') for m in models]
            
            if model_name not in model_names:
                self.logger.error(f"Cannot activate model {model_name}: Model not found locally")
                return False
                
            self.status_manager.set_active_model(model_name)
            return True
        except Exception as e:
            self.logger.error(f"Error activating model {model_name}: {e}")
            return False

    async def generate_response(self, prompt: str, system_prompt: str = "", manifest: str = "") -> Optional[str]:
        """
        Generate a response using the active model and maintain chat history (Asynchronous).
        
        Args:
            prompt: User message.
            system_prompt: System prompt from character.
            manifest: Character manifest info.
            
        Returns:
            Optional[str]: Generated response or None if failed.
        """
        model = self.status_manager.get_active_model()
        if not model:
            self.logger.error("No active model for generation")
            return None
            
        # Prepare system context
        full_system_prompt = ""
        if system_prompt:
            full_system_prompt += f"{system_prompt}\n\n"
        if manifest:
            full_system_prompt += f"Character Context:\n{manifest}"
        
        # Build messages for Ollama API
        messages = []
        if full_system_prompt.strip():
            messages.append({"role": "system", "content": full_system_prompt})
        
        # Add history
        messages.extend(self.chat_history)
        
        # Add current prompt
        messages.append({"role": "user", "content": prompt})
        
        try:
            start_time = time.time()
            total_chars = sum(len(m.get('content', '')) for m in messages)
            self.logger.info(f"LLM Request [Ready]: Model='{model}', Messages={len(messages)}, Total Chars={total_chars}")
            
            # Check if subprocess is still alive
            if hasattr(self, 'process') and self.process:
                poll = self.process.poll()
                if poll is not None:
                    self.logger.error(f"Ollama process died with exit code {poll}. Restarting...")
                    self.start_service()
            
            # Run blocking request in a separate thread to keep the event loop responsive
            def make_request():
                try:
                    url = f"{self.api_base_url}/api/chat"
                    self.logger.info(f"LLM Request [Sending]: {url} (Model: {model}, Payload: {total_chars} chars)")
                    
                    # Verify model exists before sending
                    self.logger.debug(f"Verifying model '{model}' exists on server...")
                    tags_response = requests.get(f"{self.api_base_url}/api/tags", timeout=10)
                    if tags_response.status_code == 200:
                        available_models = [m.get('name') for m in tags_response.json().get('models', [])]
                        if model not in available_models:
                            self.logger.error(f"Model '{model}' not found on server! Available: {available_models}")
                            return None
                    
                    self.logger.info(f"LLM Request [Posting]: {model}...")
                    req_start = time.time()
                    response = requests.post(
                        url,
                        json={
                            "model": model,
                            "messages": messages,
                            "stream": False
                        },
                        timeout=180 # Increased timeout for large models/first load
                    )
                    req_duration = time.time() - req_start
                    self.logger.info(f"LLM Request [Received]: Status={response.status_code}, Duration={req_duration:.2f}s")
                    return response
                except requests.exceptions.Timeout:
                    self.logger.error(f"LLM Request [Timeout]: Request exceeded 180s limit.")
                    return None
                except Exception as e:
                    self.logger.error(f"LLM Request [Error]: {e}")
                    return None

            response_obj = await asyncio.to_thread(make_request)
            
            if response_obj is None:
                self.logger.error("LLM Request [Failed]: No response object returned.")
                return None

            duration = time.time() - start_time
            
            if response_obj.status_code != 200:
                self.logger.error(f"LLM Request [Ollama Error] {response_obj.status_code}: {response_obj.text}")
                return None
                
            data = response_obj.json()
            response_text = data.get("message", {}).get("content", "")
            
            if response_text:
                # Add BOTH user prompt and assistant response to history
                self.chat_history.append({"role": "user", "content": prompt})
                self.chat_history.append({"role": "assistant", "content": response_text})
                
                # Keep history manageable (last 20 messages = 10 rounds)
                if len(self.chat_history) > 20: 
                    self.chat_history = self.chat_history[-20:]
                
                self.logger.debug(f"Chat history updated. Current size: {len(self.chat_history)} messages")
            else:
                self.logger.warning("Ollama returned an empty response content")
            
            return response_text
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return None

    def get_model_download_progress(self, model_name: str) -> Dict[str, Any]:
        """
        Get download progress information for a model.

        Args:
            model_name: Name of the model.

        Returns:
            Dictionary with progress information.
        """
        return self.model_download_manager.get_download_progress(model_name)

    def get_gpu_info(self) -> Dict[str, Any]:
        """
        Get GPU information from Ollama server logs.

        Returns:
            Dictionary with GPU information.
        """
        try:
            log_path = os.path.join(os.path.dirname(self.ollama_path), "ollama_server.log")
            if not os.path.exists(log_path):
                return {"gpu_detected": False, "message": "Log file not found"}

            gpu_info = {
                "gpu_detected": False,
                "gpu_name": None,
                "gpu_memory_total": None,
                "gpu_memory_available": None,
                "gpu_library": None,
                "gpu_compute": None,
                "message": "GPU information not found in logs"
            }

            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[-1000:]  # Read last 1000 lines for efficiency

            for line in reversed(lines):  # Start from most recent
                if "inference compute" in line and "library=CUDA" in line:
                    # Parse GPU info from log line
                    gpu_info["gpu_detected"] = True
                    gpu_info["message"] = "GPU detected and in use"

                    # Extract GPU name
                    if "description=" in line:
                        desc_start = line.find('description="') + len('description="')
                        desc_end = line.find('"', desc_start)
                        if desc_end > desc_start:
                            gpu_info["gpu_name"] = line[desc_start:desc_end]

                    # Extract memory info
                    if "total=" in line:
                        total_start = line.find('total="') + len('total="')
                        total_end = line.find('"', total_start)
                        if total_end > total_start:
                            gpu_info["gpu_memory_total"] = line[total_start:total_end]

                    if "available=" in line:
                        avail_start = line.find('available="') + len('available="')
                        avail_end = line.find('"', avail_start)
                        if avail_end > avail_start:
                            gpu_info["gpu_memory_available"] = line[avail_start:avail_end]

                    # Extract library and compute
                    if "library=" in line:
                        lib_start = line.find('library=') + len('library=')
                        lib_end = line.find(' ', lib_start)
                        if lib_end == -1:
                            lib_end = len(line)
                        gpu_info["gpu_library"] = line[lib_start:lib_end]

                    if "compute=" in line:
                        comp_start = line.find('compute=') + len('compute=')
                        comp_end = line.find(' ', comp_start)
                        if comp_end == -1:
                            comp_end = len(line)
                        gpu_info["gpu_compute"] = line[comp_start:comp_end]

                    break  # Found the most recent GPU info

            return gpu_info

        except Exception as e:
            self.logger.error(f"Error reading GPU info from logs: {e}")
            return {"gpu_detected": False, "message": f"Error reading logs: {e}"}
    
    def clear_history(self):
        """Clear the current conversation context history."""
        self.chat_history = []
        self.logger.info("Chat history cleared in OllamaManager.")
    
    # --- GGUF Model Support Methods ---
    
    def create_gguf_model(self, gguf_path: str, model_name: str, 
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
            return self.gguf_manager.create_model_from_gguf(
                gguf_path, model_name, system_prompt, manifest
            )
        except Exception as e:
            self.logger.error(f"Error creating GGUF model: {e}")
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
            return self.gguf_manager.update_model_character(
                model_name, system_prompt, manifest
            )
        except Exception as e:
            self.logger.error(f"Error updating model character: {e}")
            return False
    
    def list_gguf_models(self) -> List[Dict[str, Any]]:
        """
        List all GGUF models registered in the system.
        
        Returns:
            List[Dict[str, Any]]: List of GGUF model information.
        """
        try:
            return self.gguf_manager.list_gguf_models()
        except Exception as e:
            self.logger.error(f"Error listing GGUF models: {e}")
            return []
    
    def is_gguf_model(self, model_name: str) -> bool:
        """
        Check if a model is a GGUF model.
        
        Args:
            model_name: Name of the model.
            
        Returns:
            bool: True if model is GGUF, False otherwise.
        """
        try:
            return self.gguf_manager.is_model_registered(model_name)
        except Exception as e:
            self.logger.error(f"Error checking if model is GGUF: {e}")
            return False
    
    def delete_gguf_model(self, model_name: str) -> bool:
        """
        Delete a GGUF model and its files.
        
        Args:
            model_name: Name of the model to delete.
            
        Returns:
            bool: True if deletion successful, False otherwise.
        """
        try:
            return self.gguf_manager.delete_gguf_model(model_name)
        except Exception as e:
            self.logger.error(f"Error deleting GGUF model: {e}")
            return False
    
    def create_character_model(self, base_model: str, character_data: Dict[str, Any]) -> str:
        """
        Create a character-specific model from base model.
        
        Args:
            base_model: Base model name or GGUF file path.
            character_data: Character data including system prompt and manifest.
            
        Returns:
            str: Name of the created character model.
        """
        try:
            # Generate character model name
            character_name = character_data.get("name", "character")
            model_name = self.modelfile_generator.create_character_model_name(
                base_model, character_name
            )
            
            # Create Modelfile
            modelfile_content = self.modelfile_generator.generate_character_modelfile(
                model_name, base_model, character_data
            )
            
            # Save Modelfile
            from .config import get_model_folder_path
            model_folder = Path(get_model_folder_path(model_name))
            model_folder.mkdir(parents=True, exist_ok=True)
            
            modelfile_path = model_folder / "Modelfile"
            with open(modelfile_path, 'w', encoding='utf-8') as f:
                f.write(modelfile_content)
            
            # Register model with Ollama
            response = requests.post(
                f"{self.api_base_url}/api/create",
                json={
                    "name": model_name,
                    "modelfile": modelfile_content
                },
                timeout=300
            )
            
            if response.status_code == 200:
                self.logger.info(f"Successfully created character model: {model_name}")
                return model_name
            else:
                self.logger.error(f"Failed to create character model: HTTP {response.status_code}")
                return ""
                
        except Exception as e:
            self.logger.error(f"Error creating character model: {e}")
            return ""
    
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
                        self.logger.info(f"Killed existing Ollama process (PID: {proc.info['pid']})")
                    except psutil.NoSuchProcess:
                        pass
        except ImportError:
            # Fallback for systems without psutil
            try:
                import os
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/F', '/IM', 'ollama.exe'], capture_output=True)
                else:
                    subprocess.run(['pkill', '-f', 'ollama'], capture_output=True)
            except:
                pass

    def _is_process_running(self, process_name: str) -> bool:
        """Check if a process is running by name."""
        try:
            import psutil
            for proc in psutil.process_iter(['name']):
                if proc.info['name'].lower() == process_name.lower():
                    return True
            return False
        except ImportError:
            # Fallback without psutil
            try:
                import os
                if os.name == 'nt':
                    output = subprocess.check_output(['tasklist'], text=True)
                    return process_name.lower() in output.lower()
                else:
                    subprocess.check_output(['pgrep', '-f', process_name])
                    return True
            except:
                return False
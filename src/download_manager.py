"""
Download Manager Module.

This module provides the DownloadManager class for handling file downloads
with progress tracking and error handling.

Classes:
    DownloadManager: Class for managing file downloads.
"""

import os
import requests
import threading
from typing import Optional, Callable
import logging


class DownloadManager:
    """
    Manager class for file downloads.
    
    Handles downloading files with progress tracking and error handling.
    
    Attributes:
        logger: Logger instance for logging operations.
    """
    
    def __init__(self):
        """Initialize DownloadManager."""
        self.logger = logging.getLogger(__name__)
    
    def download_file(self, url: str, destination: str, progress_callback: Optional[Callable] = None, complete_callback: Optional[Callable] = None):
        """
        Download a file with progress tracking.
        
        Args:
            url: URL to download from.
            destination: Local path to save the file.
            progress_callback: Optional callback for progress updates.
            complete_callback: Optional callback for completion.
        """
        download_thread = threading.Thread(
            target=self._download_worker,
            args=(url, destination, progress_callback, complete_callback)
        )
        download_thread.daemon = True
        download_thread.start()
    
    def _download_worker(self, url: str, destination: str, progress_callback: Optional[Callable], complete_callback: Optional[Callable]):
        """Worker function for downloading files."""
        try:
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            # Download file
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(destination, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Call progress callback
                        if progress_callback:
                            progress_callback(downloaded_size, total_size, f"Downloading... {downloaded_size}/{total_size}")
            
            # Call completion callback
            if complete_callback:
                complete_callback(True)
                
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            
            # Clean up partial file
            if os.path.exists(destination):
                os.remove(destination)
            
            # Call completion callback with error
            if complete_callback:
                complete_callback(False, str(e))
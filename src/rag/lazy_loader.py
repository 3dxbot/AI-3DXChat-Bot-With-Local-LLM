"""
Lazy Model Loader for FAISS RAG System.

This module provides the LazyModelLoader class for handling lazy loading
of embedding models with caching and download functionality.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Callable, Union
from urllib.request import urlretrieve
from urllib.error import URLError
import json

class LazyModelLoader:
    """
    Handles lazy loading of embedding models for FAISS RAG system.
    
    Features:
    - Downloads model only when first needed
    - Progress tracking during download
    - Local caching to avoid repeated downloads
    - Error handling with fallback mechanisms
    """
    
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Initialize LazyModelLoader.
        
        Args:
            model_name (str): Name of the embedding model to load.
        """
        self.model_name = model_name
        self.model_path = self._get_model_path()
        self._model = None
        self.logger = logging.getLogger(__name__)
        
        # Download progress tracking
        self._download_progress = 0.0
        self._download_total = 0
        
    def _get_model_path(self) -> Path:
        """
        Get path for model cache directory.
        
        Returns:
            Path: Path to model cache directory.
        """
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            base_path = Path(sys._MEIPASS)
        else:
            # Running as script
            base_path = Path(__file__).parent.parent.parent
        
        return base_path / "bin" / "rag_model" / self.model_name
    
    def is_model_cached(self) -> bool:
        """
        Check if model is already cached locally.
        
        Returns:
            bool: True if model is cached, False otherwise.
        """
        return self.model_path.exists()
    
    def load_model(self):
        """
        Load the embedding model, downloading if necessary.
        
        Returns:
            SentenceTransformer: Loaded embedding model.
            
        Raises:
            RuntimeError: If model loading fails.
        """
        if self._model is not None:
            return self._model
        
        try:
            # Try to import and load cached model
            from sentence_transformers import SentenceTransformer
            
            if self.is_model_cached():
                self.logger.info(f"Loading cached model from {self.model_path}")
                self._model = SentenceTransformer(str(self.model_path))
            else:
                self.logger.info(f"Model not cached, downloading {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
                
                # Cache the model for future use
                self._cache_model()
            
            return self._model
            
        except ImportError as e:
            self.logger.error(f"Failed to import sentence_transformers: {e}")
            raise RuntimeError("sentence_transformers not available")
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Model loading failed: {e}")
    
    def _cache_model(self):
        """
        Cache the downloaded model locally.
        """
        try:
            if self._model is not None:
                self.logger.info(f"Caching model to {self.model_path}")
                self.model_path.parent.mkdir(parents=True, exist_ok=True)
                self._model.save(str(self.model_path))
        except Exception as e:
            self.logger.warning(f"Failed to cache model: {e}")
    
    def download_model(self, progress_callback: Optional[Callable] = None):
        """
        Force download of the model with progress tracking.
        
        Args:
            progress_callback (Optional[Callable]): Callback for progress updates.
            
        Raises:
            RuntimeError: If model download fails.
        """
        try:
            from sentence_transformers import SentenceTransformer
            
            # Create temporary model to trigger download
            temp_model = SentenceTransformer(self.model_name)
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(1.0, "Download completed")
            
            # Cache the model
            self._model = temp_model
            self._cache_model()
            
        except Exception as e:
            self.logger.error(f"Model download failed: {e}")
            if progress_callback:
                progress_callback(0.0, f"Download failed: {e}")
            raise RuntimeError(f"Model download failed: {e}")
    
    def get_model_info(self) -> dict:
        """
        Get information about the loaded model.
        
        Returns:
            dict: Model information including name, path, and status.
        """
        return {
            "model_name": self.model_name,
            "model_path": str(self.model_path),
            "is_cached": self.is_model_cached(),
            "is_loaded": self._model is not None
        }
    
    def clear_cache(self):
        """
        Clear the cached model.
        """
        try:
            if self.model_path.exists():
                import shutil
                shutil.rmtree(self.model_path)
                self.logger.info(f"Cleared cached model at {self.model_path}")
        except Exception as e:
            self.logger.warning(f"Failed to clear cache: {e}")
    
    def get_model_size(self) -> Optional[int]:
        """
        Get the size of the cached model in bytes.
        
        Returns:
            Optional[int]: Model size in bytes, or None if not cached.
        """
        if not self.is_model_cached():
            return None
        
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(self.model_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    total_size += os.path.getsize(filepath)
            return total_size
        except Exception as e:
            self.logger.warning(f"Failed to get model size: {e}")
            return None
    
    def validate_model(self) -> bool:
        """
        Validate that the cached model can be loaded.
        
        Returns:
            bool: True if model is valid, False otherwise.
        """
        try:
            if not self.is_model_cached():
                return False
            
            # Try to load the model
            from sentence_transformers import SentenceTransformer
            test_model = SentenceTransformer(str(self.model_path))
            
            # Test encoding a simple sentence
            test_embedding = test_model.encode("test")
            
            return len(test_embedding) > 0
            
        except Exception as e:
            self.logger.error(f"Model validation failed: {e}")
            return False
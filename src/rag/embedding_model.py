"""
Embedding Model for FAISS RAG System.

This module provides the EmbeddingModel class for handling text encoding
using Sentence-Transformers with CPU optimization.
"""

import numpy as np
import logging
from typing import Union, List, Optional
from .lazy_loader import LazyModelLoader

class EmbeddingModel:
    """
    Handles text encoding using Sentence-Transformers with CPU optimization.
    
    Features:
    - Multilingual text encoding
    - Text preprocessing pipeline
    - Batch processing support
    - Memory-efficient operations
    """
    
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Initialize EmbeddingModel.
        
        Args:
            model_name (str): Name of the embedding model to use.
        """
        self.model_name = model_name
        self.lazy_loader = LazyModelLoader(model_name)
        self.logger = logging.getLogger(__name__)
        self._model = None
        
    def _get_model(self):
        """
        Get the loaded embedding model.
        
        Returns:
            SentenceTransformer: Loaded embedding model.
        """
        if self._model is None:
            self._model = self.lazy_loader.load_model()
        return self._model
    
    def encode(self, texts: Union[str, List[str]], normalize: bool = True) -> np.ndarray:
        """
        Encode text(s) into embeddings.
        
        Args:
            texts (Union[str, List[str]]): Text or list of texts to encode.
            normalize (bool): Whether to normalize embeddings. Defaults to True.
            
        Returns:
            np.ndarray: Array of embeddings.
            
        Raises:
            RuntimeError: If encoding fails.
        """
        try:
            model = self._get_model()
            
            # Ensure input is a list
            if isinstance(texts, str):
                texts = [texts]
            
            # Preprocess texts
            processed_texts = [self.preprocess_text(text) for text in texts]
            
            # Encode with CPU optimization
            embeddings = model.encode(
                processed_texts,
                normalize_embeddings=normalize,
                convert_to_numpy=True,
                show_progress_bar=False  # Disable progress bar for batch operations
            )
            
            return embeddings
            
        except Exception as e:
            self.logger.error(f"Failed to encode text: {e}")
            raise RuntimeError(f"Text encoding failed: {e}")
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text before encoding.
        
        Args:
            text (str): Input text.
            
        Returns:
            str: Preprocessed text.
        """
        if not text:
            return ""
        
        # Basic text cleaning
        text = text.strip()
        text = text.replace('\n', ' ')
        text = text.replace('\t', ' ')
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        return text
    
    def get_dimension(self) -> int:
        """
        Get the dimension of embeddings.
        
        Returns:
            int: Embedding dimension.
        """
        try:
            model = self._get_model()
            # Test with a simple sentence to get dimension
            test_embedding = model.encode("test")
            return len(test_embedding)
        except Exception as e:
            self.logger.error(f"Failed to get embedding dimension: {e}")
            return 384  # Default for MiniLM
    
    def batch_encode(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Encode texts in batches for memory efficiency.
        
        Args:
            texts (List[str]): List of texts to encode.
            batch_size (int): Size of each batch. Defaults to 32.
            
        Returns:
            np.ndarray: Array of embeddings.
        """
        if not texts:
            return np.array([])
        
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = self.encode(batch)
            all_embeddings.append(embeddings)
        
        return np.vstack(all_embeddings) if all_embeddings else np.array([])
    
    def get_model_info(self) -> dict:
        """
        Get information about the embedding model.
        
        Returns:
            dict: Model information.
        """
        return {
            "model_name": self.model_name,
            "dimension": self.get_dimension(),
            "is_loaded": self._model is not None,
            "cache_info": self.lazy_loader.get_model_info()
        }
    
    def clear_cache(self):
        """
        Clear the cached model.
        """
        self.lazy_loader.clear_cache()
        self._model = None
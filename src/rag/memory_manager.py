"""
Memory Manager for FAISS RAG System.

This module provides the MemoryManager class for handling FAISS index operations,
including index creation, search, and management of character memory cards.
"""

import os
import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Union, Callable
from .embedding_model import EmbeddingModel
from .config import RAG_VECTORS_DIR, RAG_SEARCH_K, RAG_EMBEDDING_DIM

class MemoryManager:
    """
    Manages FAISS index operations for character memory cards.
    
    Features:
    - Automatic index creation and rebuilding
    - FAISS IndexFlatL2 integration
    - Character data validation
    - Performance optimization
    """
    
    def __init__(self, character_name: str, character_path: str):
        """
        Initialize MemoryManager.
        
        Args:
            character_name (str): Name of the character.
            character_path (str): Path to the character JSON file.
        """
        self.character_name = character_name
        self.character_path = character_path
        self.index_path = self.get_index_path()
        self.embedding_model = EmbeddingModel()
        self.logger = logging.getLogger(__name__)
        
        # FAISS index
        self._index = None
        self._card_data = []
        self._card_embeddings = None
        
        # Caching
        self._embedding_cache = {}
        self._query_cache = {}
        
    def get_index_path(self) -> Path:
        """
        Get path for FAISS index file.
        
        Returns:
            Path: Path to FAISS index file.
        """
        base_path = Path(__file__).parent.parent.parent
        return base_path / RAG_VECTORS_DIR / f"{self.character_name}.index"
    
    def get_character_data(self) -> Dict:
        """
        Load character data from JSON file.
        
        Returns:
            Dict: Character data including memory cards.
        """
        try:
            with open(self.character_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load character data: {e}")
            return {"name": self.character_name, "memory_cards": []}
    
    def is_index_valid(self) -> bool:
        """
        Check if the FAISS index is valid and matches character data.
        
        Returns:
            bool: True if index is valid, False otherwise.
        """
        if not self.index_path.exists():
            return False
        
        try:
            # Check if character data has been modified
            char_data = self.get_character_data()
            card_count = len(char_data.get("memory_cards", []))
            
            # Load index to check if it has the right number of vectors
            import faiss
            index = faiss.read_index(str(self.index_path))
            
            return index.ntotal == card_count
            
        except Exception as e:
            self.logger.warning(f"Index validation failed: {e}")
            return False
    
    def load_or_create_index(self) -> bool:
        """
        Load existing index or create new one from character data.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            if self.is_index_valid():
                self._load_index()
                self.logger.info(f"Loaded existing index for {self.character_name}")
                return True
            else:
                return self.rebuild_index()
                
        except Exception as e:
            self.logger.error(f"Failed to load or create index: {e}")
            return False
    
    def _load_index(self):
        """
        Load FAISS index from file.
        """
        import faiss
        
        self._index = faiss.read_index(str(self.index_path))
        
        # Load character data and embeddings
        char_data = self.get_character_data()
        self._card_data = char_data.get("memory_cards", [])
        
        # Precompute embeddings for search
        if self._card_data:
            card_texts = [self._format_card_text(card) for card in self._card_data]
            self._card_embeddings = self.embedding_model.encode(card_texts)
        
        self.logger.info(f"Index loaded with {self._index.ntotal} vectors")
    
    def rebuild_index(self) -> bool:
        """
        Rebuild FAISS index from character data.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            char_data = self.get_character_data()
            memory_cards = char_data.get("memory_cards", [])
            
            if not memory_cards:
                self.logger.warning(f"No memory cards found for {self.character_name}")
                return False
            
            # Create FAISS index
            import faiss
            dimension = self.embedding_model.get_dimension()
            self._index = faiss.IndexFlatL2(dimension)
            
            # Prepare card data and embeddings
            self._card_data = memory_cards
            card_texts = [self._format_card_text(card) for card in memory_cards]
            
            # Encode all card texts
            self._card_embeddings = self.embedding_model.encode(card_texts)
            
            # Add embeddings to index
            self._index.add(self._card_embeddings.astype('float32'))
            
            # Save index to file
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            faiss.write_index(self._index, str(self.index_path))
            
            self.logger.info(f"Index rebuilt with {len(memory_cards)} cards")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to rebuild index: {e}")
            return False
    
    def _format_card_text(self, card: Dict) -> str:
        """
        Format memory card for embedding.
        
        Args:
            card (Dict): Memory card data.
            
        Returns:
            str: Formatted text for embedding.
        """
        key = card.get("key", "")
        data = card.get("data", "")
        
        # Combine key and data for better semantic representation
        return f"{key}: {data}".strip()
    
    def search(self, query: str, k: int = RAG_SEARCH_K) -> List[str]:
        """
        Search for relevant memory cards using semantic similarity.
        
        Args:
            query (str): Search query.
            k (int): Number of results to return. Defaults to RAG_SEARCH_K.
            
        Returns:
            List[str]: List of relevant card contents.
        """
        try:
            # Check query cache first
            cache_key = f"{query}_{k}"
            if cache_key in self._query_cache:
                return self._query_cache[cache_key]
            
            if self._index is None or self._card_embeddings is None:
                self.logger.warning("Index not loaded, attempting to load...")
                if not self.load_or_create_index():
                    return []
            
            # Preprocess query
            query_text = self.embedding_model.preprocess_text(query)
            
            # Encode query
            query_embedding = self.embedding_model.encode(query_text)
            query_embedding = query_embedding.reshape(1, -1).astype('float32')
            
            # Search in FAISS
            distances, indices = self._index.search(query_embedding, k)
            
            # Get relevant cards
            results = []
            for idx in indices[0]:
                if idx < len(self._card_data):
                    card = self._card_data[idx]
                    card_content = self._format_card_text(card)
                    results.append(card_content)
            
            # Cache result
            self._query_cache[cache_key] = results
            
            self.logger.debug(f"Search for '{query}' returned {len(results)} results")
            return results
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []
    
    def get_card_count(self) -> int:
        """
        Get the number of memory cards in the index.
        
        Returns:
            int: Number of memory cards.
        """
        if self._index is None:
            return 0
        return self._index.ntotal
    
    def clear_cache(self):
        """
        Clear all caches.
        """
        self._embedding_cache.clear()
        self._query_cache.clear()
        self.logger.info("Cleared all caches")
    
    def get_memory_stats(self) -> Dict:
        """
        Get statistics about the memory system.
        
        Returns:
            Dict: Memory statistics.
        """
        stats = {
            "character_name": self.character_name,
            "card_count": self.get_card_count(),
            "index_path": str(self.index_path),
            "index_exists": self.index_path.exists(),
            "index_valid": self.is_index_valid(),
            "embedding_dimension": self.embedding_model.get_dimension(),
            "cache_size": len(self._query_cache)
        }
        
        # Add model info
        stats["model_info"] = self.embedding_model.get_model_info()
        
        return stats
    
    def delete_index(self) -> bool:
        """
        Delete the FAISS index file.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            if self.index_path.exists():
                self.index_path.unlink()
                self._index = None
                self._card_data = []
                self._card_embeddings = None
                self.logger.info(f"Deleted index for {self.character_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete index: {e}")
            return False
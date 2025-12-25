#!/usr/bin/env python3
"""
Test script for FAISS RAG System.

This script provides a simple way to test the RAG system functionality
without running the full chatbot application.
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from rag.memory_manager import MemoryManager
from rag.lazy_loader import LazyModelLoader
from rag.embedding_model import EmbeddingModel

def test_lazy_loader():
    """Test the lazy loading functionality."""
    print("Testing LazyModelLoader...")
    
    loader = LazyModelLoader()
    
    # Check if model is cached
    print(f"Model cached: {loader.is_model_cached()}")
    
    # Try to load model
    try:
        model = loader.load_model()
        print(f"Model loaded successfully: {type(model)}")
        print(f"Model info: {loader.get_model_info()}")
        return True
    except Exception as e:
        print(f"Model loading failed: {e}")
        return False

def test_embedding_model():
    """Test the embedding model functionality."""
    print("\nTesting EmbeddingModel...")
    
    try:
        model = EmbeddingModel()
        test_text = "Hello world, this is a test sentence."
        
        # Test single text encoding
        embedding = model.encode(test_text)
        print(f"Single text embedding shape: {embedding.shape}")
        
        # Test batch encoding
        batch_texts = ["Test 1", "Test 2", "Test 3"]
        batch_embeddings = model.encode(batch_texts)
        print(f"Batch encoding shape: {batch_embeddings.shape}")
        
        # Test dimension
        dimension = model.get_dimension()
        print(f"Embedding dimension: {dimension}")
        
        return True
    except Exception as e:
        print(f"Embedding model test failed: {e}")
        return False

def test_memory_manager():
    """Test the memory manager functionality."""
    print("\nTesting MemoryManager...")
    
    # Create test character data
    test_data = {
        "name": "TestCharacter",
        "memory_cards": [
            {"key": "Origin", "data": "Born in 2025 in a digital world for testing purposes"},
            {"key": "Hobby", "data": "Likes talking to users and learning new things"},
            {"key": "Personality", "data": "Friendly and helpful assistant designed to assist users"}
        ]
    }
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_data, f)
        character_path = f.name
    
    try:
        # Create memory manager
        manager = MemoryManager("TestCharacter", character_path)
        
        # Test index creation
        success = manager.load_or_create_index()
        print(f"Index creation successful: {success}")
        
        if success:
            card_count = manager.get_card_count()
            print(f"Number of cards: {card_count}")
            
            # Test search
            query = "Where was the character born?"
            results = manager.search(query, k=2)
            print(f"Search results for '{query}':")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result}")
            
            # Test memory stats
            stats = manager.get_memory_stats()
            print(f"Memory stats: {stats}")
        
        return success
    except Exception as e:
        print(f"Memory manager test failed: {e}")
        return False
    finally:
        # Clean up
        os.unlink(character_path)

def main():
    """Run all tests."""
    print("FAISS RAG System Test Suite")
    print("=" * 40)
    
    tests = [
        ("Lazy Loader", test_lazy_loader),
        ("Embedding Model", test_embedding_model),
        ("Memory Manager", test_memory_manager)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 40)
    print("Test Results Summary:")
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("All tests passed! RAG system is working correctly.")
    else:
        print("Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()
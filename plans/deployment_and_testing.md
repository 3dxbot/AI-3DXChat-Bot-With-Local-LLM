# Deployment and Testing Plan for FAISS RAG System

## Overview

This document outlines the deployment strategy and testing approach for the FAISS RAG system integration. It covers PyInstaller build optimization, cross-platform compatibility, and comprehensive testing procedures.

## Deployment Strategy

### 1. PyInstaller Build Configuration

#### Build Script Enhancement
```bash
#!/bin/bash
# build_with_rag.sh

echo "Building ChatBot with FAISS RAG support..."

# Clean previous builds
rm -rf dist build *.spec

# Create optimized build with FAISS support
pyinstaller main.py \
    --name "ChatBot_RAG" \
    --onedir \
    --windowed \
    --icon="resources/logo.ico" \
    --add-data="resources;resources" \
    --add-data="config;config" \
    --add-data="bin;bin" \
    --add-data="data;data" \
    --exclude-module torch.cuda \
    --exclude-module faiss.contrib.gpu \
    --exclude-module matplotlib \
    --exclude-module scipy \
    --hidden-import faiss \
    --hidden-import sentence_transformers \
    --hidden-import transformers \
    --hidden-import torch \
    --hidden-import numpy \
    --hidden-import opencv-python \
    --collect-all faiss \
    --collect-all sentence_transformers \
    --collect-all transformers \
    --collect-all torch \
    --collect-all numpy \
    --collect-all opencv-python \
    --noconfirm

echo "Build completed. Check dist/ChatBot_RAG/ directory."
```

#### Hook Files for PyInstaller

**hook-faiss.py**
```python
# hooks/hook-faiss.py
from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all('faiss')

# Add specific FAISS modules
hiddenimports.extend([
    'faiss._swigfaiss',
    'faiss.contrib',
    'faiss.contrib.exact_scoring',
    'faiss.contrib.inspect_tools',
    'faiss.contrib.ondisk_ivf',
    'faiss.contrib.pca',
    'faiss.contrib.torch_utils'
])

# Exclude GPU modules to reduce size
excludedimports = [
    'faiss.contrib.gpu',
    'torch.cuda'
]
```

**hook-sentence_transformers.py**
```python
# hooks/hook-sentence_transformers.py
from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all('sentence_transformers')

# Add transformers dependencies
hiddenimports.extend([
    'transformers',
    'transformers.models',
    'transformers.models.bert',
    'transformers.models.roberta',
    'transformers.models.distilbert',
    'tokenizers',
    'tokenizers.models',
    'tokenizers.pre_tokenizers',
    'tokenizers.processors',
    'tokenizers.normalizers',
    'tokenizers.decoders'
])
```

### 2. Dependency Management

#### Requirements.txt Optimization
```txt
# requirements.txt - Optimized for deployment
# Core dependencies
customtkinter>=5.0.0
pyautogui>=0.9.53
keyboard>=0.13.5
pyperclip>=1.8.2
pytesseract>=0.3.9
pillow>=9.0.0
numpy>=1.21.0
opencv-python>=4.5.0

# OCR and text processing
langdetect>=1.0.9
deep-translator>=1.11.4

# FAISS RAG system
faiss-cpu>=1.7.0
sentence-transformers>=2.2.0
transformers>=4.20.0
torch>=1.12.0

# Optional: For development only
# playwright>=1.20.0
# pywin32>=300
```

#### Lazy Loading Implementation
```python
# src/rag/lazy_loader.py
import os
import sys
from pathlib import Path
from typing import Optional, Callable
import logging

class LazyModelLoader:
    """Handles lazy loading of embedding models for FAISS RAG system."""
    
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        self.model_name = model_name
        self.model_path = self._get_model_path()
        self._model = None
        self.logger = logging.getLogger(__name__)
        
    def _get_model_path(self) -> Path:
        """Get path for model cache directory."""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            base_path = Path(sys._MEIPASS)
        else:
            # Running as script
            base_path = Path(__file__).parent.parent.parent
        
        return base_path / "bin" / "rag_model" / self.model_name
    
    def is_model_cached(self) -> bool:
        """Check if model is already cached locally."""
        return self.model_path.exists()
    
    def load_model(self):
        """Load the embedding model, downloading if necessary."""
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
        """Cache the downloaded model locally."""
        try:
            if self._model is not None:
                self.logger.info(f"Caching model to {self.model_path}")
                self.model_path.parent.mkdir(parents=True, exist_ok=True)
                self._model.save(str(self.model_path))
        except Exception as e:
            self.logger.warning(f"Failed to cache model: {e}")
    
    def download_model(self, progress_callback: Optional[Callable] = None):
        """Force download of the model with progress tracking."""
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
            raise
```

### 3. Cross-Platform Compatibility

#### Platform-Specific Handling
```python
# src/rag/platform_utils.py
import platform
import sys
from pathlib import Path

class PlatformUtils:
    """Utilities for handling platform-specific operations."""
    
    @staticmethod
    def get_platform_info():
        """Get current platform information."""
        return {
            'system': platform.system(),
            'release': platform.release(),
            'architecture': platform.architecture(),
            'python_version': sys.version,
            'is_frozen': getattr(sys, 'frozen', False)
        }
    
    @staticmethod
    def get_app_data_dir(app_name: str = "ChatBot") -> Path:
        """Get application data directory for current platform."""
        system = platform.system()
        
        if system == "Windows":
            return Path.home() / "AppData" / "Local" / app_name
        elif system == "Darwin":  # macOS
            return Path.home() / "Library" / "Application Support" / app_name
        else:  # Linux
            return Path.home() / ".local" / "share" / app_name
    
    @staticmethod
    def is_supported_platform() -> bool:
        """Check if current platform is supported."""
        supported_systems = ["Windows", "Darwin", "Linux"]
        return platform.system() in supported_systems
```

## Testing Strategy

### 1. Unit Testing

#### Test Structure
```
tests/
├── __init__.py
├── test_memory_manager.py
├── test_lazy_loader.py
├── test_embedding_model.py
├── test_rag_integration.py
├── test_ui_integration.py
└── conftest.py
```

#### MemoryManager Tests
```python
# tests/test_memory_manager.py
import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from src.rag.memory_manager import MemoryManager

class TestMemoryManager:
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.character_name = "TestCharacter"
        self.character_path = os.path.join(self.temp_dir, "test_character.json")
        
        # Create test character data
        test_data = {
            "name": self.character_name,
            "memory_cards": [
                {"key": "Origin", "data": "Born in 2025 in a digital world"},
                {"key": "Hobby", "data": "Likes talking to users and learning"}
            ]
        }
        
        with open(self.character_path, 'w') as f:
            import json
            json.dump(test_data, f)
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('src.rag.memory_manager.LazyModelLoader')
    def test_index_creation(self, mock_loader):
        """Test FAISS index creation."""
        manager = MemoryManager(self.character_name, self.character_path)
        
        # Mock the model loader
        mock_model = Mock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_loader.return_value.load_model.return_value = mock_model
        
        # Test index creation
        result = manager.load_or_create_index()
        assert result is True
        assert manager.get_card_count() == 2
    
    def test_search_functionality(self):
        """Test memory search functionality."""
        manager = MemoryManager(self.character_name, self.character_path)
        
        # Mock successful index loading
        with patch.object(manager, 'load_or_create_index', return_value=True):
            with patch.object(manager, '_perform_faiss_search', return_value=["Found card"]):
                results = manager.search("test query", k=3)
                assert len(results) == 1
                assert results[0] == "Found card"
    
    def test_error_handling(self):
        """Test error handling in memory operations."""
        manager = MemoryManager(self.character_name, self.character_path)
        
        # Test search with no index
        results = manager.search("test query")
        assert results == []
```

### 2. Integration Testing

#### End-to-End Tests
```python
# tests/test_rag_integration.py
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from src.rag.memory_manager import MemoryManager
from src.ollama_manager import OllamaManager

class TestRAGIntegration:
    @pytest.mark.asyncio
    async def test_end_to_end_search(self):
        """Test complete RAG search workflow."""
        # Mock character data
        character_data = {
            "name": "TestCharacter",
            "memory_cards": [
                {"key": "Background", "data": "Created in 2025 for testing purposes"},
                {"key": "Personality", "data": "Friendly and helpful assistant"}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump(character_data, f)
            character_path = f.name
        
        try:
            # Create memory manager
            manager = MemoryManager("TestCharacter", character_path)
            
            # Mock model and FAISS operations
            with patch('src.rag.lazy_loader.LazyModelLoader.load_model') as mock_load:
                mock_model = Mock()
                mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
                mock_load.return_value = mock_model
                
                # Test index creation and search
                assert manager.load_or_create_index() is True
                results = manager.search("background information")
                
                # Verify results
                assert len(results) > 0
                assert any("Created in 2025" in result for result in results)
                
        finally:
            os.unlink(character_path)
    
    @pytest.mark.asyncio
    async def test_character_activation_with_memory(self):
        """Test character activation with memory loading."""
        # This would test the integration between UI, bot, and memory manager
        pass
```

### 3. Performance Testing

#### Load Testing
```python
# tests/test_performance.py
import time
import pytest
from src.rag.memory_manager import MemoryManager

class TestPerformance:
    def test_search_latency(self):
        """Test search operation latency."""
        # Create test data with many cards
        test_cards = [{"key": f"Card_{i}", "data": f"Content for card {i} " * 10} 
                     for i in range(100)]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump({"name": "Test", "memory_cards": test_cards}, f)
            character_path = f.name
        
        try:
            manager = MemoryManager("Test", character_path)
            
            # Time search operations
            start_time = time.time()
            results = manager.search("content", k=5)
            search_time = time.time() - start_time
            
            # Verify performance requirements
            assert search_time < 0.1  # Should complete in under 100ms
            assert len(results) <= 5  # Should return at most k results
            
        finally:
            os.unlink(character_path)
    
    def test_index_rebuild_performance(self):
        """Test index rebuild performance."""
        # Test with large dataset
        large_cards = [{"key": f"Card_{i}", "data": f"Content {i} " * 50} 
                      for i in range(1000)]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump({"name": "LargeTest", "memory_cards": large_cards}, f)
            character_path = f.name
        
        try:
            manager = MemoryManager("LargeTest", character_path)
            
            start_time = time.time()
            success = manager.rebuild_index()
            rebuild_time = time.time() - start_time
            
            # Verify performance requirements
            assert success is True
            assert rebuild_time < 30  # Should complete in under 30 seconds
            
        finally:
            os.unlink(character_path)
```

### 4. Compatibility Testing

#### Cross-Platform Tests
```python
# tests/test_compatibility.py
import platform
import pytest
from src.rag.platform_utils import PlatformUtils

class TestCompatibility:
    def test_platform_detection(self):
        """Test platform detection utilities."""
        info = PlatformUtils.get_platform_info()
        
        assert 'system' in info
        assert 'release' in info
        assert 'architecture' in info
        assert 'python_version' in info
        assert 'is_frozen' in info
    
    def test_app_data_directory(self):
        """Test application data directory creation."""
        app_dir = PlatformUtils.get_app_data_dir("TestApp")
        
        # Should return a Path object
        assert isinstance(app_dir, type(Path()))
        
        # Should be in appropriate location for platform
        system = platform.system()
        if system == "Windows":
            assert "AppData" in str(app_dir)
        elif system == "Darwin":
            assert "Application Support" in str(app_dir)
        else:
            assert ".local" in str(app_dir)
    
    @pytest.mark.skipif(not PlatformUtils.is_supported_platform(), 
                       reason="Platform not supported")
    def test_supported_platform(self):
        """Test supported platform detection."""
        assert PlatformUtils.is_supported_platform() is True
```

### 5. Manual Testing Procedures

#### Testing Checklist
```markdown
# Manual Testing Checklist

## Installation Testing
- [ ] Fresh installation with no cached models
- [ ] Installation with existing cached models
- [ ] Installation on different operating systems
- [ ] PyInstaller build verification

## Functionality Testing
- [ ] Character creation with memory cards
- [ ] Memory index creation and rebuilding
- [ ] Semantic search functionality
- [ ] Character activation with memory loading
- [ ] UI memory controls

## Performance Testing
- [ ] Search latency with small datasets (< 100 cards)
- [ ] Search latency with large datasets (> 1000 cards)
- [ ] Index rebuild time with various dataset sizes
- [ ] Memory usage during operations

## Error Handling Testing
- [ ] Model download failure scenarios
- [ ] FAISS index corruption handling
- [ ] Network connectivity issues
- [ ] Insufficient disk space scenarios

## Integration Testing
- [ ] End-to-end chat flow with memory
- [ ] Character switching with memory
- [ ] Memory persistence across sessions
- [ ] UI responsiveness during memory operations
```

### 6. Continuous Integration

#### GitHub Actions Workflow
```yaml
# .github/workflows/test-rag.yml
name: Test FAISS RAG System

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: [3.8, 3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-asyncio
    
    - name: Run unit tests
      run: pytest tests/test_memory_manager.py tests/test_lazy_loader.py tests/test_embedding_model.py
    
    - name: Run integration tests
      run: pytest tests/test_rag_integration.py
    
    - name: Run performance tests
      run: pytest tests/test_performance.py
    
    - name: Run compatibility tests
      run: pytest tests/test_compatibility.py
```

This comprehensive deployment and testing plan ensures that the FAISS RAG system is properly integrated, thoroughly tested, and ready for production deployment across different platforms and use cases.
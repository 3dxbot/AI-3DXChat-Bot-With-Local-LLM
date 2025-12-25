# FAISS RAG System - Code Implementation Plan

## File Structure Overview

```
src/
├── rag/
│   ├── __init__.py
│   ├── lazy_loader.py          # Lazy loading for embedding model
│   ├── memory_manager.py       # Core FAISS index management
│   ├── embedding_model.py      # Sentence-Transformers integration
│   └── config.py              # RAG-specific configuration
├── ui_character.py            # Enhanced with memory controls
├── chat_actions.py            # Modified for RAG integration
└── config.py                  # Updated with new paths
```

## Core Classes Implementation

### 1. LazyModelLoader Class

```python
class LazyModelLoader:
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2")
    def load_model(self) -> SentenceTransformer
    def download_model(self, progress_callback: Optional[Callable] = None)
    def is_model_cached(self) -> bool
    def get_model_path(self) -> str
```

**Key Features:**
- Downloads model only when first needed
- Progress tracking during download
- Local caching to avoid repeated downloads
- Error handling with fallback mechanisms

### 2. MemoryManager Class

```python
class MemoryManager:
    def __init__(self, character_name: str, character_path: str)
    def load_or_create_index(self) -> bool
    def rebuild_index(self) -> bool
    def search(self, query: str, k: int = 3) -> List[str]
    def get_card_count(self) -> int
    def is_index_valid(self) -> bool
    def get_index_path(self) -> str
    def get_character_data(self) -> Dict
```

**Key Features:**
- Automatic index creation and rebuilding
- FAISS IndexFlatL2 integration
- Character data validation
- Performance optimization

### 3. EmbeddingModel Class

```python
class EmbeddingModel:
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2")
    def encode(self, texts: Union[str, List[str]]) -> np.ndarray
    def get_dimension(self) -> int
    def preprocess_text(self, text: str) -> str
```

**Key Features:**
- Multilingual text encoding
- Text preprocessing pipeline
- Batch processing support
- Memory-efficient operations

## Integration Points

### Chat Processing Pipeline

```python
# In chat_actions.py - Modified send_to_game method
async def send_to_game(self, processed_parts, force=False):
    # Existing logic...
    
    # NEW: RAG Integration
    if hasattr(self, 'memory_manager') and self.memory_manager:
        context = self.memory_manager.search(user_input, k=3)
        if context:
            # Format context for LLM
            formatted_context = self._format_rag_context(context)
            # Include in LLM prompt
            response = await self.ui.ollama_manager.generate_response(
                f"{formatted_context}\n\nUser: {user_input}",
                system_prompt=self.global_prompt,
                manifest=self.character_manifest
            )
    # Rest of existing logic...
```

### Character UI Enhancement

```python
# In ui_character.py - Enhanced _populate_character_view method
def _populate_character_view(self):
    # Existing UI setup...
    
    # NEW: Memory Management Controls
    mem_controls = ctk.CTkFrame(self.editor_scroll, fg_color="transparent")
    mem_controls.pack(fill="x", pady=(0, 20))
    
    # Memory status indicator
    self.memory_status_label = ctk.CTkLabel(mem_controls, text="Memory: Not Loaded", 
                                           font=UIStyles.FONT_SMALL)
    self.memory_status_label.pack(side="left", padx=20)
    
    # Refresh memory button
    UIStyles.create_button(mem_controls, text="Refresh Memory", 
                          command=self._refresh_character_memory, 
                          width=120).pack(side="right", padx=20)
```

## Configuration Updates

### New Configuration Constants

```python
# In src/config.py - Add new constants
RAG_MODELS_DIR = os.path.join(BASE_DIR, 'bin', 'rag_model')
RAG_VECTORS_DIR = os.path.join(BASE_DIR, 'data', 'vectors')
RAG_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
RAG_SEARCH_K = 3
RAG_EMBEDDING_DIM = 384
```

### Requirements.txt Updates

```txt
# Add to requirements.txt
faiss-cpu>=1.7.0
sentence-transformers>=2.2.0
transformers>=4.20.0
torch>=1.12.0
```

## Error Handling Strategy

### Graceful Degradation

```python
class MemoryManager:
    def search(self, query: str, k: int = 3) -> List[str]:
        try:
            # Try FAISS search
            return self._perform_faiss_search(query, k)
        except Exception as e:
            # Log error but don't crash
            self.logger.warning(f"FAISS search failed: {e}")
            # Return empty context - LLM continues without memory
            return []
```

### Model Download Fallbacks

```python
class LazyModelLoader:
    def download_model(self, progress_callback=None):
        try:
            # Primary download from HuggingFace
            self._download_from_hf(progress_callback)
        except Exception as e:
            self.logger.error(f"Primary download failed: {e}")
            # Try alternative mirror or provide offline instructions
            self._handle_download_failure()
```

## Performance Optimizations

### Caching Strategy

```python
class MemoryManager:
    def __init__(self, character_name: str, character_path: str):
        self._embedding_cache = {}  # Cache for card embeddings
        self._query_cache = {}      # Cache for recent queries
        
    def search(self, query: str, k: int = 3) -> List[str]:
        # Check query cache first
        cache_key = f"{query}_{k}"
        if cache_key in self._query_cache:
            return self._query_cache[cache_key]
        
        # Perform search and cache result
        result = self._perform_search(query, k)
        self._query_cache[cache_key] = result
        return result
```

### Memory Management

```python
class MemoryManager:
    def load_or_create_index(self) -> bool:
        # Load index only when needed
        if not hasattr(self, '_index'):
            self._index = faiss.read_index(self.get_index_path())
        return True
```

## Testing Framework

### Unit Tests Structure

```python
# tests/test_memory_manager.py
class TestMemoryManager:
    def test_index_creation(self)
    def test_search_functionality(self)
    def test_index_rebuilding(self)
    def test_error_handling(self)

# tests/test_lazy_loader.py
class TestLazyModelLoader:
    def test_model_download(self)
    def test_model_caching(self)
    def test_download_failure(self)

# tests/test_embedding_model.py
class TestEmbeddingModel:
    def test_text_encoding(self)
    def test_multilingual_support(self)
    def test_batch_processing(self)
```

### Integration Tests

```python
# tests/test_rag_integration.py
class TestRAGIntegration:
    def test_end_to_end_search(self)
    def test_character_activation_with_memory(self)
    def test_ui_memory_controls(self)
    def test_performance_under_load(self)
```

## Deployment Considerations

### PyInstaller Configuration

```python
# pyinstaller_hooks/hook-faiss.py
hiddenimports = [
    'faiss._swigfaiss',
    'faiss.contrib',
    'faiss.contrib.exact_scoring',
    'faiss.contrib.inspect_tools',
    'faiss.contrib.ondisk_ivf',
    'faiss.contrib.pca',
    'faiss.contrib.torch_utils'
]
```

### Build Optimization

```bash
# PyInstaller build command with optimizations
pyinstaller main.py \
    --onedir \
    --exclude-module torch.cuda \
    --exclude-module faiss.contrib.gpu \
    --hidden-import faiss \
    --hidden-import sentence_transformers
```

This implementation plan provides a comprehensive roadmap for integrating FAISS-based RAG into your chatbot application, with detailed code structure, integration points, and deployment considerations.
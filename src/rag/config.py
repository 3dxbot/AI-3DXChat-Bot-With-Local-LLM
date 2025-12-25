# FAISS RAG System Configuration

# Directory paths for RAG system
RAG_MODELS_DIR = "bin/rag_model"
RAG_VECTORS_DIR = "data/vectors"

# Embedding model configuration
RAG_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
RAG_EMBEDDING_DIM = 384

# FAISS configuration
RAG_SEARCH_K = 3  # Number of most relevant cards to retrieve
RAG_INDEX_TYPE = "IndexFlatL2"  # Exact search for small datasets

# Performance settings
RAG_CACHE_SIZE = 100  # Number of cached embeddings
RAG_QUERY_CACHE_SIZE = 50  # Number of cached queries

# Download settings
RAG_MODEL_DOWNLOAD_TIMEOUT = 300  # 5 minutes
RAG_MODEL_DOWNLOAD_RETRIES = 3

# Error handling
RAG_GRACEFUL_DEGRADATION = True  # Continue without memory if FAISS fails
RAG_SEARCH_TIMEOUT = 10  # 10 seconds max search time
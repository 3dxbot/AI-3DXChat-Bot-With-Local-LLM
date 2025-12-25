# FAISS RAG System User Guide

## Overview

The FAISS RAG (Retrieval-Augmented Generation) system enhances your chatbot with semantic memory capabilities. It allows characters to remember and reference important information from their memory cards during conversations.

## Features

### 🧠 Semantic Memory Search
- **Automatic Indexing**: Memory cards are automatically indexed using state-of-the-art embedding models
- **Semantic Search**: Find relevant information based on meaning, not just keywords
- **Multilingual Support**: Works with Russian, English, and other languages

### 🚀 Lazy Loading
- **On-Demand Downloads**: Embedding model downloads only when first needed
- **Local Caching**: Model cached locally to avoid repeated downloads
- **Fast Startup**: Bot starts quickly without waiting for model downloads

### 🎯 CPU-Optimized
- **No GPU Required**: Runs entirely on CPU to avoid video memory usage
- **Lightweight**: Optimized for systems with 32GB+ RAM
- **PyInstaller Compatible**: Works with compiled executables

## Getting Started

### 1. Character Memory Cards

Memory cards are stored within your character JSON files. Each card has:
- **Key**: A short identifier for the memory
- **Data**: The actual memory content

Example character.json:
```json
{
  "name": "Roxy",
  "greeting": "Hello! I'm Roxy.",
  "global_prompt": "You are a helpful assistant.",
  "manifest": "Roxy is a friendly character who loves to help users.",
  "memory_cards": [
    {
      "key": "Origin",
      "data": "Created in 2025 as a digital companion for users"
    },
    {
      "key": "Personality",
      "data": "Friendly, helpful, and always eager to learn"
    }
  ]
}
```

### 2. Creating Memory Cards

1. **Open Character Page**: Navigate to the Character management section
2. **Select Character**: Choose the character you want to edit
3. **Add Memory Cards**: Use the "Long-term Memory (RAG)" section
4. **Fill Details**: Enter a key and the memory content
5. **Save Character**: Click "Save" to store the changes

### 3. Memory Management

#### Refresh Memory
- **When to Use**: After editing memory cards or when memory seems outdated
- **What It Does**: Rebuilds the search index from current memory cards
- **How to Use**: Click "Refresh Memory" in the character page

#### Rebuild Index
- **When to Use**: If memory search is not working correctly
- **What It Does**: Completely rebuilds the FAISS index
- **How to Use**: Click "Rebuild Index" in the character page

#### Test Search
- **When to Use**: To verify memory search is working
- **What It Does**: Tests semantic search with your query
- **How to Use**: Click "Test Search" and enter a query

### 4. Using Memory in Conversations

The RAG system automatically activates when:
1. A character is activated
2. The character has memory cards
3. A user sends a message

The system will:
1. Analyze the user's message
2. Search for relevant memory cards
3. Include relevant information in the LLM prompt
4. Generate responses that reference the character's memories

## Performance

### Search Speed
- **Typical Response**: <100ms for most queries
- **Large Datasets**: <30 seconds for index rebuilding
- **Memory Usage**: Optimized for 32GB RAM systems

### Model Information
- **Model**: paraphrase-multilingual-MiniLM-L12-v2
- **Size**: ~150MB
- **Languages**: Multilingual (RU/EN/ES/FR/DE/IT)
- **Dimensions**: 384

## Troubleshooting

### Common Issues

#### "Model not cached" Warning
- **Cause**: Embedding model not downloaded yet
- **Solution**: The model will download automatically on first use
- **Prevention**: Ensure internet connection for initial download

#### Slow Search Performance
- **Cause**: Large number of memory cards or complex queries
- **Solution**: Use more specific queries or reduce card count
- **Prevention**: Keep memory cards focused and concise

#### Memory Not Found
- **Cause**: Index not updated after card changes
- **Solution**: Click "Refresh Memory" to rebuild index
- **Prevention**: Always refresh after editing cards

#### PyInstaller Build Issues
- **Cause**: Missing FAISS dependencies in build
- **Solution**: Use provided PyInstaller hooks in `hooks/` directory
- **Prevention**: Include hooks in build process

### Error Messages

#### "FAISS search failed"
- **Meaning**: Search operation encountered an error
- **Action**: The bot will continue without memory context
- **Investigation**: Check logs for specific error details

#### "Model loading failed"
- **Meaning**: Embedding model could not be loaded
- **Action**: Bot continues without RAG features
- **Investigation**: Check internet connection and model cache

#### "Index not valid"
- **Meaning**: FAISS index is corrupted or outdated
- **Action**: Index will be automatically rebuilt
- **Investigation**: Usually resolves automatically

## Advanced Usage

### Memory Card Best Practices

#### Writing Effective Memory Cards
1. **Be Specific**: Use clear, descriptive keys
2. **Keep Concise**: Focus on essential information
3. **Use Complete Sentences**: Helps with semantic understanding
4. **Avoid Ambiguity**: Be clear about context and meaning

#### Example Memory Cards
```json
{
  "key": "User Preferences",
  "data": "User prefers formal communication style and enjoys technical discussions"
}
```

```json
{
  "key": "Character Background",
  "data": "Born in a digital world, designed to assist users with various tasks and conversations"
}
```

### Integration with Character Settings

The RAG system works seamlessly with:
- **Global Prompts**: Memory context enhances prompt effectiveness
- **Character Manifests**: Provides additional character information
- **Language Settings**: Automatically handles multilingual content

## Development

### File Structure
```
project_root/
├── src/rag/              # RAG system source code
│   ├── __init__.py
│   ├── lazy_loader.py    # Model download and caching
│   ├── memory_manager.py # FAISS index management
│   ├── embedding_model.py # Text encoding
│   └── config.py        # Configuration
├── bin/rag_model/        # Cached embedding models
├── data/vectors/         # FAISS index files
└── hooks/               # PyInstaller hooks
```

### API Reference

#### MemoryManager
```python
from src.rag.memory_manager import MemoryManager

# Create manager
manager = MemoryManager("CharacterName", "path/to/character.json")

# Load or create index
success = manager.load_or_create_index()

# Search memory
results = manager.search("user query", k=3)

# Get statistics
stats = manager.get_memory_stats()
```

#### LazyModelLoader
```python
from src.rag.lazy_loader import LazyModelLoader

# Create loader
loader = LazyModelLoader()

# Check if model cached
cached = loader.is_model_cached()

# Load model
model = loader.load_model()
```

## Support

### Getting Help
- **Documentation**: Check this guide for common questions
- **Logs**: Review application logs for error details
- **Community**: Join discussions for additional support

### Reporting Issues
When reporting issues, please include:
1. Error messages from logs
2. Steps to reproduce the issue
3. System information (OS, Python version)
4. Character configuration (if relevant)

## Updates

The RAG system is designed to be:
- **Backward Compatible**: Existing characters continue to work
- **Extensible**: Easy to add new features and models
- **Maintainable**: Clear code structure and documentation

Check for updates to:
- New embedding models
- Performance improvements
- Additional language support
- Enhanced search algorithms

## Conclusion

The FAISS RAG system provides powerful memory capabilities for your chatbot characters. By following this guide, you can:
- Create effective memory cards
- Manage memory efficiently
- Troubleshoot common issues
- Integrate seamlessly with existing character settings

The system is designed to be user-friendly while providing advanced semantic search capabilities that enhance the overall chatbot experience.
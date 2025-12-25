# UI Integration Plan for FAISS RAG System

## Overview

This document details the UI enhancements required to integrate the FAISS RAG system into the existing character management interface. The goal is to provide seamless memory management controls while maintaining the current UI design patterns.

## Current UI Structure Analysis

### Character Management Page
The character page currently consists of:
1. **Sidebar**: Character list with create/delete functionality
2. **Editor Workspace**: Character details editing
   - Static Greetings section
   - LLM Behavior section (Global Prompt + Manifest)
   - Long-term Memory section (Memory Cards)

### Integration Points Identified
- Memory Cards section needs enhancement with RAG controls
- Character activation should trigger memory loading
- Dashboard needs memory status indicators

## UI Enhancement Specifications

### 1. Enhanced Memory Cards Section

#### Current State
```python
# In ui_character.py - Current memory section
self.memory_section = UIStyles.create_card_frame(self.editor_scroll)
self.memory_section.pack(fill="x", pady=(0, 20))

mem_header = ctk.CTkFrame(self.memory_section, fg_color="transparent")
mem_header.pack(fill="x", padx=20, pady=(20, 10))
UIStyles.create_section_header(mem_header, text="Long-term Memory (RAG)").pack(side="left")
UIStyles.create_button(mem_header, text="+ Add Card", command=self._add_memory_card, width=100, height=28).pack(side="right")
```

#### Enhanced State
```python
# Enhanced memory section with RAG controls
self.memory_section = UIStyles.create_card_frame(self.editor_scroll)
self.memory_section.pack(fill="x", pady=(0, 20))

# Header with status and controls
mem_header = ctk.CTkFrame(self.memory_section, fg_color="transparent")
mem_header.pack(fill="x", padx=20, pady=(20, 10))

# Left side: Title and status
mem_title_frame = ctk.CTkFrame(mem_header, fg_color="transparent")
mem_title_frame.pack(side="left")

UIStyles.create_section_header(mem_title_frame, text="Long-term Memory (RAG)").pack(anchor="w")
self.memory_status_label = ctk.CTkLabel(mem_title_frame, text="Status: Not Loaded", 
                                       font=UIStyles.FONT_SMALL, text_color=UIStyles.TEXT_SECONDARY)
self.memory_status_label.pack(anchor="w", pady=(5, 0))

# Right side: Controls
mem_controls_frame = ctk.CTkFrame(mem_header, fg_color="transparent")
mem_controls_frame.pack(side="right")

# Memory management buttons
UIStyles.create_button(mem_controls_frame, text="Refresh Memory", 
                      command=self._refresh_character_memory, 
                      width=120, height=28).pack(side="left", padx=(0, 10))

UIStyles.create_button(mem_controls_frame, text="Rebuild Index", 
                      command=self._rebuild_character_index, 
                      width=120, height=28).pack(side="left", padx=(0, 10))

UIStyles.create_button(mem_controls_frame, text="Test Search", 
                      command=self._test_memory_search, 
                      width=120, height=28).pack(side="left")

# Memory cards container (existing)
self.cards_container = ctk.CTkFrame(self.memory_section, fg_color="transparent")
self.cards_container.pack(fill="x", padx=20, pady=(0, 20))
```

### 2. Memory Status Indicators

#### Status States and Colors
```python
class MemoryStatus:
    NOT_LOADED = ("Not Loaded", UIStyles.TEXT_SECONDARY)
    LOADING = ("Loading...", UIStyles.TEXT_SECONDARY)
    READY = ("Ready", UIStyles.SUCCESS_COLOR)
    REBUILDING = ("Rebuilding...", UIStyles.WARNING_COLOR)
    ERROR = ("Error", UIStyles.ERROR_COLOR)
    SEARCHING = ("Searching...", UIStyles.TEXT_SECONDARY)
```

#### Status Update Methods
```python
def _update_memory_status(self, status: str, color: str = None):
    """Update memory status label with appropriate styling."""
    if color is None:
        color = UIStyles.TEXT_SECONDARY
    
    self.root.after(0, lambda: self.memory_status_label.configure(
        text=f"Status: {status}",
        text_color=color
    ))

def _show_memory_progress(self, message: str, progress: float = None):
    """Show progress indicator for memory operations."""
    if progress is not None:
        # Show progress bar
        if not hasattr(self, '_progress_bar'):
            self._progress_bar = ctk.CTkProgressBar(self.memory_section)
            self._progress_bar.pack(fill="x", padx=20, pady=(10, 0))
        
        self._progress_bar.set(progress)
        self._update_memory_status(message)
    else:
        # Hide progress bar
        if hasattr(self, '_progress_bar'):
            self._progress_bar.pack_forget()
            delattr(self, '_progress_bar')
        self._update_memory_status(message)
```

### 3. Character Activation Integration

#### Enhanced Activation Method
```python
def _activate_current_character(self):
    if not self.current_character: return
    
    self.active_character_name = self.current_character.name
    if hasattr(self.bot, 'active_character_name'):
        self.bot.active_character_name = self.active_character_name
        
        # Apply data to bot
        self.bot.global_prompt = self.current_character.global_prompt
        self.bot.character_greeting = self.current_character.greeting
        self.bot.character_manifest = self.current_character.manifest
        
        # NEW: Initialize memory manager
        if hasattr(self.bot, 'memory_manager'):
            self.bot.memory_manager = None  # Will be created on first use
        
        # Log what is being applied for transparency
        self.bot.log(f"Activating character: {self.active_character_name}", internal=True)
        self.bot.log(f"Global Prompt: {len(self.bot.global_prompt)} chars applied", internal=True)
        self.bot.log(f"Manifest: {len(self.bot.character_manifest)} chars applied", internal=True)
        
        # Save settings - will update active_character_name in chatbot_settings.json
        self.bot.save_settings()
        
        # Sync with StatusManager for UI-wide tracking
        if hasattr(self, 'status_manager'):
            self.status_manager.set_active_character(self.active_character_name)
            self.status_manager.set_character_synced(True)

    # Update Chat UI if available (Reset greeting sender)
    if hasattr(self, 'bot'):
        self.bot.first_message_sent = False

    if hasattr(self, '_display_character_greeting'):
        self._display_character_greeting()

    self._refresh_character_list()
    self._update_activate_btn_state()
    
    # NEW: Update memory status
    self._update_memory_status("Ready", UIStyles.SUCCESS_COLOR)
    
    messagebox.showinfo("Activated", f"Character '{self.active_character_name}' is now active.\nSettings applied to LLM context.\nMemory system ready.")
```

### 4. Dashboard Integration

#### Memory Status Widget
```python
# In dashboard view - Add memory status indicator
def _create_dashboard_view(self):
    # Existing dashboard code...
    
    # NEW: Memory status section
    memory_frame = UIStyles.create_card_frame(self.dashboard_frame)
    memory_frame.pack(fill="x", pady=(0, 20))
    
    UIStyles.create_section_header(memory_frame, text="Memory System").pack(anchor="w", padx=20, pady=(20, 10))
    
    # Memory stats
    stats_frame = ctk.CTkFrame(memory_frame, fg_color="transparent")
    stats_frame.pack(fill="x", padx=20, pady=(0, 20))
    
    self.memory_stats_label = ctk.CTkLabel(stats_frame, text="No active character", 
                                          font=UIStyles.FONT_SMALL)
    self.memory_stats_label.pack(anchor="w")
    
    # Memory controls
    controls_frame = ctk.CTkFrame(memory_frame, fg_color="transparent")
    controls_frame.pack(fill="x", padx=20, pady=(0, 20))
    
    UIStyles.create_button(controls_frame, text="Manage Characters", 
                          command=self._open_character_page, 
                          width=150).pack(side="left")
    
    self.refresh_memory_btn = UIStyles.create_button(controls_frame, text="Refresh Memory", 
                                                    command=self._refresh_active_memory, 
                                                    width=120)
    self.refresh_memory_btn.pack(side="left", padx=(10, 0))
    self.refresh_memory_btn.configure(state="disabled")
```

### 5. Memory Management Methods

#### Core Memory Management Functions
```python
def _refresh_character_memory(self):
    """Refresh memory for current character."""
    if not self.current_character: return
    
    self._show_memory_progress("Refreshing memory...", 0.1)
    
    # Create memory manager if not exists
    if not hasattr(self, 'memory_manager'):
        from src.rag.memory_manager import MemoryManager
        self.memory_manager = MemoryManager(
            self.current_character.name,
            os.path.join(CHARACTERS_DIR, f"{self.current_character.name}.json")
        )
    
    try:
        # Load or rebuild index
        success = self.memory_manager.load_or_create_index()
        if success:
            card_count = self.memory_manager.get_card_count()
            self._update_memory_status(f"Ready ({card_count} cards)", UIStyles.SUCCESS_COLOR)
            self._show_memory_progress("Memory refreshed successfully", 1.0)
        else:
            self._update_memory_status("Error loading memory", UIStyles.ERROR_COLOR)
    except Exception as e:
        self._update_memory_status(f"Error: {str(e)}", UIStyles.ERROR_COLOR)
    finally:
        self._show_memory_progress(None)  # Hide progress

def _rebuild_character_index(self):
    """Force rebuild of character index."""
    if not self.current_character: return
    
    self._show_memory_progress("Rebuilding index...", 0.1)
    
    try:
        if not hasattr(self, 'memory_manager'):
            from src.rag.memory_manager import MemoryManager
            self.memory_manager = MemoryManager(
                self.current_character.name,
                os.path.join(CHARACTERS_DIR, f"{self.current_character.name}.json")
            )
        
        success = self.memory_manager.rebuild_index()
        if success:
            card_count = self.memory_manager.get_card_count()
            self._update_memory_status(f"Index rebuilt ({card_count} cards)", UIStyles.SUCCESS_COLOR)
            self._show_memory_progress("Index rebuilt successfully", 1.0)
        else:
            self._update_memory_status("Error rebuilding index", UIStyles.ERROR_COLOR)
    except Exception as e:
        self._update_memory_status(f"Error: {str(e)}", UIStyles.ERROR_COLOR)
    finally:
        self._show_memory_progress(None)

def _test_memory_search(self):
    """Test memory search functionality."""
    if not self.current_character: return
    
    # Create simple test dialog
    test_window = ctk.CTkToplevel(self.root)
    test_window.title("Test Memory Search")
    test_window.geometry("400x200")
    test_window.transient(self.root)
    
    # Input field
    query_var = tk.StringVar()
    ctk.CTkLabel(test_window, text="Enter search query:").pack(pady=10)
    query_entry = UIStyles.create_input_field(test_window, textvariable=query_var)
    query_entry.pack(fill="x", padx=20, pady=5)
    
    # Results area
    results_text = ctk.CTkTextbox(test_window, height=80, fg_color=UIStyles.CARD_BG)
    results_text.pack(fill="x", padx=20, pady=10)
    
    def perform_search():
        query = query_var.get().strip()
        if not query:
            results_text.delete("1.0", tk.END)
            results_text.insert("1.0", "Please enter a query")
            return
        
        try:
            if not hasattr(self, 'memory_manager'):
                from src.rag.memory_manager import MemoryManager
                self.memory_manager = MemoryManager(
                    self.current_character.name,
                    os.path.join(CHARACTERS_DIR, f"{self.current_character.name}.json")
                )
                self.memory_manager.load_or_create_index()
            
            results = self.memory_manager.search(query, k=3)
            results_text.delete("1.0", tk.END)
            if results:
                results_text.insert("1.0", f"Found {len(results)} relevant cards:\n\n")
                for i, card in enumerate(results, 1):
                    results_text.insert(tk.END, f"{i}. {card[:100]}...\n\n")
            else:
                results_text.insert("1.0", "No relevant cards found")
        except Exception as e:
            results_text.delete("1.0", tk.END)
            results_text.insert("1.0", f"Error: {str(e)}")
    
    # Search button
    UIStyles.create_button(test_window, text="Search", command=perform_search).pack(pady=10)
```

### 6. Error Handling and User Feedback

#### Error Display System
```python
def _show_memory_error(self, error_message: str):
    """Display memory-related errors to user."""
    self._update_memory_status("Error", UIStyles.ERROR_COLOR)
    messagebox.showerror("Memory Error", f"An error occurred with the memory system:\n\n{error_message}\n\nThe chatbot will continue to work without memory features.")
    
    # Log error for debugging
    if hasattr(self, 'bot') and self.bot:
        self.bot.log(f"Memory system error: {error_message}", internal=True)

def _handle_memory_exception(self, func):
    """Decorator to handle memory-related exceptions gracefully."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self._show_memory_error(str(e))
            return None
    return wrapper
```

### 7. Integration with Existing UI Patterns

#### Consistent Styling
```python
# Ensure all new UI elements follow existing patterns
def _create_memory_card_ui(self, card_data, index):
    """Create UI for individual memory card with RAG enhancements."""
    card_frame = UIStyles.create_card_frame(self.cards_container, fg_color=UIStyles.CARD_BG)
    card_frame.pack(fill="x", pady=5)
    
    # Header with card info
    header_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
    header_frame.pack(fill="x", padx=10, pady=5)
    
    # Key concept input
    key_var = tk.StringVar(value=card_data.get("key", ""))
    key_entry = UIStyles.create_input_field(header_frame, textvariable=key_var, 
                                           placeholder_text="Key Concept", width=200)
    key_entry.pack(side="left")
    
    # Card status indicator
    status_label = ctk.CTkLabel(header_frame, text="Status: OK", 
                               font=UIStyles.FONT_SMALL, text_color=UIStyles.TEXT_SECONDARY)
    status_label.pack(side="right", padx=10)
    
    # Data textarea
    data_text = ctk.CTkTextbox(card_frame, height=80, fg_color=UIStyles.APP_BG)
    data_text.pack(fill="x", padx=10, pady=(0, 10))
    data_text.insert("1.0", card_data.get("data", ""))
    
    # Update handlers
    key_var.trace_add("write", lambda *args: self._update_card_data(index, "key", key_var.get()))
    data_text.bind("<KeyRelease>", lambda *args: self._update_card_data(index, "data", data_text.get("1.0", tk.END).strip()))
```

This UI integration plan ensures that the FAISS RAG system is seamlessly integrated into the existing character management interface while providing users with clear feedback and control over the memory system.
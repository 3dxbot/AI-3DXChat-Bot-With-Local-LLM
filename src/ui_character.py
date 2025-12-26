"""
Character Management UI Module.

This module provides the UICharacterMixin class, which handles character profile
management, including creation, editing, memory cards, and activation.
"""

import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from .ui_styles import UIStyles
from .config import CHARACTERS_DIR

class CharacterProfile:
    def __init__(self, name="New Character", greeting="", global_prompt="", manifest="", memory_cards=None, rag_enabled=True):
        self.name = name
        self.greeting = greeting
        self.global_prompt = global_prompt
        self.manifest = manifest
        self.memory_cards = memory_cards if memory_cards else []
        self.rag_enabled = rag_enabled

    def to_dict(self):
        return {
            "name": self.name,
            "greeting": self.greeting,
            "global_prompt": self.global_prompt,
            "manifest": self.manifest,
            "memory_cards": self.memory_cards,
            "rag_enabled": self.rag_enabled
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data.get("name", "New Character"),
            greeting=data.get("greeting", ""),
            global_prompt=data.get("global_prompt", ""),
            manifest=data.get("manifest", ""),
            memory_cards=data.get("memory_cards", []),
            rag_enabled=data.get("rag_enabled", True)
        )

class UICharacterMixin:
    """Mixin class for character profile management UI."""
    
    def _initialize_character_vars(self):
        self.characters = {} # name -> CharacterProfile
        self.current_character = None # CharacterProfile instance being edited
        self.active_character_name = getattr(self.bot, 'active_character_name', None)
        
        # UI variables
        self.char_name_var = tk.StringVar()
        self.char_list_buttons = {} # name -> button widget

    def _populate_character_view(self):
        """Main entry point to build the character page."""
        if not hasattr(self, 'char_name_var'):
            self._initialize_character_vars()
            self._load_all_characters()

        # Clear existing content if any
        for widget in self.character_frame.winfo_children():
            widget.destroy()

        # Configure grid for the character frame
        self.character_frame.columnconfigure(0, weight=0, minsize=200) # Sidebar
        self.character_frame.columnconfigure(1, weight=1) # Editor
        self.character_frame.rowconfigure(0, weight=1)

        # 1. Sidebar
        self.char_sidebar = ctk.CTkFrame(self.character_frame, fg_color=UIStyles.HEADER_BG, corner_radius=0)
        self.char_sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 2))
        
        UIStyles.create_button(self.char_sidebar, text="+ Create New", 
                               command=self._create_new_character).pack(fill="x", padx=10, pady=20)
        
        self.char_scroll_list = ctk.CTkScrollableFrame(self.char_sidebar, fg_color="transparent")
        self.char_scroll_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        self._refresh_character_list()

        # 2. Editor Workspace
        self.char_editor = ctk.CTkFrame(self.character_frame, fg_color="transparent")
        self.char_editor.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.char_editor.columnconfigure(0, weight=1)
        self.char_editor.rowconfigure(1, weight=1)

        # Editor Header
        header = ctk.CTkFrame(self.char_editor, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header.columnconfigure(0, weight=1)

        self.name_entry = UIStyles.create_input_field(header, textvariable=self.char_name_var, 
                                                      placeholder_text="Character Name", font=UIStyles.FONT_H1)
        self.name_entry.grid(row=0, column=0, sticky="w", padx=(0, 10))

        btn_container = ctk.CTkFrame(header, fg_color="transparent")
        btn_container.grid(row=0, column=1, sticky="e")

        UIStyles.create_secondary_button(btn_container, text="Import", command=self._import_character, width=80).pack(side="left", padx=5)
        UIStyles.create_secondary_button(btn_container, text="Export", command=self._export_character, width=80).pack(side="left", padx=5)
        UIStyles.create_button(btn_container, text="Save", command=self._save_current_character, width=80).pack(side="left", padx=5)
        
        self.rewrite_btn = UIStyles.create_secondary_button(btn_container, text="Rewrite Modelfile", 
                                                 command=self._rewrite_character_modelfile, 
                                                 width=140)
        self.rewrite_btn.pack(side="left", padx=5)

        self.activate_btn = UIStyles.create_button(btn_container, text="Activate", 
                                                   command=self._activate_current_character, 
                                                   fg_color=UIStyles.WARNING_COLOR, hover_color="#d97706", width=100)
        self.activate_btn.pack(side="left", padx=(15, 0))

        # Editor Content (Scrollable)
        self.editor_scroll = ctk.CTkScrollableFrame(self.char_editor, fg_color="transparent")
        self.editor_scroll.grid(row=1, column=0, sticky="nsew")

        # Section 1: Greetings
        self._create_section(self.editor_scroll, "Static Greetings", "Greeting for User", "greeting_text")

        # Section 2: LLM Behavior
        behavior_card = UIStyles.create_card_frame(self.editor_scroll)
        behavior_card.pack(fill="x", pady=(0, 20))
        
        UIStyles.create_section_header(behavior_card, text="LLM Behavior (Core)").pack(anchor="w", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(behavior_card, text="Global Prompt", font=UIStyles.FONT_SMALL, text_color=UIStyles.TEXT_SECONDARY).pack(anchor="w", padx=20)
        self.global_prompt_text = ctk.CTkTextbox(behavior_card, height=100, fg_color=UIStyles.CARD_BG, border_width=1, border_color=UIStyles.BORDER_COLOR)
        self.global_prompt_text.pack(fill="x", padx=20, pady=(5, 15))

        ctk.CTkLabel(behavior_card, text="Character Manifest (Core Info)", font=UIStyles.FONT_SMALL, text_color=UIStyles.TEXT_SECONDARY).pack(anchor="w", padx=20)
        self.manifest_text = ctk.CTkTextbox(behavior_card, height=150, fg_color=UIStyles.CARD_BG, border_width=1, border_color=UIStyles.BORDER_COLOR)
        self.manifest_text.pack(fill="x", padx=20, pady=(5, 20))

        # Section 3: Memory Cards
        self.memory_section = UIStyles.create_card_frame(self.editor_scroll)
        self.memory_section.pack(fill="x", pady=(0, 20))
        
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
        
        # REMOVED: Test Search button
        
        UIStyles.create_button(mem_header, text="+ Add Card", command=self._add_memory_card, width=100, height=28).pack(side="right")

        self.cards_container = ctk.CTkFrame(self.memory_section, fg_color="transparent")
        self.cards_container.pack(fill="x", padx=20, pady=(0, 20))

        # Load first character or empty
        if self.characters:
            first_name = list(self.characters.keys())[0]
            self._load_character_into_editor(first_name)
        else:
            self._create_new_character()

    def _create_section(self, parent, title, label, attr_name):
        card = UIStyles.create_card_frame(parent)
        card.pack(fill="x", pady=(0, 20))
        UIStyles.create_section_header(card, text=title).pack(anchor="w", padx=20, pady=(20, 10))
        ctk.CTkLabel(card, text=label, font=UIStyles.FONT_SMALL, text_color=UIStyles.TEXT_SECONDARY).pack(anchor="w", padx=20)
        
        setattr(self, attr_name, ctk.CTkTextbox(card, height=100, fg_color=UIStyles.CARD_BG, border_width=1, border_color=UIStyles.BORDER_COLOR))
        getattr(self, attr_name).pack(fill="x", padx=20, pady=(5, 20))

    def _refresh_character_list(self):
        for widget in self.char_scroll_list.winfo_children():
            widget.destroy()
        
        self.char_list_buttons = {}
        for name in sorted(self.characters.keys()):
            btn_frame = ctk.CTkFrame(self.char_scroll_list, fg_color="transparent")
            btn_frame.pack(fill="x", pady=2)
            
            display_name = name
            if name == self.active_character_name:
                display_name = "★ " + name

            btn = ctk.CTkButton(btn_frame, text=display_name, anchor="w",
                                fg_color="transparent", hover_color=UIStyles.HOVER_COLOR,
                                text_color=UIStyles.TEXT_PRIMARY,
                                command=lambda n=name: self._load_character_into_editor(n))
            btn.pack(side="left", fill="x", expand=True)
            
            # Delete Icon (small)
            UIStyles.create_secondary_button(btn_frame, text="×", width=24, height=24,
                                             command=lambda n=name: self._delete_character(n),
                                             fg_color="transparent", hover_color=UIStyles.ERROR_COLOR).pack(side="right", padx=2)
            
            self.char_list_buttons[name] = btn
        
        self._update_list_highlight()

    def _update_list_highlight(self):
        if not hasattr(self, 'char_list_buttons'): return
        for name, btn in self.char_list_buttons.items():
            if self.current_character and name == self.current_character.name:
                btn.configure(fg_color=UIStyles.SURFACE_COLOR)
            else:
                btn.configure(fg_color="transparent")

    def _load_character_into_editor(self, name):
        if name not in self.characters: return
        
        # Save previous if needed? (User explicitly clicks save for now)
        self.current_character = self.characters[name]
        self.char_name_var.set(self.current_character.name)
        
        # Update Textboxes
        self._set_textbox_text(self.greeting_text, self.current_character.greeting)
        self._set_textbox_text(self.global_prompt_text, self.current_character.global_prompt)
        self._set_textbox_text(self.manifest_text, self.current_character.manifest)
        
        # Update Memory Cards
        self._refresh_memory_cards_ui()
        self._update_list_highlight()
        self._update_activate_btn_state()

    def _set_textbox_text(self, widget, text):
        widget.delete("1.0", tk.END)
        widget.insert("1.0", text)

    def _refresh_memory_cards_ui(self):
        for widget in self.cards_container.winfo_children():
            widget.destroy()
        
        for i, card in enumerate(self.current_character.memory_cards):
            card_ui = UIStyles.create_card_frame(self.cards_container, fg_color=UIStyles.CARD_BG)
            card_ui.pack(fill="x", pady=5)
            
            header = ctk.CTkFrame(card_ui, fg_color="transparent")
            header.pack(fill="x", padx=10, pady=5)
            
            # Key Concept Input
            key_var = tk.StringVar(value=card.get("key", ""))
            key_entry = UIStyles.create_input_field(header, textvariable=key_var, placeholder_text="Key Concept", width=150)
            key_entry.pack(side="left")
            key_var.trace_add("write", lambda *args, idx=i, v=key_var: self._update_card_data(idx, "key", v.get()))

            # Delete button
            UIStyles.create_secondary_button(header, text="Delete", width=60, height=24, 
                                             command=lambda idx=i: self._remove_memory_card(idx),
                                             fg_color=UIStyles.ERROR_COLOR, hover_color="#991b1b").pack(side="right")

            # Data Textarea
            data_text = ctk.CTkTextbox(card_ui, height=60, fg_color=UIStyles.APP_BG)
            data_text.pack(fill="x", padx=10, pady=(0, 10))
            data_text.insert("1.0", card.get("data", ""))
            # Use *args to be robust against different callback signatures
            data_text.bind("<KeyRelease>", lambda *args, idx=i, w=data_text: self._update_card_data(idx, "data", w.get("1.0", tk.END).strip()))

    def _update_card_data(self, idx, field, value):
        if self.current_character and idx < len(self.current_character.memory_cards):
            self.current_character.memory_cards[idx][field] = value

    def _add_memory_card(self):
        if self.current_character:
            self.current_character.memory_cards.append({"key": "", "data": ""})
            self._refresh_memory_cards_ui()

    def _remove_memory_card(self, idx):
        if self.current_character and idx < len(self.current_character.memory_cards):
            self.current_character.memory_cards.pop(idx)
            self._refresh_memory_cards_ui()

    def _create_new_character(self):
        new_name = "New Character"
        counter = 1
        while new_name in self.characters:
            new_name = f"New Character {counter}"
            counter += 1
        
        new_char = CharacterProfile(name=new_name)
        self.characters[new_name] = new_char
        self._refresh_character_list()
        self._load_character_into_editor(new_name)

    def _delete_character(self, name):
        if messagebox.askyesno("Delete", f"Are you sure you want to delete '{name}'?"):
            if name in self.characters:
                del self.characters[name]
                file_path = os.path.join(CHARACTERS_DIR, f"{name}.json")
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                if self.active_character_name == name:
                    self.active_character_name = None
                    if hasattr(self.bot, 'active_character_name'):
                        self.bot.active_character_name = None

                self._refresh_character_list()
                if self.characters:
                    self._load_character_into_editor(list(self.characters.keys())[0])
                else:
                    self._create_new_character()

    def _save_current_character(self):
        if not self.current_character: return
        
        old_name = self.current_character.name
        new_name = self.char_name_var.get().strip()
        
        if not new_name:
            messagebox.showerror("Error", "Name cannot be empty")
            return

        # Update object data
        self.current_character.name = new_name
        self.current_character.greeting = self.greeting_text.get("1.0", tk.END).strip()
        self.current_character.global_prompt = self.global_prompt_text.get("1.0", tk.END).strip()
        self.current_character.manifest = self.manifest_text.get("1.0", tk.END).strip()
        
        # Handle rename
        if old_name != new_name:
            if new_name in self.characters:
                messagebox.showerror("Error", "Character with this name already exists")
                self.char_name_var.set(old_name)
                return
            
            del self.characters[old_name]
            # Delete old file
            old_file = os.path.join(CHARACTERS_DIR, f"{old_name}.json")
            if os.path.exists(old_file):
                os.remove(old_file)
            
            if self.active_character_name == old_name:
                self.active_character_name = new_name
                self.bot.active_character_name = new_name

        self.characters[new_name] = self.current_character
        
        # Save to file
        os.makedirs(CHARACTERS_DIR, exist_ok=True)
        file_path = os.path.join(CHARACTERS_DIR, f"{new_name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.current_character.to_dict(), f, indent=4, ensure_ascii=False)
        
        self._refresh_character_list()
        self._update_list_highlight()
        messagebox.showinfo("Success", f"Character '{new_name}' saved")

    def _activate_current_character(self):
        if not self.current_character: return
        
        self.active_character_name = self.current_character.name
        if hasattr(self.bot, 'active_character_name'):
            self.bot.active_character_name = self.active_character_name
            
            # Apply data to bot
            self.bot.global_prompt = self.current_character.global_prompt
            self.bot.character_greeting = self.current_character.greeting
            self.bot.character_manifest = self.current_character.manifest
            
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
        messagebox.showinfo("Activated", f"Character '{self.active_character_name}' is now active.\nSettings applied to LLM context.")

    def _update_activate_btn_state(self):
        if self.current_character and self.current_character.name == self.active_character_name:
            self.activate_btn.configure(text="Active", state="disabled", fg_color=UIStyles.SUCCESS_COLOR)
        else:
            self.activate_btn.configure(text="Activate", state="normal", fg_color=UIStyles.WARNING_COLOR)

    def _load_all_characters(self):
        self.characters = {}
        if not os.path.exists(CHARACTERS_DIR):
            os.makedirs(CHARACTERS_DIR, exist_ok=True)
            return

        for filename in os.listdir(CHARACTERS_DIR):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(CHARACTERS_DIR, filename), "r", encoding="utf-8-sig") as f:
                        data = json.load(f)
                        char = CharacterProfile.from_dict(data)
                        self.characters[char.name] = char
                        
                        # Sync active character with status manager if this is the one
                        if hasattr(self, 'active_character_name') and char.name == self.active_character_name:
                            if hasattr(self, 'status_manager'):
                                self.status_manager.set_active_character(char.name)
                except Exception as e:
                    print(f"Error loading character {filename}: {e}")

    def _import_character(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8-sig") as f:
                    data = json.load(f)
                    char = CharacterProfile.from_dict(data)
                    
                    # Ensure unique name
                    base_name = char.name
                    counter = 1
                    while char.name in self.characters:
                        char.name = f"{base_name} (Imported {counter})"
                        counter += 1
                    
                    self.characters[char.name] = char
                    self._refresh_character_list()
                    self._load_character_into_editor(char.name)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import character: {e}")

    def _export_character(self):
        if not self.current_character: return
        file_path = filedialog.asksaveasfilename(defaultextension=".json",
                                                 initialfile=f"{self.current_character.name}.json",
                                                 filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(self.current_character.to_dict(), f, indent=4, ensure_ascii=False)
                messagebox.showinfo("Success", f"Character exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export character: {e}")
    
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
    
    def _refresh_character_memory(self):
        """Refresh memory for current character."""
        if not self.current_character: return
        
        self._show_memory_progress("Refreshing memory...", 0.1)
        
        try:
            # Create memory manager if not exists
            from src.rag.memory_manager import MemoryManager
            character_path = os.path.join(CHARACTERS_DIR, f"{self.current_character.name}.json")
            memory_manager = MemoryManager(self.current_character.name, character_path)
            
            # Load or rebuild index
            success = memory_manager.load_or_create_index()
            if success:
                card_count = memory_manager.get_card_count()
                self._update_memory_status(f"Ready ({card_count} cards)", UIStyles.SUCCESS_COLOR)
                self._show_memory_progress("Memory refreshed successfully", 1.0)
                
                # Initialize bot's memory manager
                if hasattr(self.bot, 'initialize_memory_manager'):
                    self.bot.initialize_memory_manager(self.current_character.name, character_path)
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
            from src.rag.memory_manager import MemoryManager
            character_path = os.path.join(CHARACTERS_DIR, f"{self.current_character.name}.json")
            memory_manager = MemoryManager(self.current_character.name, character_path)
            
            success = memory_manager.rebuild_index()
            if success:
                card_count = memory_manager.get_card_count()
                self._update_memory_status(f"Index rebuilt ({card_count} cards)", UIStyles.SUCCESS_COLOR)
                self._show_memory_progress("Index rebuilt successfully", 1.0)
                
                # Initialize bot's memory manager
                if hasattr(self.bot, 'initialize_memory_manager'):
                    self.bot.initialize_memory_manager(self.current_character.name, character_path)
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
                from src.rag.memory_manager import MemoryManager
                character_path = os.path.join(CHARACTERS_DIR, f"{self.current_character.name}.json")
                memory_manager = MemoryManager(self.current_character.name, character_path)
                memory_manager.load_or_create_index()
                
                results = memory_manager.search(query, k=3)
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
    
    def _activate_current_character(self):
        if not self.current_character: return
        
        self.active_character_name = self.current_character.name
        if hasattr(self.bot, 'active_character_name'):
            self.bot.active_character_name = self.active_character_name
            
            # Apply data to bot
            self.bot.global_prompt = self.current_character.global_prompt
            self.bot.character_greeting = self.current_character.greeting
            self.bot.character_manifest = self.current_character.manifest
            
            # Initialize RAG memory manager
            character_path = os.path.join(CHARACTERS_DIR, f"{self.current_character.name}.json")
            if hasattr(self.bot, 'initialize_memory_manager'):
                self.bot.initialize_memory_manager(self.current_character.name, character_path)
            
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
        
        # Update memory status
        self._update_memory_status("Ready", UIStyles.SUCCESS_COLOR)
        
        
        messagebox.showinfo("Activated", f"Character '{self.active_character_name}' is now active.\nSettings applied to LLM context.\nMemory system ready.")

    def _rewrite_character_modelfile(self):
        """Rewrite Modelfile for the current character using active settings."""
        if not self.current_character: return
        
        # 1. Identify Base Model
        if hasattr(self, 'status_manager'):
            current_model = self.status_manager.get_active_model()
        else:
            current_model = None
            
        if not current_model:
            messagebox.showerror("Error", "No active model to use as base.")
            return

        # Simple heuristic to strip suffix if it's already a character model
        # E.g. "llama3-Alice" -> "llama3"
        base_model = current_model
        char_suffix = f"-{self.current_character.name.replace(' ', '_').replace(':', '_')}"
        if current_model.endswith(char_suffix):
            base_model = current_model[:-len(char_suffix)]
            if not messagebox.askyesno("Confirm Base Model", f"Detected base model: '{base_model}'\n(derived from '{current_model}').\n\nProceed to overwrite '{current_model}'?"):
                return
        else:
             if not messagebox.askyesno("Confirm Base Model", f"Using active model '{current_model}' as BASE.\nRun this only if '{current_model}' is a raw model (e.g. llama3, mistral).\n\nIf '{current_model}' is already a custom character model, this will create a double-nested model (bad).\n\nProceed?"):
                 return
        
        # 2. Prepare Character Data with Params
        char_data = self.current_character.to_dict()
        
        # Add generation params
        if hasattr(self, 'bot'):
            char_data["model_params"] = {
                "temperature": getattr(self.bot, 'temperature', 0.7),
                "repeat_penalty": getattr(self.bot, 'repeat_penalty', 1.1)
            }
        
        # 3. Create Model
        try:
            if hasattr(self, 'ollama_manager'):
                self.activate_btn.configure(state="disabled", text="Rewriting...")
                
                # Run in thread to avoid freezing UI
                def rewrite_task():
                    try:
                         # create_character_model returns the name of the created model
                        new_model_name = self.ollama_manager.create_character_model(base_model, char_data)
                        
                        if new_model_name:
                             # 4. Activate the new model
                             self.ollama_manager.activate_model(new_model_name)
                             self.root.after(0, lambda: messagebox.showinfo("Success", f"Modelfile rewritten and applied!\nActive Model: {new_model_name}"))
                        else:
                             self.root.after(0, lambda: messagebox.showerror("Error", "Failed to create/rewrite model."))
                             
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        err_msg = repr(e)
                        self.root.after(0, lambda: messagebox.showerror("Error", f"Error rewriting Modelfile: {err_msg}"))
                    finally:
                        self.root.after(0, lambda: self._update_activate_btn_state())

                import threading
                threading.Thread(target=rewrite_task, daemon=True).start()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initiate rewrite: {e}")
            self._update_activate_btn_state()

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
    def __init__(self, name="New Character", greeting="", global_prompt="", manifest="", memory_cards=None):
        self.name = name
        self.greeting = greeting
        self.global_prompt = global_prompt
        self.manifest = manifest
        self.memory_cards = memory_cards if memory_cards else []

    def to_dict(self):
        return {
            "name": self.name,
            "greeting": self.greeting,
            "global_prompt": self.global_prompt,
            "manifest": self.manifest,
            "memory_cards": self.memory_cards
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data.get("name", "New Character"),
            greeting=data.get("greeting", ""),
            global_prompt=data.get("global_prompt", ""),
            manifest=data.get("manifest", ""),
            memory_cards=data.get("memory_cards", [])
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
        UIStyles.create_section_header(mem_header, text="Long-term Memory (RAG)").pack(side="left")
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
            data_text.bind("<KeyRelease>", lambda e, idx=i, w=data_text: self._update_card_data(idx, "data", w.get("1.0", tk.END).strip()))

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
            self.bot.save_settings()
            
            # Sync with StatusManager for UI-wide tracking
            if hasattr(self, 'status_manager'):
                self.status_manager.set_active_character(self.active_character_name)

        # Update Chat UI if available
        if hasattr(self, '_display_character_greeting'):
            self._display_character_greeting()

        self._refresh_character_list()
        self._update_activate_btn_state()
        messagebox.showinfo("Activated", f"Character '{self.active_character_name}' is now active.")

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
                    with open(os.path.join(CHARACTERS_DIR, filename), "r", encoding="utf-8") as f:
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
                with open(file_path, "r", encoding="utf-8") as f:
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

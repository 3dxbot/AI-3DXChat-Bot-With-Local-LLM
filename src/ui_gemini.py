"""
Gemini UI Module.

This module provides UI components for Gemini integration.
"""

import tkinter as tk
import customtkinter as ctk
import webbrowser
from .gemini_manager import GeminiManager
from .status_manager import StatusManager
from .ui_styles import UIStyles

class GeminiUI:
    """
    UI class for Gemini integration.
    """
    
    def __init__(self, parent, gemini_manager: GeminiManager, status_manager: StatusManager):
        self.parent = parent
        self.gemini_manager = gemini_manager
        self.status_manager = status_manager
        
        self.api_key_var = tk.StringVar(value=self.gemini_manager.api_key or "")
        
        # UI Components
        self.status_label = None
        self.status_indicator = None
        self.model_dropdown = None
        
        # Bind status callbacks
        self.status_manager.add_callback('ollama_status', self._on_status_change)
        
    def create_dashboard_zone(self, parent):
        """Create Gemini status zone for Dashboard."""
        zone = UIStyles.create_card_frame(parent)
        
        header = ctk.CTkFrame(zone, fg_color="transparent")
        header.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_MD))
        
        ctk.CTkLabel(header, text="Gemini Status", font=UIStyles.FONT_TITLE, text_color=UIStyles.TEXT_PRIMARY).pack(side='left')
        
        status_frame = ctk.CTkFrame(header, fg_color="transparent")
        status_frame.pack(side='right')
        
        self.status_indicator = ctk.CTkLabel(status_frame, text="●", font=(UIStyles.FONT_FAMILY, 20))
        self.status_indicator.pack(side='left', padx=(0, UIStyles.SPACE_SM))
        
        self.status_label = ctk.CTkLabel(status_frame, text="Checking...", font=UIStyles.FONT_NORMAL, text_color=UIStyles.TEXT_SECONDARY)
        self.status_label.pack(side='left')
        
        # Trigger initial check
        self._on_status_change(self.status_manager.get_ollama_status(), "")
        return zone

    def create_ai_setup_zones(self, parent):
        """Create zones for AI Setup page."""
        zones = {}
        zones['connection'] = self._create_connection_zone(parent)
        zones['models'] = self._create_model_zone(parent)
        return zones

    def _create_connection_zone(self, parent):
        """Create connection settings zone."""
        zone = UIStyles.create_card_frame(parent)
        zone.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=UIStyles.SPACE_LG)
        
        header = ctk.CTkFrame(zone, fg_color="transparent")
        header.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_MD))
        
        ctk.CTkLabel(header, text="Gemini API Connection", font=UIStyles.FONT_TITLE, text_color=UIStyles.TEXT_PRIMARY).pack(side='left')
        
        # Help link
        help_link = ctk.CTkLabel(header, text="Get API Key from Google AI Studio", font=UIStyles.FONT_NORMAL, text_color=UIStyles.PRIMARY_COLOR, cursor="hand2")
        help_link.pack(side='right')
        help_link.bind("<Button-1>", lambda e: webbrowser.open("https://aistudio.google.com/app/apikey"))

        content = ctk.CTkFrame(zone, fg_color="transparent")
        content.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_2XL))
        
        ctk.CTkLabel(content, text="Gemini API Key:", font=UIStyles.FONT_NORMAL, text_color=UIStyles.TEXT_SECONDARY).pack(anchor='w', pady=(0, UIStyles.SPACE_SM))
        
        input_frame = ctk.CTkFrame(content, fg_color="transparent")
        input_frame.pack(fill='x')
        
        self.api_key_entry = UIStyles.create_input_field(input_frame)
        self.api_key_entry.pack(side='left', fill='x', expand=True, padx=(0, UIStyles.SPACE_MD))
        self.api_key_entry.insert(0, self.api_key_var.get())
        
        UIStyles.create_button(input_frame, text="Save & Connect", command=self._on_save_key, width=120).pack(side='right')
        
        return zone

    def _create_model_zone(self, parent):
        """Create model selection zone."""
        zone = UIStyles.create_card_frame(parent)
        zone.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=UIStyles.SPACE_LG)
        
        header = ctk.CTkFrame(zone, fg_color="transparent")
        header.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_MD))
        
        ctk.CTkLabel(header, text="Model Selection", font=UIStyles.FONT_TITLE, text_color=UIStyles.TEXT_PRIMARY).pack(side='left')
        
        content = ctk.CTkFrame(zone, fg_color="transparent")
        content.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_2XL))
        
        self.model_dropdown = ctk.CTkComboBox(
            content,
            values=["gemini-1.5-flash", "gemini-1.5-pro"], # Defaults
            command=self._on_model_select,
            width=300,
            fg_color=UIStyles.SURFACE_COLOR,
            button_color=UIStyles.SECONDARY_COLOR
        )
        self.model_dropdown.pack(anchor='w')
        
        # Load models if connected
        if self.gemini_manager.api_key:
            self._refresh_models()
            
        return zone

    def _on_save_key(self):
        """Handle API key save."""
        key = self.api_key_entry.get().strip()
        if self.gemini_manager.save_api_key(key):
            self._refresh_models()
            tk.messagebox.showinfo("Success", "Gemini API Key saved and connected!")
        else:
            tk.messagebox.showerror("Error", "Failed to save API key")

    def _refresh_models(self):
        """Fetch and update model list."""
        try:
            models = self.gemini_manager.list_models()
            model_ids = [m['id'] for m in models if 'gemini' in m['id']]
            if model_ids:
                if hasattr(self, 'model_dropdown') and self.model_dropdown:
                    self.model_dropdown.configure(values=model_ids)
                    current = self.status_manager.get_active_model()
                    if current in model_ids:
                        self.model_dropdown.set(current)
                    else:
                        self.model_dropdown.set(model_ids[0])
                        self.status_manager.set_active_model(model_ids[0])
        except Exception as e:
            print(f"Error fetching models: {e}")

    def _on_model_select(self, model_name):
        self.status_manager.set_active_model(model_name)

    def _on_status_change(self, new_status, old_status):
        color_map = {
            "Connected": "#10b981",
            "Auth Error": "#ef4444",
            "Connection Error": "#ef4444",
            "No API Key": "#f59e0b"
        }
        color = color_map.get(new_status, "#94a3b8")
        
        if self.status_label:
            self.status_label.configure(text=new_status)
        if self.status_indicator:
            self.status_indicator.configure(text_color=color)

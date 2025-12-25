"""
Ollama UI Module.

This module provides UI components for Ollama integration.

Classes:
    OllamaUI: Class for Ollama-specific UI components.
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from typing import Optional, Callable
import threading
import time
import logging

from .ollama_manager import OllamaManager
from .status_manager import StatusManager
from .file_manager import FileManager
from .download_manager import DownloadManager
from .ui_styles import UIStyles


class OllamaUI:
    """
    UI class for Ollama integration.
    
    Handles UI components and interactions for Ollama management.
    
    Attributes:
        parent: Parent widget.
        ollama_manager: OllamaManager instance.
        status_manager: StatusManager instance.
        file_manager: FileManager instance.
        download_manager: DownloadManager instance.
    """
    
    def __init__(self, parent, ollama_manager: OllamaManager, status_manager: StatusManager,
                 file_manager: FileManager, download_manager: DownloadManager):
        """
        Initialize OllamaUI.

        Args:
            parent: Parent widget.
            ollama_manager: OllamaManager instance.
            status_manager: StatusManager instance.
            file_manager: FileManager instance.
            download_manager: DownloadManager instance.
        """
        self.parent = parent
        self.ollama_manager = ollama_manager
        self.status_manager = status_manager
        self.file_manager = file_manager
        self.download_manager = download_manager
        self.logger = logging.getLogger(__name__)
        
        # Enhanced download progress tracking
        self.model_progress_details = None
        self.model_progress_text = None
        
        # UI components
        self.status_label = None
        self.status_indicator = None
        self.active_model_label = None
        self.download_progress = None
        self.download_status = None
        self.model_dropdown = None
        self.active_char_label = None
        self.char_sync_label = None
        self.gpu_info_label = None
        
        # Bind status callbacks
        self.status_manager.add_callback('ollama_status', self._on_ollama_status_change)
        self.status_manager.add_callback('active_model', self._on_active_model_change)
        self.status_manager.add_callback('active_character', self._on_active_character_change)
        self.status_manager.add_callback('character_sync', self._on_character_sync_change)
    
    def format_bytes(self, b: int) -> str:
        """Format bytes to human readable format."""
        if b < 1024:
            return f"{b} B"
        elif b < 1024 * 1024:
            return f"{b / 1024:.1f} KB"
        elif b < 1024 * 1024 * 1024:
            return f"{b / (1024 * 1024):.1f} MB"
        else:
            return f"{b / (1024 * 1024 * 1024):.1f} GB"
    
    def create_dashboard_zone(self, parent):
        """Create Ollama status zone for Dashboard - compact version without control buttons."""
        # Main container
        ollama_zone = UIStyles.create_card_frame(parent)
        # Note: This will be gridded by the parent, not packed
        
        # Zone header
        zone_header = ctk.CTkFrame(ollama_zone, fg_color="transparent")
        zone_header.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_MD))
        
        # Title
        title = ctk.CTkLabel(
            zone_header,
            text="Ollama Status",
            font=UIStyles.FONT_TITLE,
            text_color=UIStyles.TEXT_PRIMARY
        )
        title.pack(side='left')
        
        # Status indicator and text
        status_frame = ctk.CTkFrame(zone_header, fg_color="transparent")
        status_frame.pack(side='right')
        
        self.status_indicator = ctk.CTkLabel(
            status_frame,
            text="●",
            font=(UIStyles.FONT_FAMILY, 20),
            text_color="#f59e0b"
        )
        self.status_indicator.pack(side='left', padx=(0, UIStyles.SPACE_SM))
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Checking...",
            font=UIStyles.FONT_NORMAL,
            text_color=UIStyles.TEXT_SECONDARY
        )
        self.status_label.pack(side='left')
        
        # Active model info
        model_info = ctk.CTkFrame(ollama_zone, fg_color="transparent")
        model_info.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_LG))
        
        model_text = ctk.CTkLabel(
            model_info,
            text="Active Model:",
            font=UIStyles.FONT_NORMAL,
            text_color=UIStyles.TEXT_TERTIARY
        )
        model_text.pack(side='left')
        
        self.active_model_label = ctk.CTkLabel(
            model_info,
            text="None",
            font=UIStyles.FONT_NORMAL,
            text_color=UIStyles.TEXT_PRIMARY
        )
        self.active_model_label.pack(side='left', padx=(UIStyles.SPACE_SM, 0))
        
        # Character Profile info (New)
        char_info = ctk.CTkFrame(ollama_zone, fg_color="transparent")
        char_info.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_LG))
        
        char_text = ctk.CTkLabel(
            char_info,
            text="Active Profile:",
            font=UIStyles.FONT_NORMAL,
            text_color=UIStyles.TEXT_TERTIARY
        )
        char_text.pack(side='left')
        
        self.active_char_label = ctk.CTkLabel(
            char_info,
            text="None",
            font=UIStyles.FONT_NORMAL,
            text_color=UIStyles.PRIMARY_COLOR
        )
        self.active_char_label.pack(side='left', padx=(UIStyles.SPACE_SM, 0))

        self.char_sync_label = ctk.CTkLabel(
            char_info,
            text="(Not Applied)",
            font=UIStyles.FONT_SMALL,
            text_color="#94a3b8" # Muted slate
        )
        self.char_sync_label.pack(side='left', padx=(UIStyles.SPACE_MD, 0))

        # GPU information
        gpu_info = ctk.CTkFrame(ollama_zone, fg_color="transparent")
        gpu_info.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_2XL))

        gpu_text = ctk.CTkLabel(
            gpu_info,
            text="GPU Status:",
            font=UIStyles.FONT_NORMAL,
            text_color=UIStyles.TEXT_TERTIARY
        )
        gpu_text.pack(side='left')

        self.gpu_info_label = ctk.CTkLabel(
            gpu_info,
            text="Checking...",
            font=UIStyles.FONT_NORMAL,
            text_color=UIStyles.TEXT_SECONDARY
        )
        self.gpu_info_label.pack(side='left', padx=(UIStyles.SPACE_SM, 0))

        # Trigger initial status sync
        current_status = self.status_manager.get_ollama_status()
        self._on_ollama_status_change(current_status, "")

        # Initial character sync
        current_char = self.status_manager.get_active_character()
        if current_char:
            self._on_active_character_change(current_char, None)

        # Initial GPU info update
        self._update_gpu_info()

        return ollama_zone
    
    def create_ai_setup_zones(self, parent):
        """Create all zones for AI Setup page."""
        zones = {}
        
        # Zone 1: Ollama Management
        zones['ollama_management'] = self._create_ollama_management_zone(parent)
        
        # Zone 2: Download Progress - REMOVED, progress bars are now inline
        # zones['download_progress'] = self._create_download_progress_zone(parent)
        
        # Zone 3: Model Management
        zones['model_management'] = self._create_model_management_zone(parent)
        
        # Zone 4: System Information
        zones['system_info'] = self._create_system_info_zone(parent)
        
        return zones
    
    def _create_ollama_management_zone(self, parent):
        """Create Ollama management zone."""
        zone = UIStyles.create_card_frame(parent)
        zone.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=UIStyles.SPACE_LG)
        
        # Header
        header = ctk.CTkFrame(zone, fg_color="transparent")
        header.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_MD))
        
        title = ctk.CTkLabel(
            header,
            text="Ollama Management",
            font=UIStyles.FONT_TITLE,
            text_color=UIStyles.TEXT_PRIMARY
        )
        title.pack(side='left')
        
        # Status display
        status_frame = ctk.CTkFrame(zone, fg_color="transparent")
        status_frame.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_LG))
        
        self.ai_status_label = ctk.CTkLabel(
            status_frame,
            text="Status: Checking...",
            font=UIStyles.FONT_TITLE,
            text_color=UIStyles.TEXT_PRIMARY
        )
        self.ai_status_label.pack(anchor='w')
        
        # Action buttons
        action_frame = ctk.CTkFrame(zone, fg_color="transparent")
        action_frame.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_2XL))
        
        # Row 1
        row1 = ctk.CTkFrame(action_frame, fg_color="transparent")
        row1.pack(fill='x', pady=(0, UIStyles.SPACE_MD))
        
        # Combined Action Button (Download/Delete)
        self.ai_action_btn = UIStyles.create_button(
            row1,
            text="Download Ollama",
            command=self._on_action_click,
            width=140
        )
        self.ai_action_btn.pack(side='left', padx=(0, UIStyles.SPACE_MD))
        
        # Combined Service Button (Start/Stop)
        self.ai_service_btn = UIStyles.create_button(
            row1,
            text="Start Service",
            command=self._on_service_toggle_click,
            state="disabled",
            width=120
        )
        self.ai_service_btn.pack(side='left', padx=(0, UIStyles.SPACE_MD))
        
        # Removed redundant Row 2 buttons, consolidated into Row 1
        # Progress Section (Hidden by default)
        self.ollama_progress_frame = ctk.CTkFrame(zone, fg_color="transparent")
        self.ollama_progress_frame.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_2XL))
        self.ollama_progress_frame.pack_forget() # Hide initially

        progress_header = ctk.CTkFrame(self.ollama_progress_frame, fg_color="transparent")
        progress_header.pack(fill='x', pady=(0, 5))
        
        ctk.CTkLabel(progress_header, text="Downloading Ollama...", font=UIStyles.FONT_NORMAL, text_color=UIStyles.TEXT_SECONDARY).pack(side='left')
        self.ollama_progress_label = ctk.CTkLabel(progress_header, text="0%", font=UIStyles.FONT_NORMAL, text_color=UIStyles.TEXT_PRIMARY)
        self.ollama_progress_label.pack(side='right')

        self.ollama_progress_bar = ctk.CTkProgressBar(self.ollama_progress_frame, height=10, progress_color=UIStyles.PRIMARY_COLOR)
        self.ollama_progress_bar.pack(fill='x')
        self.ollama_progress_bar.set(0)

        # Trigger initial status sync
        current_status = self.status_manager.get_ollama_status()
        self._on_ollama_status_change(current_status, "")

        return zone
    
    def _create_download_progress_zone(self, parent):
        """Create download progress zone."""
        zone = UIStyles.create_card_frame(parent)
        zone.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=UIStyles.SPACE_LG)
        
        # Header
        header = ctk.CTkFrame(zone, fg_color="transparent")
        header.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_MD))
        
        title = ctk.CTkLabel(
            header,
            text="Download Progress",
            font=UIStyles.FONT_TITLE,
            text_color=UIStyles.TEXT_PRIMARY
        )
        title.pack(side='left')
        
        # Progress display
        progress_frame = ctk.CTkFrame(zone, fg_color="transparent")
        progress_frame.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_LG))
        
        self.download_progress = ctk.CTkProgressBar(progress_frame)
        self.download_progress.pack(fill='x', pady=(UIStyles.SPACE_MD, 0))
        self.download_progress.set(0)
        self.download_progress.configure(
            progress_color=UIStyles.PRIMARY_COLOR,
            fg_color=UIStyles.SURFACE_COLOR,
            height=12
        )
        
        self.download_status = ctk.CTkLabel(
            progress_frame,
            text="Ready to download",
            font=UIStyles.FONT_NORMAL,
            text_color=UIStyles.TEXT_SECONDARY
        )
        self.download_status.pack(anchor='w', pady=(UIStyles.SPACE_MD, UIStyles.SPACE_2XL))
        
        return zone
    
    def _create_model_management_zone(self, parent):
        """Create model management zone."""
        zone = UIStyles.create_card_frame(parent)
        zone.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=UIStyles.SPACE_LG)
        
        # Header
        header = ctk.CTkFrame(zone, fg_color="transparent")
        header.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_MD))
        
        title = ctk.CTkLabel(
            header,
            text="Model Management",
            font=UIStyles.FONT_TITLE,
            text_color=UIStyles.TEXT_PRIMARY
        )
        title.pack(side='left')
    
        # Active model indicator in setup
        current_model = self.status_manager.get_active_model()
        model_text = current_model if current_model else "None"
        
        self.setup_active_model_label = ctk.CTkLabel(
            header,
            text=f" (Active: {model_text})",
            font=UIStyles.FONT_NORMAL,
            text_color=UIStyles.PRIMARY_COLOR
        )
        self.setup_active_model_label.pack(side='left', padx=(UIStyles.SPACE_SM, 0))
        
        # Download section
        download_section = ctk.CTkFrame(zone, fg_color="transparent")
        download_section.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_LG))
        
        # Input
        input_label = ctk.CTkLabel(
            download_section,
            text="Model Name (e.g., llama2, mistral):",
            font=UIStyles.FONT_NORMAL,
            text_color=UIStyles.TEXT_SECONDARY
        )
        input_label.pack(anchor='w', pady=(0, UIStyles.SPACE_SM))
        
        # Input and Download Button Row
        input_row = ctk.CTkFrame(download_section, fg_color="transparent")
        input_row.pack(fill='x', pady=(0, UIStyles.SPACE_MD))
        
        self.model_input = UIStyles.create_input_field(
            input_row,
            placeholder_text="Enter model name from Ollama repository..."
        )
        self.model_input.pack(side='left', fill='x', expand=True, padx=(0, UIStyles.SPACE_MD))
        
        self.download_model_btn = UIStyles.create_button(
            input_row,
            text="Download Model",
            command=self._on_download_model_click,
            width=140
        )
        self.download_model_btn.pack(side='right')
        
        # Model list section
        list_section = ctk.CTkFrame(zone, fg_color="transparent")
        list_section.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_2XL))
        
        list_label = ctk.CTkLabel(
            list_section,
            text="Available Models:",
            font=UIStyles.FONT_NORMAL,
            text_color=UIStyles.TEXT_SECONDARY
        )
        list_label.pack(anchor='w', pady=(UIStyles.SPACE_LG, UIStyles.SPACE_SM))
        
        # Model controls
        control_frame = ctk.CTkFrame(list_section, fg_color="transparent")
        control_frame.pack(fill='x')
        
        self.model_dropdown = ctk.CTkComboBox(
            control_frame,
            values=[],
            command=self._on_model_select,
            width=280,
            height=34,
            fg_color=UIStyles.SURFACE_COLOR,
            button_color=UIStyles.SECONDARY_COLOR,
            button_hover_color=UIStyles.HOVER_COLOR,
            dropdown_fg_color=UIStyles.SURFACE_COLOR,
            text_color=UIStyles.TEXT_SECONDARY # Start with muted text for placeholder
        )
        self.model_dropdown.set("empty")
        self.model_dropdown.pack(side='left', padx=(0, UIStyles.SPACE_MD))
        
        self.activate_model_btn = UIStyles.create_button(
            control_frame,
            text="Activate",
            command=self._on_activate_model_click,
            state="disabled",
            width=110
        )
        self.activate_model_btn.pack(side='left', padx=(0, UIStyles.SPACE_MD))
        
        self.delete_model_btn = UIStyles.create_secondary_button(
            control_frame,
            text="Delete",
            command=self._on_delete_model_click,
            state="disabled",
            width=110,
            fg_color=UIStyles.SECONDARY_COLOR,
            hover_color=UIStyles.ERROR_COLOR
        )
        self.delete_model_btn.pack(side='left')
        
        # Progress Section (Hidden by default)
        self.model_progress_frame = ctk.CTkFrame(zone, fg_color="transparent")
        self.model_progress_frame.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_2XL))
        self.model_progress_frame.pack_forget() # Hide initially

        progress_header = ctk.CTkFrame(self.model_progress_frame, fg_color="transparent")
        progress_header.pack(fill='x', pady=(0, 5))
        
        self.model_progress_title = ctk.CTkLabel(progress_header, text="Downloading Model...", font=UIStyles.FONT_NORMAL, text_color=UIStyles.TEXT_SECONDARY)
        self.model_progress_title.pack(side='left')
        self.model_progress_label = ctk.CTkLabel(progress_header, text="0%", font=UIStyles.FONT_NORMAL, text_color=UIStyles.TEXT_PRIMARY)
        self.model_progress_label.pack(side='right')

        self.model_progress_bar = ctk.CTkProgressBar(self.model_progress_frame, height=10, progress_color=UIStyles.PRIMARY_COLOR)
        self.model_progress_bar.pack(fill='x')
        self.model_progress_bar.set(0)
        
        # Enhanced progress details
        self.model_progress_details = ctk.CTkLabel(
            self.model_progress_frame,
            text="Status: Waiting for manifest...",
            font=UIStyles.FONT_SMALL,
            text_color=UIStyles.TEXT_TERTIARY
        )
        self.model_progress_details.pack(anchor='w', pady=(5, 0))

        # Trigger initial model list refresh if running
        if self.status_manager.get_ollama_status() == "Running":
            self._refresh_model_list()

        return zone
    
    def _create_system_info_zone(self, parent):
        """Create system information zone."""
        zone = UIStyles.create_card_frame(parent)
        zone.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=UIStyles.SPACE_LG)
        
        # Header
        header = ctk.CTkFrame(zone, fg_color="transparent")
        header.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_MD))
        
        title = ctk.CTkLabel(
            header,
            text="System Information",
            font=UIStyles.FONT_TITLE,
            text_color=UIStyles.TEXT_PRIMARY
        )
        title.pack(side='left')
        
        # Info content
        content = ctk.CTkFrame(zone, fg_color="transparent")
        content.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_2XL))
        
        # Installation path
        path_frame = ctk.CTkFrame(content, fg_color="transparent")
        path_frame.pack(fill='x', pady=(0, UIStyles.SPACE_SM))
        
        path_label = ctk.CTkLabel(
            path_frame,
            text="Installation Path:",
            font=UIStyles.FONT_NORMAL,
            text_color=UIStyles.TEXT_SECONDARY
        )
        path_label.pack(side='left')
        
        self.install_path_label = ctk.CTkLabel(
            path_frame,
            text="Not installed",
            font=UIStyles.FONT_NORMAL,
            text_color=UIStyles.TEXT_PRIMARY
        )
        self.install_path_label.pack(side='left', padx=(UIStyles.SPACE_MD, 0))
        
        # Storage usage
        storage_frame = ctk.CTkFrame(content, fg_color="transparent")
        storage_frame.pack(fill='x', pady=(0, UIStyles.SPACE_SM))
        
        storage_label = ctk.CTkLabel(
            storage_frame,
            text="Storage Usage:",
            font=UIStyles.FONT_NORMAL,
            text_color=UIStyles.TEXT_SECONDARY
        )
        storage_label.pack(side='left')
        
        self.storage_label = ctk.CTkLabel(
            storage_frame,
            text="0 MB",
            font=UIStyles.FONT_NORMAL,
            text_color=UIStyles.TEXT_PRIMARY
        )
        self.storage_label.pack(side='left', padx=(UIStyles.SPACE_MD, 0))
        
        # Last update
        update_frame = ctk.CTkFrame(content, fg_color="transparent")
        update_frame.pack(fill='x')
        
        update_label = ctk.CTkLabel(
            update_frame,
            text="Last Update:",
            font=UIStyles.FONT_NORMAL,
            text_color=UIStyles.TEXT_SECONDARY
        )
        update_label.pack(side='left')
        
        self.update_label = ctk.CTkLabel(
            update_frame,
            text="Never",
            font=UIStyles.FONT_NORMAL,
            text_color=UIStyles.TEXT_PRIMARY
        )
        self.update_label.pack(side='left', padx=(UIStyles.SPACE_MD, 0))
        
        return zone
    
    # Event handlers
    def _on_ollama_status_change(self, new_status: str, old_status: str):
        """Handle Ollama status changes."""
        # Update status text and colors
        # Update status indicator color
        color_map = {
            "Stopped": "#94a3b8", # Neutral grey-blue
            "Not Installed": "#ef4444",
            "Starting": "#f59e0b",
            "Running": "#10b981",
            "Error": "#ef4444",
            "Downloading": "#3b82f6",
            "Installing": "#8b5cf6"
        }
        
        color = color_map.get(new_status, "#f59e0b")
        
        # Safely update UI using after()
        def safe_update():
            # Check if parent is still valid and has 'after'
            if not hasattr(self.parent, 'after'):
                return
            try:
                if hasattr(self, 'status_label') and self.status_label:
                    self.status_label.configure(text=new_status)
                if hasattr(self, 'ai_status_label') and self.ai_status_label:
                    self.ai_status_label.configure(text=f"Status: {new_status}")
                if hasattr(self, 'status_indicator') and self.status_indicator:
                    self.status_indicator.configure(text_color=color)
                self._update_button_states(new_status)
            except Exception:
                pass # UI may be closing or not in main loop yet

        try:
            self.parent.after(0, safe_update)
        except Exception:
            pass # Handle "main thread not in main loop" or similar init errors
        
        # Refresh model list if service just started running
        if new_status == "Running":
            self.parent.after(500, self._refresh_model_list)
            # Update GPU info when Ollama starts
            self.parent.after(1000, self._update_gpu_info)
    
    def _on_active_model_change(self, new_model: Optional[str], old_model: Optional[str]):
        """Handle active model changes."""
        self.parent.after(0, lambda: self._handle_active_model_ui_update(new_model))

    def _on_active_character_change(self, new_char: Optional[str], old_char: Optional[str]):
        """Handle active character profile changes."""
        self.parent.after(0, lambda: self._handle_active_character_ui_update(new_char))

    def _on_character_sync_change(self, is_synced: bool, was_synced: bool):
        """Handle character manifest sync status changes."""
        self.parent.after(0, lambda: self._handle_character_sync_ui_update(is_synced))

    def _handle_character_sync_ui_update(self, is_synced: bool):
        active_model = self.status_manager.get_active_model()
        if is_synced and active_model:
            text = f"(Synced with {active_model})"
            color = "#10b981" # Emerald
        else:
            text = "(Not Applied)"
            color = "#94a3b8" # Slate
        
        if hasattr(self, 'char_sync_label') and self.char_sync_label:
            self.char_sync_label.configure(text=text, text_color=color)
        
        if hasattr(self, 'setup_char_sync_label') and self.setup_char_sync_label:
            self.setup_char_sync_label.configure(text=text, text_color=color)

    def _handle_active_character_ui_update(self, new_char):
        char_text = new_char if new_char else "None"
        if hasattr(self, 'active_char_label') and self.active_char_label:
            self.active_char_label.configure(text=char_text)

    def _handle_active_model_ui_update(self, new_model):
        model_text = new_model if new_model else "None"
        if hasattr(self, 'active_model_label') and self.active_model_label:
            self.active_model_label.configure(text=model_text)
        
        if hasattr(self, 'setup_active_model_label') and self.setup_active_model_label:
            self.setup_active_model_label.configure(text=f" (Active: {model_text})")
        
        # Update dropdown selection
        if new_model and hasattr(self, 'model_dropdown') and self.model_dropdown:
            self.model_dropdown.set(new_model)
    
    def _update_button_states(self, status: str):
        """Update button states based on Ollama status."""
        # Dashboard buttons (if they exist)
        if hasattr(self, 'start_btn'):
            self.start_btn.configure(state="disabled")
        if hasattr(self, 'stop_btn'):
            self.stop_btn.configure(state="disabled")
        if hasattr(self, 'restart_btn'):
            self.restart_btn.configure(state="disabled")
        if hasattr(self, 'delete_btn'):
            self.delete_btn.configure(state="disabled")

        if not hasattr(self, 'ai_service_btn') or not self.ai_service_btn:
             return

        ollama_installed = self.file_manager.ollama_exists()

        if status == "Not Installed":
            # If not installed, disable service button
            self.ai_service_btn.configure(
                state="disabled", 
                text="ON", 
                fg_color=UIStyles.SUCCESS_COLOR
            )
            self.ai_action_btn.configure(state="normal", text="Download Ollama")
        elif status == "Stopped":
            self.ai_service_btn.configure(
                state="normal", 
                text="ON", 
                fg_color=UIStyles.SUCCESS_COLOR,
                hover_color=UIStyles.PRIMARY_HOVER
            )
            self.ai_action_btn.configure(state="normal", text="Delete Ollama")
        elif status == "Running":
            self.ai_service_btn.configure(
                state="normal", 
                text="OFF", 
                fg_color=UIStyles.SECONDARY_COLOR, 
                hover_color=UIStyles.ERROR_COLOR
            )
            self.ai_action_btn.configure(state="normal", text="Delete Ollama")
        elif status == "Checking":
            self.ai_service_btn.configure(state="disabled", text="...")
            self.ai_action_btn.configure(state="disabled")
        elif status == "Downloading":
            self.ai_service_btn.configure(state="disabled", text="ON")
            self.ai_action_btn.configure(state="disabled", text="Downloading...")
        elif status == "Installing":
            self.ai_service_btn.configure(state="disabled", text="ON")
            self.ai_action_btn.configure(state="disabled", text="Installing...")
        elif status == "Starting":
            self.ai_service_btn.configure(state="disabled", text="...")
            self.ai_action_btn.configure(state="disabled", text="Delete Ollama")
        elif status == "Stopping":
            self.ai_service_btn.configure(state="disabled", text="...")
            self.ai_action_btn.configure(state="disabled", text="Delete Ollama")
        elif status == "Error":
            self.ai_service_btn.configure(
                state="normal" if ollama_installed else "disabled", 
                text="ON", 
                fg_color=UIStyles.SUCCESS_COLOR
            )
            if ollama_installed:
                self.ai_action_btn.configure(state="normal", text="Delete Ollama")
            else:
                self.ai_action_btn.configure(state="normal", text="Download Ollama")
        else: # e.g. "Checking"
            self.ai_service_btn.configure(state="disabled", text="Checking...")
            self.ai_action_btn.configure(state="disabled")

    def _refresh_model_list(self):
        """Fetch models from Ollama and update dropdown."""
        if not hasattr(self, 'model_dropdown') or not self.model_dropdown:
            return

        def update():
            try:
                models = self.ollama_manager.list_models()
                model_names = [m.get('name') for m in models if m.get('name')]
                
                if not model_names:
                    model_names = ["empty"]
                
                self.parent.after(0, lambda: self._update_dropdown_items(model_names))
            except Exception as e:
                print(f"Error refreshing model list: {e}")

        threading.Thread(target=update, daemon=True).start()
    
    def _show_partial_download_info(self, model_name: str):
        """Show information about partial download for a model."""
        try:
            progress = self.ollama_manager.get_model_download_progress(model_name)
            
            if progress['has_partial']:
                message = f"Model '{model_name}' has partial download:\n\n"
                message += f"Status: {progress['status']}\n"
                message += f"Downloaded: {self.format_bytes(progress['partial_size'])}\n"
                message += f"Can Resume: {'Yes' if progress['can_resume'] else 'No'}\n"
                message += f"Manifest Available: {'Yes' if progress['manifest_available'] else 'No'}\n\n"
                message += "The system will automatically clean up partial files before starting a new download."
                
                self.parent.after(0, lambda: tk.messagebox.showinfo("Partial Download Detected", message))
                
        except Exception as e:
            self.logger.error(f"Error showing partial download info: {e}")

    def _update_dropdown_items(self, model_names: list):
        """Update model dropdown items safely."""
        if hasattr(self, 'model_dropdown') and self.model_dropdown:
            self.model_dropdown.configure(values=model_names)

            # If current selection is not in list, set to first or empty
            current = self.model_dropdown.get()
            if current not in model_names and current != "empty":
                new_val = model_names[0] if model_names else "empty"
                self.model_dropdown.set(new_val)
                self._on_model_select(new_val)

            # Auto-select active model if it exists in the list
            active = self.status_manager.get_active_model()
            if active and active in model_names:
                self.model_dropdown.set(active)
                self._on_model_select(active)
            elif active and active not in model_names and active != current:
                # If active model doesn't exist, clear it
                self.status_manager.set_active_model(None)
    
    # Button click handlers
    def _on_service_toggle_click(self):
        """Handle start/stop service toggle."""
        status = self.status_manager.get_ollama_status()
        
        # Immediate visual feedback
        self.ai_service_btn.configure(state="disabled", text="...")
        
        if status == "Running":
            threading.Thread(target=self.ollama_manager.stop_service).start()
        else:
            threading.Thread(target=self.ollama_manager.start_service).start()

    def _on_action_click(self):
        """Handle download/delete action click."""
        if self.file_manager.ollama_exists():
            # Delete logic
            if messagebox.askyesno("Delete Ollama", "Are you sure you want to delete Ollama and all models?"):
                threading.Thread(target=self.ollama_manager.delete_ollama).start()
        else:
            # Download logic
            self._on_download_click()

    def _on_start_click(self):
        """Handle start button click (legacy/other)."""
        threading.Thread(target=self.ollama_manager.start_service).start()
    
    def _on_stop_click(self):
        """Handle stop button click (legacy/other)."""
        pass
    
    def _on_restart_click(self):
        """Handle restart button click (legacy/other)."""
        threading.Thread(target=self.ollama_manager.restart_service).start()
    
    def _on_download_click(self):
        """Handle download button click."""
        self.ollama_progress_frame.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_2XL))
        self.ollama_progress_bar.set(0)
        self.ollama_progress_label.configure(text="0%")
        
        # Disable button during download
        self.ai_action_btn.configure(state="disabled", text="Downloading...")
        
        def progress_callback(current, total, status_text):
            if total > 0:
                progress = current / total
                size_info = f"{self.format_bytes(current)} / {self.format_bytes(total)}"
                self.parent.after(0, lambda: self.ollama_progress_bar.set(progress))
                self.parent.after(0, lambda: self.ollama_progress_label.configure(text=f"{int(progress * 100)}% ({size_info})"))
        
        def ollama_status_callback(new_status, old_status):
            if new_status == "Installing":
                self.parent.after(0, lambda: self.ollama_progress_label.configure(text="Installing... (Extracting files)"))
                self.parent.after(0, lambda: self.ollama_progress_bar.set(1.0))
        
        # Temporary subscribe to status changes
        self.status_manager.add_callback('ollama_status', ollama_status_callback)

        def complete_callback(success, error_message=None):
            self.status_manager.remove_callback('ollama_status', ollama_status_callback)
            self.parent.after(2000, lambda: self.ollama_progress_frame.pack_forget())
            # Re-enable button is now handled by _on_ollama_status_change
            
            if not success and error_message:
                self.parent.after(0, lambda: tk.messagebox.showerror("Download Error", error_message))

        threading.Thread(target=self.ollama_manager.download_ollama, args=(progress_callback, complete_callback)).start()
    
    def _on_delete_click(self):
        """Handle delete button click (legacy/other)."""
        threading.Thread(target=self.ollama_manager.delete_ollama).start()
    
    def _on_download_model_click(self):
        """Handle model download button click with enhanced progress tracking."""
        if hasattr(self, 'model_input') and self.model_input:
            model_name = self.model_input.get().strip()
            if model_name:
                self.model_progress_frame.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_2XL))
                self.model_progress_bar.set(0)
                self.model_progress_label.configure(text="0%")
                self.model_progress_title.configure(text=f"Downloading {model_name}...")
                self.model_progress_details.configure(text="Status: Waiting for manifest...")

                def progress_callback(status, total, completed):
                    if total > 0 and completed >= 0:
                        progress = min(1.0, max(0.0, completed / total))
                        size_info = f"{self.format_bytes(completed)} / {self.format_bytes(total)}"
                        self.parent.after(0, lambda: self.model_progress_bar.set(progress))
                        self.parent.after(0, lambda: self.model_progress_label.configure(text=f"{int(progress * 100)}% ({size_info})"))
                        
                        # Update detailed status
                        if status == "pulling manifest":
                            self.parent.after(0, lambda: self.model_progress_details.configure(
                                text="Status: Pulling manifest from Ollama registry...",
                                text_color=UIStyles.TEXT_SECONDARY
                            ))
                        elif status == "downloading":
                            self.parent.after(0, lambda: self.model_progress_details.configure(
                                text=f"Status: Downloading model layers...",
                                text_color=UIStyles.TEXT_SECONDARY
                            ))
                        elif status == "writing manifest":
                            self.parent.after(0, lambda: self.model_progress_details.configure(
                                text="Status: Writing model manifest...",
                                text_color=UIStyles.TEXT_SECONDARY
                            ))
                        elif status == "verifying sha256 digest":
                            self.parent.after(0, lambda: self.model_progress_details.configure(
                                text="Status: Verifying download integrity...",
                                text_color=UIStyles.TEXT_SECONDARY
                            ))
                    else:
                        # Handle cases where total is 0 or completed is negative
                        self.parent.after(0, lambda: self.model_progress_label.configure(text=f"Status: {status}"))
                        self.parent.after(0, lambda: self.model_progress_details.configure(
                            text=f"Status: {status}",
                            text_color=UIStyles.TEXT_SECONDARY
                        ))

                def complete_callback(success, error_message=None):
                    self.parent.after(2000, lambda: self.model_progress_frame.pack_forget())
                    if success:
                        self.parent.after(0, self._refresh_model_list)
                        # Show success message with model info
                        self.parent.after(0, lambda: tk.messagebox.showinfo(
                            "Download Complete",
                            f"Model '{model_name}' downloaded successfully!"
                        ))
                    elif error_message:
                        self.parent.after(0, lambda: tk.messagebox.showerror("Download Error", error_message))

                threading.Thread(target=self.ollama_manager.download_model, args=(model_name, progress_callback, complete_callback)).start()
    
    def _on_model_select(self, model_name: str):
        """Handle model selection from dropdown."""
        # Restore normal text color if not empty
        if model_name != "empty":
            self.model_dropdown.configure(text_color=UIStyles.TEXT_PRIMARY)
        else:
            self.model_dropdown.configure(text_color=UIStyles.TEXT_SECONDARY)

        if hasattr(self, 'activate_model_btn') and self.activate_model_btn:
            self.activate_model_btn.configure(state="normal" if model_name != "empty" else "disabled")
        if hasattr(self, 'delete_model_btn') and self.delete_model_btn:
            self.delete_model_btn.configure(
                state="normal" if model_name != "empty" else "disabled",
                fg_color=UIStyles.SECONDARY_COLOR,
                hover_color=UIStyles.ERROR_COLOR
            )
    
    def _on_activate_model_click(self):
        """Handle activate model button click."""
        if hasattr(self, 'model_dropdown') and self.model_dropdown:
            model_name = self.model_dropdown.get()
            if model_name and model_name != "empty":
                success = self.ollama_manager.activate_model(model_name)
                if success:
                     messagebox.showinfo("Model Activated", f"Model '{model_name}' is now active.")
                else:
                     messagebox.showerror("Activation Error", f"Failed to activate model '{model_name}'.")
    
    def _on_delete_model_click(self):
        """Handle delete model button click."""
        if hasattr(self, 'model_dropdown') and self.model_dropdown:
            model_name = self.model_dropdown.get()
            if model_name and model_name != "empty":
                if messagebox.askyesno("Delete Model", f"Are you sure you want to delete model '{model_name}'?"):
                    def delete_task():
                        success = self.ollama_manager.delete_model(model_name)
                        if success:
                            self.parent.after(0, lambda: messagebox.showinfo("Success", f"Model '{model_name}' deleted."))
                            self._refresh_model_list()
                        else:
                            self.parent.after(0, lambda: messagebox.showerror("Error", f"Failed to delete model '{model_name}'."))
                    
                    threading.Thread(target=delete_task, daemon=True).start()

    def _update_gpu_info(self):
        """Update GPU information display."""
        try:
            gpu_info = self.ollama_manager.get_gpu_info()

            if gpu_info.get("gpu_detected", False):
                gpu_name = gpu_info.get("gpu_name", "Unknown GPU")
                gpu_memory = gpu_info.get("gpu_memory_total", "Unknown")
                text = f"GPU: {gpu_name} ({gpu_memory})"
                color = UIStyles.SUCCESS_COLOR  # Green for detected GPU
            else:
                text = gpu_info.get("message", "GPU not detected")
                color = UIStyles.TEXT_TERTIARY  # Muted color for no GPU

            self._update_gpu_label(text, color)
        except Exception as e:
            self.logger.error(f"Error updating GPU info: {e}")
            self._update_gpu_label("Error reading GPU info", UIStyles.ERROR_COLOR)

    def _update_gpu_label(self, text: str, color: str):
        """Update GPU label safely."""
        if hasattr(self, 'gpu_info_label') and self.gpu_info_label:
            self.gpu_info_label.configure(text=text, text_color=color)

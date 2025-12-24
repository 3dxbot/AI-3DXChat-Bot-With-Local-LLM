"""
Ollama UI Module.

This module provides UI components for Ollama integration.

Classes:
    OllamaUI: Class for Ollama-specific UI components.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Optional, Callable
import threading
import time

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
        
        # UI components
        self.status_label = None
        self.status_indicator = None
        self.active_model_label = None
        self.download_progress = None
        self.download_status = None
        self.model_dropdown = None
        
        # Bind status callbacks
        self.status_manager.add_callback('ollama_status', self._on_ollama_status_change)
        self.status_manager.add_callback('active_model', self._on_active_model_change)
    
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
        
        self.ai_download_btn = UIStyles.create_button(
            row1,
            text="Download Ollama",
            command=self._on_download_click,
            width=160,
            height=40
        )
        self.ai_download_btn.pack(side='left', padx=(0, UIStyles.SPACE_MD))
        
        self.ai_start_btn = UIStyles.create_button(
            row1,
            text="Start Service",
            command=self._on_start_click,
            state="disabled",
            width=160,
            height=40
        )
        self.ai_start_btn.pack(side='left', padx=(0, UIStyles.SPACE_MD))
        
        # Row 2
        row2 = ctk.CTkFrame(action_frame, fg_color="transparent")
        row2.pack(fill='x')
        
        self.ai_stop_btn = UIStyles.create_secondary_button(
            row2,
            text="Stop Service",
            command=self._on_stop_click,
            state="disabled",
            width=160,
            height=40
        )
        self.ai_stop_btn.pack(side='left', padx=(0, UIStyles.SPACE_MD))
        
        self.ai_restart_btn = UIStyles.create_secondary_button(
            row2,
            text="Restart Service",
            command=self._on_restart_click,
            state="disabled",
            width=160,
            height=40
        )
        self.ai_restart_btn.pack(side='left', padx=(0, UIStyles.SPACE_MD))
        
        self.ai_delete_btn = UIStyles.create_secondary_button(
            row2,
            text="Delete Ollama",
            command=self._on_delete_click,
            state="disabled",
            width=160,
            height=40
        )
        self.ai_delete_btn.pack(side='left')
        
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
        
        self.model_input = UIStyles.create_input_field(
            download_section,
            placeholder_text="Enter model name from Ollama repository..."
        )
        self.model_input.pack(fill='x', pady=(0, UIStyles.SPACE_MD))
        
        self.download_model_btn = UIStyles.create_button(
            download_section,
            text="Download Model",
            command=self._on_download_model_click,
            width=160,
            height=40
        )
        self.download_model_btn.pack(anchor='e')
        
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
            width=300,
            height=36
        )
        self.model_dropdown.pack(side='left', padx=(0, UIStyles.SPACE_MD))
        
        self.activate_model_btn = UIStyles.create_button(
            control_frame,
            text="Activate Model",
            command=self._on_activate_model_click,
            state="disabled",
            width=140,
            height=36
        )
        self.activate_model_btn.pack(side='left', padx=(0, UIStyles.SPACE_MD))
        
        self.delete_model_btn = UIStyles.create_secondary_button(
            control_frame,
            text="Delete Model",
            command=self._on_delete_model_click,
            state="disabled",
            width=140,
            height=36
        )
        self.delete_model_btn.pack(side='left')
        
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
        if hasattr(self, 'status_label') and self.status_label:
            self.status_label.configure(text=new_status)
        if hasattr(self, 'ai_status_label') and self.ai_status_label:
            self.ai_status_label.configure(text=f"Status: {new_status}")
        
        # Update status indicator color
        color_map = {
            "Checking": "#f59e0b",
            "Not Installed": "#ef4444",
            "Starting": "#f59e0b",
            "Running": "#10b981",
            "Error": "#ef4444"
        }
        
        color = color_map.get(new_status, "#f59e0b")
        if hasattr(self, 'status_indicator') and self.status_indicator:
            self.status_indicator.configure(text_color=color)
        
        # Update button states
        self._update_button_states(new_status)
    
    def _on_active_model_change(self, new_model: Optional[str], old_model: Optional[str]):
        """Handle active model changes."""
        model_text = new_model if new_model else "None"
        if hasattr(self, 'active_model_label') and self.active_model_label:
            self.active_model_label.configure(text=model_text)
        
        # Update dropdown selection
        if new_model and hasattr(self, 'model_dropdown') and self.model_dropdown:
            self.model_dropdown.set(new_model)
    
    def _update_button_states(self, status: str):
        """Update button states based on Ollama status."""
        if status == "Not Installed":
            # Dashboard buttons (if they exist)
            if hasattr(self, 'start_btn'):
                self.start_btn.configure(state="disabled")
            if hasattr(self, 'stop_btn'):
                self.stop_btn.configure(state="disabled")
            if hasattr(self, 'restart_btn'):
                self.restart_btn.configure(state="disabled")
            if hasattr(self, 'delete_btn'):
                self.delete_btn.configure(state="disabled")

            # AI Setup buttons
            if hasattr(self, 'ai_start_btn'):
                self.ai_start_btn.configure(state="disabled")
            if hasattr(self, 'ai_stop_btn'):
                self.ai_stop_btn.configure(state="disabled")
            if hasattr(self, 'ai_restart_btn'):
                self.ai_restart_btn.configure(state="disabled")
            if hasattr(self, 'ai_delete_btn'):
                self.ai_delete_btn.configure(state="disabled")
        elif status == "Running":
            # Dashboard buttons (if they exist)
            if hasattr(self, 'start_btn'):
                self.start_btn.configure(state="disabled")
            if hasattr(self, 'stop_btn'):
                self.stop_btn.configure(state="normal")
            if hasattr(self, 'restart_btn'):
                self.restart_btn.configure(state="normal")
            if hasattr(self, 'delete_btn'):
                self.delete_btn.configure(state="normal")

            # AI Setup buttons
            if hasattr(self, 'ai_start_btn'):
                self.ai_start_btn.configure(state="disabled")
            if hasattr(self, 'ai_stop_btn'):
                self.ai_stop_btn.configure(state="normal")
            if hasattr(self, 'ai_restart_btn'):
                self.ai_restart_btn.configure(state="normal")
            if hasattr(self, 'ai_delete_btn'):
                self.ai_delete_btn.configure(state="normal")
        elif status == "Starting":
            # Dashboard buttons (if they exist)
            if hasattr(self, 'start_btn'):
                self.start_btn.configure(state="disabled")
            if hasattr(self, 'stop_btn'):
                self.stop_btn.configure(state="disabled")
            if hasattr(self, 'restart_btn'):
                self.restart_btn.configure(state="disabled")
            if hasattr(self, 'delete_btn'):
                self.delete_btn.configure(state="disabled")

            # AI Setup buttons
            if hasattr(self, 'ai_start_btn'):
                self.ai_start_btn.configure(state="disabled")
            if hasattr(self, 'ai_stop_btn'):
                self.ai_stop_btn.configure(state="disabled")
            if hasattr(self, 'ai_restart_btn'):
                self.ai_restart_btn.configure(state="disabled")
            if hasattr(self, 'ai_delete_btn'):
                self.ai_delete_btn.configure(state="disabled")
    
    # Button click handlers
    def _on_start_click(self):
        """Handle start button click."""
        threading.Thread(target=self.ollama_manager.start_service).start()
    
    def _on_stop_click(self):
        """Handle stop button click."""
        threading.Thread(target=self.ollama_manager.stop_service).start()
    
    def _on_restart_click(self):
        """Handle restart button click."""
        threading.Thread(target=self.ollama_manager.restart_service).start()
    
    def _on_download_click(self):
        """Handle download button click."""
        threading.Thread(target=self.ollama_manager.download_ollama).start()
    
    def _on_delete_click(self):
        """Handle delete button click."""
        threading.Thread(target=self.ollama_manager.delete_ollama).start()
    
    def _on_download_model_click(self):
        """Handle model download button click."""
        if hasattr(self, 'model_input') and self.model_input:
            model_name = self.model_input.get().strip()
            if model_name:
                threading.Thread(target=self.ollama_manager.download_model, args=(model_name,)).start()
    
    def _on_model_select(self, model_name: str):
        """Handle model selection from dropdown."""
        if hasattr(self, 'activate_model_btn') and self.activate_model_btn:
            self.activate_model_btn.configure(state="normal")
        if hasattr(self, 'delete_model_btn') and self.delete_model_btn:
            self.delete_model_btn.configure(state="normal")
    
    def _on_activate_model_click(self):
        """Handle activate model button click."""
        if hasattr(self, 'model_dropdown') and self.model_dropdown:
            model_name = self.model_dropdown.get()
            if model_name:
                self.ollama_manager.activate_model(model_name)
    
    def _on_delete_model_click(self):
        """Handle delete model button click."""
        if hasattr(self, 'model_dropdown') and self.model_dropdown:
            model_name = self.model_dropdown.get()
            if model_name:
                threading.Thread(target=self.ollama_manager.delete_model, args=(model_name,)).start()
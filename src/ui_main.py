"""
UI Main Module.

This module provides the ChatBotUI class, which serves as the main user interface
for the chatbot application. It combines multiple mixins to provide comprehensive
UI functionality including initialization, event handling, hotkeys, and settings.

Classes:
    ChatBotUI: Main UI class combining all UI mixins.
"""

import tkinter as tk
import customtkinter as ctk
import keyboard
from .bot import ChatBot
from .gemini_manager import GeminiManager
from .status_manager import StatusManager
from .download_manager import DownloadManager
from .file_manager import FileManager
from .ui_gemini import GeminiUI
from .ui_character import UICharacterMixin
from .ui_chat import UIChatMixin
import time
import traceback
import json
import os
from .config import HOTKEY_PHRASES_FILE
from .ui_styles import UIStyles
from .ui_utils import UIUtilsMixin
from .ui_handlers import UIHandlersMixin
from .ui_windows import UIWindowsMixin
from .ui_init import UIInitMixin
from .ui_hotkeys import HotkeyMixin as UIHotkeysMixin # Renamed for consistency with snippet
from .ui_settings import SettingsMixin
try:
    import win32api
except ImportError:
    win32api = None


class ChatBotUI(UIUtilsMixin, UIHandlersMixin, UIWindowsMixin, UIInitMixin, UIHotkeysMixin, UICharacterMixin, UIChatMixin, SettingsMixin):
    """
    Main UI class for the ChatBot application with modern design.

    This class combines multiple mixins to provide a complete user interface
    for the chatbot application, including UI initialization, event handling,
    hotkey management, and settings management.

    Attributes:
        root: Main Tkinter root window.
        bot: ChatBot instance.
        view_mode: UI view mode (always expanded).
        hotkey_locks: Dictionary for hotkey debouncing.
        is_processing: Dictionary for tracking processing states.
        autonomous_var: Boolean variable for autonomous mode.
        auto_lang_var: Boolean variable for auto language switching.
        hiwaifu_language_var: String variable for HiWaifu language.
        manual_input_var: String variable for manual input field.

    Methods:
        __init__: Initialize the UI.
        on_close: Handle window close event.
        _check_keyboard_layout: Check and warn about keyboard layout.
    """

    def __init__(self, root):
        """
        Initialize the ChatBot UI.

        Sets up the main window, initializes UI components, creates the bot instance,
        loads settings, checks keyboard layout, and sets up hotkeys.

        Args:
            root: Tkinter root window.
        """
        self.root = root
        self.root.title("ChatBot [Not Running]")
        self.is_busy = False
        self.bot = None  # Initialize later
        self.hwnd = None
        self.last_toggle_time = 0
        self.hotkey_locks = {}
        self.is_processing = {}
        self.global_prompt_var = None
        self.autonomous_var = ctk.BooleanVar(value=False)
        self.hiwaifu_language_var = tk.StringVar(value="en")
        self.use_translation_var = ctk.BooleanVar(value=False)
        self.hooker_enabled_var = ctk.BooleanVar(value=False)
        self.show_zones_var = ctk.BooleanVar(value=False)
        self.view_mode = 0  # Always expanded view
        self.settings_mode = False  # Track if in settings view
        self.current_view = 'dashboard'  # Track current navigation view
        self.current_status = "Not Running"
        self.scanning_status = ""
        self._dots_count = 0
        self.icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'logo.ico')
        
        # Gemini integration
        self.file_manager = FileManager()
        self.status_manager = StatusManager()
        self.download_manager = DownloadManager() # Keep for file ops if needed
        self.gemini_manager = GeminiManager(self.status_manager)
        self.gemini_ui = GeminiUI(self.root, self.gemini_manager, self.status_manager)


        # Configure modern styles
        UIStyles.configure_styles()
        UIStyles.apply_to_root(self.root)

        self.setup_ui()
        self.bot = ChatBot(self)  # Initialize bot after UI setup
        self.load_settings()  # Bot is now available
        # Sync UI variables with bot settings
        self.use_translation_var.set(getattr(self.bot, 'use_translation_layer', False))
        self.autonomous_var.set(getattr(self.bot, 'autonomous_mode', False))
        self.hooker_enabled_var.set(getattr(self.bot, 'hooker_mod_enabled', False))
        self.update_switch_colors()

        # Initialize system
        self.status_manager.start_monitoring()
        
        # Check Gemini connection in background
        import threading
        threading.Thread(target=self.gemini_manager.check_connection, daemon=True).start()
        
        # Add callback for status changes to update Start button
        self.status_manager.add_callback('ollama_status', self._on_status_changed) # Reused callback name for simplicity
        # Add callback for active model change to save it
        self.status_manager.add_callback('active_model', self._on_active_model_changed_persistence)

        # Check keyboard layout and warn if not English
        self._check_keyboard_layout()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.setup_hotkeys()
        self.root.attributes("-topmost", True)
        self.hwnd = self.root.winfo_id()
        if self.hwnd == 0:
            self.root.update_idletasks()
            self.hwnd = self.root.winfo_id()


    def on_close(self):
        """
        Handle window close event.

        Unhooks all hotkeys, stops the bot if running, and destroys the window.
        """
        keyboard.unhook_all()
        if self.bot and self.bot.bot_running:
            self.bot.stop_bot(wait=False)
        self.root.destroy()

    def _check_keyboard_layout(self):
        """
        Check current keyboard layout and warn if not English.

        Uses win32api to detect the current keyboard layout and shows a warning
        if it's not English, as text insertion may not work correctly otherwise.
        """
        if win32api is None:
            self.log_message("Failed to import win32api for keyboard layout check.", internal=True)
            return

        try:
            current_layout = win32api.GetKeyboardLayout(0) & 0xFFFF
            english_layout = 0x0409  # English (United States)

            if current_layout != english_layout:
                message = (
                    "Warning: Current keyboard layout is not English.\n\n"
                    "Text insertion into HiWaifu may not work correctly with non-English layout.\n"
                    "It is recommended to switch to English (EN) layout for proper bot operation.\n\n"
                    "You can continue, but text insertion functionality may be limited."
                )
                tk.messagebox.showwarning("Keyboard Layout Warning", message)
                self.log_message("Non-English keyboard layout detected. Text insertion may work incorrectly.", internal=True)
            else:
                self.log_message("Keyboard layout is English - text insertion should work correctly.", internal=True)
        except Exception as e:
            self.log_message(f"Error checking keyboard layout: {e}", internal=True)
    
    def _on_status_changed(self, new_status, old_status):
        """
        Handle API status changes.
        """
        if hasattr(self, 'start_button'):
            if new_status == "Connected":
                self.root.after(0, lambda: self.start_button.configure(
                    state="normal", 
                    text="Disconnect",
                    fg_color=UIStyles.SECONDARY_COLOR, 
                    hover_color=UIStyles.ERROR_COLOR
                ))
                # Automatically start bot when Connected
                if self.bot and not self.bot.bot_running:
                    self.bot.start_bot()
            else:
                self.root.after(0, lambda: self.start_button.configure(
                    state="normal", 
                    text="Wait Connection..." if new_status == "Checking..." else "Connect",
                    fg_color=UIStyles.SUCCESS_COLOR, 
                    hover_color="#059669"
                ))
                # Stop bot if connection lost
                if self.bot and self.bot.bot_running:
                    self.bot.stop_bot()

    def _on_active_model_changed_persistence(self, new_model, old_model):
        """Handle active model changes for persistence."""
        if self.bot:
            self.bot.active_model = new_model
            self.bot.save_settings()

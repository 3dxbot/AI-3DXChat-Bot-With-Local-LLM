"""
UI Hotkeys Module.

This module provides the HotkeyMixin class, which handles global hotkey
registration and management for the chatbot application. It includes
functionality for setup, locking mechanisms, and hotkey event handling.

Hotkeys:
- F2: Start/pause/resume bot or handle setup
- F3: Toggle window visibility (minimize/restore)
- F4: Clear chat history
- F5-F12: Initiate chat with hotkey phrases
- Ctrl+E: Change language to English
- Ctrl+R: Change language to Russian
- Ctrl+F: Change language to French
- Ctrl+S: Change language to Spanish

Classes:
    HotkeyMixin: Mixin class for hotkey management.
"""

import time
import traceback
import keyboard


class HotkeyMixin:
    """
    Mixin class for hotkey management and related functionality.

    This mixin provides methods for setting up global hotkeys, managing
    key locks to prevent rapid triggering, and handling hotkey events.
    It ensures proper debouncing and processing locks for UI responsiveness.

    Attributes:
        hotkey_locks (dict): Dictionary tracking key lock timestamps.
        is_processing (dict): Dictionary tracking keys currently being processed.

    Methods:
        setup_hotkeys: Set up all global hotkeys.
        _check_lock: Check if a key is locked or processing.
        _unlock: Unlock a key after processing.
        on_f2_press: Handle F2 key press.
        on_hotkey_initiate_chat: Handle hotkey chat initiation.
    """

    def setup_hotkeys(self):
        """
        Set up all global hotkeys.

        Registers hotkeys for bot control, language switching, chat initiation,
        and window management. Includes debouncing and error handling.
        """
        try:
            keyboard.add_hotkey('f2', self.on_f2_press)
            keyboard.add_hotkey('f3', self.toggle_window_visibility)
            keyboard.add_hotkey('f4', self.on_clear_chat_click)
            keyboard.add_hotkey('ctrl+e', lambda: self.on_change_language_click('en'))
            keyboard.add_hotkey('ctrl+r', lambda: self.on_change_language_click('ru'))
            keyboard.add_hotkey('ctrl+f', lambda: self.on_change_language_click('fr'))
            keyboard.add_hotkey('ctrl+s', lambda: self.on_change_language_click('es'))

            for i in range(5, 13):
                key = f'f{i}'
                keyboard.add_hotkey(key, lambda k=key: self.on_hotkey_initiate_chat(k.upper()))

            self.log_message("Global hotkeys (F2-F4, F5-F12, Ctrl+E/R/F/S) active.", internal=True)
        except Exception:
            self.log_message(f"Error setting up hotkeys: {traceback.format_exc()}", internal=True)

    def _check_lock(self, key, debounce_time=0.5, full_lock=False):
        """
        Check if a key is locked or processing.

        Prevents rapid key presses and ensures proper sequencing of operations.

        Args:
            key (str): The key to check.
            debounce_time (float): Minimum time between key presses.
            full_lock (bool): Whether to check processing status.

        Returns:
            bool: True if key is locked, False otherwise.
        """
        current_time = time.time()
        if key in self.hotkey_locks and current_time - self.hotkey_locks[key] < debounce_time:
            return True
        if full_lock and key in self.is_processing and self.is_processing[key]:
            return True
        self.hotkey_locks[key] = current_time
        if full_lock:
            self.is_processing[key] = True
        return False

    def _unlock(self, key):
        """
        Unlock a key after processing.

        Args:
            key (str): The key to unlock.
        """
        if key in self.is_processing:
            self.is_processing[key] = False

    def on_f2_press(self):
        """
        Handle F2 key press.

        Controls bot start/pause/resume or handles setup steps.
        """
        if self._check_lock('f2', debounce_time=0.2):
            return
        if self.bot.setup_step > 0:
            self.bot._handle_setup_key_press()
            return
        if self.bot.bot_running:
            if self.bot.scanning_active:
                self.bot.pause_bot()
            else:
                self.bot.resume_bot()
        self._unlock('f2')

    def on_hotkey_initiate_chat(self, key):
        """
        Handle hotkey chat initiation.

        Initiates chat using the hotkey's associated phrase.

        Args:
            key (str): The hotkey that was pressed.
        """
        if self._check_lock(key, full_lock=True):
            return
        try:
            if self.bot:
                self.bot.initiate_chat_from_hotkey(key)
        finally:
            self._unlock(key)
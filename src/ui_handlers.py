"""
UI Handlers Module.

This module provides the UIHandlersMixin class, which contains event handlers
for the chatbot application's graphical user interface. It manages button clicks,
language changes, overlay toggles, and other UI interactions.

Classes:
    UIHandlersMixin: Mixin class for UI event handling.
"""

import tkinter as tk
import traceback


class UIHandlersMixin:
    """
    Mixin class for UI event handlers.

    This mixin provides methods to handle various UI events such as button clicks,
    language changes, overlay toggles, and manual message sending. It ensures
    proper interaction between the UI and the bot backend.

    Methods:
        on_start_click: Handle start button click.
        on_pause_click: Handle pause/resume button click.
        on_stop_click: Handle stop button click.
        update_buttons_state: Update button states based on bot status.
        on_set_hiwaifu_language: Handle HiWaifu language change.
        on_clear_chat_click: Handle clear chat button click.
        on_close_partnership_click: Handle close partnership button click.
        on_change_language_click: Handle language change.
        on_manual_send_click: Handle manual send button click.
        on_toggle_overlay: Handle overlay toggle.
        on_autonomous_toggle: Handle autonomous mode toggle.
        toggle_window_visibility: Toggle window visibility.
        toggle_nicks_collapse: Toggle nick lists section visibility.
        toggle_logs_collapse: Toggle logs section visibility.
    """

    def on_start_click(self):
        """
        Handle start button click.

        Starts the bot if it exists and is not already running.
        """
        if hasattr(self, 'ollama_manager') and hasattr(self, 'status_manager'):
            status = self.status_manager.get_ollama_status()
            if status == "Running":
                import threading
                threading.Thread(target=self.ollama_manager.stop_service, daemon=True).start()
            else:
                import threading
                threading.Thread(target=self.ollama_manager.start_service, daemon=True).start()

    def on_pause_click(self):
        """
        Handle pause/resume button click.

        Pauses the bot if running and scanning, or resumes if paused.
        """
        if self.bot.bot_running and not self.bot.scanning_active:
            self.bot.resume_bot()
        else:
            self.bot.pause_bot()

    def on_stop_click(self):
        """
        Legacy handler for stop button (removed).
        """
        pass

    def update_buttons_state(self, running, paused=False):
        """
        Update button states based on bot status.

        Configures the enabled/disabled state and colors of UI buttons
        based on whether the bot is running and paused.

        Args:
            running (bool): Whether the bot is currently running.
            paused (bool): Whether the bot is currently paused.
        """
        from .ui_styles import UIStyles
        
        # Start button - Success green when available
        # Start button - Handled via Ollama status callback (_on_ollama_status_changed in ui_main.py)
        # We comment out the standard state management to let the callback handle it exclusively
        # self.start_button.configure(
        #    state="disabled" if running else "normal", 
        #    fg_color=UIStyles.DISABLED_COLOR if running else UIStyles.SUCCESS_COLOR
        # )
        
        # Stop button REMOVED - functionality merged with Ollama control
        # self.stop_button.configure(
        #    state="normal" if running else "disabled", 
        #    fg_color=UIStyles.ERROR_COLOR if running else UIStyles.DISABLED_COLOR
        # )
        
        # Action buttons - Primary blue when running
        btn_state = "normal" if running else "disabled"
        btn_color = UIStyles.PRIMARY_COLOR if running else UIStyles.DISABLED_COLOR
        
        self.clear_chat_button.configure(state=btn_state, fg_color=btn_color)
        self.close_partnership_button.configure(state=btn_state, fg_color=btn_color)
        
        if running:
            # Pause button - Warning amber when running
            self.pause_button.configure(state="normal", fg_color=UIStyles.WARNING_COLOR)
            self.pause_button.configure(text="Pause Scan" if not paused else "Start Scan")
        else:
            self.pause_button.configure(state="disabled", fg_color=UIStyles.DISABLED_COLOR, text="Start Scan")

    def on_set_hiwaifu_language(self):
        """
        Handle HiWaifu language change.

        Gets the selected language from the UI variable and triggers language change.
        """
        language = self.hiwaifu_language_var.get()
        self.on_change_language_click(language)

    def on_clear_chat_click(self):
        """
        Handle clear chat button click.

        Clears bot memory, LLM history and UI chat history.
        """
        if self.bot:
            import tkinter.messagebox as messagebox
            if messagebox.askyesno("Clear Chat", "Are you sure you want to clear the chat history and memory?"):
                self.bot.clear_chat_history()

    def on_close_partnership_click(self):
        """
        Handle close partnership button click.

        Closes the active partnership if one exists, with proper locking and async handling.
        """
        key = 'close_partnership'
        if self._check_lock(key, full_lock=True):
            return
        try:
            if self.bot:
                if self.bot.partnership_active:
                    import asyncio
                    if self.bot.loop:
                        asyncio.run_coroutine_threadsafe(self.bot._close_partnership(), self.bot.loop)
                    else:
                        self.bot.log("Bot not running, cannot close partnership.", internal=True)
                else:
                    self.bot.log("Partnership not active, nothing to close.", internal=True)
        finally:
            self._unlock(key)

    def on_change_language_click(self, language):
        """
        Handle language change.

        Changes the bot's language and updates UI elements accordingly.

        Args:
            language (str): The language code to change to.
        """
        key = f'change_{language}'
        if self._check_lock(key, full_lock=True):
            return
        try:
            if self.bot:
                self.bot.change_language(language)
                self.hiwaifu_language_var.set(language)
        finally:
            self._unlock(key)

    def on_manual_send_click(self):
        """
        Legacy handler for manual send (removed).
        """
        pass

    def on_toggle_overlay(self):
        """
        Handle overlay toggle.

        Toggles the overlay display on/off and syncs UI state.
        """
        if self.bot:
            self.bot.toggle_overlay()
            # Sync variable
            self.show_zones_var.set(self.bot.show_overlay)
            self.update_switch_colors()

            # Refresh game sync view if open to update button text
            if self.current_view == 'game_sync' and hasattr(self, '_populate_game_sync_view'):
                self.show_game_sync_view()

    def on_autonomous_toggle(self):
        """
        Handle autonomous mode toggle.

        Enables or disables autonomous mode and saves the setting.
        """
        if self.bot:
            self.bot.autonomous_mode = self.autonomous_var.get()
            self.bot.save_settings()
            self.bot.log(f"Autonomous mode {'enabled' if self.bot.autonomous_mode else 'disabled'}.", internal=True)

        # Update switch colors
        from .ui_styles import UIStyles
        if self.autonomous_var.get():
            self.auto_mode_switch.configure(fg_color=UIStyles.HOVER_COLOR, progress_color=UIStyles.HOVER_COLOR)
        else:
            self.auto_mode_switch.configure(fg_color=UIStyles.DISABLED_COLOR, progress_color=UIStyles.DISABLED_COLOR)


    def toggle_window_visibility(self):
        """
        Toggle window visibility.

        Minimizes or restores the application window.
        """
        if self.root.state() == 'iconic':
            self.root.deiconify()
            self.root.update_idletasks()  # Force immediate redraw
        else:
            self.root.iconify()

    def toggle_nicks_collapse(self):
        """Toggle nick lists section visibility."""
        if not hasattr(self, 'nicks_content_frame'):
            return
            
        if self.nicks_collapsed:
            self.nicks_content_frame.grid()
            self.nicks_collapse_btn.configure(text="▲")
            self.nicks_collapsed = False
        else:
            self.nicks_content_frame.grid_remove()
            self.nicks_collapse_btn.configure(text="▼")
            self.nicks_collapsed = True

    def toggle_logs_collapse(self):
        """Toggle logs section visibility."""
        if not hasattr(self, 'logs_content_frame'):
            return
            
        if self.logs_collapsed:
            self.logs_content_frame.grid()
            self.logs_collapse_btn.configure(text="▲")
            self.logs_collapsed = False
        else:
            self.logs_content_frame.grid_remove()
            self.logs_collapse_btn.configure(text="▼")
            self.logs_collapsed = True

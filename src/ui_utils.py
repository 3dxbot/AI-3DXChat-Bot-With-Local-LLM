"""
UI Utils Module.

This module provides the UIUtilsMixin class, which contains utility methods
for UI operations including logging, nick list management, status updates,
and temporary message windows.

Classes:
    UIUtilsMixin: Mixin class for UI utility operations.
"""

import tkinter as tk
import customtkinter as ctk
import time
from .ui_styles import UIStyles


class UIUtilsMixin:
    """
    Utility methods for UI operations.

    This mixin provides helper methods for logging messages, managing nick lists,
    updating UI status, and displaying temporary messages. It handles the
    interaction between the bot backend and the UI frontend.

    Methods:
        log_message: Log a message to the UI.
        clear_log_history: Clear the log history.
        add_nick: Add a nick to a list.
        remove_nick: Remove a nick from a list.
        load_lists: Load and display nick lists.
        update_suggested_nicks: Update suggested nicks list.
        add_nick_from_suggested: Add nick from suggested to target list.
        update_status: Update window title status.
        update_scanning_status: Update scanning status with animation.
        _perform_clear_status: Clear status after delay.
        _animate_scanning_dots: Animate dots for scanning status.
        _update_title_with_scanning: Update title with scanning info.
        show_temp_message: Show temporary message window.
    """

    def log_message(self, message, internal=False):
        """
        Log a message to the UI log text area.

        Adds a timestamped message to the log display with optional internal prefix.

        Args:
            message (str): Message to log.
            internal (bool): Whether this is an internal system message.
        """
        if not hasattr(self, 'log_text') or not self.log_text:
            return  # UI not ready yet
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.configure(state=tk.NORMAL)
        prefix = "[i] " if internal else ""
        self.log_text.insert(tk.END, f"[{timestamp}] {prefix}{message}\n")
        self.log_text.yview(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def clear_log_history(self):
        """
        Clear the log history.

        Removes all text from the log display area.
        """
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete('1.0', tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def add_nick(self, nick, list_type):
        """
        Add a nick to the specified list.

        Adds a nickname to either the ignore or target list and refreshes the UI.

        Args:
            nick (str): Nickname to add.
            list_type (str): Type of list ("ignore" or "target").
        """
        if not nick:
            return
        self.bot.add_nick(nick, list_type)
        self.load_lists()

    def remove_nick(self, listbox, list_type):
        """
        Remove a nick from the specified listbox.

        Removes the selected nickname from the listbox and underlying bot data.

        Args:
            listbox: Tkinter Listbox widget.
            list_type (str): Type of list ("ignore" or "target").
        """
        selected_index = listbox.curselection()
        if not selected_index:
            return
        nick = listbox.get(selected_index[0])
        self.bot.remove_nick(nick, list_type)
        self.load_lists()

    def load_lists(self):
        """
        Load and display nick lists.

        Populates the ignore, target, and suggested nick listboxes with
        current data from the bot, sorted alphabetically.
        """
        self.ignore_listbox.delete(0, tk.END)
        for nick in sorted(list(self.bot.ignore_nicks)):
            self.ignore_listbox.insert(tk.END, nick)
        self.target_listbox.delete(0, tk.END)
        for nick in sorted(list(self.bot.target_nicks)):
            self.target_listbox.insert(tk.END, nick)
        self.update_suggested_nicks(list(self.bot.suggested_nicks))

    def update_suggested_nicks(self, nicks):
        """
        Update the suggested nicks listbox.

        Refreshes the suggested nicks display with the provided list.

        Args:
            nicks (list): List of suggested nicknames.
        """
        self.suggested_listbox.delete(0, tk.END)
        for nick in sorted(nicks):
            self.suggested_listbox.insert(tk.END, nick)

    def add_nick_from_suggested(self, list_type):
        """
        Add a nick from suggested list to specified list.

        Moves a selected nickname from the suggested list to either
        ignore or target list.

        Args:
            list_type (str): Type of list to add to ("ignore" or "target").
        """
        selected_index = self.suggested_listbox.curselection()
        if not selected_index:
            return
        nick = self.suggested_listbox.get(selected_index[0])
        self.add_nick(nick, list_type)
        self.log_message(f"Nick '{nick}' added to '{'ignore' if list_type == 'ignore' else 'tracked'}' list.",
                         internal=True)
        if self.bot and nick in self.bot.suggested_nicks:
            self.bot.suggested_nicks.remove(nick)
        self.update_suggested_nicks(list(self.bot.suggested_nicks))

    def update_status(self, status):
        """
        Update the window title with status and reset scanning status.

        Sets the main status and clears any ongoing scanning animation.

        Args:
            status (str): New status to display in title.
        """
        self.current_status = status
        # Reset scanning status and cancel any ongoing blink animation
        self.update_scanning_status("")
        self._update_title_with_scanning()

    def update_scanning_status(self, scanning_type):
        """
        Update scanning status with dot progression animation.

        Manages the scanning status display with animated dots. Uses debouncing
        to prevent flickering when status changes rapidly.

        Args:
            scanning_type (str): Type of scanning activity or empty string to clear.
        """
        # Cancel pending clear if any
        if hasattr(self, "_clear_job") and self._clear_job:
            try:
                self.root.after_cancel(self._clear_job)
            except Exception:
                pass
            self._clear_job = None

        if scanning_type:
            # If same status is requested, ignore to keep animation smooth
            if scanning_type == self.scanning_status:
                return

            # New status requested: stop old animation
            if hasattr(self, "_blink_job") and self._blink_job:
                try:
                    self.root.after_cancel(self._blink_job)
                except Exception:
                    pass
                self._blink_job = None

            self.scanning_status = scanning_type
            self._dots_count = 0
            self._update_title_with_scanning()
            # Schedule first animation step
            self._blink_job = self.root.after(500, self._animate_scanning_dots)
        else:
            # Clear requested: schedule it with a small delay
            # This prevents flickering if the status is immediately set again
            self._clear_job = self.root.after(200, self._perform_clear_status)

    def _perform_clear_status(self):
        """
        Actually clear the status and stop animation.

        Cancels any ongoing animation jobs and resets scanning status.
        """
        self._clear_job = None
        if hasattr(self, "_blink_job") and self._blink_job:
            try:
                self.root.after_cancel(self._blink_job)
            except Exception:
                pass
            self._blink_job = None

        self.scanning_status = ""
        self._dots_count = 0
        self._update_title_with_scanning()

    def _animate_scanning_dots(self):
        """
        Animate dots for scanning status.

        Increments dot count from 0 to 7, then resets, updating the title.
        """
        if not self.scanning_status:
            self._blink_job = None
            return

        self._dots_count += 1
        if self._dots_count > 7:
            self._dots_count = 0

        self._update_title_with_scanning()
        self._blink_job = self.root.after(500, self._animate_scanning_dots)

    def _update_title_with_scanning(self):
        """
        Update title including scanning status and dots.

        Updates the window title to show current status and scanning progress.
        """
        if self.scanning_status:
            dots = "." * getattr(self, "_dots_count", 0)
            self.root.title(f"ChatBot [{self.current_status}] {self.scanning_status}{dots}")
        else:
            self.root.title(f"ChatBot [{self.current_status}]")

    def show_temp_message(self, title, message, duration=None):
        """
        Show a temporary message window.

        Displays a modal or persistent message window with the given title and message.

        Args:
            title (str): Window title.
            message (str): Message text to display.
            duration (int, optional): Auto-close duration in milliseconds. If None, persists.

        Returns:
            tk.Toplevel: The created message window.
        """
        if duration is not None:
            temp_window = tk.Toplevel(self.root)
            temp_window.attributes('-topmost', True)
            temp_window.transient(self.root)
            temp_window.grab_set()
        else:
            temp_window = tk.Toplevel()
        temp_window.title(title)
        tk.Label(temp_window, text=message, font=(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_TITLE, "bold")).pack(padx=10, pady=10)
        if duration is not None:
            self.root.after(duration, temp_window.destroy)
        return temp_window
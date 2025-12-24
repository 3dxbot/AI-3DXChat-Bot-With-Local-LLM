"""
UI Windows Module.

This module provides the UIWindowsMixin class, which handles additional
UI windows and dialogs for the chatbot application, including settings
windows, nick management dialogs, and confirmation prompts.

Classes:
    UIWindowsMixin: Mixin class for UI window management.
"""

import json
import tkinter as tk
import customtkinter as ctk
import tkinter.ttk as ttk
import os
import time
import threading
import shutil
import subprocess
import zipfile
from tkinter import filedialog, simpledialog, messagebox
from PIL import Image
import cv2
import numpy as np
from .ui_styles import UIStyles


class UIWindowsMixin:
    """
    Mixin class for additional UI windows.

    This mixin provides methods for creating and managing various UI windows
    and dialogs, including settings configuration, nick management, and
    user confirmations.

    Methods:
        open_settings_window: Open the main settings window with tabs.
        save_hotkeys_and_prompt: Save hotkey settings and close window.
        show_manage_nick_window: Show window to manage a discovered nick.
        show_confirm_nick_window: Show confirmation dialog for nick addition.
        _confirm_nick: Handle nick confirmation response.
    """

    def open_settings_window(self):
        """
        Toggle between dashboard and settings view.
        """
        if self.current_view == 'settings':
            self.switch_to_dashboard()
        else:
            self.switch_to_settings()

    def _populate_settings_tabs(self):
        """
        Populate the settings frame with content.
        """
        # Page title
        ctk.CTkLabel(self.settings_frame, text="Prompts", font=(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_DISPLAY, "bold"), text_color=UIStyles.TEXT_PRIMARY).pack(anchor='w', padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_LG))

        # General section
        tab_general = self.settings_frame

        # Global prompt card
        prompt_frame = UIStyles.create_card_frame(tab_general)
        prompt_frame.pack(padx=UIStyles.SPACE_2XL, pady=UIStyles.SPACE_LG, fill='x', anchor='n')
        
        ctk.CTkLabel(prompt_frame, text="Global Prompt", 
                      font=UIStyles.FONT_TITLE, text_color=UIStyles.TEXT_PRIMARY).pack(anchor='w', padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_SM))
        ctk.CTkLabel(prompt_frame, text="Added before each request",
                      font=UIStyles.FONT_SMALL, text_color=UIStyles.TEXT_SECONDARY).pack(anchor='w', padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_MD))

        self.global_prompt_var = tk.StringVar(value=self.bot.global_prompt)
        prompt_entry = UIStyles.create_input_field(prompt_frame, textvariable=self.global_prompt_var)
        prompt_entry.pack(padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_2XL), fill='x')

        # Messages card
        messages_frame = UIStyles.create_card_frame(tab_general)
        messages_frame.pack(padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_LG), fill='x', anchor='n')
        
        ctk.CTkLabel(messages_frame, text="Messages for Invitations and Pose Changes",
                      font=UIStyles.FONT_TITLE, text_color=UIStyles.TEXT_PRIMARY).pack(anchor='w', padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_MD))

        inner_messages = ctk.CTkFrame(messages_frame, fg_color="transparent")
        inner_messages.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_2XL))

        # Pose Change Message
        ctk.CTkLabel(inner_messages, text="Pose Change Message:", font=UIStyles.FONT_SMALL, text_color=UIStyles.TEXT_SECONDARY).pack(anchor='w', pady=(0, UIStyles.SPACE_XS))
        self.pose_message_var = tk.StringVar(value=self.bot.get_pose_message())
        pose_entry = UIStyles.create_input_field(inner_messages, textvariable=self.pose_message_var)
        pose_entry.pack(fill='x', pady=(0, UIStyles.SPACE_MD))

        # Gift Detection Message  
        ctk.CTkLabel(inner_messages, text="Gift Detection Message:", font=UIStyles.FONT_SMALL, text_color=UIStyles.TEXT_SECONDARY).pack(anchor='w', pady=(0, UIStyles.SPACE_XS))
        self.gift_message_var = tk.StringVar(value=self.bot.get_gift_message())
        gift_entry = UIStyles.create_input_field(inner_messages, textvariable=self.gift_message_var)
        gift_entry.pack(fill='x', pady=(0, UIStyles.SPACE_MD))

        # Unknown Pose Message (EN)
        ctk.CTkLabel(inner_messages, text="Unknown Pose Message (EN/Other):", font=UIStyles.FONT_SMALL, text_color=UIStyles.TEXT_SECONDARY).pack(anchor='w', pady=(0, UIStyles.SPACE_XS))
        self.unknown_pose_message_var = tk.StringVar(value=self.bot.unknown_pose_message)
        unknown_pose_entry = UIStyles.create_input_field(inner_messages, textvariable=self.unknown_pose_message_var)
        unknown_pose_entry.pack(fill='x', pady=(0, UIStyles.SPACE_MD))

        # Unknown Pose Message (RU)
        ctk.CTkLabel(inner_messages, text="Unknown Pose Message (RU):", font=UIStyles.FONT_SMALL, text_color=UIStyles.TEXT_SECONDARY).pack(anchor='w', pady=(0, UIStyles.SPACE_XS))
        self.unknown_pose_message_ru_var = tk.StringVar(value=getattr(self.bot, 'unknown_pose_message_ru', ""))
        unknown_pose_ru_entry = UIStyles.create_input_field(inner_messages, textvariable=self.unknown_pose_message_ru_var)
        unknown_pose_ru_entry.pack(fill='x')

        # Hotkeys card
        hotkeys_card = UIStyles.create_card_frame(tab_general)
        hotkeys_card.pack(padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_LG), fill='x')
        
        ctk.CTkLabel(hotkeys_card, text="Hotkey Phrases (F5-F12)",
                      font=UIStyles.FONT_TITLE, text_color=UIStyles.TEXT_PRIMARY).pack(anchor='w', padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_MD))

        hotkeys_frame = ctk.CTkFrame(hotkeys_card, fg_color="transparent")
        hotkeys_frame.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_2XL))
        hotkeys_frame.grid_columnconfigure(1, weight=1)

        self.hotkey_entries = {}
        for i in range(5, 13):
            key = f"F{i}"
            ctk.CTkLabel(hotkeys_frame, text=f"Key {key}:", font=UIStyles.FONT_SMALL, text_color=UIStyles.TEXT_SECONDARY).grid(row=i - 5, column=0, padx=(0, UIStyles.SPACE_MD), pady=UIStyles.SPACE_XS, sticky="w")

            entry_var = tk.StringVar(value=self.bot.get_hotkey_phrase(key))
            entry = UIStyles.create_input_field(hotkeys_frame, textvariable=entry_var)
            entry.grid(row=i - 5, column=1, pady=UIStyles.SPACE_XS, sticky="ew")
            self.hotkey_entries[key] = entry_var

        # Save button - prominent and fixed
        save_frame = ctk.CTkFrame(tab_general, fg_color="transparent")
        save_frame.pack(fill="x", padx=UIStyles.SPACE_2XL, pady=UIStyles.SPACE_3XL)
        UIStyles.create_button(save_frame, text="Save Settings", width=150, height=44,
                      command=self.save_hotkeys_and_prompt).pack(side=tk.RIGHT)


    def _populate_hooker_mod_view(self):
        # Page title
        ctk.CTkLabel(self.hooker_mod_frame, text="Hooker Mod", 
                      font=(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_DISPLAY, "bold"), 
                      text_color=UIStyles.TEXT_PRIMARY).pack(anchor='w', padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_LG))
        
        # Numeric fields card
        numeric_card = UIStyles.create_card_frame(self.hooker_mod_frame)
        numeric_card.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=UIStyles.SPACE_LG)
        
        ctk.CTkLabel(numeric_card, text="Timing & Payment Settings",
                      font=UIStyles.FONT_TITLE, text_color=UIStyles.TEXT_PRIMARY).pack(anchor='w', padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_MD))
        
        numeric_inner = ctk.CTkFrame(numeric_card, fg_color="transparent")
        numeric_inner.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_2XL))
        numeric_inner.grid_columnconfigure(1, weight=1)

        # Free mins
        ctk.CTkLabel(numeric_inner, text="Free Minutes:", font=UIStyles.FONT_SMALL, text_color=UIStyles.TEXT_SECONDARY).grid(row=0, column=0, sticky='w', pady=UIStyles.SPACE_XS)
        self.hooker_free_mins_var = tk.StringVar(value=str(getattr(self.bot, 'hooker_free_mins', 0)))
        UIStyles.create_input_field(numeric_inner, textvariable=self.hooker_free_mins_var, width=100).grid(row=0, column=1, sticky='w', pady=UIStyles.SPACE_XS, padx=(UIStyles.SPACE_MD, 0))

        # Paid mins
        ctk.CTkLabel(numeric_inner, text="Paid Minutes:", font=UIStyles.FONT_SMALL, text_color=UIStyles.TEXT_SECONDARY).grid(row=1, column=0, sticky='w', pady=UIStyles.SPACE_XS)
        self.hooker_paid_mins_var = tk.StringVar(value=str(getattr(self.bot, 'hooker_paid_mins', 0)))
        UIStyles.create_input_field(numeric_inner, textvariable=self.hooker_paid_mins_var, width=100).grid(row=1, column=1, sticky='w', pady=UIStyles.SPACE_XS, padx=(UIStyles.SPACE_MD, 0))

        # Coins
        ctk.CTkLabel(numeric_inner, text="Coins per Paid:", font=UIStyles.FONT_SMALL, text_color=UIStyles.TEXT_SECONDARY).grid(row=2, column=0, sticky='w', pady=UIStyles.SPACE_XS)
        self.hooker_coins_var = tk.StringVar(value=str(getattr(self.bot, 'hooker_coins_per_paid', 0)))
        UIStyles.create_input_field(numeric_inner, textvariable=self.hooker_coins_var, width=100).grid(row=2, column=1, sticky='w', pady=UIStyles.SPACE_XS, padx=(UIStyles.SPACE_MD, 0))

        # Wait time
        ctk.CTkLabel(numeric_inner, text="Payment Wait Time (sec):", font=UIStyles.FONT_SMALL, text_color=UIStyles.TEXT_SECONDARY).grid(row=3, column=0, sticky='w', pady=UIStyles.SPACE_XS)
        self.hooker_wait_time_var = tk.StringVar(value=str(getattr(self.bot, 'hooker_payment_wait_time', 60)))
        UIStyles.create_input_field(numeric_inner, textvariable=self.hooker_wait_time_var, width=100).grid(row=3, column=1, sticky='w', pady=UIStyles.SPACE_XS, padx=(UIStyles.SPACE_MD, 0))

        # Messages card
        messages_card = UIStyles.create_card_frame(self.hooker_mod_frame)
        messages_card.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_LG))
        
        ctk.CTkLabel(messages_card, text="Messages",
                      font=UIStyles.FONT_TITLE, text_color=UIStyles.TEXT_PRIMARY).pack(anchor='w', padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_MD))
        
        messages_inner = ctk.CTkFrame(messages_card, fg_color="transparent")
        messages_inner.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_2XL))
        
        # Warning message
        ctk.CTkLabel(messages_inner, text="Warning Message (Game Chat):", font=UIStyles.FONT_SMALL, text_color=UIStyles.TEXT_SECONDARY).pack(anchor='w', pady=(0, UIStyles.SPACE_XS))
        self.hooker_warn_var = tk.StringVar(value=getattr(self.bot, 'hooker_warning_message', ""))
        UIStyles.create_input_field(messages_inner, textvariable=self.hooker_warn_var).pack(fill='x', pady=(0, UIStyles.SPACE_MD))

        # Success message
        ctk.CTkLabel(messages_inner, text="Success Message (AI):", font=UIStyles.FONT_SMALL, text_color=UIStyles.TEXT_SECONDARY).pack(anchor='w', pady=(0, UIStyles.SPACE_XS))
        self.hooker_hiwaifu_msg_var = tk.StringVar(value=getattr(self.bot, 'hooker_hiwaifu_message', ""))
        UIStyles.create_input_field(messages_inner, textvariable=self.hooker_hiwaifu_msg_var).pack(fill='x')

        # Save button
        save_frame = ctk.CTkFrame(self.hooker_mod_frame, fg_color="transparent")
        save_frame.pack(fill="x", padx=UIStyles.SPACE_2XL, pady=UIStyles.SPACE_3XL)
        UIStyles.create_button(save_frame, text="Save Hooker Mod Settings", width=180, height=44,
                              command=self.save_hooker_mod_settings).pack(side=tk.RIGHT)

    def _populate_game_sync_view(self):
        """
        Populate the game sync view with settings.
        """
        # Page title  
        ctk.CTkLabel(self.game_sync_frame, text="Game Sync", 
                      font=(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_DISPLAY, "bold"), 
                      text_color=UIStyles.TEXT_PRIMARY).pack(anchor='w', padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_LG))
        
        # Message delay card
        delay_frame = UIStyles.create_card_frame(self.game_sync_frame)
        delay_frame.pack(padx=UIStyles.SPACE_2XL, pady=UIStyles.SPACE_LG, fill='x', anchor='n')
        
        ctk.CTkLabel(delay_frame, text="Message Typing Speed",
                      font=UIStyles.FONT_TITLE, text_color=UIStyles.TEXT_PRIMARY).pack(anchor='w', padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_MD))

        delay_inner = ctk.CTkFrame(delay_frame, fg_color="transparent")
        delay_inner.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_2XL))

        self.time_per_500_chars_var = tk.DoubleVar(value=self.bot.time_per_500_chars)
        self.time_per_500_chars_slider = ctk.CTkSlider(
            delay_inner, 
            from_=0, 
            to=100, 
            number_of_steps=100, 
            variable=self.time_per_500_chars_var,
            button_color=UIStyles.PRIMARY_COLOR,
            button_hover_color=UIStyles.PRIMARY_HOVER,
            progress_color=UIStyles.PRIMARY_COLOR,
            height=18
        )
        self.time_per_500_chars_slider.pack(side=tk.LEFT, fill='x', expand=True, padx=(0, UIStyles.SPACE_LG))

        self.time_per_500_chars_label = ctk.CTkLabel(
            delay_inner, 
            text=f"{self.time_per_500_chars_var.get():.1f} sec",
            font=UIStyles.FONT_NORMAL,
            text_color=UIStyles.TEXT_PRIMARY,
            width=80
        )
        self.time_per_500_chars_label.pack(side=tk.LEFT)

        # Update label when slider moves
        def update_delay_label(*args):
            self.time_per_500_chars_label.configure(text=f"{self.time_per_500_chars_var.get():.1f} sec")
        self.time_per_500_chars_var.trace_add("write", update_delay_label)

        # Zones card
        zones_frame = UIStyles.create_card_frame(self.game_sync_frame)
        zones_frame.pack(padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_LG), fill='x', anchor='n')
        
        ctk.CTkLabel(zones_frame, text="Screen Area Settings",
                      font=UIStyles.FONT_TITLE, text_color=UIStyles.TEXT_PRIMARY).pack(anchor='w', padx=UIStyles.SPACE_2XL, pady=(UIStyles.SPACE_2XL, UIStyles.SPACE_MD))

        zones_buttons = ctk.CTkFrame(zones_frame, fg_color="transparent")
        zones_buttons.pack(fill='x', padx=UIStyles.SPACE_2XL, pady=(0, UIStyles.SPACE_2XL))
        
        UIStyles.create_button(zones_buttons, text="Configure Zones", command=self.setup_screen_area, width=150, height=40).pack(side=tk.LEFT, padx=(0, UIStyles.SPACE_MD))
        
        # Sync button text with current state
        overlay_text = "Hide Zones" if self.bot.show_overlay else "Show Zones"
        # Also sync the variable if it wasn't already
        self.show_zones_var.set(self.bot.show_overlay)
        
        UIStyles.create_secondary_button(zones_buttons, text=overlay_text, command=self.on_toggle_overlay, width=150, height=40).pack(side=tk.LEFT)

        # Save button
        save_frame = ctk.CTkFrame(self.game_sync_frame, fg_color="transparent")
        save_frame.pack(fill="x", padx=UIStyles.SPACE_2XL, pady=UIStyles.SPACE_3XL)
        UIStyles.create_button(save_frame, text="Save Game Sync Settings", width=180, height=44,
                              command=self.save_game_sync_settings).pack(side=tk.RIGHT)

    def save_game_sync_settings(self):
        """
        Save game sync settings.
        """
        new_time_per_500_chars = self.time_per_500_chars_var.get()
        self.bot.time_per_500_chars = new_time_per_500_chars
        self.bot.save_settings()
        self.log_message("Game Sync settings saved.", internal=True)

    def save_hotkeys_and_prompt(self):
        """
        Save hotkey phrases, prompt, and message delay.

        Collects settings from the UI and saves them to the bot configuration,
        then exits settings mode.
        """
        new_phrases = {}
        for key, entry_var in self.hotkey_entries.items():
            phrase = entry_var.get().strip()
            if phrase:
                new_phrases[key] = phrase

        new_global_prompt = self.global_prompt_var.get().strip()
        new_pose_message = self.pose_message_var.get().strip()
        new_pose_message_ru = new_pose_message  # Use the same message for both languages since UI has one field
        new_gift_message = self.gift_message_var.get().strip()
        new_unknown_pose_message = self.unknown_pose_message_var.get().strip()
        new_unknown_pose_message_ru = self.unknown_pose_message_ru_var.get().strip()

        # Hooker Mod settings
        hooker_enabled = self.hooker_enabled_var.get()
        try:
            # Only try to get hooker mod values if the variables exist (i.e., Hooker Mod tab was loaded)
            if hasattr(self, 'hooker_free_mins_var'):
                hooker_free = int(self.hooker_free_mins_var.get().strip() or 0)
                hooker_paid = int(self.hooker_paid_mins_var.get().strip() or 0)
                hooker_coins = int(self.hooker_coins_var.get().strip() or 0)
                hooker_wait = int(self.hooker_wait_time_var.get().strip() or 60)
                hooker_warn = self.hooker_warn_var.get().strip()
                hooker_hiwaifu = self.hooker_hiwaifu_msg_var.get().strip()
            else:
                # If hooker mod variables don't exist, use current bot values or defaults
                hooker_free = getattr(self.bot, 'hooker_free_mins', 0)
                hooker_paid = getattr(self.bot, 'hooker_paid_mins', 0)
                hooker_coins = getattr(self.bot, 'hooker_coins_per_paid', 0)
                hooker_wait = getattr(self.bot, 'hooker_payment_wait_time', 60)
                hooker_warn = getattr(self.bot, 'hooker_warning_message', "")
                hooker_hiwaifu = getattr(self.bot, 'hooker_hiwaifu_message', "")
        except (ValueError, AttributeError):
            hooker_free = 0
            hooker_paid = 0
            hooker_coins = 0
            hooker_wait = 60
            hooker_warn = ""
            hooker_hiwaifu = ""

        try:
            self.bot.save_hotkeys_and_prompt(
                new_phrases, new_global_prompt, None, new_pose_message,
                new_pose_message_ru, new_gift_message, new_unknown_pose_message,
                new_unknown_pose_message_ru,
                hooker_enabled=hooker_enabled,
                hooker_free=hooker_free,
                hooker_paid=hooker_paid,
                hooker_coins=hooker_coins,
                hooker_warn=hooker_warn,
                hooker_hiwaifu=hooker_hiwaifu,
                hooker_wait=hooker_wait
            )
        except Exception as e:
            self.bot.log(f"Ошибка при сохранении фраз и промпта: {e}", internal=True)

    def save_hooker_mod_settings(self):
        """
        Save hooker mod settings.

        Collects hooker mod settings from the UI and saves them to the bot configuration.
        """
        try:
            hooker_enabled = self.hooker_enabled_var.get()
            # Only try to get hooker mod values if the variables exist (i.e., Hooker Mod tab was loaded)
            if hasattr(self, 'hooker_free_mins_var'):
                hooker_free = int(self.hooker_free_mins_var.get().strip() or 0)
                hooker_paid = int(self.hooker_paid_mins_var.get().strip() or 0)
                hooker_coins = int(self.hooker_coins_var.get().strip() or 0)
                hooker_wait = int(self.hooker_wait_time_var.get().strip() or 60)
                hooker_warn = self.hooker_warn_var.get().strip()
                hooker_hiwaifu = self.hooker_hiwaifu_msg_var.get().strip()
            else:
                # If hooker mod variables don't exist, use current bot values or defaults
                hooker_free = getattr(self.bot, 'hooker_free_mins', 0)
                hooker_paid = getattr(self.bot, 'hooker_paid_mins', 0)
                hooker_coins = getattr(self.bot, 'hooker_coins_per_paid', 0)
                hooker_wait = getattr(self.bot, 'hooker_payment_wait_time', 60)
                hooker_warn = getattr(self.bot, 'hooker_warning_message', "")
                hooker_hiwaifu = getattr(self.bot, 'hooker_hiwaifu_message', "")
        except (ValueError, AttributeError):
            self.log_message("Invalid numeric values in Hooker Mod settings.", internal=True)
            return

        try:
            self.bot.save_hotkeys_and_prompt(
                {}, "", None, None, None, None, None, None,
                hooker_enabled=hooker_enabled,
                hooker_free=hooker_free,
                hooker_paid=hooker_paid,
                hooker_coins=hooker_coins,
                hooker_warn=hooker_warn,
                hooker_hiwaifu=hooker_hiwaifu,
                hooker_wait=hooker_wait
            )
            self.log_message("Hooker Mod settings saved.", internal=True)
        except Exception as e:
            self.log_message(f"Error saving Hooker Mod settings: {e}", internal=True)


    def show_manage_nick_window(self, nick):
        """
        Show window to manage a discovered nick.

        Displays a dialog allowing the user to add a newly discovered
        nickname to either the ignore or target lists.

        Args:
            nick (str): The nickname to manage.
        """
        manage_window = ctk.CTkToplevel(self.root)
        manage_window.title("Manage Nickname")
        manage_window.attributes('-topmost', True)
        ctk.CTkLabel(manage_window, text=f"New nick found: '{nick}'.\nAdd to a list?").pack(pady=10)

        def on_ignore_click():
            self.add_nick(nick, 'ignore')
            self.log_message(f"Nick '{nick}' added to ignored list.", internal=True)
            manage_window.destroy()

        def on_target_click():
            self.add_nick(nick, 'target')
            self.log_message(f"Nick '{nick}' added to target list.", internal=True)
            manage_window.destroy()

        def on_cancel_click():
            self.log_message(f"Nick '{nick}' ignored (temporary).", internal=True)
            manage_window.destroy()

        button_frame = ctk.CTkFrame(manage_window, fg_color="transparent")
        button_frame.pack(pady=5)
        UIStyles.create_button(button_frame, text="Ignore", command=on_ignore_click).pack(side=tk.LEFT, padx=5)
        UIStyles.create_button(button_frame, text="Track", command=on_target_click).pack(side=tk.LEFT, padx=5)
        UIStyles.create_button(button_frame, text="Cancel", command=on_cancel_click).pack(side=tk.LEFT, padx=5)
        manage_window.transient(self.root)
        manage_window.grab_set()

    def show_confirm_nick_window(self, nick):
        """
        Show confirmation window for nick addition.

        Displays a yes/no dialog to confirm adding a nickname to the target list.

        Args:
            nick (str): The nickname to confirm.
        """
        confirm_window = ctk.CTkToplevel(self.root)
        confirm_window.title("Confirmation")
        confirm_window.attributes('-topmost', True)
        ctk.CTkLabel(confirm_window, text=f"Add '{nick}' to tracked list?").pack(pady=10)
        frame = ctk.CTkFrame(confirm_window, fg_color="transparent")
        frame.pack(pady=5)
        yes_button = UIStyles.create_button(frame, text="Yes", command=lambda: self._confirm_nick(confirm_window, True, nick))
        no_button = UIStyles.create_button(frame, text="No", command=lambda: self._confirm_nick(confirm_window, False, nick))
        yes_button.pack(side=tk.LEFT, padx=5)
        no_button.pack(side=tk.LEFT, padx=5)
        confirm_window.transient(self.root)
        confirm_window.grab_set()

    def _confirm_nick(self, window, add_to_list, nick):
        """
        Handle nick confirmation response.

        Processes the user's response to the nick confirmation dialog,
        adding the nick to the target list if confirmed.

        Args:
            window: The confirmation window to close.
            add_to_list (bool): Whether to add the nick to the list.
            nick (str): The nickname being confirmed.
        """
        if add_to_list:
            self.add_nick(nick, "target")
            self.log_message(f"Nick '{nick}' added to target list.", internal=True)
        else:
            self.log_message(f"Nick '{nick}' not added.", internal=True)
        window.destroy()



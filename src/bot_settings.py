"""
Bot Settings Module.

This module provides the BotSettingsMixin class, which handles loading,
saving, and managing bot settings, hotkeys, and user preferences. It includes
functionality for managing ignore/target nick lists, OCR language settings,
and hotkey phrases.

Classes:
    BotSettingsMixin: Mixin class for bot settings management.
"""

import json
import os
from .config import (SETTINGS_FILE, HOTKEY_PHRASES_FILE)


class BotSettingsMixin:
    """
    Mixin class for handling bot settings and hotkeys.

    This mixin provides methods to load and save bot configuration, manage
    hotkey phrases, handle nick lists (ignore/target), and manage various
    bot preferences like OCR language and autonomous mode.

    Attributes:
        hotkey_phrases (dict): Dictionary of hotkey phrases.
        global_prompt (str): Global prompt for the bot.
        partnership_message (str): Default partnership message.
        pose_message (str): Default pose change message.
        gift_message (str): Default gift detection message.
        unknown_pose_message (str): Message for unknown poses (English/other).
        unknown_pose_message_ru (str): Message for unknown poses (Russian).
        ignore_nicks (set): Set of nicks to ignore.
        target_nicks (set): Set of target nicks.
        areas (dict): Dictionary of screen areas.
        ocr_language (str): OCR language setting.
        current_language (str): Current language setting.
        show_overlay (bool): Whether to show overlay.
        autonomous_mode (bool): Whether autonomous mode is enabled.
        time_per_500_chars (float): Time per 500 characters for typing.
        hooker_mod_enabled (bool): Whether Hooker Mod is enabled.
        hooker_free_mins (int): Number of free minutes.
        hooker_paid_mins (int): Number of paid minutes.
        hooker_coins_per_paid (int): Number of coins for paid time.
        hooker_warning_message (str): Message when time is ending.
        hooker_hiwaifu_message (str): Successful payment message for AI.
        hooker_payment_wait_time (int): Seconds to wait for payment.
        active_character_name (str): Name of the currently active character profile.

    Methods:
        _load_hotkey_settings: Load hotkey settings from file.
        _save_hotkey_settings: Save hotkey settings to file.
        save_hotkeys_and_prompt: Public method to update and save settings.
        get_hotkey_phrase: Get phrase for a hotkey.
        get_partnership_message: Get partnership message.
        get_pose_message: Get pose message.
        get_gift_message: Get gift detection message.
        get_unknown_pose_message: Get unknown pose message.
        update_hotkey_phrase: Update a hotkey phrase.
        create_default_settings: Create default settings.
        load_settings: Load settings from file.
        save_settings: Save settings to file.
        add_nick: Add a nick to a list.
        remove_nick: Remove a nick from a list.
        change_language: Change the bot's language.
    """

    def _load_hotkey_settings(self):
        """
        Load hotkey phrases and global prompt from file.

        Attempts to load hotkey settings from the configured file. If the file
        exists, it loads the global prompt, partnership message, pose message,
        unknown pose message, and hotkey phrases. If the file does not exist,
        it initializes default values.

        Raises:
            Exception: Logs any errors during loading and uses default values.
        """
        try:
            if os.path.exists(HOTKEY_PHRASES_FILE):
                with open(HOTKEY_PHRASES_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.global_prompt = settings.get("global_prompt", "")
                    self.partnership_message = settings.get("partnership_message", "Partnership accepted. I am ready.")
                    self.pose_message = settings.get("pose_message", "Pose changed.")
                    self.pose_message_ru = settings.get("pose_message_ru", "Поза изменена.")
                    self.gift_message = settings.get("gift_message", "Gift received!")
                    self.unknown_pose_message = settings.get("unknown_pose_message", "PLEASE HELP MAKE BOT BETTER! The position is unknown and isn't in the database yet please describe it and bot will know it.")
                    self.unknown_pose_message_ru = settings.get("unknown_pose_message_ru", "ПОМОГИТЕ СДЕЛАТЬ БОТА ЛУЧШЕ! Эта поза неизвестна и еще не в базе данных, пожалуйста опишите ее и бот запомнит.")
                    self.hotkey_phrases = settings.get("hotkey_phrases", {})
                    self.hooker_mod_enabled = settings.get("hooker_mod_enabled", False)
                    self.hooker_free_mins = settings.get("hooker_free_mins", 0)
                    self.hooker_paid_mins = settings.get("hooker_paid_mins", 0)
                    self.hooker_coins_per_paid = settings.get("hooker_coins_per_paid", 0)
                    self.hooker_warning_message = settings.get("hooker_warning_message", "")
                    self.hooker_hiwaifu_message = settings.get("hooker_hiwaifu_message", "")
                    self.hooker_payment_wait_time = settings.get("hooker_payment_wait_time", 60)
                    self.use_translation_layer = settings.get("use_translation_layer", False)
                    if not self.hotkey_phrases and isinstance(settings, dict):
                        self.hotkey_phrases = {k: v for k, v in settings.items() if k not in ['global_prompt', 'partnership_message', 'pose_message', 'pose_message_ru', 'gift_message', 'unknown_pose_message', 'unknown_pose_message_ru', 'hooker_mod_enabled', 'hooker_free_mins', 'hooker_paid_mins', 'hooker_coins_per_paid', 'hooker_warning_message', 'hooker_hiwaifu_message', 'hooker_payment_wait_time']}
                    self.log("Hotkey settings and prompt loaded.", internal=True)
            else:
                self.log("Hotkey settings file not found. Creating empty.", internal=True)
                self.hotkey_phrases = {}
                self.global_prompt = ""
                self.partnership_message = "Partnership accepted. I am ready."
                self.pose_message = "Pose changed."
                self.gift_message = "Gift received!"
                self.unknown_pose_message = "Unknown pose detected."
                self.hooker_mod_enabled = False
                self.hooker_free_mins = 0
                self.hooker_paid_mins = 0
                self.hooker_coins_per_paid = 0
                self.hooker_warning_message = ""
                self.hooker_hiwaifu_message = ""
                self.hooker_payment_wait_time = 60
        except Exception as e:
            self.log(f"Error loading phrases/prompt: {e}", internal=True)
            self.hotkey_phrases = {}
            self.global_prompt = ""
            self.partnership_message = "Partnership accepted. I am ready."
            self.pose_message = "Pose changed."
            self.pose_message_ru = "Поза изменена."
            self.gift_message = "Gift received!"
            self.unknown_pose_message = "PLEASE HELP MAKE BOT BETTER! The position is unknown and isn't in the database yet please describe it and bot will know it."
            self.unknown_pose_message_ru = "ПОМОГИТЕ СДЕЛАТЬ БОТА ЛУЧШЕ! Эта поза неизвестна и еще не в базе данных, пожалуйста опишите ее и бот запомнит."
            self.hooker_mod_enabled = False
            self.hooker_free_mins = 0
            self.hooker_paid_mins = 0
            self.hooker_coins_per_paid = 0
            self.hooker_warning_message = ""
            self.hooker_hiwaifu_message = ""
            self.hooker_payment_wait_time = 60
            self.use_translation_layer = False

    def _save_hotkey_settings(self):
        """
        Save hotkey phrases and global prompt to file.

        Saves the current hotkey phrases, global prompt, partnership message,
        pose message, and unknown pose message to the configured file in JSON format.

        Raises:
            Exception: Logs any errors during saving.
        """
        try:
            data_to_save = {
                "hotkey_phrases": self.hotkey_phrases,
                "global_prompt": self.global_prompt,
                "partnership_message": self.partnership_message,
                "pose_message": self.pose_message,
                "pose_message_ru": self.pose_message_ru,
                "gift_message": self.gift_message,
                "unknown_pose_message": self.unknown_pose_message,
                "unknown_pose_message_ru": self.unknown_pose_message_ru,
                "hooker_mod_enabled": self.hooker_mod_enabled,
                "hooker_free_mins": self.hooker_free_mins,
                "hooker_paid_mins": self.hooker_paid_mins,
                "hooker_coins_per_paid": self.hooker_coins_per_paid,
                "hooker_warning_message": self.hooker_warning_message,
                "hooker_hiwaifu_message": self.hooker_hiwaifu_message,
                "hooker_payment_wait_time": self.hooker_payment_wait_time,
                "use_translation_layer": self.use_translation_layer
            }
            os.makedirs(os.path.dirname(HOTKEY_PHRASES_FILE), exist_ok=True)
            with open(HOTKEY_PHRASES_FILE, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
            self.log("Hotkey phrases and global prompt saved.", internal=True)
        except Exception as e:
            self.log(f"Error saving phrases: {e}", internal=True)

    def save_hotkeys_and_prompt(self, new_phrases, new_prompt, new_partnership_message=None, new_pose_message=None, new_pose_message_ru=None, new_gift_message=None, new_unknown_pose_message=None, new_unknown_pose_message_ru=None,
                                hooker_enabled=None, hooker_free=None, hooker_paid=None, hooker_coins=None, hooker_warn=None, hooker_hiwaifu=None, hooker_wait=None):
        """
        Public method to update and save prompt and phrases.

        Updates the global prompt, hotkey phrases, and optional messages,
        then saves the settings to file.

        Args:
            new_phrases (dict): New hotkey phrases dictionary.
            new_prompt (str): New global prompt.
            new_partnership_message (str, optional): New partnership message.
            new_pose_message (str, optional): New pose message.
            new_gift_message (str, optional): New gift message.
            new_unknown_pose_message (str, optional): New unknown pose message.
        """
        self.global_prompt = new_prompt
        self.hotkey_phrases = new_phrases
        if new_partnership_message is not None:
            self.partnership_message = new_partnership_message
        if new_pose_message is not None:
            self.pose_message = new_pose_message
        if new_pose_message_ru is not None:
            self.pose_message_ru = new_pose_message_ru
        if new_gift_message is not None:
            self.gift_message = new_gift_message
        if new_unknown_pose_message is not None:
            self.unknown_pose_message = new_unknown_pose_message
        if new_unknown_pose_message_ru is not None:
            self.unknown_pose_message_ru = new_unknown_pose_message_ru
        if hooker_enabled is not None:
            self.hooker_mod_enabled = hooker_enabled
        if hooker_free is not None:
            self.hooker_free_mins = hooker_free
        if hooker_paid is not None:
            self.hooker_paid_mins = hooker_paid
        if hooker_coins is not None:
            self.hooker_coins_per_paid = hooker_coins
        if hooker_warn is not None:
            self.hooker_warning_message = hooker_warn
        if hooker_hiwaifu is not None:
            self.hooker_hiwaifu_message = hooker_hiwaifu
        if hooker_wait is not None:
            self.hooker_payment_wait_time = hooker_wait
        self._save_hotkey_settings()
        self.log("Global prompt and phrases updated and saved.", internal=True)

    def get_hotkey_phrase(self, key):
        """
        Get the phrase for a specific hotkey.

        Args:
            key (str): The hotkey identifier.

        Returns:
            str: The phrase associated with the key, or empty string if not found.
        """
        return self.hotkey_phrases.get(key, "")

    def get_partnership_message(self):
        """
        Get the default partnership message.

        Returns:
            str: The partnership message.
        """
        return self.partnership_message

    def get_pose_message(self):
        """
        Get the default pose change message based on OCR language.
        
        Returns:
            str: The pose message in the appropriate language.
        """
        if self.ocr_language == 'ru':
            return self.pose_message_ru
        else:
            return self.pose_message

    def get_gift_message(self):
        """
        Get the default gift detection message.

        Returns:
            str: The gift message.
        """
        return self.gift_message

    def get_unknown_pose_message(self):
        """
        Get the message for unknown poses based on OCR language.

        Returns:
            str: The unknown pose message in the appropriate language.
        """
        if self.current_language == 'ru':
            return self.unknown_pose_message_ru
        else:
            return self.unknown_pose_message

    def update_hotkey_phrase(self, key, phrase):
        """
        Update the phrase for a specific hotkey.

        Args:
            key (str): The hotkey identifier.
            phrase (str): The new phrase to associate with the key.
        """
        self.hotkey_phrases[key] = phrase
        self._save_hotkey_settings()
        self.log(f"Phrase for {key} updated.", internal=True)

    def create_default_settings(self):
        """
        Create and save default settings.

        Initializes default values for ignore nicks, target nicks, areas,
        OCR language, and typing speed, then saves them.
        """
        self.ignore_nicks = set()
        self.target_nicks = set()
        self.areas = {"chat_area": None, "input_area": None, "game_window_name": "Your game window name"}
        self.ocr_language = 'en'
        self.current_language = 'en'
        self.time_per_500_chars = 2.0
        self.save_settings()

    def load_settings(self):
        """
        Load settings from file.

        Attempts to load settings from the configured file. If the file exists,
        it loads areas, ignore/target nicks, OCR language, overlay settings,
        autonomous mode, and typing speed. If the file does not exist, it creates
        default settings.

        The OCR language is validated against supported languages and synced
        with current_language. If show_overlay is enabled, the overlay is created.

        Raises:
            Exception: Logs any errors and creates default settings.
        """
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.areas = settings.get("areas", self.areas)
                    ignore_nicks = settings.get("ignore_nicks", [])
                    self.ignore_nicks = set(nick.strip().lower() for nick in ignore_nicks if nick)
                    target_nicks = settings.get("target_nicks", [])
                    self.target_nicks = set(nick.strip().lower() for nick in target_nicks if nick)
                    self.active_model = settings.get("active_model", None)
                    ocr_lang = settings.get('ocr_language', 'en')
                    # Ensure ocr_language is one of the supported languages
                    supported_langs = ['en', 'ru', 'fr', 'es', 'it', 'de']
                    self.ocr_language = ocr_lang if ocr_lang in supported_langs else 'en'
                    self.current_language = self.ocr_language  # Sync current_language with loaded ocr_language
                    self.show_overlay = settings.get('show_overlay', False)
                    self.autonomous_mode = settings.get('autonomous_mode', False)
                    self.active_character_name = settings.get("active_character_name", None)
                    self.time_per_500_chars = settings.get('time_per_500_chars', 2.0)
                    if self.show_overlay:
                        self._create_overlay()
                    
                    # 1. Notify StatusManager about active model FIRST
                    if self.active_model and hasattr(self.ui, 'status_manager'):
                        self.ui.status_manager.set_active_model(self.active_model)

                    # 2. Load and Notify active character data (sets sync to True)
                    if self.active_character_name:
                        self._load_active_character_data()
                        if hasattr(self.ui, 'status_manager'):
                            self.ui.status_manager.set_active_character(self.active_character_name)
                            self.ui.status_manager.set_character_synced(True)

                    self.log("Settings loaded.", internal=True)
            else:
                self.create_default_settings()
                self.log("Settings file not found, default settings created.", internal=True)
        except Exception as e:
            self.log(f"Error loading settings: {e}", internal=True)
            self.create_default_settings()

    def save_settings(self):
        """
        Save current settings to file.

        Saves the current areas, ignore/target nicks, OCR language, overlay
        settings, autonomous mode, and typing speed to the configured file
        in JSON format.

        Raises:
            Exception: Logs any errors during saving.
        """
        try:
            settings = {
                "areas": self.areas,
                "ignore_nicks": [nick for nick in self.ignore_nicks],
                "target_nicks": [nick for nick in self.target_nicks],
                "ocr_language": self.ocr_language,
                "show_overlay": self.show_overlay,
                "autonomous_mode": self.autonomous_mode,
                "time_per_500_chars": self.time_per_500_chars,
                "active_model": getattr(self, 'active_model', None),
                "active_character_name": getattr(self, 'active_character_name', None)
            }
            os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            self.log("Settings saved.", internal=True)
        except Exception as e:
            self.log(f"Error saving settings: {e}", internal=True)

    def add_nick(self, nick, list_type):
        """
        Add a nick to the specified list.

        Args:
            nick (str): The nick to add.
            list_type (str): The list type ('ignore' or 'target').
        """
        if list_type == "ignore":
            self.ignore_nicks.add(nick)
        elif list_type == "target":
            self.target_nicks.add(nick)
        self.save_settings()
        if self.chat_processor:
            self.chat_processor.update_nicks(self.ignore_nicks, self.target_nicks)
        if nick in self.suggested_nicks:
            self.suggested_nicks.remove(nick)
        self.ui.update_suggested_nicks(list(self.suggested_nicks))
        self.log(f"Nick '{nick}' added to '{list_type}' list.", internal=True)

    def remove_nick(self, nick, list_type):
        """
        Remove a nick from the specified list.

        Args:
            nick (str): The nick to remove.
            list_type (str): The list type ('ignore' or 'target').
        """
        sets = {"ignore": self.ignore_nicks, "target": self.target_nicks}
        if nick in sets[list_type]:
            sets[list_type].remove(nick)
            self.log(f"Nick '{nick}' removed from '{list_type}' list.", internal=True)
        self.save_settings()
        if self.chat_processor:
            self.chat_processor.update_nicks(self.ignore_nicks, self.target_nicks)

    def _load_active_character_data(self):
        """Load data from the active character file and apply to bot."""
        if not getattr(self, 'active_character_name', None):
            return
        
        from .config import CHARACTERS_DIR
        char_file = os.path.join(CHARACTERS_DIR, f"{self.active_character_name}.json")
        if os.path.exists(char_file):
            try:
                with open(char_file, "r", encoding="utf-8-sig") as f:
                    data = json.load(f)
                    # Prioritize character data
                    self.global_prompt = data.get("global_prompt", "")
                    self.character_greeting = data.get("greeting", "")
                    self.character_manifest = data.get("manifest", "")
                    
                    # Log application
                    self.log(f"Applied character profile: {self.active_character_name}", internal=True)
                    self.log(f"- Greeting: {'Yes' if self.character_greeting else 'No'}", internal=True)
                    self.log(f"- Manifest: {len(self.character_manifest)} chars", internal=True)
                    self.log(f"- Global Prompt: {len(self.global_prompt)} chars", internal=True)
            except Exception as e:
                self.log(f"Error loading active character data: {e}", internal=True)

    def change_language(self, language):
        """
        Change the bot's language and update OCR settings.

        Args:
            language (str): The language code to change to.
        """
        self.current_language = language
        
        # Update OCR language based on the selected language
        if language == 'ru':
            self.ocr_language = "eng+rus"
        elif language == 'fr':
            self.ocr_language = "eng+fra"
        elif language == 'es':
            self.ocr_language = "eng+spa"
        elif language == 'it':
            self.ocr_language = "eng+ita"
        elif language == 'de':
            self.ocr_language = "eng+deu"
        else:
            self.ocr_language = "eng"
        
        if self.chat_processor:
            self.chat_processor.ocr_language = self.ocr_language
            
        # Auto-enable translation layer for non-en
        if language != 'en' and not self.use_translation_layer:
            self.use_translation_layer = True
            if hasattr(self, 'ui') and self.ui:
                self.ui.use_translation_var.set(True)
                self.ui.root.after(0, self.ui.update_switch_colors)
            self.log(f"Auto-enabling translation layer for {language}.", internal=True)

        self.save_settings()
        self.log(f"Language changed to: {language}", internal=True)

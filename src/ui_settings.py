"""
UI Settings Module.

This module provides the SettingsMixin class, which handles UI-related
settings management including loading settings, screen area setup, and
language selection.

Classes:
    SettingsMixin: Mixin class for UI settings management.
"""

class SettingsMixin:
    """
    Mixin class for settings management.

    This mixin provides methods for loading and managing UI settings,
    including bot settings synchronization, screen area setup, and
    language selection handling.

    Methods:
        load_settings: Load and synchronize bot settings with UI.
        setup_screen_area: Initiate screen area setup process.
        on_language_selected: Handle language selection from dropdown.
    """

    def load_settings(self):
        """
        Load and synchronize bot settings with UI.

        Loads bot settings and updates UI elements to reflect current
        configuration including autonomous mode, language, and lists.
        """
        self.bot.load_settings()

        self.autonomous_var.set(self.bot.autonomous_mode)
        self.hiwaifu_language_var.set(self.bot.ocr_language)
        self.use_translation_var.set(getattr(self.bot, 'use_translation_layer', False))
        
        # Sync active model to StatusManager
        active_model = getattr(self.bot, 'active_model', None)
        if active_model:
            self.status_manager.set_active_model(active_model)
            
        self.load_lists()

    def setup_screen_area(self):
        """
        Initiate screen area setup process.

        Logs setup instructions and starts the bot's screen area configuration.
        """
        self.log_message("SCREEN AREA SETUP: Follow the instructions...", internal=True)
        self.bot.setup_screen_area()

    def on_language_selected(self, selected_value):
        """
        Handle language selection from dropdown.

        Converts the selected language to lowercase and updates the UI
        and bot language settings.

        Args:
            selected_value (str): Selected language code from dropdown.
        """
        try:
            # Convert back to lowercase for internal use
            lang_code = selected_value.lower()
            self.hiwaifu_language_var.set(lang_code)
            self.on_set_hiwaifu_language()
        except Exception as e:
            self.log_message(f"Error setting language: {e}", internal=True)
"""
Utility Actions Module.

This module provides the UtilityActionsMixin class, which contains utility
methods for bot operations including typing animations, input field management,
chat history clearing, and language changes.

Classes:
    UtilityActionsMixin: Mixin class for utility bot actions.
"""

import asyncio
import pyautogui


class UtilityActionsMixin:
    """
    Mixin class for utility bot actions.

    This mixin provides helper methods for various bot utility functions,
    including anti-AFK typing animations, input field management, and
    language switching operations.

    Methods:
        _type_dot_in_game_loop: Anti-AFK typing animation.
        _erase_input_field: Clear game input field.
        clear_chat_history: Clear browser chat history.
        change_language: Change OCR and interface language.
    """

    async def _type_dot_in_game_loop(self):
        """
        Anti-AFK typing animation in the game.

        Performs a continuous typing animation by clicking the input field,
        typing a dot, and deleting it to prevent being kicked for inactivity.
        Runs until cancelled.

        Raises:
            asyncio.CancelledError: When the animation is cancelled.
            Exception: Logs any errors during the animation.
        """
        input_pos = self.areas.get('input_area')
        if not input_pos: return
        try:
            while True:
                pyautogui.click(input_pos['x'], input_pos['y'])
                pyautogui.write('.')
                await asyncio.sleep(0.5)
                pyautogui.press('backspace')
                await asyncio.sleep(2.0)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.log(f"Ошибка анимации печати: {e}", internal=True)

    async def _erase_input_field(self):
        """
        Clear the input field in the game.

        Selects all text in the input field and deletes it to prepare
        for new input.

        Raises:
            Exception: Logs any errors during field clearing.
        """
        input_pos = self.areas.get('input_area')
        if not input_pos: return
        try:
            pyautogui.click(input_pos['x'], input_pos['y'])
            pyautogui.hotkey('ctrl', 'a')
            await asyncio.sleep(0.1)
            pyautogui.press('backspace')
        except Exception as e:
            self.log(f"Ошибка очистки поля: {e}", internal=True)

    def clear_chat_history(self):
        """
        Clear the chat history memory.
        """
        self.log("Clearing processed messages memory.", internal=True)
        if self.chat_processor:
            self.chat_processor.last_message_hash = None

    def change_language(self, language: str):
        """
        Change the OCR and interface language.

        Updates the OCR language settings and requests language change
        in the browser if the bot is running.

        Args:
            language (str): The language code to switch to.
        """
        self.ocr_language = language.lower()
        self.current_language = self.ocr_language
        self.save_settings()
        self.log(f"OCR language updated to {self.ocr_language}.", internal=True)

        if self.bot_running and self.loop and self.browser_manager:
            self.log(f"Requesting language change in HiWaifu to {language}...", internal=True)
            asyncio.run_coroutine_threadsafe(self.browser_manager.change_language(language), self.loop)
            if self.chat_processor:
                self.chat_processor.ocr_language = self.ocr_language
        else:
            self.log("Bot not running. Language changed locally, will apply on startup.", internal=True)
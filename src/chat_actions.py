"""
Chat Actions Module.

This module provides the ChatActionsMixin class, which handles sending messages
to the game chat, processing hotkey commands, and managing text input interactions.

Classes:
    ChatActionsMixin: Mixin class for chat and messaging actions.
"""

import asyncio
import pyautogui
import pyperclip
import time


class ChatActionsMixin:
    """
    Mixin class for handling chat and messaging actions.

    This mixin provides methods for sending messages to the game with dynamic delays,
    handling hotkey-initiated chats, and processing text-based commands.

    Methods:
        send_to_game: Send a list of messages to the game chat.
        initiate_chat_from_hotkey: Initiate chat from a hotkey press.
        _async_initiate_chat: Async handler for hotkey chat initiation.
        initiate_chat_from_text: Initiate chat from text input.
        _async_initiate_chat_from_text: Async handler for text chat initiation.
        _prepare_message_with_prompt: Prepare message with global prompt and partner nick.
    """

    async def send_to_game(self, messages, force=False):
        """
        Send a list of messages to the game chat with dynamic delays.

        Simulates typing delays between messages based on message length,
        pastes each message into the input field, and sends it.

        Args:
            messages (list): List of message strings to send.
            force (bool): Force sending even if already in progress. Defaults to False.
        """
        input_pos = self.areas.get('input_area')
        if not input_pos: return

        if self.sending_in_progress and not force:
            self.log("Sending already in progress, skipping.", internal=True)
            return

        try:
            self.sending_in_progress = True
            self.log(f"Sending {len(messages)} messages to text field...", internal=True)
            
            # Import constants here to avoid circular imports
            from .config import READING_SPEED_CPM, TYPING_SPEED_CPM

            previous_message_length = 0

            for i, msg in enumerate(messages):
                if not self.bot_running or self.paused:
                    self.log("Sending cancelled (bot stopped or paused).", internal=True)
                    break

                # Calculate delay based on message length
                if i == 0:
                    delay = 0
                    self.log("Delay skipped for first message.", internal=True)
                else:
                    delay = (len(msg) / 500.0) * self.time_per_500_chars
                self.log(f"Delay before sending: {delay:.1f}s (for {len(msg)} characters)", internal=True)

                # Simulate typing if delay > 0
                if delay > 0:
                    start_time = time.time()
                    while time.time() - start_time < delay:
                        if not self.bot_running or self.paused:
                            break

                        pyautogui.click(input_pos['x'], input_pos['y'])

                        pyautogui.write('.')
                        await asyncio.sleep(0.2)
                        pyautogui.press('backspace')

                        remaining_time = delay - (time.time() - start_time)
                        sleep_time = min(remaining_time, 1.5)
                        if sleep_time > 0:
                            await asyncio.sleep(sleep_time)

                # Send message
                pyautogui.click(input_pos['x'], input_pos['y'])
                await asyncio.sleep(0.1)

                try:
                    pyperclip.copy(msg)
                    await asyncio.sleep(0.05)
                    pyautogui.hotkey('ctrl', 'v')
                    await asyncio.sleep(0.1)
                    self.log(f"Text '{msg}' pasted.", internal=True)
                except Exception as e:
                    self.log(f"Error pasting: {e}", internal=True)
                    continue

                pyautogui.press('enter')
                self.log(f"-> {msg}", internal=True)

                previous_message_length = len(msg)
                await asyncio.sleep(0.5)

        except Exception as e:
            self.log(f"Error sending: {e}", internal=True)
        finally:
            self.sending_in_progress = False
            self.log("Sending completed.", internal=True)

    def initiate_chat_from_hotkey(self, key):
        """
        Initiate chat from a hotkey press.

        Retrieves the phrase for the hotkey and starts the async chat process.

        Args:
            key (str): The hotkey identifier.
        """
        if self.bot_running and not self.paused and self.loop:
            asyncio.run_coroutine_threadsafe(self._async_initiate_chat(key), self.loop)
        else:
            self.log("Cannot initiate chat: bot not running or paused.", internal=True)

    async def _async_initiate_chat(self, key):
        """
        Async handler for hotkey chat initiation.

        Processes the hotkey phrase, sends it to the browser, gets response,
        and sends it to the game.

        Args:
            key (str): The hotkey identifier.
        """
        # Block scanning immediately
        if self.sending_in_progress:
            self.log("⚠ Bot busy sending message, command skipped.", internal=True)
            return
        self.sending_in_progress = True

        try:
            phrase = self.get_hotkey_phrase(key)
            if not phrase:
                self.log(f"⚠ No phrase for key {key}", internal=True)
                self.sending_in_progress = False
                return

            message_with_prompt = self._prepare_message_with_prompt(phrase)
            
            # Use the browser-based HiWaifu chat
            response = await self.browser_manager.send_message_and_get_response(message_with_prompt)

            if response:
                self.log(f"Received response for key {key}: {response[:50]}...", internal=True)
                processed_parts = self.chat_processor.process_message(response)
                await self.send_to_game(processed_parts, force=True)
                self.last_message_time = time.time()  # Update activity time after sending
                self.log(f"Response for key {key} inserted into game.", internal=True)
            else:
                self.log(f"Failed to get response for key {key}.", internal=True)
                self.sending_in_progress = False
        except Exception as e:
            self.log(f"Error processing hotkey: {e}", internal=True)
            self.sending_in_progress = False

    def initiate_chat_from_text(self, message):
        """
        Initiate chat from text input.

        Starts the async process for handling a text-based chat request.

        Args:
            message (str): The text message to process.
        """
        if self.bot_running and not self.paused and self.loop:
            asyncio.run_coroutine_threadsafe(self._async_initiate_chat_from_text(message), self.loop)
        else:
            self.log("Cannot initiate chat: bot not running or paused.", internal=True)

    async def _async_initiate_chat_from_text(self, message):
        """
        Async handler for text chat initiation.

        Processes a text message, sends it to the browser, gets response,
        and sends it to the game with input field management.

        Args:
            message (str): The text message to process.
        """
        input_pos = self.areas.get('input_area')
        if not input_pos:
            self.log("ERROR: Input field not configured! Set the text input area (Ctrl+R).",
                     internal=True)
            return

        # Block scanning immediately
        if self.sending_in_progress:
            self.log("⚠ Bot busy sending message, command skipped.", internal=True)
            return
        self.sending_in_progress = True

        try:
            self.log("Activating input field for manual request...", internal=True)
            dot_task = asyncio.create_task(self._type_dot_in_game_loop())
            
            message_with_prompt = self._prepare_message_with_prompt(message)
            
            # Use the browser-based HiWaifu chat
            response = await self.browser_manager.send_message_and_get_response(message_with_prompt)

            dot_task.cancel()
            try:
                await dot_task
            except asyncio.CancelledError:
                pass

            await self._erase_input_field()

            if response:
                self.log(f"Received response: {response[:50]}...", internal=True)
                processed_text = self.chat_processor.process_message(response)
                await self.send_to_game(processed_text, force=True)
                self.last_message_time = time.time()  # Update activity time after sending
                self.log("Response inserted and sent to game.", internal=True)
            else:
                self.log("❌ Error: Failed to get response from HiWaifu.", internal=True)
                self.sending_in_progress = False
        except Exception as e:
            self.log(f"Error processing request: {e}", internal=True)
            self.sending_in_progress = False

    def _prepare_message_with_prompt(self, message):
        """
        Prepare message with global prompt and partner nick.

        Combines the global prompt, current partner nick (if any),
        and the message into a formatted string.

        Args:
            message (str): The base message.

        Returns:
            str: The formatted message with prompt and nick.
        """
        prompt = self.global_prompt.strip()
        message = message.strip()

        prefix = ""
        if self.current_partner_nick:
            prefix = f"{self.current_partner_nick}: "

        if prompt:
            return f"{prompt} {prefix}{message}"
        return f"{prefix}{message}"
"""
Bot Module.

This module provides the ChatBot class, the main controller for the chatbot
application. It manages the bot's lifecycle, integrates various mixins for
settings, setup, actions, and handles the main event loop for interacting
with the game and browser.

Classes:
    ChatBot: Main chatbot class inheriting from multiple mixins.
"""

# Imports of necessary libraries and modules
import asyncio
import pyautogui
import threading
import json
import os
import re
import pyperclip
import pytesseract
import time
import traceback
from .config import (SETTINGS_FILE, TESSERACT_PATH, SCAN_INTERVAL_IDLE, SCAN_INTERVAL_ACTIVE,
                    HOTKEY_PHRASES_FILE, OVERLAY_COLOR, OVERLAY_THICKNESS, INPUT_SQUARE_SIZE,
                    PARTNERSHIP_COLOR, POSE_COLOR, CLOSE_BTN_COLOR,
                    CLOSE_BTN_IMAGE_PATH)
from .chat_processor import ChatProcessor
from .utils import extract_text_from_image, extract_digits_from_image
from .translation_manager import TranslationManager
from .rag.memory_manager import MemoryManager
from .chat_memory import ChatMemory

# Import mixins
from .bot_settings import BotSettingsMixin
from .bot_setup import BotSetupMixin
from .partnership_actions import PartnershipActionsMixin
from .autonomous_actions import AutonomousActionsMixin
from .pose_actions import PoseActionsMixin
from .chat_actions import ChatActionsMixin
from .utility_actions import UtilityActionsMixin
# BrowserManager removed (Migrating to Local LLM)


class ChatBot(BotSettingsMixin, BotSetupMixin, PartnershipActionsMixin, AutonomousActionsMixin, PoseActionsMixin, ChatActionsMixin, UtilityActionsMixin):
    """
    Main chatbot class managing interaction with the game and browser.

    This class inherits from multiple mixins to provide comprehensive bot
    functionality including settings management, setup, partnerships, autonomous
    actions, poses, chat handling, and utilities. It controls the bot's lifecycle,
    threading, and main event loop.

    Attributes:
        ui: User interface object for interaction.
        areas (dict): Screen area coordinates.
        ignore_nicks (set): Set of nicks to ignore.
        target_nicks (set): Set of target nicks.
        suggested_nicks (set): Suggested nicks from chat.
        auto_added_nicks_session (set): Auto-added nicks in session.
        current_partner_nick (str): Current partner nick.
        auto_lang_switch (bool): Auto language switching flag.
        chat_processor: Chat processing object.
        # Migrated to local LLM: browser_manager removed
        bot_running (bool): Bot running flag.
        scanning_active (bool): Scanning active flag.
        bot_thread: Bot thread object.
        setup_step (int): Current setup step.
        setup_coords (dict): Setup coordinates.
        selection_window: Selection window object.
        selecting_area (bool): Selecting area flag.
        selection_start: Selection start point.
        current_temp_window: Current temporary window.
        ocr_language (str): OCR language.
        loop: Asyncio event loop.
        hotkey_phrases (dict): Hotkey phrases.
        global_prompt (str): Global prompt.
        overlay_window: Overlay window object.
        show_overlay (bool): Show overlay flag.
        autonomous_mode (bool): Autonomous mode flag.
        partnership_active (bool): Partnership active flag.
        last_message_time (float): Last message timestamp.
        scanning_partnerships (bool): Scanning partnerships flag.
        scanning_poses (bool): Scanning poses flag.
        sending_in_progress (bool): Sending in progress flag.
        last_pose_action_time (float): Last pose action timestamp.
        last_partnership_action_time (float): Last partnership action timestamp.
        last_clothes_action_time (float): Last clothes action timestamp.
        last_clothes_loc: Last clothes button location.
        paused (bool): Paused flag.
        discard_current (bool): Discard current flag.
        pause_start_time (float): Pause start time.
        first_message_sent (bool): First message sent flag.
        initial_check_done (bool): Initial check done flag.

    Methods:
        __init__: Initialize the bot.
        log: Log messages to UI.
        start_bot: Start the bot.
        pause_bot: Pause the bot.
        resume_bot: Resume the bot.
        stop_bot: Stop the bot.
        _run_async_wrapper: Run async wrapper.
        _bot_loop: Main bot loop.
        _main_loop: Main processing loop.
    """

    def __init__(self, ui, ocr_language="eng+rus"):
        """
        Initialize the main components of the bot.

        Sets up all necessary attributes, loads settings, initializes mixins,
        and prepares the bot for operation.

        Args:
            ui: User interface object for interaction.
            ocr_language (str): Default OCR language. Defaults to "eng+rus".
        """
        self.ui = ui
        # Dictionary for storing screen area coordinates
        self.areas = {"chat_area": None, "input_area": None, "game_window_name": "Your game window name"}
        # Sets for nicks to ignore or track
        self.ignore_nicks = set()
        self.target_nicks = set()
        self.suggested_nicks = set()
        self.auto_added_nicks_session = set()
        self.current_partner_nick = None
        self.current_language = 'en'
        self.chat_processor = None
        # Migrated to local LLM: browser_manager removed
        self.bot_running = False  # Flag for controlling main bot loop
        self.scanning_active = False  # Flag for controlling chat scanning
        self.bot_thread = None  # Thread for async loop
        self.setup_step = 0  # Current setup step
        self.setup_coords = {}  # Coordinates captured during setup
        self.selection_window = None
        self.selecting_area = False
        self.selection_start = None
        self.current_temp_window = None  # Current temporary message window
        self.ocr_language = ocr_language
        self.loop = None  # Asyncio event loop object

        # Language switching state
        self.lang_consistency_counter = 0
        self.pending_new_language = None
        self.translation_manager = TranslationManager()

        self.hotkey_phrases = {}
        self.global_prompt = ""
        self.character_manifest = ""
        self.character_greeting = ""
        self.use_translation_layer = False
        self._load_hotkey_settings()
        
        # RAG Memory System
        self.memory_manager = None
        self.active_character_name = None
        
        # Chat Memory System (Short-term memory with summarization)
        self.chat_memory = ChatMemory(recent_limit=12, summary_trigger_limit=20)

        # Set path to Tesseract executable
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

        # New: For overlay
        self.overlay_window = None
        self.show_overlay = False

        # --- Autonomous Mode Variables ---
        self.autonomous_mode = False
        self.partnership_active = False
        self.last_message_time = time.time()

        # Scanning status variables
        self.scanning_partnerships = False
        self.scanning_poses = False

        # Sending status variable
        self.sending_in_progress = False

        # Pose action cooldown
        self.last_pose_action_time = 0

        # Partnership action cooldown
        self.last_partnership_action_time = 0

        # Clothes action cooldown
        self.last_clothes_action_time = 0

        # Last clothes button location
        self.last_clothes_loc = None

        # Pause status
        self.paused = False
        self.discard_current = False
        self.pause_start_time = None
        self.first_message_sent = False
        self.initial_check_done = False

        # Pose naming state
        self.waiting_for_pose_name = False
        self.pending_pose_screenshot = None
        self.pending_accept_location = None

        # --- Hooker Mod State ---
        self.hooker_current_state = None  # None, 'FREE', 'WAITING_PAYMENT', 'PAID'
        self.hooker_timer_end = 0
        self.hooker_initial_amount = 0
        self.hooker_wait_start_time = 0

        # Add new areas
        self.areas.update({
            "partnership_area": None,
            "pose_area": None,
            "close_partnership_btn": None,  # Now this is search area
            "clothes_menu_area": None,
            "stop_sex_area": None,
            "put_on_all_point": None, # Point to click for Put On All button
            "amount_area": None
        })

    def clear_chat_history(self):
        """
        Clear bot conversation history in local LLM context and UI.
        """
        self.clear_all_memory()

    def log(self, message, internal=False):
        """
        Log messages to the UI and file.

        Args:
            message (str): The message to log.
            internal (bool): Whether this is an internal log message. Defaults to False.
        """
        # Log to file
        import logging
        logging.info(message)
        # Log to UI
        self.ui.root.after(0, self.ui.log_message, message, internal)

    def _initialize_hooker_session(self):
        """Initialize state for a new hooker mod session."""
        if getattr(self, 'hooker_mod_enabled', False):
            self.hooker_current_state = 'FREE'
            self.hooker_timer_end = time.time() + (self.hooker_free_mins * 60)
            self.log(f"Hooker Mod: Free time started ({self.hooker_free_mins} mins).", internal=True)
        else:
            self.hooker_current_state = None

    def start_bot(self):
        """
        Start the bot.

        Initializes and starts the bot thread, resets partnership state,
        and updates UI status. Starts in paused state.
        """
        if self.bot_running:
            return
        
        # Check Ollama status before starting
        if hasattr(self.ui, 'status_manager'):
            ollama_status = self.ui.status_manager.get_ollama_status()
            active_model = self.ui.status_manager.get_active_model()
            
            if ollama_status != "Running":
                self.log("Cannot start bot: Ollama is not running. Please start Ollama first.", internal=True)
                return
            
            if not active_model:
                self.log("Cannot start bot: No active model selected. Please download and activate a model first.", internal=True)
                return
        
        self.bot_running = True
        self.scanning_active = False
        self.paused = True  # Start in paused state
        # Reset partnership state to avoid retaining state from previous runs
        self.partnership_active = False
        self.current_partner_nick = None
        self.auto_added_nicks_session.clear()
        self.initial_check_done = False
        self.bot_thread = threading.Thread(target=self._run_async_wrapper, daemon=True)
        self.bot_thread.start()
        self.log("Bot started. Press F2 to begin scanning.", internal=True)
        self.ui.update_status("Waiting for F2")
        self.ui.update_buttons_state(True, paused=True)

    def pause_bot(self):
        """
        Pause the bot.

        Stops scanning, sets paused flag, and updates UI status.
        """
        if self.bot_running and self.scanning_active:
            self.scanning_active = False
            self.paused = True
            self.discard_current = True
            self.pause_start_time = time.time()
            self.log("Scanning paused. Press F2 to resume.", internal=True)
            self.ui.update_status("Paused")
            self.ui.update_buttons_state(True, paused=True)

    def resume_bot(self):
        """
        Resume the bot.

        Restarts scanning, adjusts message timing for paused duration,
        and checks for existing partnerships.
        """
        if self.bot_running and not self.scanning_active:
            self.scanning_active = True
            self.paused = False
            if self.pause_start_time is not None:
                paused_duration = time.time() - self.pause_start_time
                self.last_message_time += paused_duration
                self.pause_start_time = None
            self.log("Scanning started.", internal=True)
            self.ui.update_status("Running")
        self.ui.update_buttons_state(True, paused=False)
        # Check for existing partnership when starting scanning
        if os.path.exists(CLOSE_BTN_IMAGE_PATH):
            try:
                search_area = self.areas.get('close_partnership_btn')
                if search_area:
                    location = pyautogui.locateCenterOnScreen(
                        CLOSE_BTN_IMAGE_PATH,
                        confidence=0.9,
                        region=(search_area['x'], search_area['y'], search_area['width'], search_area['height'])
                    )
                    if location:
                        self.partnership_active = True
                        self.log("Existing partnership detected when starting scanning.", internal=True)
                else:
                    self.log("Close partnership button area not configured, skipping partnership check.", internal=True)
            except Exception as e:
                self.log("No existing partnership detected.", internal=True)

    def stop_bot(self, wait=True):
        """
        Stop the bot.

        Stops all bot operations, destroys overlay, clears memory,
        and updates UI status.

        Args:
            wait (bool): Whether to wait for the bot thread to finish.
        """
        if not self.bot_running:
            return
        self.bot_running = False
        self.scanning_active = False
        self.paused = False
        self._destroy_overlay()
        self.log("Stopping bot...", internal=True)

        # Memory cleanup
        self.target_nicks.clear()
        self.suggested_nicks.clear()
        self.auto_added_nicks_session.clear()
        self.current_partner_nick = None
        self.partnership_active = False
        self.waiting_for_pose_name = False
        self.pending_pose_screenshot = None
        self.pending_accept_location = None
        self.log("Bot memory cleared (except ignore list).", internal=True)
        
        # Clear RAG memory manager
        self.memory_manager = None

        if wait and self.bot_thread and self.bot_thread.is_alive():
            self.bot_thread.join(timeout=1)
        self.log("Bot stopped.", internal=True)
        self.ui.update_status("Not running")
        self.ui.update_buttons_state(False)
    
    def initialize_memory_manager(self, character_name: str, character_path: str):
        """
        Initialize the RAG memory manager for the active character.
        
        Args:
            character_name (str): Name of the character.
            character_path (str): Path to the character JSON file.
        """
        try:
            from .config import CHARACTERS_DIR
            self.active_character_name = character_name
            
            # Create memory manager
            self.memory_manager = MemoryManager(character_name, character_path)
            
            # Load or create index
            success = self.memory_manager.load_or_create_index()
            
            if success:
                card_count = self.memory_manager.get_card_count()
                self.log(f"Memory manager initialized for '{character_name}' with {card_count} cards.", internal=True)
            else:
                self.log(f"Failed to initialize memory manager for '{character_name}'.", internal=True)
                self.memory_manager = None
                
        except Exception as e:
            self.log(f"Error initializing memory manager: {e}", internal=True)
            self.memory_manager = None
    
    def add_chat_message(self, role: str, content: str):
        """
        Add a message to chat memory and handle summarization.
        
        Args:
            role (str): Message role ("user" or "assistant").
            content (str): Message content.
        """
        self.chat_memory.add_message(role, content)
        
        # Check if summarization is needed
        if self.chat_memory.is_ready_for_summarization():
            self._handle_summarization()
    
    def _handle_summarization(self):
        """Handle automatic summarization of conversation."""
        pending = self.chat_memory.get_pending_summarization()
        if not pending:
            return
        
        try:
            # Create summarization prompt
            summarization_prompt = pending['prompt']
            
            # Generate summary using Ollama
            summary_response = self.ui.ollama_manager.generate_response(
                summarization_prompt,
                system_prompt="You are a helpful assistant that summarizes conversations.",
                manifest=""
            )
            
            if summary_response:
                # Process the summary
                self.chat_memory.process_summarization_result(summary_response)
                self.log(f"Conversation summarized. Summary length: {len(self.chat_memory.summary)} chars", internal=True)
            else:
                self.log("Failed to generate conversation summary.", internal=True)
                
        except Exception as e:
            self.log(f"Summarization failed: {e}", internal=True)
    
    def get_chat_context(self) -> str:
        """
        Get chat context including summary and recent messages.
        
        Returns:
            str: Formatted chat context.
        """
        return self.chat_memory.get_context_for_llm()
    
    def clear_all_memory(self):
        """Clear all memory systems (RAG, chat memory, and Ollama history)."""
        # Clear RAG memory
        self.memory_manager = None
        self.active_character_name = None
        
        # Clear chat memory
        self.chat_memory.clear()
        
        # Clear Ollama history
        self.ui.ollama_manager.clear_history()
        
        # Clear UI chat messages
        if hasattr(self.ui, 'chat_messages'):
            self.ui.chat_messages = []
            if hasattr(self.ui, '_refresh_chat_display'):
                self.ui.root.after(0, self.ui._refresh_chat_display)
        
        self.log("All memory systems cleared (RAG, chat memory, and UI).", internal=True)
        self.first_message_sent = False

    def _run_async_wrapper(self):
        """
        Run the async wrapper for the bot thread.

        Creates a new asyncio event loop and runs the main bot loop.
        """
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._bot_loop())

    def translate_user_input(self, text):
        """Translate user input to English if translation layer is active."""
        if not self.use_translation_layer or self.current_language == 'en':
            return text
        
        self.log(f"Translating user input from {self.current_language}...", internal=True)
        return self.translation_manager.translate_to_en(text, self.current_language)

    def translate_bot_response(self, text):
        """Translate bot response from English to current language if active."""
        if not self.use_translation_layer or self.current_language == 'en':
            return text

        self.log(f"Translating bot response to {self.current_language}...", internal=True)
        return self.translation_manager.translate_from_en(text, self.current_language)

    def handle_language_detection(self, message):
        """
        Detect language of the message and handle switching logic.
        """
        if not self.chat_processor:
            return
            
        detected_lang, is_certain = self.chat_processor.detect_language(message, self.current_language)
        
        if detected_lang != self.current_language:
            # If we are certain about the language (long text or many markers)
            if is_certain:
                self.log(f"High confidence language detection: {detected_lang}. Switching.", internal=True)
                should_switch = True
            else:
                # Otherwise accumulate 'stickiness' counter
                if detected_lang == self.pending_new_language:
                    self.lang_consistency_counter += 1
                else:
                    self.pending_new_language = detected_lang
                    self.lang_consistency_counter = 1

                if self.lang_consistency_counter >= 2:
                    self.log(f"Sustained language change detected: {detected_lang}. Switching.", internal=True)
                    should_switch = True
                else:
                    should_switch = False
                    self.log(f"Potential language change ({detected_lang}) detected. Waiting for confirmation ({self.lang_consistency_counter}/2).", internal=True)
            
            if should_switch:
                self.current_language = detected_lang
                self.lang_consistency_counter = 0
                self.pending_new_language = None
                
                # Update UI Var
                if hasattr(self.ui, 'ocr_language_var'):
                    self.ui.ocr_language_var.set(detected_lang)
                if hasattr(self.ui, 'language_dropdown'):
                    self.ui.root.after(0, lambda lang=detected_lang: self.ui.language_dropdown.set(lang))
                
                # Auto-enable translation layer for non-en
                if detected_lang != 'en' and not self.use_translation_layer:
                    self.use_translation_layer = True
                    if hasattr(self.ui, 'use_translation_var'):
                        self.ui.use_translation_var.set(True)
                        self.ui.root.after(0, self.ui.update_switch_colors)
                    self.log(f"Auto-enabling translation layer for {detected_lang}.", internal=True)
                
                # Update OCR language dynamically
                if detected_lang == 'ru':
                    self.ocr_language = "eng+rus"
                elif detected_lang == 'fr':
                    self.ocr_language = "eng+fra"
                elif detected_lang == 'es':
                    self.ocr_language = "eng+spa"
                elif detected_lang == 'it':
                    self.ocr_language = "eng+ita"
                elif detected_lang == 'de':
                    self.ocr_language = "eng+deu"
                else:
                    self.ocr_language = "eng"
                
                if self.chat_processor:
                    self.chat_processor.ocr_language = self.ocr_language
        else:
            # Reset counter if language matches current
            self.lang_consistency_counter = 0
            self.pending_new_language = None

        # Always ensure translation layer is enabled if we are in a non-en language
        if self.current_language != 'en' and not self.use_translation_layer:
            self.use_translation_layer = True
            if hasattr(self, 'ui') and self.ui:
                self.ui.use_translation_var.set(True)
                self.ui.root.after(0, self.ui.update_switch_colors)
            self.log(f"Auto-enabling translation layer for {self.current_language}.", internal=True)

    def _get_memory_context(self, query: str) -> str:
        """
        Get memory context from RAG system.
        
        Args:
            query (str): User message to search memory for.
            
        Returns:
            str: Formatted memory context or empty string.
        """
        try:
            if not self.memory_manager or not self.active_character_name:
                return ""
            
            # Search memory for relevant cards
            relevant_cards = self.memory_manager.search(query, k=3)
            
            if not relevant_cards:
                return ""
            
            # Format context for LLM
            context_lines = ["Relevant character information:"]
            for i, card in enumerate(relevant_cards, 1):
                context_lines.append(f"{i}. {card}")
            
            return "\n".join(context_lines)
            
        except Exception as e:
            self.log(f"Memory search failed: {e}", internal=True)
            return ""

    async def get_translated_response(self, message, author=None):
        """
        Unified method to handle language detection, translation, LLM call, and response translation.
        Used by both scanning loop and UI chat.
        """
        # 1. Detection and Auto-Switching
        self.handle_language_detection(message)
        
        # 2. Translate User Input
        translated_input = self.translate_user_input(message)
        
        # 3. Get Memory Context (RAG)
        memory_context = self._get_memory_context(translated_input)
        
        # 4. Get Chat Context (Short-term memory with summarization)
        chat_context = self.get_chat_context()
        
        # 5. Format for LLM
        nick = author if author else self.current_partner_nick
        llm_input = f"{nick}: {translated_input}" if nick else translated_input
        
        # 6. Include memory context if available
        if memory_context:
            llm_input = f"{memory_context}\n\nUser: {llm_input}"
            self.log(f"LLM Input with Memory Context: {repr(llm_input)}", internal=True)
        else:
            self.log(f"LLM Input (Translated): {repr(llm_input)}", internal=True)
        
        # 7. Include chat context if available
        if chat_context:
            llm_input = f"{chat_context}\n\n{llm_input}"
            self.log(f"LLM Input with Chat Context: {repr(llm_input)}", internal=True)
        
        # 8. Generate Response
        response = await self.ui.ollama_manager.generate_response(
            llm_input,
            system_prompt=self.global_prompt,
            manifest=self.character_manifest
        )
        
        if response:
            # 9. Translate Response Back
            translated_response = self.translate_bot_response(response)
            
            # 10. Add bot response to chat memory
            self.add_chat_message("assistant", translated_response)
            
            return translated_response
        return None


    async def _bot_loop(self):
        """
        Main bot loop optimized for local LLM operation.
        
        Initializes processor and runs the main processing loop.
        """
        self.chat_processor = ChatProcessor(self.ignore_nicks, self.target_nicks, self.log, self.ocr_language)

        while self.bot_running:
            try:
                # Start main process
                await self._main_loop()

            except Exception as e:
                if not self.bot_running:
                    break  # If stopped manually, don't restart

                self.log(f"Loop error: {e}. Restarting in 5s...", internal=True)
                import traceback
                self.log(traceback.format_exc(), internal=True)
                await asyncio.sleep(5)  # Pause before recovery attempt

        self.log("Bot loop finished.", internal=True)

    async def _main_loop(self):
        """
        Main processing loop.

        Continuously monitors chat for new messages, handles autonomous actions,
        manages partnerships, and processes responses. Runs while bot is active.
        """
        while self.bot_running:
            # Check partnership status only when not paused
            if not self.paused and os.path.exists(CLOSE_BTN_IMAGE_PATH):
                try:
                    search_area = self.areas.get('close_partnership_btn')
                    if search_area:
                        # Use specific search area for more accurate detection
                        location = pyautogui.locateCenterOnScreen(
                            CLOSE_BTN_IMAGE_PATH,
                            confidence=0.9,
                            region=(search_area['x'], search_area['y'], search_area['width'], search_area['height'])
                        )
                        if location:
                            if not self.partnership_active:
                                self.log("Partnership found.", internal=True)
                                self.partnership_active = True
                                self.last_message_time = time.time()
                                self._initialize_hooker_session()
                        else:
                            if self.partnership_active:
                                self.log("Partnership closed.", internal=True)
                                await self._close_partnership()
                                continue
                    else:
                        self.log("Close partnership button area not configured, skipping partnership status check.", internal=True)
                except Exception as e:
                    # Treat exceptions as button not found (UI changes, region issues, etc.)
                    if self.partnership_active:
                        self.log("Partnership closed.", internal=True)
                        await self._close_partnership()
                        self.hooker_current_state = None
                        continue

            # Chat scanning only happens during active partnerships
            if not self.partnership_active and not self.paused:
                # Scan for partnerships when no partnership is active and not paused
                await self._scan_for_partnership()
                await asyncio.sleep(SCAN_INTERVAL_IDLE)
                continue

            if not ((self.scanning_active or self.autonomous_mode) and not self.paused):
                await asyncio.sleep(SCAN_INTERVAL_IDLE)
                continue

            if not ((self.scanning_active or self.autonomous_mode) and not self.paused):
                await asyncio.sleep(SCAN_INTERVAL_IDLE)
                continue

            if not all(self.areas.get(key) for key in ["chat_area", "input_area"]):
                self.log("ERROR: Chat or input areas not configured!", internal=True)
                await asyncio.sleep(5)
                continue

            if self.sending_in_progress:
                await asyncio.sleep(SCAN_INTERVAL_IDLE)
                continue


            try:
                chat_area = self.areas['chat_area']
                screenshot = pyautogui.screenshot(
                    region=(chat_area['x'], chat_area['y'], chat_area['width'], chat_area['height']))
                text = extract_text_from_image(screenshot, self.ocr_language)
                new_messages, potential_new_nicks = self.chat_processor.get_new_messages(text)
                self.suggested_nicks.update(potential_new_nicks)
                self.ui.root.after(0, self.ui.update_suggested_nicks, list(self.suggested_nicks))

                if self.discard_current:
                    new_messages = []
                    self.discard_current = False

                # If partnership is active, automatically add new nicks from chat to tracked
                if self.partnership_active and potential_new_nicks:
                    for nick in potential_new_nicks:
                        normalized_nick = self.chat_processor._normalize_nick(nick)
                        if normalized_nick and normalized_nick not in self.ignore_nicks and normalized_nick not in self.target_nicks:
                            self.target_nicks.add(normalized_nick)
                            self.chat_processor.update_nicks(self.ignore_nicks, self.target_nicks) # Update lists in processor
                            self.log(f"Automatically added partner from chat: {normalized_nick}", internal=True)
                            self.current_partner_nick = normalized_nick # Update current partner
                            self.auto_added_nicks_session.add(normalized_nick) # Mark that partner was added automatically

                # Handle Hooker Mod logic
                await self._handle_hooker_logic()

                if new_messages:
                    message = new_messages[0]['message']
                    author = new_messages[0].get('author')

                    # Check if waiting for pose name
                    if self.waiting_for_pose_name and author:
                        # Add delay to allow full multi-line message to be captured
                        await asyncio.sleep(1.0)
                        # Re-scan the chat area for the full message
                        chat_area = self.areas['chat_area']
                        updated_screenshot = pyautogui.screenshot(
                            region=(chat_area['x'], chat_area['y'], chat_area['width'], chat_area['height']))
                        updated_text = extract_text_from_image(updated_screenshot, self.ocr_language)
                        updated_messages, _ = self.chat_processor.get_new_messages(updated_text)
                        if updated_messages and updated_messages[0]['author'] == author:
                            message = updated_messages[0]['message']
                        pose_name = message.strip()
                        self.log(f"Received pose name from user: {pose_name}", internal=True)
                        
                        # Add pose name message to chat memory
                        self.add_chat_message("user", pose_name)
                        if pose_name and self.pending_accept_location:
                            self.last_pose_action_time = time.time()
                            await self._save_named_pose_screenshot(pose_name, self.pending_pose_screenshot)
                            await asyncio.sleep(0.5)  # Give time for saving to complete
                            self.log(f"Pose named and accepted (already clicked): {pose_name}", internal=True)
                            
                            # Notify AI about the new pose and wait for response
                            notification_msg = f"{self.get_pose_message()} {pose_name}"
                            self.log(f"Notifying LLM about the new pose: {notification_msg}", internal=True)
                            
                            response = await self.ui.ollama_manager.generate_response(
                                notification_msg,
                                system_prompt=self.global_prompt,
                                manifest=self.character_manifest
                            )
                            if response:
                                processed_parts = self.chat_processor.process_message(response)
                                await self.send_to_game(processed_parts, force=True)
                                self.log("Pose response from LLM inserted into game.", internal=True)
                            else:
                                self.log("Failed to get pose response from LLM.", internal=True)
                            
                        self.waiting_for_pose_name = False
                        self.pending_pose_screenshot = None
                        self.pending_accept_location = None
                        await asyncio.sleep(SCAN_INTERVAL_ACTIVE)
                        continue

                    # Update current partner if recognized
                    if author:
                        self.current_partner_nick = author

                    # Add user message to chat memory
                    self.add_chat_message("user", message)

                    # Automatic language switching based on detected language
                    self.handle_language_detection(message)

                    # --- Processing Message ---
                    llm_message = message

                    if not self.first_message_sent:
                        # Use character greeting from profile
                        response = self.character_greeting if self.character_greeting else "Hello!"
                        self.first_message_sent = True
                        self.log(f"Sending initial character greeting: {repr(response)}", internal=True)
                    else:
                        dot_task = asyncio.create_task(self._type_dot_in_game_loop())
                        
                        # Add scanned message to UI
                        if hasattr(self.ui, '_add_message'):
                            self.ui.root.after(0, lambda a=author, m=message: self.ui._add_message(a, m, is_bot=False))

                        # Use consolidated translation and response generation
                        response = await self.get_translated_response(message, author=author)

                        dot_task.cancel()
                        try:
                            await dot_task
                        except asyncio.CancelledError:
                            pass
                        await self._erase_input_field()

                    if response:
                        self.log(f"Final response to send: {repr(response)}", internal=True)
                        processed_parts = self.chat_processor.process_message(response)
                        await self.send_to_game(processed_parts, force=True)
                        self.last_message_time = time.time()  # Update activity time after sending
                        
                        # Add bot response to UI
                        if hasattr(self.ui, '_add_message'):
                            active_name = getattr(self, 'active_character_name', "Bot")
                            self.ui.root.after(0, lambda n=active_name, r=response: self.ui._add_message(n, r, is_bot=True))
                    else:
                        self.log("Failed to get response from local LLM.", internal=True)

                    await asyncio.sleep(SCAN_INTERVAL_ACTIVE)
                else:
                    await asyncio.sleep(SCAN_INTERVAL_IDLE)

                # Scan for poses and clothes when partnership is active and not paused
                if self.partnership_active and not self.paused:
                    await self._scan_for_poses()
                    await self._scan_for_gifts()
                    await self._scan_for_clothes_requests()

            except Exception as e:
                self.log(f"Error in main loop: {traceback.format_exc()}", internal=True)
                await asyncio.sleep(1)

    async def _handle_hooker_logic(self):
        """
        Handle the Hooker Mod state machine logic.

        Manages the states for free time, waiting for payment, and paid time,
        including timer checks, payment detection, and sending messages.
        """
        if not getattr(self, 'hooker_mod_enabled', False) or not self.partnership_active:
            return

        current_time = time.time()

        if self.hooker_current_state in ['FREE', 'PAID']:
            if current_time >= self.hooker_timer_end:
                self.log("Hooker Mod: Time is up! Asking for payment.", internal=True)
                if self.hooker_warning_message:
                    await self.send_to_game([self.hooker_warning_message], force=True)

                # Start waiting for payment
                self.hooker_current_state = 'WAITING_PAYMENT'
                self.hooker_wait_start_time = current_time

                # Capture initial amount for comparison
                amount_area = self.areas.get('amount_area')
                if amount_area:
                    screenshot = pyautogui.screenshot(region=(amount_area['x'], amount_area['y'], amount_area['width'], amount_area['height']))
                    self.hooker_initial_amount = extract_digits_from_image(screenshot)
                    self.log(f"Hooker Mod: Initial amount captured: {self.hooker_initial_amount}", internal=True)
                else:
                    self.log("ERROR: Amount area not configured! Closing partnership.", internal=True)
                    await self._close_partnership()
                    self.hooker_current_state = None
                    return

        if self.hooker_current_state == 'WAITING_PAYMENT':
            # 1. Check for timeout
            if current_time - self.hooker_wait_start_time > self.hooker_payment_wait_time:
                self.log("Hooker Mod: Payment timeout. Closing partnership.", internal=True)
                await self._close_partnership()
                # Clear state
                self.hooker_current_state = None
                return

            # 2. Check for payment
            amount_area = self.areas.get('amount_area')
            if amount_area:
                curr_screenshot = pyautogui.screenshot(region=(amount_area['x'], amount_area['y'], amount_area['width'], amount_area['height']))
                current_amount = extract_digits_from_image(curr_screenshot)

                if current_amount > self.hooker_initial_amount:
                    paid = current_amount - self.hooker_initial_amount
                    self.log(f"Hooker Mod: Payment detected! Amount: {paid}", internal=True)

                    # Calculate extra time
                    # User logic: 600 coins = 30 mins -> 1 coin = 30/600 mins = 0.05 mins
                    # extra_mins = (paid / coins_per_paid) * paid_mins
                    if self.hooker_coins_per_paid > 0:
                        extra_mins = (paid / self.hooker_coins_per_paid) * self.hooker_paid_mins
                    else:
                        extra_mins = self.hooker_paid_mins # Fallback

                    self.log(f"Hooker Mod: Adding {extra_mins:.1f} minutes of paid time.", internal=True)
                    self.hooker_current_state = 'PAID'
                    self.hooker_timer_end = current_time + (extra_mins * 60)

                    # Send success message to LLM for processing
                    if self.hooker_success_message:
                        self.log(f"Sending payment confirmation to LLM: {self.hooker_success_message}", internal=True)
                        response = await self.ui.ollama_manager.generate_response(
                            self.hooker_success_message,
                            system_prompt=self.global_prompt,
                            manifest=self.character_manifest
                        )
                        if response:
                            processed_parts = self.chat_processor.process_message(response)
                            await self.send_to_game(processed_parts, force=True)
                            self.log("Hooker Mod: Payment confirmation processed by LLM and sent to game.", internal=True)
                        else:
                            self.log("Hooker Mod: Failed to get response from LLM.", internal=True)
                    else:
                        self.log("Hooker Mod: No custom payment message configured.", internal=True)

                    # Resume normal flow
                else:
                    # Still waiting, skip other scanning
                    await asyncio.sleep(2) # Sleep longer while waiting for payment
                    return
            else:
                # Should not happen if checked above, but for safety
                await self._close_partnership()
                self.hooker_current_state = None
                return
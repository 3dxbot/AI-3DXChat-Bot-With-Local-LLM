"""
Partnership Actions Module.

This module provides the PartnershipActionsMixin class, which handles
partnership-related actions in the chatbot application. It includes
functionality for scanning partnerships, managing clothes control requests,
stopping sex actions, and closing partnerships.

Classes:
    PartnershipActionsMixin: Mixin class for partnership actions.
"""

import asyncio
import pyautogui
import pytesseract
import re
import time
import pyperclip
import difflib
import os
import math
from .config import CLOSE_BTN_IMAGE_PATH, AGREE_PARTNERSHIP_TILE_PATH, PRIVATE_MESSAGE_BTN_IMAGE_PATH, STOP_SEX_IMAGE_PATH, CLEAN_SPERM_IMAGE_PATH
from .utils import extract_text_from_image


class PartnershipActionsMixin:
    """
    Mixin class for handling partnership-related actions.

    This mixin provides methods for automated partnership management,
    including scanning for partnership tiles, accepting clothes control,
    stopping sex actions, and properly closing partnerships.

    Methods:
        _scan_for_partnership: Scan for partnership tiles and accept them.
        _open_private_chat_via_context_menu: Open private chat via context menu.
        _scan_for_clothes_requests: Scan for clothes control requests.
        _stop_sex: Click the Stop Sex button.
        _close_partnership: Close the current partnership.
        _reset_clothes: Reset clothes by clicking Clothes -> Put On All -> Clothes.
    """

    async def _scan_for_partnership(self):
        """
        Scan for partnership tiles and accept partnerships.

        Searches for partnership agreement tiles on screen, clicks to accept,
        opens private chat, and sends initial greeting message.
        """
        # Cooldown to prevent double-clicks
        if time.time() - self.last_partnership_action_time < 3.0:
            return

        try:
            # 1. Search for partnership tile and click on its edge
            if os.path.exists(AGREE_PARTNERSHIP_TILE_PATH):
                try:
                    # First search for tile confirming partnership
                    # Search across entire screen
                    tile_location = pyautogui.locateOnScreen(
                        AGREE_PARTNERSHIP_TILE_PATH,
                        confidence=0.9
                    )

                    if tile_location:
                        self.log(f"Partnership tile found: {tile_location}", internal=True)

                        # Click on right edge of tile (offset from left edge + width - margin)
                        # tile_location is (left, top, width, height)
                        click_x = tile_location.left + tile_location.width - 20  # 20 pixels from right edge
                        click_y = tile_location.top + tile_location.height // 2

                        self.log(f"Click on tile edge: {click_x}, {click_y}", internal=True)
                        pyautogui.mouseDown(click_x, click_y)
                        time.sleep(0.01)
                        pyautogui.mouseUp(click_x, click_y)
                        self.last_partnership_action_time = time.time()

                        self.partnership_active = True
                        self.last_message_time = time.time()
                        self.log("Partnership accepted (click on tile edge).", internal=True)
                        self._initialize_hooker_session()

                        await asyncio.sleep(2.0)  # Wait for UI update

                        # New logic: Click on nick (left of close button) -> Private Message
                        await self._open_private_chat_via_context_menu()

                        self.scanning_active = True

                        # Notify bot of new partnership

                        input_pos = self.areas.get('input_area')

                        if not input_pos:
                            self.log("ERROR: Input area not configured!", internal=True)
                            return

                        self.sending_in_progress = True

                        try:
                            # 1. Try static greeting first (preferred by user for player-facing start)
                            response = self.character_greeting if hasattr(self, 'character_greeting') and self.character_greeting else ""
                            
                            if not response:
                                # 2. Use Gemini to generate a fresh greeting if no static one exists
                                self.log("Generating fresh greeting via Gemini...", internal=True)
                                greeting_prompt = "You just started a new partnership. Greet the user in your character and start the conversation."
                                
                                response = await self.ui.gemini_manager.generate_response(
                                    greeting_prompt,
                                    system_prompt=self.global_prompt,
                                    manifest=self.character_manifest,
                                    memory_cards=getattr(self, 'memory_cards', None)
                                )

                            if response:
                                self.log(f"Greeting: {repr(response)}", internal=True)
                                processed_parts = self.chat_processor.process_message(response)
                                await self.send_to_game(processed_parts, force=True)
                                self.last_message_time = time.time()
                                self.log("Greeting sent to game.", internal=True)
                                self.first_message_sent = True
                                
                                # Sync to UI
                                if hasattr(self.ui, '_add_message'):
                                    active_name = getattr(self, 'active_character_name', "Bot")
                                    self.ui.root.after(0, lambda n=active_name, r=response: self.ui._add_message(n, r, is_bot=True))
                            else:
                                self.log("Greeting empty, skipping.", internal=True)
                        finally:
                            self.sending_in_progress = False
                        return
                except Exception as e:
                    pass  # Don't log, as absence of tile is normal state

            # 2. If image not found, try OCR (as backup option)
            # OCR across entire screen is too slow and unreliable for "agree".
            # Keep only image search for simplicity and reliability in "zoneless" mode.
            # If user wants OCR, they'll need to bring back zones, but we're simplifying now.

        except Exception as e:
            pass

    async def _open_private_chat_via_context_menu(self):
        """
        Open private chat via context menu.

        Finds the close button (X), clicks left of it (on nick),
        then finds and clicks the 'Private message' button.
        """
        try:
            # 1. Search for cross (Close Button) in configured area
            if os.path.exists(CLOSE_BTN_IMAGE_PATH):
                search_area = self.areas.get('close_partnership_btn')
                if search_area:
                    close_btn_loc = pyautogui.locateCenterOnScreen(
                        CLOSE_BTN_IMAGE_PATH,
                        confidence=0.9,
                        region=(search_area['x'], search_area['y'], search_area['width'], search_area['height'])
                    )
                else:
                    self.log("Close partnership button area not configured, cannot open private chat.", internal=True)
                    return

                if close_btn_loc:
                    # 2. Click left of cross (offset e.g. -20 pixels on X)
                    click_x = close_btn_loc.x - 20
                    click_y = close_btn_loc.y

                    self.log(f"Click on nick (left of X): {click_x}, {click_y}", internal=True)
                    pyautogui.click(click_x, click_y)
                    await asyncio.sleep(1.0)  # Wait for menu to appear

                    # 3. Search for "Private message" button in context menu
                    if os.path.exists(PRIVATE_MESSAGE_BTN_IMAGE_PATH):
                        pm_loc = pyautogui.locateCenterOnScreen(
                            PRIVATE_MESSAGE_BTN_IMAGE_PATH,
                            confidence=0.8
                        )
                        if pm_loc:
                            self.log(f"Private Message button found: {pm_loc}", internal=True)
                            pyautogui.click(pm_loc)
                            self.log("Switched to private chat.", internal=True)
                        else:
                            self.log("Private message button not found.", internal=True)
                    else:
                        self.log(f"File {PRIVATE_MESSAGE_BTN_IMAGE_PATH} not found.", internal=True)

                else:
                    self.log("Failed to find close button (X) for orientation.", internal=True)
            else:
                self.log(f"File {CLOSE_BTN_IMAGE_PATH} not found.", internal=True)

        except Exception as e:
            self.log(f"Error in _open_private_chat_via_context_menu: {e}", internal=True)

    async def _scan_for_clothes_requests(self):
        """
        Scan screen for clothes control requests.

        Searches for clothes control request tiles and accepts them.
        """
        # Cooldown to prevent double-clicks
        if time.time() - self.last_clothes_action_time < 3.0:
            return

        try:
            from .config import ACCEPT_CLOTHES_CONTROL_PATH
            if os.path.exists(ACCEPT_CLOTHES_CONTROL_PATH):
                # Search for clothes request tile across entire screen
                tile_location = pyautogui.locateOnScreen(
                    ACCEPT_CLOTHES_CONTROL_PATH,
                    confidence=0.9
                )

                if tile_location:
                    self.log(f"Clothes control request found: {tile_location}", internal=True)

                    # Click on right edge of tile
                    click_x = tile_location.left + tile_location.width - 20
                    click_y = tile_location.top + tile_location.height // 2

                    self.log(f"Click on Agree (clothes): {click_x}, {click_y}", internal=True)
                    pyautogui.mouseDown(click_x, click_y)
                    time.sleep(0.01)
                    pyautogui.mouseUp(click_x, click_y)
                    self.last_clothes_action_time = time.time()

                    # Don't block, just click and continue
                    await asyncio.sleep(0.5)
        except Exception as e:
            pass

    async def _stop_sex(self):
        """
        Click the Stop Sex button in the game.

        Searches for and clicks the Stop Sex button if found.
        """
        if not os.path.exists(STOP_SEX_IMAGE_PATH):
            self.log(f"Stop Sex button template file not found: {STOP_SEX_IMAGE_PATH}", internal=True)
            return

        try:
            # Search across entire screen
            stop_sex_location = pyautogui.locateCenterOnScreen(
                STOP_SEX_IMAGE_PATH,
                confidence=0.7
            )
            if stop_sex_location:
                self.log(f"Stop Sex button found: {stop_sex_location}, clicking on it.", internal=True)
                await asyncio.sleep(0.2)  # Small delay before click
                pyautogui.click(stop_sex_location)
                self.log("Stop Sex executed.", internal=True)
            else:
                self.log("Stop Sex button not found.", internal=True)
        except Exception as e:
            self.log(f"Error clicking Stop Sex: {e}", internal=True)

    async def _close_partnership(self):
        """
        Close the current partnership using image search for buttons.

        Performs cleanup actions: stops sex, closes partnership, cleans sperm,
        resets clothes, clears chat, and resets language and nicks.
        """
        try:
            # 1. Check for Stop Sex button presence, click if exists
            if os.path.exists(STOP_SEX_IMAGE_PATH):
                try:
                    stop_sex_location = pyautogui.locateCenterOnScreen(
                        STOP_SEX_IMAGE_PATH,
                        confidence=0.7
                    )
                    if stop_sex_location:
                        self.log(f"Stop_sex button found: {stop_sex_location}, clicking on it.", internal=True)
                        await asyncio.sleep(0.2)
                        pyautogui.click(stop_sex_location)
                        self.log("Click on Stop Sex during partnership closure executed.", internal=True)
                        await asyncio.sleep(2.0)
                    else:
                        self.log("Stop_sex button not found, skipping.", internal=True)
                except Exception as e:
                    self.log(f"Error searching for stop_sex button: {e}, skipping.", internal=True)

            # 2. Check for Close Partnership button presence, click if exists
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
                            self.log(f"Close button found: {location}, clicking on it.", internal=True)
                            pyautogui.click(location)
                            self.log("Partnership closed.", internal=True)
                        else:
                            self.log("Close button not found, assuming partnership already closed.", internal=True)
                    else:
                        self.log("Close partnership button area not configured, cannot close partnership.", internal=True)
                except Exception as e:
                    self.log(f"Error searching for close button: {e}, skipping.", internal=True)
            else:
                self.log("Close button file not found, skipping.", internal=True)

            # 3. Check for Clean Sperm button presence, click if exists
            if os.path.exists(CLEAN_SPERM_IMAGE_PATH):
                try:
                    clean_sperm_location = pyautogui.locateCenterOnScreen(
                        CLEAN_SPERM_IMAGE_PATH,
                        confidence=0.7
                    )
                    if clean_sperm_location:
                        self.log(f"Clean_sperm button found: {clean_sperm_location}, clicking on it.", internal=True)
                        await asyncio.sleep(0.2)
                        pyautogui.click(clean_sperm_location)
                        self.log("Click on Clean Sperm during partnership closure executed.", internal=True)
                        await asyncio.sleep(2.0)
                    else:
                        self.log("Clean_sperm button not found, skipping.", internal=True)
                except Exception as e:
                    self.log(f"Error searching for clean_sperm button: {e}, skipping.", internal=True)

            # 4. Then always click clothes -> put on all -> clothes
            await self._reset_clothes()

            # 4. Clear conversation history
            self.ui.gemini_manager.clear_history()
            self.log("Chat history cleared.", internal=True)

            # Cleanup always performed
            if self.current_partner_nick and self.current_partner_nick in self.auto_added_nicks_session:
                self.log(f"Removing automatically added partner nick: {self.current_partner_nick}", internal=True)
                self.remove_nick(self.current_partner_nick, "target")
                self.auto_added_nicks_session.discard(self.current_partner_nick)
                self.current_partner_nick = None
            elif self.current_partner_nick:
                self.log(f"Partnership with {self.current_partner_nick} completed (nick saved).", internal=True)
                self.current_partner_nick = None

            self.partnership_active = False
            self.last_message_time = time.time()
            
            # After clearing chat, change language back to English (default) if not already set
            if self.current_language != 'en':
                self.current_language = 'en'
                # Update UI dropdown - use lowercase to match language_options
                self.ui.root.after(0, lambda: self.ui.language_dropdown.set('en'))
                self.ui.hiwaifu_language_var.set('en')
                self.log("Language set to English (default) in game UI.", internal=True)
                
                # Local language reset. No browser change needed.
                pass
            else:
                self.log("Language already set to English, skipping change.", internal=True)
            
            self.first_message_sent = False
            # Clear nicks database except ignore list
            self.target_nicks.clear()
            self.suggested_nicks.clear()
            self.auto_added_nicks_session.clear()
            # Waiting for new partnership is handled in autonomous loop
            await asyncio.sleep(1.0)

        except Exception as e:
            self.log(f"Error closing partnership: {e}", internal=True)

    async def _reset_clothes(self):
        """
        Reset clothes by clicking Clothes -> Put On All -> Clothes.

        Opens clothes menu, clicks Put On All to reset clothes,
        then closes the menu.
        """
        from .config import CLOTHES_BTN_PATH

        try:
            # 1. Click Clothes Button
            if os.path.exists(CLOTHES_BTN_PATH):
                clothes_loc = pyautogui.locateCenterOnScreen(
                    CLOTHES_BTN_PATH,
                    confidence=0.8
                )
                if clothes_loc:
                    self.log(f"Clothes button found: {clothes_loc}", internal=True)
                    # Save coordinates
                    self.last_clothes_loc = clothes_loc
                    pyautogui.click(clothes_loc)
                    await asyncio.sleep(1.0)  # Wait for menu to open
                else:
                    self.log("Clothes button not found.", internal=True)
                    return  # Cannot proceed

            # 2. Click Put On All Button
            put_on_all_point = self.areas.get('put_on_all_point')
            if put_on_all_point:
                # Wait for the button to appear (about 1 second after clicking clothes)
                await asyncio.sleep(1.0)
                self.log(f"Clicking Put On All at point: ({put_on_all_point['x']}, {put_on_all_point['y']})", internal=True)
                pyautogui.click(put_on_all_point['x'], put_on_all_point['y'])
                self.log("Clothes reset (Put On All).", internal=True)
                await asyncio.sleep(0.5)
            else:
                self.log("Put On All point not configured.", internal=True)
                return

            # 3. Click Clothes Button again to close menu
            if self.last_clothes_loc:
                # Search in the same limited region
                region_left = max(0, self.last_clothes_loc.x - 300)
                region_top = max(0, self.last_clothes_loc.y - 300)
                region_width = 600
                region_height = 600
                clothes_loc = pyautogui.locateCenterOnScreen(
                    CLOTHES_BTN_PATH,
                    confidence=0.7,  # Lower confidence for menu closing
                    region=(region_left, region_top, region_width, region_height)
                )
                if clothes_loc:
                    self.log(f"Closing clothes menu: {clothes_loc}", internal=True)
                    pyautogui.click(clothes_loc)
                    await asyncio.sleep(0.5)
                else:
                    self.log("Clothes button not found to close menu.", internal=True)

        except Exception as e:
            self.log(f"Error resetting clothes: {e}", internal=True)

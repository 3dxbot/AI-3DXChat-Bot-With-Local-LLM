import asyncio
import os
from playwright.async_api import async_playwright, TimeoutError, Error as PlaywrightError
from src.config import (
    HIWAIFU_URL, HIWAIFU_TEXT_AREA, HIWAIFU_BOT_MESSAGE_SELECTOR, HIWAIFU_COPY_BUTTON_SELECTOR,
    STORAGE_STATE_FILE, RIGHT_UP_ARROW, SAVE_AND_START_NEW_CHAT, AGREE_DELETE_CHAT,
    SETTING_GEAR, SELECT_TRANSlATE_LANG, ENG_TRANSLATE_LANG, RU_TRANSLATE_LANG,
    ESP_TRANSLATE_LANG, FRANCE_TRANSLATE_LANG, CHAT_MENU, FIRST_CHAT, HIWAIFU_TYPING_MESSAGE
)


class BrowserManager:
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def log(self, message, internal=True):
        if self.log_callback:
            self.log_callback(message, internal=internal)

    async def start(self):
        """Initializes the browser and opens the page."""
        self.log("Starting browser...")
        self.playwright = await async_playwright().start()

        # Use built-in Chromium Playwright
        self.browser = await self.playwright.chromium.launch(headless=False)

        url_to_open = HIWAIFU_URL
        text_area_selector = HIWAIFU_TEXT_AREA

        if os.path.exists(STORAGE_STATE_FILE):
            self.log("State file found. Loading session...")
            self.context = await self.browser.new_context(storage_state=STORAGE_STATE_FILE,
                                                          permissions=['clipboard-read', 'clipboard-write'])
            self.page = await self.context.new_page()
            await self.page.goto(url_to_open)
            self.log("Page loaded from saved session.")
        else:
            self.log("State file not found. Please log in and enter captcha if required.")
            self.context = await self.browser.new_context(viewport={'width': 1280, 'height': 720},
                                                          permissions=['clipboard-read', 'clipboard-write'])
            self.page = await self.context.new_page()
            await self.page.goto(url_to_open)

            self.log("Waiting for you to complete login...")
            await self.page.locator(text_area_selector).wait_for(state="visible",
                                                                 timeout=120000)

            self.log("Login completed. Saving session state...")
            await self.context.storage_state(path=STORAGE_STATE_FILE)

        self.log("Site is ready to work.")
        return self.page

    async def open_first_chat(self):
        """Open the first chat in the list."""
        try:
            self.log("Opening first chat...")
            await self.page.locator(f"css={CHAT_MENU}").click()
            await asyncio.sleep(1)
            await self.page.locator(f"xpath={FIRST_CHAT}").click()
            await asyncio.sleep(1)
            self.log("✅ First chat opened.")
        except PlaywrightError as e:
            self.log(f"❌ PLAYWRIGHT ERROR: {e}. Reloading page...")
            await self.page.reload()
        except Exception as e:
            self.log(f"❌ ERROR: {e}.")

    async def clear_chat_history(self):
        """Clear the chat history in HiWaifu."""
        try:
            self.log("Clearing chat history...")
            await self.page.locator(f"css={RIGHT_UP_ARROW}").click()
            await asyncio.sleep(1)
            await self.page.locator(f"xpath={SAVE_AND_START_NEW_CHAT}").click()
            await asyncio.sleep(1)
            await self.page.locator(f"css={AGREE_DELETE_CHAT}").click()
            await asyncio.sleep(1)
            await self.page.locator(f"css={CHAT_MENU}").click()
            await asyncio.sleep(1)
            await self.page.locator(f"xpath={FIRST_CHAT}").click()
            await asyncio.sleep(1)
            self.log("✅ Chat history cleared.")
        except PlaywrightError as e:
            self.log(f"❌ PLAYWRIGHT ERROR: {e}. Reloading page...")
            await self.page.reload()
        except Exception as e:
            self.log(f"❌ ERROR: {e}.")

    async def change_language(self, language: str):
        """Change the interface language in HiWaifu."""
        try:
            self.log(f"Changing language to {language}...")

            await self.page.locator(f"xpath={SETTING_GEAR}").click()
            await self.page.wait_for_timeout(500)

            await self.page.get_by_text("Language Settings").click()
            self.log("-> Opened language settings menu.")

            await self.page.locator(f"xpath={SELECT_TRANSlATE_LANG}").click()
            self.log("-> Opened language dropdown.")

            lang_map = {
                'en': ENG_TRANSLATE_LANG,
                'ru': RU_TRANSLATE_LANG,
                'es': ESP_TRANSLATE_LANG,
                'fr': FRANCE_TRANSLATE_LANG
            }
            lang_selector = lang_map.get(language.lower())

            if lang_selector:
                await self.page.locator(f"xpath={lang_selector}").click()
                self.log(f"-> Selected language '{language}'.")
                await self.page.wait_for_timeout(1000)
            else:
                self.log(f"⚠ Unknown language: {language}. Supported: en, ru, es, fr.")
                await self.page.locator(f"xpath={SETTING_GEAR}").click()
                return

            await self.page.locator(f"css={CHAT_MENU}").click()
            await self.page.locator(f"xpath={FIRST_CHAT}").click()

            await self.page.locator(f"css={HIWAIFU_BOT_MESSAGE_SELECTOR}").last.wait_for(state="visible", timeout=30000)
            self.log(f"✅ Language successfully changed to {language}, bot ready to work.")
        except PlaywrightError as e:
            self.log(f"❌ PLAYWRIGHT ERROR: {e}. Reloading page...")
            await self.page.reload()
        except Exception as e:
            self.log(f"❌ ERROR: {e}.")

    async def get_default_message(self):
        """Get the first bot message (default) without sending a request."""
        try:
            self.log("Getting default message...")
            await self.page.locator(f"css={HIWAIFU_BOT_MESSAGE_SELECTOR}").last.wait_for(state="visible", timeout=30000)

            first_bot_message_locator = self.page.locator(f"css={HIWAIFU_BOT_MESSAGE_SELECTOR}").last

            await first_bot_message_locator.hover()
            copy_button_locator = first_bot_message_locator.locator(f"css={HIWAIFU_COPY_BUTTON_SELECTOR}")
            await copy_button_locator.wait_for(state="visible", timeout=10000)
            await copy_button_locator.click()

            copied_text = await self.page.evaluate("navigator.clipboard.readText()")
            self.log("Copied default text: " + copied_text)
            return copied_text
        except PlaywrightError as e:
            self.log(f"❌ PLAYWRIGHT ERROR: {e}. Reloading page...")
            await self.page.reload()
            return None
        except Exception as e:
            self.log(f"❌ ERROR: An unexpected error occurred: {e}.")
            return None

    async def send_message_and_get_response(self, message):
        """Sends a message and waits for a response."""
        try:
            text_area_selector = HIWAIFU_TEXT_AREA
            response_selector = HIWAIFU_BOT_MESSAGE_SELECTOR

            self.log("Inserting message...")
            await self.page.locator(text_area_selector).fill(message)
            self.log("Sending message...")
            await self.page.keyboard.press("Enter")

            self.log("Message sent. Waiting for typing to start...")

            # Wait for typing indicator to appear (short timeout, may appear instantly)
            try:
                await self.page.locator(HIWAIFU_TYPING_MESSAGE).wait_for(state="visible", timeout=3000)
            except:
                pass  # If bot responded instantly and indicator flashed

            # Wait for typing indicator to disappear
            self.log("Waiting for AI to finish typing...")
            await self.page.locator(HIWAIFU_TYPING_MESSAGE).wait_for(state="hidden", timeout=120000)

            self.log("Typing finished. Copying response...")

            # Copy the last message
            last_bot_message = self.page.locator(response_selector).last
            await last_bot_message.hover()
            await last_bot_message.locator(HIWAIFU_COPY_BUTTON_SELECTOR).click()

            copied_text = await self.page.evaluate("navigator.clipboard.readText()")
            self.log("Copied text: " + copied_text)
            return copied_text

        except Exception as e:
            self.log(f"Error sending/receiving response: {e}. Reloading page...")
            await self.page.close()
            raise

    async def close(self):
        """Closes the browser."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
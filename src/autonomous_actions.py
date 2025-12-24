"""
Autonomous Actions Module.

This module provides the AutonomousActionsMixin class, which contains methods
for handling automated bot behaviors in the chatbot application. It manages
scanning for partnerships, poses, and clothes requests, as well as monitoring
partnership status.

Classes:
    AutonomousActionsMixin: Mixin class for autonomous action handling.
"""

import asyncio
import pyautogui
import os
from .config import CLOSE_BTN_IMAGE_PATH


class AutonomousActionsMixin:
    """
    Mixin class for handling autonomous bot actions.

    This mixin provides methods to automate various bot behaviors, such as
    scanning for partnerships, poses, and clothes control requests. It ensures
    the bot operates independently when in autonomous mode.

    Methods:
        _handle_autonomous_actions: Main method to handle autonomous logic.
    """

    async def _handle_autonomous_actions(self):
        """
        Handle the main autonomous actions logic.

        This method orchestrates the bot's autonomous behavior based on the
        current partnership status. When a partnership is active, it scans for
        clothes requests and poses, and monitors for partnership termination.

        The method ensures that sending is not in progress before proceeding
        and updates the UI scanning status accordingly.

        Raises:
            Exception: Logs any errors encountered during autonomous actions.
        """
        if self.sending_in_progress:
            return
        try:
            if self.partnership_active:
                # Scan for clothes requests (same area as partnership)
                await self._scan_for_clothes_requests()
                # Constant check for close button when partnership is active
                search_area = self.areas.get('close_partnership_btn')
                if search_area and os.path.exists(CLOSE_BTN_IMAGE_PATH):
                    try:
                        location = pyautogui.locateCenterOnScreen(
                            CLOSE_BTN_IMAGE_PATH,
                            confidence=0.9,
                            region=(search_area['x'], search_area['y'], search_area['width'], search_area['height'])
                        )
                        if not location:
                            self.log("Close button not found, closing partnership.", internal=True)
                            await self._close_partnership()
                            return
                    except Exception as e:
                        pass
            else:
                # Scan for partnership offers when no partnership is active
                await self._scan_for_partnership()
        except Exception as e:
            self.log(f"Error in autonomous loop: {e}", internal=True)
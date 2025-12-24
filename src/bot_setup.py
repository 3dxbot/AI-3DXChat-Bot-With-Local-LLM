"""
Bot Setup Module.

This module provides the BotSetupMixin class, which handles the setup process
for bot areas (chat, input, poses, etc.) and overlay functionality for visual
guidance during bot operation.

Classes:
    BotSetupMixin: Mixin class for bot setup and overlay management.
"""

import tkinter as tk
import pyautogui
from .config import (OVERLAY_COLOR, OVERLAY_THICKNESS, INPUT_SQUARE_SIZE, POSE_COLOR, POSE_ICON_COLOR, CLOSE_BTN_COLOR, PUT_ON_ALL_COLOR, AMOUNT_COLOR, POSES_DIR)


class BotSetupMixin:
    """
    Mixin class for handling bot setup and overlay.

    This mixin provides methods for setting up screen areas through a step-by-step
    process, creating visual overlays for area indication, and managing selection
    windows for area definition.

    Methods:
        toggle_overlay: Toggle the overlay on/off.
        _create_overlay: Create the overlay window with area rectangles.
        _destroy_overlay: Destroy the overlay window.
        _start_selection: Start the area selection process.
        _update_selection: Update the selection rectangle.
        _stop_selection: Stop the selection process.
        setup_screen_area: Initiate the setup process.
        _handle_setup_key_press: Handle key presses during setup.
    """

    def toggle_overlay(self):
        """
        Toggle the visual overlay on or off.

        Switches the overlay state and creates or destroys the overlay window
        accordingly. Saves the new state to settings.
        """
        self.show_overlay = not self.show_overlay
        if self.show_overlay:
            self._create_overlay()
        else:
            self._destroy_overlay()
        self.log(f"Overlay {'enabled' if self.show_overlay else 'disabled'}.", internal=True)
        self.save_settings()

    def _create_overlay(self):
        """
        Create a fullscreen overlay window with area rectangles.

        Destroys any existing overlay, then creates a new transparent fullscreen
        window with colored rectangles indicating the defined areas (chat, input,
        pose, pose icon, close partnership button).
        """
        if self.overlay_window:
            self._destroy_overlay()

        self.overlay_window = tk.Toplevel(self.ui.root)
        self.overlay_window.attributes('-fullscreen', True)
        self.overlay_window.attributes('-topmost', True)
        self.overlay_window.attributes('-transparentcolor', 'white')
        self.overlay_window.overrideredirect(True)

        canvas = tk.Canvas(self.overlay_window, bg='white', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        chat = self.areas.get('chat_area')
        if chat:
            canvas.create_rectangle(
                chat['x'], chat['y'], chat['x'] + chat['width'], chat['y'] + chat['height'],
                outline=OVERLAY_COLOR, width=OVERLAY_THICKNESS
            )

        input_pos = self.areas.get('input_area')
        if input_pos:
            half = INPUT_SQUARE_SIZE // 2
            canvas.create_rectangle(
                input_pos['x'] - half, input_pos['y'] - half,
                input_pos['x'] + half, input_pos['y'] + half,
                outline=OVERLAY_COLOR, width=OVERLAY_THICKNESS
            )

        pose_area = self.areas.get('pose_area')
        if pose_area:
            canvas.create_rectangle(
                pose_area['x'], pose_area['y'], pose_area['x'] + pose_area['width'], pose_area['y'] + pose_area['height'],
                outline=POSE_COLOR, width=OVERLAY_THICKNESS
            )

        pose_icon_area = self.areas.get('pose_icon_area')
        if pose_icon_area:
            canvas.create_rectangle(
                pose_icon_area['x'], pose_icon_area['y'], pose_icon_area['x'] + pose_icon_area['width'], pose_icon_area['y'] + pose_icon_area['height'],
                outline=POSE_ICON_COLOR, width=OVERLAY_THICKNESS
            )

        close_partnership_area = self.areas.get('close_partnership_btn')
        if close_partnership_area:
            canvas.create_rectangle(
                close_partnership_area['x'], close_partnership_area['y'], close_partnership_area['x'] + close_partnership_area['width'], close_partnership_area['y'] + close_partnership_area['height'],
                outline=CLOSE_BTN_COLOR, width=OVERLAY_THICKNESS
            )

        put_on_all_point = self.areas.get('put_on_all_point')
        if put_on_all_point:
            half = INPUT_SQUARE_SIZE // 2
            canvas.create_rectangle(
                put_on_all_point['x'] - half, put_on_all_point['y'] - half,
                put_on_all_point['x'] + half, put_on_all_point['y'] + half,
                outline=PUT_ON_ALL_COLOR, width=OVERLAY_THICKNESS
            )
        
        amount_area = self.areas.get('amount_area')
        if amount_area:
            canvas.create_rectangle(
                amount_area['x'], amount_area['y'], amount_area['x'] + amount_area['width'], amount_area['y'] + amount_area['height'],
                outline=AMOUNT_COLOR, width=OVERLAY_THICKNESS
            )

        self.overlay_window.update()

    def _destroy_overlay(self):
        """
        Destroy the overlay window.

        Closes and removes the overlay window if it exists.
        """
        if self.overlay_window:
            self.overlay_window.destroy()
            self.overlay_window = None

    def _start_selection(self):
        """
        Start the area selection process.

        Creates a fullscreen transparent window for selecting screen areas
        with a canvas for drawing the selection rectangle.
        """
        if self.selection_window:
            self._stop_selection()

        self.selection_window = tk.Toplevel(self.ui.root)
        self.selection_window.attributes('-fullscreen', True)
        self.selection_window.attributes('-topmost', True)
        self.selection_window.attributes('-transparentcolor', 'white')
        self.selection_window.overrideredirect(True)

        self.canvas = tk.Canvas(self.selection_window, bg='white', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.rectangle_id = None
        self._update_selection()

    def _update_selection(self):
        """
        Update the selection rectangle.

        Continuously updates the dashed red rectangle on the canvas to show
        the current selection area from start to current mouse position.
        Schedules itself to run every 50ms for smooth updates.
        """
        if not self.selecting_area or not self.selection_window:
            return

        current_pos = pyautogui.position()
        x1, y1 = self.selection_start.x, self.selection_start.y
        x2, y2 = current_pos.x, current_pos.y

        try:
            if self.rectangle_id:
                self.canvas.delete(self.rectangle_id)

            self.rectangle_id = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline='red', width=2, fill='', dash=(5,5)
            )

            self.selection_window.update()
            self.ui.root.after(50, self._update_selection)  # Update every 50ms
        except tk.TclError:
            pass  # Window might be closed

    def _stop_selection(self):
        """
        Stop the area selection process.

        Destroys the selection window and resets selection flags and start position.
        """
        if self.selection_window:
            self.selection_window.destroy()
            self.selection_window = None
        self.selecting_area = False
        self.selection_start = None

    def setup_screen_area(self):
        """
        Initiate the screen area setup process.

        Starts an 8-step guided setup process for defining bot areas:
        1. Chat area (top-left and bottom-right corners)
        2. Input area (click position)
        3. Pose area (selection rectangle)
        4. Pose icon area (selection rectangle)
        5. Close partnership button area (selection rectangle)
        6. Put on all button point (click position)

        Resets any ongoing setup and displays instructions via temporary messages.
        """
        # If already in setup, close current temp window and reset
        if self.setup_step > 0 and self.current_temp_window:
            try:
                self.current_temp_window.destroy()
            except:
                pass
            self.current_temp_window = None
        self.setup_step = 1
        self.ui.update_status("Setting up...")
        self.current_temp_window = self.ui.show_temp_message("Step 1/9", "Move cursor to TOP LEFT corner of chat and press F2.", duration=None)

    def _handle_setup_key_press(self):
        """
        Handle key press events during the setup process.

        Processes F2 key presses at different setup steps to capture mouse positions
        and define screen areas. Advances through the 8-step setup process:
        - Steps 1-2: Define chat area
        - Step 3: Define input area
        - Steps 4-5: Define pose area
        - Steps 6-7: Define pose icon area
        - Steps 8-9: Define close partnership button area
        - Step 10: Define put on all button point

        Args:
            pos (Point): Current mouse position from pyautogui.position().
        """
        pos = pyautogui.position()

        if self.setup_step == 1:
            self.setup_coords['x1'] = pos.x
            self.setup_coords['y1'] = pos.y
            self.selection_start = pos
            self.selecting_area = True
            self._start_selection()
            self.log(f"Step 1: Top left corner of chat: {pos}", internal=True)
            if self.current_temp_window:
                try:
                    self.current_temp_window.destroy()
                except:
                    pass
                self.current_temp_window = None
            self.setup_step = 2
            self.current_temp_window = self.ui.show_temp_message("Step 2/9", "Move to BOTTOM RIGHT corner of chat and press F2.", duration=None)
        elif self.setup_step == 2:
            self._stop_selection()
            x2, y2 = pos.x, pos.y
            self.areas['chat_area'] = {
                'x': self.setup_coords['x1'], 'y': self.setup_coords['y1'],
                'width': x2 - self.setup_coords['x1'], 'height': y2 - self.setup_coords['y1']
            }
            self.log("Step 2: Chat area saved.", internal=True)
            if self.current_temp_window:
                try:
                    self.current_temp_window.destroy()
                except:
                    pass
                self.current_temp_window = None
            self.setup_step = 3
            self.current_temp_window = self.ui.show_temp_message("Step 3/9", "Click in the TEXT INPUT field in the game and press F2.", duration=None)
        elif self.setup_step == 3:
            self.areas['input_area'] = {'x': pos.x, 'y': pos.y}
            self.log("Step 3: Input field saved.", internal=True)
            if self.current_temp_window:
                try:
                    self.current_temp_window.destroy()
                except:
                    pass
                self.current_temp_window = None
            self.setup_step = 4
            self.current_temp_window = self.ui.show_temp_message("Step 4/9", "Select area (TL->BR) for POSES (Accept/Proposals button).")
            
        elif self.setup_step == 4:
            self.setup_coords['pose_x1'] = pos.x
            self.setup_coords['pose_y1'] = pos.y
            self.selection_start = pos
            self.selecting_area = True
            self._start_selection()
            self.log(f"Step 4: Pose TL: {pos}", internal=True)
            self.setup_step = 41
        elif self.setup_step == 41:
            self._stop_selection()
            x2, y2 = pos.x, pos.y
            self.areas['pose_area'] = {
                'x': self.setup_coords['pose_x1'], 'y': self.setup_coords['pose_y1'],
                'width': x2 - self.setup_coords['pose_x1'], 'height': y2 - self.setup_coords['pose_y1']
            }
            self.log("Pose area saved.", internal=True)
            if self.current_temp_window:
                try:
                    self.current_temp_window.destroy()
                except:
                    pass
                self.current_temp_window = None
            self.setup_step = 5
            self.current_temp_window = self.ui.show_temp_message("Step 5/9", "Select area (TL->BR) for POSE ICON.")

        elif self.setup_step == 5:
            self.setup_coords['pi_x1'] = pos.x
            self.setup_coords['pi_y1'] = pos.y
            self.selection_start = pos
            self.selecting_area = True
            self._start_selection()
            self.log(f"Step 5: Pose Icon TL: {pos}", internal=True)
            self.setup_step = 51
        elif self.setup_step == 51:
            self._stop_selection()
            x2, y2 = pos.x, pos.y
            self.areas['pose_icon_area'] = {
                'x': self.setup_coords['pi_x1'], 'y': self.setup_coords['pi_y1'],
                'width': x2 - self.setup_coords['pi_x1'], 'height': y2 - self.setup_coords['pi_y1']
            }
            self.log("Pose icon area saved.", internal=True)
            if self.current_temp_window:
                try:
                    self.current_temp_window.destroy()
                except:
                    pass
                self.current_temp_window = None
            self.setup_step = 6
            self.current_temp_window = self.ui.show_temp_message("Step 6/9", "Select area (TL->BR) for CLOSE PARTNERSHIP BUTTON.")
        elif self.setup_step == 6:
            self.setup_coords['cp_x1'] = pos.x
            self.setup_coords['cp_y1'] = pos.y
            self.selection_start = pos
            self.selecting_area = True
            self._start_selection()
            self.log(f"Step 6: Close Partnership TL: {pos}", internal=True)
            self.setup_step = 61
        elif self.setup_step == 61:
            self._stop_selection()
            x2, y2 = pos.x, pos.y
            self.areas['close_partnership_btn'] = {
                'x': self.setup_coords['cp_x1'], 'y': self.setup_coords['cp_y1'],
                'width': x2 - self.setup_coords['cp_x1'], 'height': y2 - self.setup_coords['cp_y1']
            }
            self.log("Close partnership button area saved.", internal=True)
            if self.current_temp_window:
                try:
                    self.current_temp_window.destroy()
                except:
                    pass
                self.current_temp_window = None
            self.setup_step = 7
            self.current_temp_window = self.ui.show_temp_message("Step 7/9", "Click on the PUT ON ALL button in the clothes menu and press F2.", duration=None)
        elif self.setup_step == 7:
            self.areas['put_on_all_point'] = {'x': pos.x, 'y': pos.y}
            self.log("Put on all point saved.", internal=True)
            if self.current_temp_window:
                try:
                    self.current_temp_window.destroy()
                except:
                    pass
                self.current_temp_window = None
            self.setup_step = 8
            self.current_temp_window = self.ui.show_temp_message("Step 8/9", "Select area (TL->BR) for AMOUNT (Money).")
        elif self.setup_step == 8:
            self.setup_coords['amt_x1'] = pos.x
            self.setup_coords['amt_y1'] = pos.y
            self.selection_start = pos
            self.selecting_area = True
            self._start_selection()
            self.log(f"Step 8: Amount TL: {pos}", internal=True)
            self.setup_step = 81
        elif self.setup_step == 81:
            self._stop_selection()
            x2, y2 = pos.x, pos.y
            self.areas['amount_area'] = {
                'x': self.setup_coords['amt_x1'], 'y': self.setup_coords['amt_y1'],
                'width': x2 - self.setup_coords['amt_x1'], 'height': y2 - self.setup_coords['amt_y1']
            }
            self.log("Amount area saved.", internal=True)

            # Завершаем настройку
            if self.current_temp_window:
                try:
                    self.current_temp_window.destroy()
                except:
                    pass
                self.current_temp_window = None
            self.setup_step = 0
            self.save_settings()
            self.ui.update_status("Ready to start")
            self.log("Setup completed! (9 steps)", internal=True)
            self.log(f"IMPORTANT: Place pose icon images in {POSES_DIR}", internal=True)
            if self.show_overlay:
                self._create_overlay()

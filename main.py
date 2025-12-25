"""
Main entry point for the ChatBot application.

This module initializes and starts the chatbot GUI application. It handles
application path detection for both development and PyInstaller builds,
sets up logging, and launches the main UI window.

Author: [3DXChatBot]
Version: 1.0.0
Date: [14.12.2025]
"""

import customtkinter as ctk
import logging
import os
import sys
import multiprocessing  # Required for PyInstaller compatibility

from src.config import LOG_DIR
from src.ui_main import ChatBotUI


# --- APPLICATION BASE PATH DETERMINATION ---
# Check if the application is running from an EXE file (PyInstaller build)
if getattr(sys, 'frozen', False):
    # If yes, base path is the temporary directory created by PyInstaller
    BASE_PATH = sys._MEIPASS
else:
    # If not (running as a regular Python script), base path is the current directory
    BASE_PATH = os.path.dirname(__file__)


# --- ICON PATH CONSTANT ---
# Relative path to the icon within the project
RELATIVE_ICON_PATH = r'resources\logo.ico'
# Combine base path with relative path to get the full path
ICON_PATH = os.path.join(BASE_PATH, RELATIVE_ICON_PATH)


if __name__ == "__main__":
    # Enable multiprocessing support for PyInstaller compatibility
    multiprocessing.freeze_support()

    # Ensure log directory exists
    os.makedirs(LOG_DIR, exist_ok=True)

    # Configure logging with single file that gets overwritten
    log_file = os.path.join(LOG_DIR, "chatbot.log")
    logging.basicConfig(filename=log_file, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s', filemode='w')

    try:
        # Create the main Tkinter root window using CustomTkinter
        root = ctk.CTk()

        # === ICON SETUP ===
        # Check if the icon file exists at the absolute path before setting
        if os.path.exists(ICON_PATH):
            try:
                root.iconbitmap(ICON_PATH)
            except Exception as e:
                logging.warning(f"Failed to set icon: {e}. Check the file format.")
        else:
            logging.warning(f"Icon file not found at absolute path: {ICON_PATH}")
        # ========================

        # Initialize the ChatBot UI application
        app = ChatBotUI(root)
        # Start the Tkinter event loop
        root.mainloop()
    except Exception as e:
        logging.error(f"Critical error: {e}")
        print(f"An error occurred: {e}. Check the log file {log_file}.")
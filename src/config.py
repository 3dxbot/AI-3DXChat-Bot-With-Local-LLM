"""
Configuration Module.

This module contains all configuration constants and paths used throughout
the chatbot application. It defines paths, intervals, colors, selectors,
and other settings for the bot's operation.

Configuration Categories:
    - Base directories and paths
    - OCR and timing settings
    - UI visualization colors
    - Image resource paths
    - File paths for settings and storage
    - Ollama API and service settings
"""

import os
import sys

# --- Configuration Constants ---

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directory for logs
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# Path to Tesseract
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# OCR scan interval (in seconds)
SCAN_INTERVAL_ACTIVE = 2.0
SCAN_INTERVAL_IDLE = 1.5

# Reading and typing speed (characters per minute)
READING_SPEED_CPM = 1200
TYPING_SPEED_CPM = 400

# Area visualization
OVERLAY_COLOR = 'red'
OVERLAY_THICKNESS = 1
INPUT_SQUARE_SIZE = 10

# Colors for new zones
PARTNERSHIP_COLOR = 'green'
POSE_COLOR = 'blue'
POSE_ICON_COLOR = 'cyan'
CLOSE_BTN_COLOR = 'red'
STOP_SEX_COLOR = 'purple'
PUT_ON_ALL_COLOR = 'orange'
AMOUNT_COLOR = 'yellow'

# Paths to images for search
RESOURCES_DIR = os.path.join(BASE_DIR, "resources")
CLOSE_BTN_IMAGE_PATH = os.path.join(RESOURCES_DIR, "close_partnership.png")
ACCEPT_POSE_IMAGE_PATH = os.path.join(RESOURCES_DIR, "accept_pose.png")
AGREE_PARTNERSHIP_TILE_PATH = os.path.join(RESOURCES_DIR, "agree_partnership_tile.png")
PRIVATE_MESSAGE_BTN_IMAGE_PATH = os.path.join(RESOURCES_DIR, "private_message.png")
STOP_SEX_IMAGE_PATH = os.path.join(RESOURCES_DIR, "stop_sex.png")
CLEAN_SPERM_IMAGE_PATH = os.path.join(RESOURCES_DIR, "clean_sperm.png")
ACCEPT_CLOTHES_CONTROL_PATH = os.path.join(RESOURCES_DIR, "accept_clothes_control.png")
CLOTHES_BTN_PATH = os.path.join(RESOURCES_DIR, "clothes.png")
PUT_ON_ALL_BTN_PATH = os.path.join(RESOURCES_DIR, "put_on_all.png")
GIFT_IMAGE_PATH = os.path.join(RESOURCES_DIR, "gift.png")
POSES_DIR = os.path.join(RESOURCES_DIR, "poses")
UNKNOWN_POSES_DIR = os.path.join(POSES_DIR, "unknown")

# Ollama paths
OLLAMA_DIR = os.path.join(RESOURCES_DIR, "ollama")
OLLAMA_EXE_PATH = os.path.join(OLLAMA_DIR, "ollama.exe")
OLLAMA_MODELS_DIR = os.path.join(OLLAMA_DIR, "models")
OLLAMA_TEMP_DIR = os.path.join(OLLAMA_DIR, "temp")

# Ollama API settings
OLLAMA_API_URL = "http://localhost:11434"
OLLAMA_DOWNLOAD_URL = "https://github.com/ollama/ollama/releases/latest/download/ollama-windows-amd64.zip"

# Whether to use multiprocessing for OCR
USE_MULTIPROCESSING = True

# Translation Layer Settings
USE_TRANSLATION_LAYER = False

# File for saving settings
SETTINGS_FILE = os.path.join(BASE_DIR, 'config', 'chatbot_settings.json')
HOTKEY_PHRASES_FILE = os.path.join(BASE_DIR, 'config', 'hotkey_phrases.json')

# Directory for character profiles
CHARACTERS_DIR = os.path.join(BASE_DIR, 'config', 'characters')

# Chat history reset
RIGHT_UP_ARROW = ".expand-box"
SAVE_AND_START_NEW_CHAT = "//span[text()='Save and Start New Chat']"
AGREE_DELETE_CHAT = ".Deletes"

# Language change
SETTING_GEAR = "(//div[contains(@class, 'settings-box')])[1]"
SELECT_TRANSlATE_LANG = "(//div[contains(@class, 'select-font')])[2]"
ENG_TRANSLATE_LANG = "//div[contains(@class, 'font-box') and contains(text(), 'English')]"
RU_TRANSLATE_LANG = "//div[contains(@class, 'font-box') and contains(text(), 'Русский')]"
ESP_TRANSLATE_LANG = "//div[contains(@class, 'font-box') and contains(text(), 'Español')]"
FRANCE_TRANSLATE_LANG = "//div[contains(@class, 'font-box') and contains(text(), 'Français')]"

# Chat menu
CHAT_MENU = ".Chat-box"
FIRST_CHAT = "(//div[contains(@class, 'robot-box show-box')])[1]"
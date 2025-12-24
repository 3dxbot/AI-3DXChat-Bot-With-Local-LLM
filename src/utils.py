"""
Utils Module.

This module provides utility functions for OCR text extraction, image processing,
and text normalization. It includes Tesseract OCR configuration and multiprocessing
support for efficient text recognition.

Functions:
    get_tesseract_lang: Get Tesseract language code from language setting.
    get_tesseract_config: Get cached Tesseract configuration.
    normalize_ocr_text: Normalize OCR-extracted text.
    extract_text_from_image: Extract text from image using OCR.
    extract_digits_from_image: Extract digits from image using OCR.
"""

import pytesseract
import numpy as np
import cv2
import os
import sys
import re
from multiprocessing import Pool
from .config import USE_MULTIPROCESSING

# --- SETTINGS ---
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# IMPORTANT: This option was removed as it caused issues with Latin nicks.
# All normalization now happens in chat_processor.py
# NORMALIZE_FOR_RUSSIAN = True
# -----------------

if not os.path.exists(TESSERACT_PATH):
    print(f"Ошибка: Tesseract не найден по пути: {TESSERACT_PATH}. Проверьте путь в файле utils.py.")
    sys.exit()
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def get_tesseract_lang(ocr_language=None):
    """
    Get Tesseract language code. Returns a combined rus+eng for maximum flexibility.
    """
    return 'rus+eng'


# --- CONFIG CACHE ---
_TESSERACT_CONFIGS = {}

def get_tesseract_config(ocr_language):
    """
    Get cached Tesseract configuration.

    Returns cached Tesseract configuration string for the given language,
    creating it if not already cached.

    Args:
        ocr_language (str): OCR language code.

    Returns:
        str: Tesseract configuration string.
    """
    if ocr_language not in _TESSERACT_CONFIGS:
        _TESSERACT_CONFIGS[ocr_language] = r'--oem 3 --psm 6 -l ' + get_tesseract_lang(ocr_language)
    return _TESSERACT_CONFIGS[ocr_language]


def normalize_ocr_text(text):
    """
    Normalize OCR-extracted text.

    Fixes only the most common OCR artifacts. Language-specific normalization
    was removed to avoid damaging nicknames.
    """
    if not text:
        return ""

    # Удаляем только общие артефакты, не трогая символы разных языков.
    text = text.replace('`', '').replace('’', '')

    return text.strip()


# --- Multiprocessing pool (ленивое создание для Windows) ---
_pool = None

def _ocr_worker(args):
    binary, config = args
    return pytesseract.image_to_string(binary, config=config)


def extract_text_from_image(img, ocr_language='en'):
    """
    Extract text from image using OCR.

    Processes the image with OpenCV for better OCR results and extracts
    text using Tesseract with the specified language.

    Args:
        img: PIL Image object to process.
        ocr_language (str): Language code for OCR (default: 'en').

    Returns:
        str or None: Extracted text or None if error occurred.
    """
    try:
        img_np = np.array(img)
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)

        # Инвертируем цвета, если фон светлый
        if np.mean(gray) > 127:
            gray = cv2.bitwise_not(gray)

        _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)

        config = get_tesseract_config(ocr_language)

        global _pool
        if USE_MULTIPROCESSING:
            if _pool is None:
                _pool = Pool(processes=1)  # создаём только при первом вызове
            text = _pool.apply(_ocr_worker, [(binary, config)])
        else:
            text = pytesseract.image_to_string(binary, config=config)

        # Log raw text for debugging
        import logging
        logging.info(f"Raw OCR text: {repr(text)}")

        return normalize_ocr_text(text)

    except Exception as e:
        print(f"Error occurred during image processing: {e}")
        return None


def extract_digits_from_image(img):
    """
    Extract only digits from image using OCR.
    
    Optimized for small numeric text in the 'amount' area.
    """
    try:
        img_np = np.array(img)
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        
        # Increase resolution if image is very small
        if gray.shape[0] < 50:
            gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

        # Basic preprocessing
        if np.mean(gray) > 127:
            gray = cv2.bitwise_not(gray)
        
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Config for digits only
        config = r'--oem 3 --psm 6 outputbase digits'
        
        text = pytesseract.image_to_string(binary, config=config)
        
        # Strip everything except digits
        digits = re.sub(r'\D', '', text)
        return int(digits) if digits else 0

    except Exception as e:
        print(f"Error occurred during digit extraction: {e}")
        return 0
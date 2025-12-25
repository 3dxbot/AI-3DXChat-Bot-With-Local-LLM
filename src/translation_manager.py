"""
Translation Manager Module.

Handles local translation using deep-translator (Google Translate).
"""

import logging
from deep_translator import GoogleTranslator

class TranslationManager:
    """
    Manages translation between different languages and English.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Supported target languages
        self.supported_langs = ['ru', 'fr', 'es', 'it', 'de']

    def translate_to_en(self, text, source_lang):
        """Translate text from source language to English."""
        if not text or source_lang == 'en':
            return text
        
        try:
            translated = GoogleTranslator(source=source_lang, target='en').translate(text)
            return translated
        except Exception as e:
            self.logger.error(f"Translation to EN error: {e}")
            return text

    def translate_from_en(self, text, target_lang):
        """Translate text from English to target language."""
        if not text or target_lang == 'en':
            return text
        
        try:
            translated = GoogleTranslator(source='en', target=target_lang).translate(text)
            return translated
        except Exception as e:
            self.logger.error(f"Translation from EN error: {e}")
            return text

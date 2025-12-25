"""
Chat Processor Module.

This module provides the ChatProcessor class, which handles OCR text processing,
message deduplication, nickname normalization, fuzzy matching, and language detection
for the chatbot application.

Classes:
    ChatProcessor: Processes and analyzes chat messages from OCR text.
"""

import re
import difflib
import hashlib
import time
from collections import deque
from langdetect import detect, detect_langs
from langdetect.lang_detect_exception import LangDetectException
from .utils import normalize_ocr_text


class ChatProcessor:
    """
    Processes and analyzes chat messages from OCR text.

    This class handles OCR text normalization, message deduplication, nickname
    fuzzy matching, language detection, and message processing for the chatbot.

    Attributes:
        ignore_nicks (set): Set of nicks to ignore.
        target_nicks (set): Set of target nicks.
        log_callback: Callback function for logging.
        all_known_nicks (set): Union of ignore and target nicks.
        ocr_language (str): OCR language setting.
        last_messages (deque): Recent message hashes for deduplication.
        message_ttl (int): Time-to-live for messages in seconds.
        char_map (dict): Character mapping for OCR error correction.

    Methods:
        __init__: Initialize the chat processor.
        log: Log a message.
        update_nicks: Update nick lists.
        _normalize_nick: Normalize a nickname.
        _fuzzy_match_nick: Fuzzy match a nickname.
        _clean_text: Clean text for hashing.
        _make_message_hash: Create message hash.
        _is_recent_duplicate: Check for duplicate messages.
        get_new_messages: Extract new messages from OCR text.
        process_message: Process bot response for sending.
        contains_cyrillic: Check for Cyrillic characters.
        detect_language: Detect text language.
    """

    LANG_MARKERS = {
        'fr': {
            'words': {'est', 'et', 'le', 'la', 'les', 'des', 'un', 'une', 'je', 'vous', 'nous', 'pour', 'avec', 'mais', 'pas', 'c\'est', 'ça'},
            'chars': {'ç', 'œ', 'æ', 'è', 'ê', 'à', 'â', 'ù'}
        },
        'es': {
            'words': {'el', 'la', 'los', 'las', 'un', 'una', 'y', 'es', 'que', 'en', 'por', 'para', 'con', 'del', 'lo', 'mi', 'su'},
            'chars': {'ñ', '¿', '¡', 'á', 'é', 'í', 'ó', 'ú'}
        },
        'en': {
            'words': {'the', 'and', 'is', 'it', 'to', 'for', 'with', 'you', 'are', 'this', 'that', 'not', 'have'}
        },
        'it': {
            'words': {'il', 'la', 'i', 'le', 'un', 'una', 'e', 'è', 'di', 'a', 'in', 'che', 'non', 'per', 'con', 'su', 'mi', 'ti', 'si'},
            'chars': {'à', 'è', 'é', 'ì', 'ò', 'ù'}
        },
        'de': {
            'words': {'der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'einer', 'einem', 'einen', 'und', 'ist', 'mit', 'für', 'von', 'zu', 'dass', 'nicht'},
            'chars': {'ä', 'ö', 'ü', 'ß'}
        }
    }

    def __init__(
        self, ignore_nicks, target_nicks, log_callback=None, ocr_language="en"
    ):
        """
        Initialize the ChatProcessor.

        Args:
            ignore_nicks (set): Set of nicks to ignore.
            target_nicks (set): Set of target nicks.
            log_callback: Optional callback for logging.
            ocr_language (str): OCR language. Defaults to "en".
        """
        self.ignore_nicks = {nick.strip().lower() for nick in ignore_nicks}
        self.target_nicks = {nick.strip().lower() for nick in target_nicks}
        self.log_callback = log_callback
        self.all_known_nicks = self.ignore_nicks.union(self.target_nicks)
        self.ocr_language = ocr_language

        # Store the last 5 messages as (hash, timestamp) to prevent duplicates
        self.last_messages = deque(maxlen=5)
        # Time-to-live for a message in seconds (2 minutes)
        self.message_ttl = 120

        # A map to correct common OCR errors, converting lookalike Cyrillic/other chars to Latin
        # This is crucial for normalizing nicknames, which are always in Latin
        # script.
        self.char_map = {
            # Cyrillic to Latin
            "А": "A",
            "В": "B",
            "С": "C",
            "Е": "E",
            "Н": "H",
            "К": "K",
            "М": "M",
            "О": "O",
            "Р": "P",
            "Т": "T",
            "Х": "X",
            "У": "Y",
            "І": "I",
            "а": "a",
            "с": "c",
            "е": "e",
            "к": "k",
            "о": "o",
            "р": "p",
            "х": "x",
            "у": "y",
            "і": "i",
            # Common number/symbol to letter mistakes
            "0": "O",
            "1": "I",
            "2": "Z",
            "3": "E",
            "4": "A",
            "5": "S",
            "6": "G",
            "7": "T",
            "8": "B",
        }

    def log(self, message):
        """
        Log a message through the UI callback.

        Args:
            message (str): The message to log.
        """
        if self.log_callback:
            self.log_callback(message, internal=True)

    def update_nicks(self, ignore_nicks, target_nicks):
        """
        Update nick lists, normalizing them for correct comparison.

        Args:
            ignore_nicks (set): New ignore nicks.
            target_nicks (set): New target nicks.
        """
        self.ignore_nicks = {self._normalize_nick(nick) for nick in ignore_nicks}
        self.target_nicks = {self._normalize_nick(nick) for nick in target_nicks}

        # Удаляем пустые строки, которые могли появиться после нормализации
        # (например, из ника ":)")
        self.ignore_nicks.discard("")
        self.target_nicks.discard("")

        self.all_known_nicks = self.ignore_nicks.union(self.target_nicks)
        self.log("Nick lists in chat processor updated and normalized.")

    def _normalize_nick(self, nick):
        """
        Normalize a nickname using transliteration.

        Extra characters are already removed in get_new_messages
        strictly according to server rules.

        Args:
            nick (str): The nickname to normalize.

        Returns:
            str: The normalized nickname.
        """
        normalized = ''.join(self.char_map.get(c, c) for c in nick)
        return normalized.lower()

    def _fuzzy_match_nick(self, ocr_nick):
        """
        Finds the most likely known nickname matching the OCR-read nickname.
        This handles minor OCR errors that normalization might miss.
        """
        ocr_nick_lower = ocr_nick.lower()
        if ocr_nick_lower in self.all_known_nicks:
            return ocr_nick_lower

        best_match = None
        # Set a reasonable confidence threshold for matching
        best_ratio = 0.7
        for known_nick in self.all_known_nicks:
            ratio = difflib.SequenceMatcher(None, ocr_nick_lower, known_nick).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = known_nick

        if best_match:
            # self.log(f"-> Fuzzy nickname match: '{ocr_nick}' → '{best_match}'
            # ({best_ratio:.2f})")  # Commented out to reduce log noise
            pass
        return best_match

    def _clean_text(self, text):
        """
        Clean message text for hashing by removing non-essential characters.

        Args:
            text (str): The text to clean.

        Returns:
            str: The cleaned text.
        """
        return re.sub(r"[^A-Za-zА-Яа-яЁё0-9\s.,!?-]", "", text).strip().lower()

    def _make_message_hash(self, author, message):
        """
        Create a unique hash for a message to detect duplicates.

        Args:
            author (str): The message author.
            message (str): The message text.

        Returns:
            str: The MD5 hash of the message.
        """
        author_clean = author.strip().lower()
        message_clean = self._clean_text(message)
        combined = f"{author_clean}:{message_clean}"
        return hashlib.md5(combined.encode("utf-8")).hexdigest()

    def _is_recent_duplicate(self, message_hash):
        """
        Checks if the message hash exists in recent memory.
        It also cleans up messages older than self.message_ttl.
        """
        now = time.time()
        # Remove old messages from the deque
        self.last_messages = deque(
            [(h, t) for h, t in self.last_messages if now - t < self.message_ttl],
            maxlen=5,
        )
        # Check if the hash is in the remaining list
        return any(h == message_hash for h, _ in self.last_messages)

    def get_new_messages(self, text):
        """
        Extract new messages from OCR text.

        Parses the OCR text to find chat messages, normalizes nicks,
        performs fuzzy matching, deduplicates, and returns new messages
        and potential new nicks. Handles multi-line messages by merging
        continuation lines without ':' to the previous message.

        Args:
            text (str): The OCR text to process.

        Returns:
            tuple: (list of message dicts, set of potential new nicks)
        """
        if not text:
            return [], set()

        potential_new_nicks = set()
        # Use splitlines for reliability
        lines = text.strip().splitlines()
        found_messages = []
        last_message = None

        for line in lines:
            line = line.strip()
            # RULE FROM SCREENSHOT: Length 3-20.
            # Add buffer for message text, so lines shorter than 5 characters
            # (3 for nick + 1 colon + 1 text) are not considered.
            if len(line) < 5:
                continue

            normalized_line = normalize_ocr_text(line)

            # 1. SEARCH FOR COLON
            idx = normalized_line.find(':')
            if idx == -1:
                # Fallback: try semicolon if close to start
                idx = normalized_line.find(';')
                if idx == -1:
                    # No separator - check if continuation of previous message
                    if last_message and len(line) > 0:
                        # Append to last message
                        last_message['message'] += ' ' + normalized_line.strip()
                        continue
                    else:
                        continue  # Garbage

            # If separator too far (longer than max nick length 20 + buffer 5), not chat
            if idx > 25:
                continue

            raw_nick = normalized_line[:idx]
            message_part = normalized_line[idx+1:].strip()

            if not message_part:
                continue

            # 2. CLEAN FROM GARBAGE (Based on server rules)

            # a) Remove IDs and tags in brackets.
            # Since brackets are forbidden in name, "Zeuto[22]" -> Zeuto with ID 22.
            # We need only the name.
            cleaned_nick = re.sub(r'\[.*?\]|\(.*?\)', '', raw_nick)

            # b) Remove spaces (Forbidden by rules -> OCR error)
            cleaned_nick = cleaned_nick.replace(" ", "")

            # c) Remove everything that is NOT letters, digits, _ or -
            # If OCR saw "Zeuto." -> dot forbidden -> turn into "Zeuto"
            # If OCR saw "Ze$uto" -> $ forbidden -> turn into "Zeuto"
            cleaned_nick = re.sub(r'[^A-Za-z0-9_-]', '', cleaned_nick)

            # 3. FINAL LENGTH CHECK (Rule 3-20 characters)
            if len(cleaned_nick) < 3 or len(cleaned_nick) > 20:
                continue

            # 4. SEARCH IN DATABASE
            processed_author = self._normalize_nick(cleaned_nick) # Only translit here
            canonical_author = self._fuzzy_match_nick(processed_author)

            if not canonical_author:
                potential_new_nicks.add(processed_author)
                last_message = None
                continue

            # 5. DEDUPLICATION
            msg_hash = self._make_message_hash(canonical_author, message_part)
            if self._is_recent_duplicate(msg_hash):
                last_message = None
                continue

            # Saving (as before)
            if canonical_author in self.ignore_nicks:
                self.last_messages.append((msg_hash, time.time()))
                last_message = None
                continue

            if canonical_author in self.target_nicks:
                self.log(f"✅ Msg: {canonical_author} -> {message_part}")
                self.last_messages.append((msg_hash, time.time()))
                message_dict = {'author': canonical_author, 'message': message_part}
                found_messages.append(message_dict)
                last_message = message_dict

        # Since we processed in order, reverse to match original behavior
        found_messages.reverse()
        return found_messages, potential_new_nicks

    def process_message(self, message):
        """
        Process the bot's response for sending to the game.

        Splits the message by asterisks for actions and formats accordingly.

        Args:
            message (str): The bot's response message.

        Returns:
            list: List of processed message parts.
        """
        message = message.replace('"', "").strip()
        # Split message by text in asterisks (for actions like /me)
        parts = re.split(r"(\*.*?\*)", message)
        processed_parts = []
        for part in parts:
            if part.startswith("*") and part.endswith("*"):
                action = part[1:-1].strip()
                if action:
                    processed_parts.append(f"/me {action}")
            else:
                clean_part = part.strip()
                if clean_part:
                    processed_parts.append(clean_part)
        return processed_parts

    def contains_cyrillic(self, text):
        """
        Check if the text contains Cyrillic characters.

        Args:
            text (str): The text to check.

        Returns:
            bool: True if Cyrillic characters are found.
        """
        return bool(re.search("[а-яА-Я]", text))

    def detect_language(self, text, current_lang='en'):
        """
        Каскадное определение языка:
        1. Кириллица (Ratio) -> RU
        2. Спецсимволы (ñ, ç) -> ES/FR
        3. Словарные маркеры (el, the, est) -> ES/EN/FR
        4. Fallback -> Langdetect или EN
        
        Возвращает (lang, is_certain)
        """
        if not text or len(text.strip()) < 2:
            return current_lang, False

        # --- ШАГ 1: Очистка и Кириллица ---
        clean_text = re.sub(r'[^a-zA-Zа-яА-ЯёЁñáéíóúüçàâêèéëîïôûùœæ¿¡]', ' ', text.lower())
        words = clean_text.split()

        # Считаем кириллицу
        cyrillic_chars = len(re.findall(r'[а-яА-ЯёЁ]', clean_text))
        total_chars = len(clean_text.replace(' ', ''))

        # Кириллица - очень сильный маркер
        if total_chars > 0 and (cyrillic_chars / total_chars) > 0.15:
            # Если текста мало, но это кириллица - мы уверены
            is_certain = len(text.strip()) > 5 or cyrillic_chars > 2
            return "ru", is_certain

        # --- ШАГ 2: Проверка по уникальным спецсимволам ---
        for char in self.LANG_MARKERS['es']['chars']:
            if char in text: 
                return "es", len(text.strip()) > 10

        if 'ç' in text or 'œ' in text: 
            return "fr", len(text.strip()) > 10

        for char in self.LANG_MARKERS['it']['chars']:
            if char in text:
                return "it", len(text.strip()) > 10

        for char in self.LANG_MARKERS['de']['chars']:
            if char in text:
                return "de", len(text.strip()) > 10

        # --- ШАГ 3: "Битва словарей" ---
        scores = {'fr': 0, 'es': 0, 'en': 0, 'it': 0, 'de': 0}

        for word in words:
            if word in self.LANG_MARKERS['fr']['words']:
                scores['fr'] += 1
            elif word in self.LANG_MARKERS['es']['words']:
                scores['es'] += 1
            elif word in self.LANG_MARKERS['en']['words']:
                scores['en'] += 1
            elif word in self.LANG_MARKERS['it']['words']:
                scores['it'] += 1
            elif word in self.LANG_MARKERS['de']['words']:
                scores['de'] += 1

        best_lang = max(scores, key=scores.get)
        max_score = scores[best_lang]

        if max_score > 0:
            # Уверенность: если больше 1 уникального маркера или длинный текст
            unique_markers = scores[best_lang]
            is_certain = unique_markers >= 2 or (unique_markers == 1 and len(text.strip()) > 20)
            return best_lang, is_certain

        # --- ШАГ 4: Fallback langdetect ---
        if len(text.strip()) > 15: # Только для достаточно длинных строк
            try:
                langs = detect_langs(text)
                for l in langs:
                    if l.lang in ['fr', 'es', 'en', 'it', 'de']:
                        if l.prob > 0.9:
                            return l.lang, True
                        if l.prob > 0.7:
                            return l.lang, False
            except LangDetectException:
                pass

        return "en", False

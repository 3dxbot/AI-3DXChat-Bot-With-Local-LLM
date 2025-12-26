"""
Gemini Manager Module.

This module provides the GeminiManager class for handling Google Gemini API interactions
via the OpenAI-compatible endpoint.
"""

import os
import requests
import json
import logging
from typing import Optional, List, Dict
from .status_manager import StatusManager
from .config import GEMINI_API_URL, GEMINI_API_KEY_FILE

class GeminiManager:
    """
    Manager class for Gemini API operations.
    """
    
    def __init__(self, status_manager: StatusManager):
        self.status_manager = status_manager
        self.logger = logging.getLogger(__name__)
        self.api_base_url = GEMINI_API_URL
        self.api_key = self._load_api_key()
        self.chat_history = []

    def _load_api_key(self) -> str:
        """Load API key from file."""
        try:
            if os.path.exists(GEMINI_API_KEY_FILE):
                with open(GEMINI_API_KEY_FILE, 'r') as f:
                    return f.read().strip()
        except Exception as e:
            self.logger.error(f"Error loading API key: {e}")
        return ""

    def save_api_key(self, key: str) -> bool:
        """Save API key to file."""
        try:
            os.makedirs(os.path.dirname(GEMINI_API_KEY_FILE), exist_ok=True)
            with open(GEMINI_API_KEY_FILE, 'w') as f:
                f.write(key.strip())
            self.api_key = key.strip()
            self.check_connection()
            return True
        except Exception as e:
            self.logger.error(f"Error saving API key: {e}")
            return False

    def check_connection(self) -> bool:
        """Check connection to Gemini API."""
        if not self.api_key:
            self.status_manager.set_ollama_status("No API Key")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            # For Gemini OpenAI endpoint, we use /models
            response = requests.get(f"{self.api_base_url}/models", headers=headers, timeout=10)
            if response.status_code == 200:
                self.status_manager.set_ollama_status("Connected")
                return True
            else:
                self.logger.error(f"Gemini Auth Error: {response.status_code} - {response.text}")
                self.status_manager.set_ollama_status("Auth Error")
                return False
        except Exception as e:
            self.logger.error(f"Connection check error: {e}")
            self.status_manager.set_ollama_status("Connection Error")
            return False

    def list_models(self) -> List[Dict]:
        """List available models."""
        if not self.api_key:
            return []
            
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(f"{self.api_base_url}/models", headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Gemini models usually look like 'models/gemini-1.5-flash'
                return data.get("data", [])
            return []
        except Exception as e:
            self.logger.error(f"Error listing models: {e}")
            return []

    async def generate_response(self, prompt: str, system_prompt: str = "", manifest: str = "", memory_cards: List[Dict] = None) -> Optional[str]:
        """
        Generate a response using the Gemini API.
        """
        model = self.status_manager.get_active_model()
        if not model:
            self.logger.error("No active model selected")
            return None
            
        if not self.api_key:
            self.logger.error("No API key configured")
            return None

        # Build messages
        messages = []
        
        # System Message
        full_system_prompt = system_prompt
        if manifest:
            full_system_prompt += f"\n\nCharacter Identity/Manifest:\n{manifest}"
            
        if memory_cards:
            full_system_prompt += "\n\nLong-term Memory/Knowledge (RAG):"
            for card in memory_cards:
                key = card.get("key", "Knowledge")
                data = card.get("data", "")
                if data.strip():
                    full_system_prompt += f"\n- {key}: {data}"
        
        if full_system_prompt.strip():
            messages.append({"role": "system", "content": full_system_prompt})

        # History and current prompt
        messages.extend(self.chat_history)
        messages.append({"role": "user", "content": prompt})

        # Prepare request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }

        try:
            self.logger.info(f"Sending request to Gemini (Model: {model})")
            import asyncio
            
            def make_request():
                return requests.post(
                    f"{self.api_base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60
                )

            response = await asyncio.to_thread(make_request)

            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                
                # Update history
                self.chat_history.append({"role": "user", "content": prompt})
                self.chat_history.append({"role": "assistant", "content": content})
                
                # Limit history (Gemini has huge context, but we keep UI history sane)
                if len(self.chat_history) > 40:
                    self.chat_history = self.chat_history[-40:]
                    
                return content
            else:
                self.logger.error(f"Gemini API error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return None

    def clear_history(self):
        """Clear conversation history."""
        self.chat_history = []

import os
import logging
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types

class GeminiEngine:
    def __init__(self, api_key: Optional[str] = None, model_id: str = "gemini-3-flash-preview"):
        # The SDK looks for GOOGLE_API_KEY or GEMINI_API_KEY if api_key is None
        self.client = genai.Client(api_key=api_key)
        self.model_id = model_id
        # In-memory history for now
        self.chat_sessions: Dict[int, Any] = {}

    def _get_chat_session(self, user_id: int):
        if user_id not in self.chat_sessions:
            self.chat_sessions[user_id] = self.client.chats.create(model=self.model_id)
        return self.chat_sessions[user_id]

    async def ask(self, user_id: int, prompt: str) -> str:
        chat = self._get_chat_session(user_id)
        try:
            response = chat.send_message(prompt)
            return response.text
        except Exception as e:
            logging.error(f"Gemini error: {e}")
            return f"❌ Error from Gemini: {str(e)}"

    def clear_history(self, user_id: int):
        if user_id in self.chat_sessions:
            del self.chat_sessions[user_id]

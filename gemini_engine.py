import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from google import genai
from google.genai import types
from database import Database

# Initialize global DB for tool access
db = Database()

def create_client(name: str, phone: str = None, notes: str = None) -> str:
    """Creates a new client in the database."""
    cid = db.add_client(name, phone, notes)
    return f"Successfully created client '{name}' with ID: {cid}"

def find_clients(query: str) -> str:
    """Searches for clients by name or notes using exact or partial matches."""
    clients = db.find_clients(query)
    if not clients:
        return "No clients found matching that query."
    return str(clients)

def list_clients(limit: int = 100) -> str:
    """Returns a list of clients. Use this if find_clients fails or to resolve nicknames (e.g. Bill -> William)."""
    clients = db.list_clients(limit)
    if not clients:
        return "The client database is currently empty."
    return str(clients)

def schedule_procedure(client_id: int, timestamp_utc: str, notes: str = None) -> str:
    """Schedules a procedure for a client. timestamp_utc must be in ISO 8601 format (YYYY-MM-DD HH:MM:SS)."""
    pid = db.add_procedure(client_id, timestamp_utc, notes)
    return f"Successfully scheduled procedure with ID: {pid}"

def list_procedures(start_time_utc: str = None, end_time_utc: str = None, client_id: int = None) -> str:
    """Lists procedures filtered by time range or client."""
    procs = db.get_procedures(start_time_utc, end_time_utc, client_id)
    if not procs:
        return "No procedures found for the given criteria."
    return str(procs)

def update_procedure_state(procedure_id: int, state: str) -> str:
    """Updates the state of a procedure (planned, done, cancelled)."""
    db.update_procedure_state(procedure_id, state)
    return f"Procedure {procedure_id} updated to {state}."

class GeminiEngine:
    def __init__(self, api_key: Optional[str] = None, model_id: str = "gemini-3-flash-preview"):
        self.client = genai.Client(api_key=api_key)
        self.model_id = model_id
        self.chat_sessions: Dict[int, Any] = {}
        self.tools = [
            create_client,
            find_clients,
            list_clients,
            schedule_procedure,
            list_procedures,
            update_procedure_state
        ]

    def _get_chat_session(self, user_id: int):
        if user_id not in self.chat_sessions:
            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            sys_instruct = f"""Ты — супер-полезный ассистент для ведения учета в салоне красоты. Твоя задача — безупречно управлять списком клиентов и записями на процедуры.

ОСНОВНЫЕ ПРАВИЛА:
1. Отвечай всегда КРАТКО, вежливо и только на РУССКОМ языке.
2. Текущее время UTC: {now}. Пользователь находится в Москве (UTC+3).
3. Всегда сохраняй время в UTC, но в ответах пользователю ВСЕГДА переводи его в Московское время (UTC+3).

РАБОТА С КЛИЕНТАМИ:
1. Перед записью всегда ищи клиента через `find_clients`. 
2. Если точного совпадения нет, используй `list_clients`, чтобы найти наиболее вероятного кандидата (например, Дима -> Дмитрий). Будь проактивен в этом поиске.
3. Если кандидатов нет, спроси: "К сожалению, не нашла такого клиента. Создать нового?".
4. Номер телефона и заметки — необязательны.

ЗАПИСЬ И ПОИСК:
1. Если пользователь говорит "завтра в 3 дня", рассчитай точное время в UTC (для Москвы это будет 12:00 UTC текущего или следующего дня).
2. Используй формат YYYY-MM-DD HH:MM:SS для всех вызовов инструментов.
"""
            self.chat_sessions[user_id] = self.client.chats.create(
                model=self.model_id,
                config=types.GenerateContentConfig(
                    system_instruction=sys_instruct,
                    tools=self.tools,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
                )
            )
        return self.chat_sessions[user_id]

    async def ask(self, user_id: int, prompt: str) -> str:
        chat = self._get_chat_session(user_id)
        try:
            now_context = f"\n[User local time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC]"
            response = chat.send_message(prompt + now_context)
            return response.text
        except Exception as e:
            logging.error(f"Gemini error: {e}")
            return f"❌ Error from Gemini: {str(e)}"

    def clear_history(self, user_id: int):
        if user_id in self.chat_sessions:
            del self.chat_sessions[user_id]

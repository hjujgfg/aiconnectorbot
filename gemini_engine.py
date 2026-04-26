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
            sys_instruct = f"""You are a helpful assistant managing a beauty salon's procedures and clients.
Current UTC time: {now}. 

LANGUAGE:
1. ALWAYS respond in Russian language (на русском языке).

FUZZY MATCHING & CLIENTS:
1. If a user asks for someone like 'Bill', 'Bob', or 'Kate', and `find_clients` returns nothing, use `list_clients` to scan the names for likely matches (e.g., William, Robert, Katherine).
2. If you are still unsure between multiple clients, ask the user for clarification.

TIMEZONES:
1. Always store timestamps in UTC in the database. 
2. The user is in Moscow time (UTC+3). 
3. When the user says 'tomorrow at 3 PM', calculate the UTC time (which would be 12:00 UTC).
4. When responding with times, ALWAYS convert them back to Moscow time (UTC+3) for the user.

DATABASE TOOLS:
- Always check if a client exists before scheduling.
- Use ISO 8601 format (YYYY-MM-DD HH:MM:SS) for all timestamps in tool calls.
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

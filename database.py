import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime

class Database:
    def __init__(self, db_path: str = "bot_data.db"):
        self.db_path = db_path
        self._create_tables()

    def _create_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            # Auth table
            conn.execute("CREATE TABLE IF NOT EXISTS authorized_users (user_id INTEGER PRIMARY KEY)")
            
            # Clients table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT,
                    notes TEXT
                )
            """)
            
            # Procedures table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS procedures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL, -- UTC ISO string
                    notes TEXT,
                    state TEXT DEFAULT 'planned',
                    FOREIGN KEY (client_id) REFERENCES clients (id)
                )
            """)
            conn.commit()

    def is_user_authorized(self, user_id: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT 1 FROM authorized_users WHERE user_id = ?", (user_id,))
            return cursor.fetchone() is not None

    def authorize_user(self, user_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR IGNORE INTO authorized_users (user_id) VALUES (?)", (user_id,))
            conn.commit()

    # --- Client Methods ---
    def add_client(self, name: str, phone: str = None, notes: str = None) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO clients (name, phone, notes) VALUES (?, ?, ?)",
                (name, phone, notes)
            )
            return cursor.lastrowid

    def find_clients(self, query: str) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM clients WHERE name LIKE ? OR notes LIKE ?",
                (f"%{query}%", f"%{query}%")
            )
            return [dict(row) for row in cursor.fetchall()]

    def list_clients(self, limit: int = 100) -> List[Dict]:
        """Returns a list of clients for browsing/fuzzy matching."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT id, name, notes FROM clients LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    # --- Procedure Methods ---
    def add_procedure(self, client_id: int, timestamp: str, notes: str = None) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO procedures (client_id, timestamp, notes) VALUES (?, ?, ?)",
                (client_id, timestamp, notes)
            )
            return cursor.lastrowid

    def get_procedures(self, start_time: str = None, end_time: str = None, client_id: int = None) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            query = "SELECT p.*, c.name as client_name FROM procedures p JOIN clients c ON p.client_id = c.id"
            filters = []
            params = []
            
            if start_time:
                filters.append("p.timestamp >= ?")
                params.append(start_time)
            if end_time:
                filters.append("p.timestamp <= ?")
                params.append(end_time)
            if client_id:
                filters.append("p.client_id = ?")
                params.append(client_id)
            
            if filters:
                query += " WHERE " + " AND ".join(filters)
            
            query += " ORDER BY p.timestamp ASC"
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def update_procedure_state(self, proc_id: int, state: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE procedures SET state = ? WHERE id = ?", (state, proc_id))
            conn.commit()

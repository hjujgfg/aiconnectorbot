import sqlite3
from typing import Set

class Database:
    def __init__(self, db_path: str = "bot_data.db"):
        self.db_path = db_path
        self._create_tables()

    def _create_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS authorized_users (user_id INTEGER PRIMARY KEY)"
            )
            # Table for the "freeform" data planned for Phase 3
            conn.execute(
                "CREATE TABLE IF NOT EXISTS freeform_data (key TEXT PRIMARY KEY, value TEXT)"
            )
            conn.commit()

    def is_user_authorized(self, user_id: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM authorized_users WHERE user_id = ?", (user_id,)
            )
            return cursor.fetchone() is not None

    def authorize_user(self, user_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO authorized_users (user_id) VALUES (?)", (user_id,)
            )
            conn.commit()

    def get_all_authorized_users(self) -> Set[int]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT user_id FROM authorized_users")
            return {row[0] for row in cursor.fetchall()}

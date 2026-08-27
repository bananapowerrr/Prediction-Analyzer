import os
import json
from datetime import datetime
import logging
import sqlite3
from typing import Dict, List

class PersistenceManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                data TEXT
            )
        """)
        self.conn.commit()

    def save_event(self, event_type: str, data: Dict):
        try:
            self.cursor.execute("INSERT INTO events (event_type, data) VALUES (?, ?)", (event_type, json.dumps(data)))
            self.conn.commit()
        except Exception as e:
            logging.error(f"Error saving event: {e}")
            PersistenceManager.save_event("error", {"message": str(e)})

    def get_events(self, event_type: str = None) -> List[Dict]:
        try:
            if event_type:
                self.cursor.execute("SELECT * FROM events WHERE event_type = ?", (event_type,))
            else:
                self.cursor.execute("SELECT * FROM events")
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logging.error(f"Error loading events: {e}")
            PersistenceManager.save_event("error", {"message": str(e)})
            return []

    def close(self):
        self.conn.close()

import sqlite3
from typing import List, Dict, Set

class StateManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(StateManager, cls).__new__(cls, *args, **kwargs)
            cls._instance.recent_markets: Set[str] = set()
        return cls._instance

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS world_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                data TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def save_event(self, event_type: str, data: Dict):
        self.cursor.execute('''
            INSERT INTO world_state (event_type, data) VALUES (?, ?)
        ''', (event_type, str(data)))
        self.conn.commit()

    def get_events(self, event_type: str = None) -> List[Dict]:
        if event_type:
            self.cursor.execute(
                'SELECT * FROM world_state WHERE event_type = ?', (event_type,)
            )
        else:
            self.cursor.execute('SELECT * FROM world_state')
        columns = [col[0] for col in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def remember_markets(self, ids: List[str]):
        self.recent_markets.update(ids)
        if len(self.recent_markets) > 500:
            self.recent_markets.discard(next(iter(self.recent_markets)))

    def seen_recently(self, market_id: str) -> bool:
        return market_id in self.recent_markets

    def clear(self):
        self.recent_markets.clear()

    def close(self):
        self.conn.close()

def get_default_state() -> StateManager:
    return StateManager(db_path="default_state.db")

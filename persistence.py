import sqlite3
from typing import Dict, List
import os
import json
import logging

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class PersistenceManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_type TEXT NOT NULL,
                data TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def save_event(self, event_type: str, data: Dict):
        self.cursor.execute('INSERT INTO reports (report_type, data) VALUES (?, ?)', (event_type, str(data)))
        self.conn.commit()

    def get_events(self, event_type: str = None) -> List[Dict]:
        query = 'SELECT data FROM reports'
        if event_type:
            query += f' WHERE report_type = ?'
            self.cursor.execute(query, (event_type,))
        else:
            self.cursor.execute(query)
        results = self.cursor.fetchall()
        return [dict(row) for row in results]

    def save_report(self, report_type: str, data: Dict):
        self.cursor.execute('INSERT INTO reports (report_type, data) VALUES (?, ?)', (report_type, str(data)))
        self.conn.commit()

    def get_report(self, report_type: str) -> Dict:
        self.cursor.execute('SELECT data FROM reports WHERE report_type = ?', (report_type,))
        result = self.cursor.fetchone()
        if result:
            return dict(result)
        return None

    def get_all_reports(self) -> List[Dict]:
        self.cursor.execute('SELECT * FROM reports')
        results = self.cursor.fetchall()
        return [dict(row) for row in results]

    def save_markets_json(self, path: str, markets: List[Dict]):
        """Сохранить список dict (id, question, liquidity, spread, volume_24h) в JSON UTF-8."""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(markets, f, ensure_ascii=False, indent=4)
        except IOError as e:
            logger.error(f"Ошибка при сохранении файла {path}: {e}")

    def load_markets_json(self, path: str) -> List[Dict]:
        """Загрузить список dict (id, question, liquidity, spread, volume_24h) из JSON UTF-8. Если файла нет — []."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка при загрузке файла {path}: {e}")
            return []

def save_markets_json(path: str, markets: List[Dict]):
    """Сохранить список dict (id, question, liquidity, spread, volume_24h) в JSON UTF-8."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(markets, f, ensure_ascii=False, indent=4)
    except IOError as e:
        logger.error(f"Ошибка при сохранении файла {path}: {e}")

def load_markets_json(path: str) -> List[Dict]:
    """Загрузить список dict (id, question, liquidity, spread, volume_24h) из JSON UTF-8. Если файла нет — []."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка при загрузке файла {path}: {e}")
        return []

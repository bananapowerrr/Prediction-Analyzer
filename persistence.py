import sqlite3
from typing import Dict, List
import os
import json
import logging
import tempfile
import csv
from dataclasses import asdict, is_dataclass

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

    def save_markets_json(self, markets: list, path: str):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        data = [_to_dict(m) for m in markets]
        with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as tmp:
            json.dump(data, tmp, ensure_ascii=False, indent=4)
        os.replace(tmp.name, path)

    def load_markets_json(self, path: str) -> list:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_markets_csv(self, path: str, markets: List[Dict]):
        """Сохранить список dict (id, question, liquidity, spread, volume_24h) в CSV UTF-8 с заголовком id,question,liquidity,spread,volume_24h."""
        if not markets:
            return
        try:
            normalized_markets = [{k: v for k, v in market.items() if k in ['id', 'question', 'liquidity', 'spread', 'volume_24h']} for market in markets]
            with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as temp_file:
                writer = csv.DictWriter(temp_file, fieldnames=['id', 'question', 'liquidity', 'spread', 'volume_24h'])
                writer.writeheader()
                writer.writerows(normalized_markets)
                temp_path = temp_file.name
            os.replace(temp_path, path)
        except IOError as e:
            logger.error(f"Ошибка при сохранении файла {path}: {e}")

def _to_dict(obj):
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    if isinstance(obj, dict):
        return obj
    return getattr(obj, '__dict__', obj)

def save_markets_json(markets: list, path: str):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    data = [_to_dict(m) for m in markets]
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as tmp:
        json.dump(data, tmp, ensure_ascii=False, indent=4)
    os.replace(tmp.name, path)

def load_markets_json(path: str) -> list:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_markets_csv(path: str, markets: List[Dict]):
    """Сохранить список dict (id, question, liquidity, spread, volume_24h) в CSV UTF-8 с заголовком id,question,liquidity,spread,volume_24h."""
    if not markets:
        return
    try:
        normalized_markets = [{k: v for k, v in market.items() if k in ['id', 'question', 'liquidity', 'spread', 'volume_24h']} for market in markets]
        with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as temp_file:
            writer = csv.DictWriter(temp_file, fieldnames=['id', 'question', 'liquidity', 'spread', 'volume_24h'])
            writer.writeheader()
            writer.writerows(normalized_markets)
            temp_path = temp_file.name
        os.replace(temp_path, path)
    except IOError as e:
        logger.error(f"Ошибка при сохранении файла {path}: {e}")

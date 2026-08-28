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
        """
        Кэш недавних market id и опционально события.

        :param db_path: Путь к базе данных
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        """
        Создает таблицу для хранения событий в базе данных.
        """
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
        """
        Сохраняет событие в базе данных.

        :param event_type: Тип события
        :param data: Данные события
        """
        self.cursor.execute('''
            INSERT INTO world_state (event_type, data) VALUES (?, ?)
        ''', (event_type, str(data)))
        self.conn.commit()

    def get_events(self, event_type: str = None) -> List[Dict]:
        """
        Получает события из базы данных.

        :param event_type: Тип события (если None, возвращаются все события)
        :return: Список событий
        """
        if event_type:
            self.cursor.execute(
                'SELECT * FROM world_state WHERE event_type = ?', (event_type,)
            )
        else:
            self.cursor.execute('SELECT * FROM world_state')
        columns = [col[0] for col in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def remember_markets(self, ids: List[str]):
        """
        Сохраняет недавние market id в кэше.

        :param ids: Список market id
        """
        self.recent_markets.update(ids)
        if len(self.recent_markets) > 500:
            self.recent_markets.discard(next(iter(self.recent_markets)))

    def seen_recently(self, market_id: str) -> bool:
        """
        Проверяет, был ли market id недавно виден.

        :param market_id: Id рынка
        :return: True, если был виден, иначе False
        """
        return market_id in self.recent_markets

    def clear(self):
        """
        Очищает кэш недавних market id.
        """
        self.recent_markets.clear()

    def close(self):
        """
        Закрывает соединение с базой данных.
        """
        self.conn.close()

    def export_recent_ids(self) -> List[str]:
        """
        Возвращает копию недавних market id.

        :return: Список недавних market id
        """
        return list(self.recent_markets)

def get_default_state() -> StateManager:
    """
    Возвращает экземпляр StateManager с базой данных по умолчанию.

    :return: Экземпляр StateManager
    """
    return StateManager(db_path="default_state.db")

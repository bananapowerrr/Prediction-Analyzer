import sqlite3
from typing import List, Dict, Set, Any
import json
import logging

MAX_RECENT = 500

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class StateManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(StateManager, cls).__new__(cls, *args, **kwargs)
            cls._instance.recent_markets: Set[str] = set()
        return cls._instance

    def __init__(self, db_path: str):
        """
        Инициализирует менеджер состояния с базой данных.

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
        try:
            self.cursor.execute('''
                INSERT INTO world_state (event_type, data) VALUES (?, ?)
            ''', (event_type, str(data)))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка при сохранении события: {e}")

    def get_events(self, event_type: str = None) -> List[Dict]:
        """
        Получает события из базы данных.

        :param event_type: Тип события (если None, возвращаются все события)
        :return: Список событий
        """
        try:
            if event_type:
                self.cursor.execute(
                    'SELECT * FROM world_state WHERE event_type = ?', (event_type,)
                )
            else:
                self.cursor.execute('SELECT * FROM world_state')
            columns = [col[0] for col in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка при получении событий: {e}")
            return []

    def remember_markets(self, ids: List[str]):
        """
        Сохраняет недавние market id в кэше.

        :param ids: Список market id
        """
        self.recent_markets.update(ids)
        if len(self.recent_markets) > MAX_RECENT:
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

    def export_json(self) -> Any:
        """
        Экспортирует данные в JSON формате.

        :return: Данные в JSON формате или пустое значение при ошибке
        """
        try:
            data = {
                "recent_markets": list(self.recent_markets),
                "events": self.get_events()
            }
            return json.dumps(data, indent=4)
        except (TypeError, OverflowError, json.JSONDecodeError) as e:
            logger.error(f"Ошибка при экспорте JSON: {e}")
            return {}

    @staticmethod
    def load_json(json_data: str) -> Any:
        """
        Загружает данные из JSON формата.

        :param json_data: Данные в JSON формате
        :return: Данные или пустое значение при ошибке
        """
        try:
            return json.loads(json_data)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Ошибка при загрузке JSON: {e}")
            return {}

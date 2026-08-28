import unittest
import tempfile
import os
from persistence import PersistenceManager

class TestPersistenceManager(unittest.TestCase):
    def test_save_markets_json(self):
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name

        # Создаем объект PersistenceManager
        pm = PersistenceManager(temp_path)

        # Создаем список рынков для сохранения
        markets = [
            {"id": "market1", "name": "Market 1"},
            {"id": "market2", "name": "Market 2"}
        ]

        # Сохраняем рынки в JSON
        pm.save_markets_json(markets)

        # Загружаем рынки обратно
        loaded_markets = pm.load_markets_json()

        # Сравниваем id сохраненных и загруженных рынков
        self.assertEqual(len(loaded_markets), len(markets))
        for saved_market, loaded_market in zip(markets, loaded_markets):
            self.assertEqual(saved_market["id"], loaded_market["id"])

    def test_load_non_existent_path(self):
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name

        # Удаляем временный файл, чтобы он не существовал
        os.unlink(temp_path)

        # Создаем объект PersistenceManager
        pm = PersistenceManager(temp_path)

        # Загружаем рынки из несуществующего пути
        loaded_markets = pm.load_markets_json()

        # Проверяем, что загруженный список пуст
        self.assertEqual(loaded_markets, [])

if __name__ == '__main__':
    unittest.main()

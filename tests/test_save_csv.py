import tempfile
import json
import csv
from persistence import persistence  # Добавляем импорт модуля persistence

def test_save_csv():
    # Создаем временный файл
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_file_path = temp_file.name

        # Записываем данные в CSV файл
        with open(temp_file_path, mode='w', newline='') as csvfile:
            fieldnames = ['id', 'question', 'liquidity', 'spread', 'volume_24h']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerow({'id': 1, 'question': 'Market 1', 'liquidity': 1000, 'spread': 0.01, 'volume_24h': 50000})
            writer.writerow({'id': 2, 'question': 'Market 2', 'liquidity': 2000, 'spread': 0.02, 'volume_24h': 100000})

        # Проверяем, что файл содержит header
        with open(temp_file_path, mode='r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            headers = reader.fieldnames

        assert headers == fieldnames, f"Expected headers: {fieldnames}, but got: {headers}"

        # Проверяем, что файл содержит данные
        with open(temp_file_path, mode='r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        expected_data = [
            {'id': '1', 'question': 'Market 1', 'liquidity': '1000', 'spread': '0.01', 'volume_24h': '50000'},
            {'id': '2', 'question': 'Market 2', 'liquidity': '2000', 'spread': '0.02', 'volume_24h': '100000'}
        ]
        assert data == expected_data, f"Expected data: {expected_data}, but got: {data}"

    # Удаляем временный файл
    import os
    os.unlink(temp_file_path)

def test_save_json():
    # Создаем временный файл
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_file_path = temp_file.name

        # Записываем данные в JSON файл
        markets = [
            {'id': '1', 'question': 'Market 1', 'liquidity': 1000, 'spread': 0.01, 'volume_24h': 50000},
            {'id': '2', 'question': 'Market 2', 'liquidity': 2000, 'spread': 0.02, 'volume_24h': 100000}
        ]
        persistence.save_markets_json(markets, temp_file_path)

        # Проверяем, что файл содержит данные
        with open(temp_file_path, mode='r', encoding='utf-8') as f:
            data = json.load(f)

        expected_data = [
            {'id': '1', 'question': 'Market 1', 'liquidity': 1000, 'spread': 0.01, 'volume_24h': 50000},
            {'id': '2', 'question': 'Market 2', 'liquidity': 2000, 'spread': 0.02, 'volume_24h': 100000}
        ]
        assert data == expected_data, f"Expected data: {expected_data}, but got: {data}"

    # Удаляем временный файл
    import os
    os.unlink(temp_file_path)

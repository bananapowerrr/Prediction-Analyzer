import tempfile
import csv

def test_save_csv():
    # Создаем временный файл
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_file_path = temp_file.name

        # Записываем данные в CSV файл
        with open(temp_file_path, mode='w', newline='') as csvfile:
            fieldnames = ['id', 'name', 'value']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerow({'id': 1, 'name': 'Alice', 'value': 100})
            writer.writerow({'id': 2, 'name': 'Bob', 'value': 200})

        # Проверяем, что файл содержит header
        with open(temp_file_path, mode='r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            headers = reader.fieldnames

        assert headers == fieldnames, f"Expected headers: {fieldnames}, but got: {headers}"

    # Удаляем временный файл
    import os
    os.unlink(temp_file_path)

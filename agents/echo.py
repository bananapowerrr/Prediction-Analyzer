from typing import Any
import logging

# Константы в UPPER_CASE
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_FILE = "echo.log"

# Настройка логирования
logging.basicConfig(filename=LOG_FILE, level=logging.ERROR, format=LOG_FORMAT)

def echo_analysis(text: Any) -> str:
    """
    Простая функция, которая возвращает входной текст без изменений.

    :param text: Входной текст.
    :return: Входной текст.
    """
    if text is None:
        logging.error("Input text is None")
        raise ValueError("Input text cannot be None")
    
    return text

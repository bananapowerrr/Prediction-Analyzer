# создано диспетчером для привязки Aider

from typing import Any

def echo_analysis(text: str) -> str:
    """
    Простая функция, которая добавляет префикс '[PA]' к входному тексту.

    :param text: Входной текст.
    :return: Текст с префиксом '[PA]'.
    """
    return '[PA] ' + text

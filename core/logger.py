"""Конфигурация централизованного логирования приложения.

Настройка корневого логгера с обработчиками консоли и вращающегося файла.
Модули получают логгеры через ``logging.getLogger(__name__)``.
"""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional, Union

DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_FILE = "app.log"
DEFAULT_MAX_BYTES = 5 * 1024 * 1024
DEFAULT_BACKUP_COUNT = 5

CONSOLE_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
FILE_FORMAT = "%(asctime)s %(levelname)-8s %(name)s [%(filename)s:%(lineno)d]: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_CONFIGURED = False


def _build_formatter(fmt: str, datefmt: Optional[str] = None) -> logging.Formatter:
    return logging.Formatter(fmt, datefmt=datefmt or DATE_FORMAT)


def _level_from(value: Union[int, str]) -> int:
    if isinstance(value, int):
        return value
    level = logging.getLevelName(value.upper()) if value else logging.INFO
    if not isinstance(level, int):
        return logging.INFO
    return level


def setup_logging(
    level: Union[int, str] = logging.INFO,
    log_dir: str = DEFAULT_LOG_DIR,
    log_file: str = DEFAULT_LOG_FILE,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
    console_level: Optional[Union[int, str]] = None,
    file_level: Optional[Union[int, str]] = None,
    console_format: str = CONSOLE_FORMAT,
    file_format: str = FILE_FORMAT,
    propagate_root: bool = True,
) -> logging.Logger:
    """Настройка корневого логгера с обработчиками консоли и вращающегося файла.

    Вызов этой функции более одного раза безопасен: она перестраивает набор обработчиков,
    чтобы можно было обновить конфигурацию (например, со значениями из настроек приложения).

    Args:
        level: Основной уровень логирования для корневого логгера.
        log_dir: Директория, где записывается вращающийся файл логов.
        log_file: Имя вращающегося файла логов.
        max_bytes: Максимальный размер одного файла логов перед вращением.
        backup_count: Количество резервных файлов логов для сохранения.
        console_level: Переопределенный уровень для обработчика консоли.
        file_level: Переопределенный уровень для обработчика файла.
        console_format: Формат строки для обработчика консоли.
        file_format: Формат строки для обработчика файла.
        propagate_root: Позволяет ли дочерним логгерам передавать сообщения корневому логгеру.

    Returns:
        Настроенный корневой логгер.
    """
    global _CONFIGURED

    root = logging.getLogger()
    root.setLevel(_level_from(level))

    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()

    console_fmt = _build_formatter(console_format)
    file_fmt = _build_formatter(file_format)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(_level_from(console_level if console_level is not None else level))
    console_handler.setFormatter(console_fmt)
    root.addHandler(console_handler)

    try:
        os.makedirs(log_dir, exist_ok=True)
        file_path = os.path.join(log_dir, log_file)
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(_level_from(file_level if file_level is not None else level))
        file_handler.setFormatter(file_fmt)
        root.addHandler(file_handler)
    except OSError as exc:
        root.warning("Не удалось прикрепить обработчик вращающегося файла (%s); продолжаем только с консолью", exc)

    root.propagate = propagate_root
    _CONFIGURED = True
    return root


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Возвращает логгер, настраивая централизованное логирование при первом использовании."""
    if not _CONFIGURED:
        setup_logging()
    return logging.getLogger(name)


def reset() -> None:
    """Удаляет все обработчики и сбрасывает флаг настроек (для тестов)."""
    global _CONFIGURED
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()
    _CONFIGURED = False

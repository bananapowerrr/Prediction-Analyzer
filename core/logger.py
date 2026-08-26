"""Centralized application logging configuration.

Provides ``setup_logging`` to configure the root logger with a console
handler and a rotating file handler, each using a configurable formatter and
log level. Modules across the application should obtain loggers via
``logging.getLogger(__name__)`` so they inherit this configuration.
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
    """Configure the root logger with console and rotating file handlers.

    Calling this more than once is safe: it rebuilds the handler set so the
    configuration can be refreshed (e.g. with values from the app settings).

    Args:
        level: Base log level applied to the root logger.
        log_dir: Directory where the rotating log file is written.
        log_file: Name of the rotating log file.
        max_bytes: Maximum size of a single log file before rotation.
        backup_count: Number of rotated backup files to keep.
        console_level: Override level for the console handler.
        file_level: Override level for the file handler.
        console_format: Format string for the console handler.
        file_format: Format string for the file handler.
        propagate_root: Whether child loggers propagate to the root logger.

    Returns:
        The configured root logger.
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
        root.warning("Could not attach rotating file handler (%s); continuing with console only", exc)

    root.propagate = propagate_root
    _CONFIGURED = True
    return root


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a logger, configuring centralized logging on first use."""
    if not _CONFIGURED:
        setup_logging()
    return logging.getLogger(name)


def reset() -> None:
    """Remove all handlers and reset the configured flag (mostly for tests)."""
    global _CONFIGURED
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()
    _CONFIGURED = False

import logging
import logging.handlers
import os
import tempfile

from pathlib import Path


LOG_LINE = "test log message"


def _make_logger(log_dir, max_bytes=1024, backup_count=3):
    log_path = Path(log_dir) / "app.log"
    logger = logging.getLogger("test_logger_" + str(os.getpid()))
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    handler = logging.handlers.RotatingFileHandler(
        log_path,
        mode="a",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    return logger, handler, log_path


def test_log_written_to_file():
    with tempfile.TemporaryDirectory() as tmp:
        logger, handler, log_path = _make_logger(tmp)
        logger.info(LOG_LINE)
        handler.flush()
        handler.close()
        assert log_path.exists()
        content = log_path.read_text(encoding="utf-8")
        assert LOG_LINE in content
        assert "INFO" in content


def test_log_levels_recorded():
    with tempfile.TemporaryDirectory() as tmp:
        logger, handler, log_path = _make_logger(tmp)
        logger.debug("debug message")
        logger.warning("warning message")
        logger.error("error message")
        handler.flush()
        handler.close()
        content = log_path.read_text(encoding="utf-8")
        assert "DEBUG" in content
        assert "WARNING" in content
        assert "ERROR" in content


def test_rotation_creates_backups():
    with tempfile.TemporaryDirectory() as tmp:
        logger, handler, log_path = _make_logger(tmp, max_bytes=200, backup_count=3)
        for i in range(200):
            logger.info("rotating line %d %s", i, "x" * 40)
        handler.close()

        rotated = sorted(
            p for p in Path(tmp).glob("app.log*")
        )
        assert log_path.exists()
        backup_files = [p for p in rotated if p != log_path]
        assert len(backup_files) > 0


def test_rotation_respects_backup_count():
    with tempfile.TemporaryDirectory() as tmp:
        logger, handler, log_path = _make_logger(tmp, max_bytes=100, backup_count=2)
        for i in range(500):
            logger.info("line %d %s", i, "y" * 50)
        handler.close()

        backup_files = sorted(p for p in Path(tmp).glob("app.log.*"))
        assert len(backup_files) <= 2
        assert log_path.exists()


def test_new_logs_append_after_rotation():
    with tempfile.TemporaryDirectory() as tmp:
        logger, handler, log_path = _make_logger(tmp, max_bytes=100, backup_count=2)
        for i in range(50):
            logger.info("first batch %d %s", i, "z" * 50)
        handler.close()

        logger2, handler2, log_path2 = _make_logger(tmp, max_bytes=100, backup_count=2)
        logger2.info("appended after rotation")
        handler2.flush()
        handler2.close()

        content = log_path2.read_text(encoding="utf-8")
        assert "appended after rotation" in content


def test_existing_content_preserved_on_open():
    with tempfile.TemporaryDirectory() as tmp:
        logger, handler, log_path = _make_logger(tmp)
        logger.info("original content")
        handler.flush()
        handler.close()

        assert "original content" in log_path.read_text(encoding="utf-8")

        logger2, handler2, _ = _make_logger(tmp)
        logger2.info("more content")
        handler2.flush()
        handler2.close()

        content = log_path.read_text(encoding="utf-8")
        assert "original content" in content
        assert "more content" in content

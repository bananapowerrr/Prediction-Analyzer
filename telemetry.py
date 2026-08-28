"""Метрики и логирование сканера.

Provides:
  * ``Telemetry`` class that captures unhandled exceptions and system state
    and writes detailed, self-contained JSON reports to a configurable
    working directory.
  * ``install_exception_hook`` / ``setup`` helpers to wire the telemetry
    into the host application's ``sys.excepthook`` (and threading hook).

The module only depends on the Python standard library. Optional richer
system metrics (CPU/Memory/Disk usage) are collected when ``psutil`` is
installed; otherwise those fields are gracefully omitted.
"""

from __future__ import annotations

import datetime as _dt
import json
import logging
import os
import platform
import sys
import threading
import traceback
from types import TracebackType
from typing import Any, Callable, Dict, Optional, Tuple, Type

try:  # optional, richer metrics
    import psutil  # type: ignore
    _HAS_PSUTIL = True
except Exception:  # pragma: no cover - optional dependency
    psutil = None  # type: ignore
    _HAS_PSUTIL = False


logger = logging.getLogger("telemetry")


class TelemetryError(Exception):
    """Raised for unrecoverable errors inside the telemetry subsystem."""


class Telemetry:
    """Collects diagnostic data and persists it to disk on failures."""

    def __init__(self, log_dir: str = "telemetry_logs", app_name: str = "desktop-tutorial") -> None:
        self.app_name = app_name
        self.log_dir = log_dir
        self._lock = threading.RLock()
        self._ensured = False
        self._counters = {}
        self._last_scan_stats: Optional[Dict[str, Any]] = None
        self._scan_stats: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------ #
    # Filesystem helpers
    # ------------------------------------------------------------------ #
    def _ensure_dir(self) -> None:
        with self._lock:
            if not self._ensured:
                try:
                    os.makedirs(self.log_dir, exist_ok=True)
                except OSError as exc:
                    raise TelemetryError(
                        f"Cannot create telemetry directory {self.log_dir!r}: {exc}"
                    ) from exc
                self._ensured = True

    @staticmethod
    def _timestamp() -> str:
        return _dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    # ------------------------------------------------------------------ #
    # System state
    # ------------------------------------------------------------------ #
    def get_system_state(self) -> Dict[str, Any]:
        """Return a snapshot of the system / process state.

        Sensitive values (environment variable contents) are intentionally
        NOT captured to avoid leaking secrets such as private keys.
        """
        state: Dict[str, Any] = {
            "app_name": self.app_name,
            "timestamp": _dt.datetime.now().isoformat(timespec="seconds"),
            "python": {
                "version": platform.python_version(),
                "implementation": platform.python_implementation(),
                "executable": sys.executable,
                "argv": sys.argv,
            },
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "node": platform.node(),
            },
            "process": {
                "pid": os.getpid(),
                "ppid": os.getppid() if hasattr(os, "getppid") else None,
                "cwd": os.getcwd(),
                "uid": os.getuid() if hasattr(os, "getuid") else None,
                "open_files": self._safe_open_files(),
            },
            "runtime": {
                "thread_count": threading.active_count(),
                "threads": [t.name for t in threading.enumerate()],
                "modules_loaded": len(sys.modules),
            },
            "env_keys": sorted(os.environ.keys()),
        }

        working = self._disk_usage(os.getcwd())
        if working is not None:
            state["working_dir_disk"] = working

        if _HAS_PSUTIL:
            try:
                state["system_metrics"] = {
                    "cpu_count": psutil.cpu_count(),
                    "cpu_percent": psutil.cpu_percent(interval=None),
                    "memory": _as_dict(psutil.virtual_memory()),
                    "swap": _as_dict(psutil.swap_memory()),
                    "disk": _as_dict(psutil.disk_usage("/")),
                    "boot_time": _dt.datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                }
                state["process_metrics"] = {
                    "cpu_percent": psutil.Process().cpu_percent(interval=None),
                    "memory_info": _as_dict(psutil.Process().memory_info()),
                    "num_threads": psutil.Process().num_threads(),
                }
            except Exception as exc:  # pragma: no cover - defensive
                state["system_metrics_error"] = repr(exc)

        return state

    @staticmethod
    def _disk_usage(path: str) -> Optional[Dict[str, Any]]:
        try:
            usage = psutil.disk_usage(path) if _HAS_PSUTIL else None
        except Exception:
            usage = None
        if usage is None:
            return None
        return _as_dict(usage)

    @staticmethod
    def _safe_open_files() -> Optional[int]:
        if not _HAS_PSUTIL:
            return None
        try:
            return len(psutil.Process().open_files())
        except Exception:
            return None

    # ------------------------------------------------------------------ #
    # Dumping
    # ------------------------------------------------------------------ #
    def dump_state(self, reason: str = "manual") -> str:
        """Write a system-state snapshot to ``<log_dir>/state_*.json``."""
        self._ensure_dir()
        state_file = os.path.join(self.log_dir, f"state_{self._timestamp()}.json")
        payload = {
            "type": "state_dump",
            "reason": reason,
            "system_state": self.get_system_state(),
        }
        self._write_json(state_file, payload)
        logger.info("State dumped to %s", state_file)
        return state_file

    def log_exception(
        self,
        exc_type: Type[BaseException],
        exc_value: BaseException,
        exc_traceback: Optional[TracebackType],
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Persist a detailed diagnostic report for an exception."""
        self._ensure_dir()
        ts = self._timestamp()
        error_file = os.path.join(self.log_dir, f"error_{ts}.json")

        tb_text = "".join(
            traceback.format_exception(exc_type, exc_value, exc_traceback)
        )
        tb_frames = traceback.format_tb(exc_traceback) if exc_traceback else []

        report = {
            "type": "exception_report",
            "app_name": self.app_name,
            "timestamp": _dt.datetime.now().isoformat(timespec="microseconds"),
            "exception": {
                "type": exc_type.__name__ if exc_type else None,
                "module": getattr(exc_type, "__module__", None),
                "message": str(exc_value),
                "repr": repr(exc_value),
            },
            "traceback_text": tb_text,
            "traceback_frames": tb_frames,
            "context": context or {},
            "system_state": self.get_system_state(),
        }

        state_file = self.dump_state(reason=f"exception:{exc_type.__name__ if exc_type else 'unknown'}")
        report["companion_state_file"] = os.path.basename(state_file)

        self._write_json(error_file, report)

        logger.error(
            "Unhandled exception logged to %s\n%s", error_file, tb_text.strip()
        )
        return error_file

    # ------------------------------------------------------------------ #
    # Output writers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _write_json(path: str, payload: Dict[str, Any]) -> None:
        try:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=4, default=_json_default, ensure_ascii=False)
        except TypeError:
            # Fallback: strip non-serialisable data.
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=4, default=str, ensure_ascii=False)


def _as_dict(obj: Any) -> Dict[str, Any]:
    if hasattr(obj, "_asdict"):
        return dict(obj._asdict())
    if isinstance(obj, (int, float, str, bool)) or obj is None:
        return {"value": obj}
    return {"value": str(obj)}


def _json_default(obj: Any) -> Any:
    if isinstance(obj, (set, frozenset)):
        return sorted(obj)
    if isinstance(obj, TracebackType):
        return repr(obj)
    return str(obj)


# ---------------------------------------------------------------------- #
# Hook installation
# ---------------------------------------------------------------------- #
    def inc(self, name: str) -> None:
        """Increment the counter for the given name."""
        with self._lock:
            if name not in self._counters:
                self._counters[name] = 0
            self._counters[name] += 1

    def get(self, name: str) -> int:
        """Get the current value of the counter for the given name."""
        with self._lock:
            return self._counters.get(name, 0)

    def reset_all(self) -> None:
        """Reset all counters."""
        with self._lock:
            self._counters.clear()

    def record_scan(self, total: int, passed: int) -> None:
        """Record the results of a scan."""
        with self._lock:
            if name not in self._counters:
                self._counters[name] = 0
            self._counters[name] += 1

    def dump_counters(self) -> Dict[str, int]:
        """Return a copy of all counters."""
        with self._lock:
            return self._counters.copy()

    def get_counters(self) -> Dict[str, int]:
        """Get the current values of all counters."""
        with self._lock:
            return self._counters.copy()

    def last_scan_stats(self) -> Optional[Dict[str, Any]]:
        """Get the statistics of the last scan."""
        with self._lock:
            return self._scan_stats

    def dump_json(self, path: str) -> None:
        """Write the current state and counters to a JSON file."""
        self._ensure_dir()
        payload = {
            "type": "telemetry_dump",
            "app_name": self.app_name,
            "timestamp": _dt.datetime.now().isoformat(timespec="seconds"),
            "system_state": self.get_system_state(),
            "counters": self.get_counters(),
            "scan_stats": self.last_scan_stats(),
        }
        self._write_json(path, payload)
        logger.info("Telemetry data dumped to %s", path)

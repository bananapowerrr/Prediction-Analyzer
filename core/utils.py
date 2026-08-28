from typing import Any, Optional

def clamp(value: float, lo: float, hi: float) -> float:
    """Ограничивает значение value между lo и hi."""
    return max(lo, min(value, hi))

def safe_float(x: Any, default: float = 0.0) -> float:
    """Преобразует x в число с плавающей запятой, используя default в случае ошибки."""
    try:
        return float(x)
    except (ValueError, TypeError):
        return default

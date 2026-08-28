from typing import Any, Optional

def clamp(value: float, lo: float, hi: float) -> float:
    """Ограничивает значение value между lo и hi."""
    if value is None:
        raise ValueError("Value cannot be None")
    return max(lo, min(value, hi))

def safe_float(x: Any, default: float = 0.0) -> float:
    """Преобразует x в число с плавающей запятой, используя default в случае ошибки."""
    if x is None:
        return default
    try:
        return float(x)
    except (ValueError, TypeError):
        return default

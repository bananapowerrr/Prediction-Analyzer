def clamp(value, lo, hi):
    """Ограничивает значение value между lo и hi."""
    return max(lo, min(value, hi))

def safe_float(x, default=0.0):
    """Преобразует x в число с плавающей запятой, используя default в случае ошибки."""
    try:
        return float(x)
    except (ValueError, TypeError):
        return default

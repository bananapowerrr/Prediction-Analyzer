def clamp(value, lo, hi):
    return max(lo, min(value, hi))

def safe_float(x, default=0.0):
    try:
        return float(x)
    except (ValueError, TypeError):
        return default

import requests
from config import GAMMA_API_BASE, HTTP_TIMEOUT

class PolymarketClient:
    BASE = GAMMA_API_BASE
    
    def __init__(self, timeout: float = HTTP_TIMEOUT):
        self.timeout = timeout
    
    def fetch_markets(self, limit: int = 50) -> list:
        try:
            r = requests.get(
                f"{self.BASE}/markets",
                params={"limit": limit, "active": "true", "closed": "false"},
                timeout=self.timeout,
            )
            r.raise_for_status()
            data = r.json()
            return data if isinstance(data, list) else []
        except requests.RequestException:
            return []

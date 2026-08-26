import requests

class PolymarketClient:
    BASE = "https://gamma-api.polymarket.com"
    
    def __init__(self, timeout: float = 30.0):
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

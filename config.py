from pydantic_settings import BaseSettings, SettingsConfigDict


class RpcSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RPC_")

    endpoint: str = "https://polygon-rpc.com"
    chain_id: int = 137
    private_key: str = ""


class LiquidityGateSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LIQUIDITY_")

    min_liquidity_usd: float = 1000.0
    min_volume_24h: float = 0.0


class SpreadSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SPREAD_")

    max_spread_pct: float = 0.1


class ConnectionSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CONN_")

    gamma_api_base: str = "https://gamma-api.polymarket.com"
    http_timeout: float = 30.0
    scan_limit: int = 50


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    rpc: RpcSettings = RpcSettings()
    liquidity_gate: LiquidityGateSettings = LiquidityGateSettings()
    spread: SpreadSettings = SpreadSettings()
    connection: ConnectionSettings = ConnectionSettings()


settings = Settings()


MIN_LIQUIDITY_USD = settings.liquidity_gate.min_liquidity_usd
MAX_SPREAD_PCT = settings.spread.max_spread_pct
SCAN_LIMIT = settings.connection.scan_limit
GAMMA_API_BASE = settings.connection.gamma_api_base
MIN_VOLUME_24H = settings.liquidity_gate.min_volume_24h
HTTP_TIMEOUT = settings.connection.http_timeout


config = settings

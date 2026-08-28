"""
Настройки Prediction Analyzer из environment переменных.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class RpcSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RPC_")

    endpoint: str = "https://polygon-rpc.com"
    endpoints: str = ""
    chain_id: int = 137
    private_key: str = ""
    cooldown_seconds: float = 60.0
    max_retries: int = 3
    timeout_seconds: float = 10.0
    request_timeout: float = 30.0

    @property
    def endpoint_list(self) -> list:
        primary = [self.endpoint] if self.endpoint else []
        extra = [e.strip() for e in self.endpoints.split(",") if e.strip()]
        seen: dict = {}
        result = []
        for ep in primary + extra:
            if ep not in seen:
                seen[ep] = True
                result.append(ep)
        return result or [self.endpoint]


class BaseRpcSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BASE_RPC_")

    endpoint: str = "https://mainnet.base.org"
    endpoints: str = ""
    chain_id: int = 8453
    private_key: str = ""
    cooldown_seconds: float = 60.0
    max_retries: int = 3
    timeout_seconds: float = 10.0
    request_timeout: float = 30.0

    @property
    def endpoint_list(self) -> list:
        primary = [self.endpoint] if self.endpoint else []
        extra = [e.strip() for e in self.endpoints.split(",") if e.strip()]
        seen: dict = {}
        result = []
        for ep in primary + extra:
            if ep not in seen:
                seen[ep] = True
                result.append(ep)
        return result or [self.endpoint]


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


class CloudTierSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CLOUD_")

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    openrouter_api_key: str = ""
    openrouter_model: str = "meta-llama/llama-3.3-70b-versatile"
    timeout: float = 30.0
    max_concurrent: int = 5


class LocalTierSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LOCAL_")

    ollama_base_url: str = "http://localhost:11434"
    judge_model: str = "qwen2.5-coder:7b"
    timeout: float = 120.0
    temperature: float = 0.3


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    rpc: RpcSettings = RpcSettings()
    base_rpc: BaseRpcSettings = BaseRpcSettings()
    liquidity_gate: LiquidityGateSettings = LiquidityGateSettings()
    spread: SpreadSettings = SpreadSettings()
    connection: ConnectionSettings = ConnectionSettings()
    cloud: CloudTierSettings = CloudTierSettings()
    local: LocalTierSettings = LocalTierSettings()


settings = Settings()


MIN_LIQUIDITY_USD = settings.liquidity_gate.min_liquidity_usd
MAX_SPREAD_PCT = settings.spread.max_spread_pct
SCAN_LIMIT = settings.connection.scan_limit
GAMMA_API_BASE = settings.connection.gamma_api_base
MIN_VOLUME_24H = settings.liquidity_gate.min_volume_24h
HTTP_TIMEOUT = settings.connection.http_timeout


config = settings

BASE_RPC_ENDPOINT = settings.base_rpc.endpoint
BASE_RPC_CHAIN_ID = settings.base_rpc.chain_id
BASE_RPC_PRIVATE_KEY = settings.base_rpc.private_key

RPC_ENDPOINTS = settings.rpc.endpoint_list
RPC_CHAIN_ID = settings.rpc.chain_id
RPC_COOLDOWN = settings.rpc.cooldown_seconds
RPC_MAX_RETRIES = settings.rpc.max_retries
RPC_TIMEOUT = settings.rpc.timeout_seconds
RPC_REQUEST_TIMEOUT = settings.rpc.request_timeout

BASE_RPC_ENDPOINTS = settings.base_rpc.endpoint_list
BASE_RPC_COOLDOWN = settings.base_rpc.cooldown_seconds

CLOUD_GROQ_API_KEY = settings.cloud.groq_api_key
CLOUD_GROQ_MODEL = settings.cloud.groq_model
CLOUD_GEMINI_API_KEY = settings.cloud.gemini_api_key
CLOUD_GEMINI_MODEL = settings.cloud.gemini_model
CLOUD_OPENROUTER_API_KEY = settings.cloud.openrouter_api_key
CLOUD_OPENROUTER_MODEL = settings.cloud.openrouter_model
CLOUD_TIMEOUT = settings.cloud.timeout
CLOUD_MAX_CONCURRENT = settings.cloud.max_concurrent

LOCAL_OLLAMA_BASE_URL = settings.local.ollama_base_url
LOCAL_JUDGE_MODEL = settings.local.judge_model
LOCAL_TIMEOUT = settings.local.timeout
LOCAL_TEMPERATURE = settings.local.temperature

APP_NAME = 'prediction-analyzer'
APP_TITLE = 'Prediction Analyzer'

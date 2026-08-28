import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from core.models import MarketSchema, validate_market_data

logger = logging.getLogger(__name__)

__all__ = ["CloudAnalysis", "JudgeVerdict", "PipelineResult", "CloudTier", "LocalTier", "HybridPipeline"]


@dataclass
class CloudAnalysis:
    provider: str
    confidence: float
    reasoning: str
    indicators: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "indicators": self.indicators,
        }


@dataclass
class JudgeVerdict:
    decision: str
    confidence: float
    reasoning: str
    action: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "action": self.action,
        }


@dataclass
class PipelineResult:
    market: Any
    verdicts: Any = None

    def __init__(self, market: Any, verdicts: Any = None):
        self.market = market
        self.verdicts = verdicts

    @property
    def market_id(self) -> str:
        if isinstance(self.market, dict):
            return self.market.get("id", "unknown")
        if isinstance(self.market, MarketSchema):
            return self.market.id
        return str(getattr(self.market, "id", "unknown"))

    @property
    def cloud_analyses(self) -> List[CloudAnalysis]:
        if isinstance(self.verdicts, list):
            return [v for v in self.verdicts if isinstance(v, CloudAnalysis)]
        return []

    @property
    def verdict(self) -> Optional[JudgeVerdict]:
        if isinstance(self.verdicts, JudgeVerdict):
            return self.verdicts
        if isinstance(self.verdicts, dict):
            return JudgeVerdict(**self.verdicts)
        return None


class CloudTier:
    """Primary scanning, filtering and summarization tier using cloud LLMs."""

    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent

    async def _call_openai_compat(self, provider_name: str, prompt: str, session: Any) -> str:
        raise NotImplementedError("Cloud provider integration not yet implemented")

    async def _call_gemini(self, prompt: str, session: Any) -> str:
        raise NotImplementedError("Gemini integration not yet implemented")

    def _build_analysis_prompt(self, market_data: Dict[str, Any]) -> str:
        return (
            f"Analyze the following prediction market:\n"
            f"Question: {market_data.get('question', 'N/A')}\n"
            f"Liquidity: ${market_data.get('liquidity', 0):,.2f}\n"
            f"Spread: {market_data.get('spread', 0):.4f}\n"
            f"24h Volume: ${market_data.get('volume_24h', 0):,.2f}\n"
            f"Provide confidence (0-1), reasoning, and key indicators."
        )

    def _parse_cloud_response(self, provider: str, raw: str) -> CloudAnalysis:
        return CloudAnalysis(
            provider=provider,
            confidence=0.5,
            reasoning=raw[:500] if raw else "No response",
            indicators={},
        )

    async def _analyze_single(self, provider_name: str, market_data: Dict[str, Any], session: Any) -> CloudAnalysis:
        prompt = self._build_analysis_prompt(market_data)
        try:
            raw = await self._call_openai_compat(provider_name, prompt, session)
            return self._parse_cloud_response(provider_name, raw)
        except Exception as e:
            logger.error("Cloud analysis failed for %s: %s", provider_name, e)
            return CloudAnalysis(provider=provider_name, confidence=0.0, reasoning=f"Error: {e}")

    async def analyze(self, market_data: Dict[str, Any]) -> List[CloudAnalysis]:
        async with asyncio.ClientSession() as session:
            tasks = [self._analyze_single(name, market_data, session) for name in ["groq", "gemini"]]
            return list(await asyncio.gather(*tasks))


class LocalTier:
    """Judge tier using local Ollama for final decision in isolated environment."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5-coder:7b"):
        self.base_url = base_url
        self.model = model

    def _build_judge_prompt(self, market_data: Dict[str, Any], cloud_analyses: List[CloudAnalysis]) -> str:
        analyses_text = "\n".join(
            f"- {a.provider}: confidence={a.confidence:.2f}, reasoning={a.reasoning[:200]}"
            for a in cloud_analyses
        )
        return (
            f"Market: {market_data.get('question', 'N/A')}\n"
            f"Cloud analyses:\n{analyses_text}\n"
            f"Provide a final verdict: decision, confidence, reasoning, and action."
        )

    def _parse_verdict(self, raw: str) -> JudgeVerdict:
        return JudgeVerdict(
            decision="hold",
            confidence=0.5,
            reasoning=raw[:500] if raw else "No response",
            action="hold",
        )

    async def judge(self, market_data: Dict[str, Any], cloud_analyses: List[CloudAnalysis]) -> JudgeVerdict:
        prompt = self._build_judge_prompt(market_data, cloud_analyses)
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                payload = {"model": self.model, "prompt": prompt, "stream": False}
                async with session.post(f"{self.base_url}/api/generate", json=payload) as resp:
                    data = await resp.json()
                    raw = data.get("response", "")
                    return self._parse_verdict(raw)
        except Exception as e:
            logger.error("Local judge failed: %s", e)
            return JudgeVerdict(decision="hold", confidence=0.0, reasoning=f"Error: {e}", action="hold")


class HybridPipeline:
    """Two-tier pipeline: cloud tier for analysis, local tier for final verdict."""

    def __init__(self):
        self.cloud_tier = CloudTier()
        self.local_tier = LocalTier()

    async def process_market(self, market_data: Dict[str, Any]) -> PipelineResult:
        if not market_data:
            return PipelineResult(market={}, verdicts=JudgeVerdict(decision="hold", confidence=0.0, reasoning="No data", action="hold"))
        validated = validate_market_data(market_data)
        market_dict = {
            "id": validated.id,
            "question": validated.question,
            "liquidity": validated.liquidity,
            "spread": validated.spread,
            "volume_24h": validated.volume_24h,
        }
        cloud_analyses = await self.cloud_tier.analyze(market_dict)
        verdict = await self.local_tier.judge(market_dict, cloud_analyses)
        return PipelineResult(market=market_dict, verdicts=verdict)

    async def process_batch(self, markets: List[Dict[str, Any]]) -> List[PipelineResult]:
        results = []
        for market in markets:
            try:
                result = await self.process_market(market)
                results.append(result)
            except Exception as e:
                logger.error("Pipeline failed for market %s: %s", market.get("id", "?"), e)
        return results

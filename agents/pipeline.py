from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import aiohttp

import config

logger = logging.getLogger(__name__)


@dataclass
class CloudAnalysis:
    provider: str
    summary: str
    sentiment: float
    risk_score: float
    confidence: float
    raw_response: str = ""


@dataclass
class JudgeVerdict:
    decision: str
    reasoning: str
    final_score: float
    action: str
    raw_response: str = ""


@dataclass
class PipelineResult:
    market_id: str
    cloud_analyses: List[CloudAnalysis] = field(default_factory=list)
    verdict: Optional[JudgeVerdict] = None
    error: Optional[str] = None


class CloudTier:
    """Primary scanning, filtering and summarization tier using cloud LLMs."""

    def __init__(self, max_concurrent: int = config.CLOUD_MAX_CONCURRENT):
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._providers = self._build_providers()

    def _build_providers(self) -> Dict[str, Dict[str, Any]]:
        providers: Dict[str, Dict[str, Any]] = {}
        if config.CLOUD_GROQ_API_KEY:
            providers["groq"] = {
                "base_url": "https://api.groq.com/openai/v1",
                "api_key": config.CLOUD_GROQ_API_KEY,
                "model": config.CLOUD_GROQ_MODEL,
            }
        if config.CLOUD_GEMINI_API_KEY:
            providers["gemini"] = {
                "base_url": "https://generativelanguage.googleapis.com/v1beta",
                "api_key": config.CLOUD_GEMINI_API_KEY,
                "model": config.CLOUD_GEMINI_MODEL,
            }
        if config.CLOUD_OPENROUTER_API_KEY:
            providers["openrouter"] = {
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": config.CLOUD_OPENROUTER_API_KEY,
                "model": config.CLOUD_OPENROUTER_MODEL,
            }
        return providers

    async def _call_openai_compat(
        self, provider_name: str, prompt: str, session: aiohttp.ClientSession
    ) -> str:
        info = self._providers[provider_name]
        headers = {
            "Authorization": f"Bearer {info['api_key']}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": info["model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4,
            "max_tokens": 1024,
        }
        url = f"{info['base_url']}/chat/completions"
        async with self._semaphore:
            try:
                async with session.post(
                    url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=config.CLOUD_TIMEOUT)
                ) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        logger.warning("Cloud %s returned %d: %s", provider_name, resp.status, body[:200])
                        return ""
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
            except Exception as exc:
                logger.warning("Cloud %s error: %s", provider_name, exc)
                return ""

    async def _call_gemini(self, prompt: str, session: aiohttp.ClientSession) -> str:
        info = self._providers["gemini"]
        url = (
            f"{info['base_url']}/models/{info['model']}:generateContent"
            f"?key={info['api_key']}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 1024},
        }
        async with self._semaphore:
            try:
                async with session.post(
                    url, json=payload, timeout=aiohttp.ClientTimeout(total=config.CLOUD_TIMEOUT)
                ) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        logger.warning("Gemini returned %d: %s", resp.status, body[:200])
                        return ""
                    data = await resp.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
            except Exception as exc:
                logger.warning("Gemini error: %s", exc)
                return ""

    def _build_analysis_prompt(self, market_data: Dict[str, Any]) -> str:
        return (
            "You are a prediction market analyst. Analyze the following market and provide:\n"
            "1. A brief summary (1-2 sentences)\n"
            "2. Sentiment score from -1.0 (very bearish) to 1.0 (very bullish)\n"
            "3. Risk score from 0.0 (no risk) to 1.0 (maximum risk)\n"
            "4. Confidence in your analysis from 0.0 to 1.0\n\n"
            "Respond ONLY with valid JSON in this format:\n"
            '{"summary": "...", "sentiment": 0.0, "risk_score": 0.0, "confidence": 0.0}\n\n'
            f"Market data:\n{json.dumps(market_data, indent=2, ensure_ascii=False)}"
        )

    def _parse_cloud_response(self, provider: str, raw: str) -> CloudAnalysis:
        try:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                cleaned = "\n".join(lines)
            parsed = json.loads(cleaned)
            return CloudAnalysis(
                provider=provider,
                summary=parsed.get("summary", ""),
                sentiment=float(parsed.get("sentiment", 0.0)),
                risk_score=float(parsed.get("risk_score", 0.5)),
                confidence=float(parsed.get("confidence", 0.5)),
                raw_response=raw,
            )
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Failed to parse %s response: %s", provider, exc)
            return CloudAnalysis(
                provider=provider,
                summary=raw[:200] if raw else "No response",
                sentiment=0.0,
                risk_score=0.5,
                confidence=0.0,
                raw_response=raw,
            )

    async def _analyze_single(
        self, provider_name: str, market_data: Dict[str, Any], session: aiohttp.ClientSession
    ) -> Optional[CloudAnalysis]:
        prompt = self._build_analysis_prompt(market_data)
        if provider_name == "gemini":
            raw = await self._call_gemini(prompt, session)
        else:
            raw = await self._call_openai_compat(provider_name, prompt, session)
        if not raw:
            return None
        return self._parse_cloud_response(provider_name, raw)

    async def analyze(self, market_data: Dict[str, Any]) -> List[CloudAnalysis]:
        if not self._providers:
            logger.warning("No cloud providers configured, using fallback")
            return [CloudAnalysis(provider="fallback", summary="No cloud providers available", sentiment=0.0, risk_score=0.5, confidence=0.0)]
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._analyze_single(name, market_data, session)
                for name in self._providers
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        analyses: List[CloudAnalysis] = []
        for r in results:
            if isinstance(r, CloudAnalysis):
                analyses.append(r)
            elif isinstance(r, Exception):
                logger.warning("Cloud analysis task failed: %s", r)
        return analyses


class LocalTier:
    """Judge tier using local Ollama for final decision in isolated environment."""

    def __init__(
        self,
        base_url: str = config.LOCAL_OLLAMA_BASE_URL,
        model: str = config.LOCAL_JUDGE_MODEL,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def _build_judge_prompt(
        self, market_data: Dict[str, Any], cloud_analyses: List[CloudAnalysis]
    ) -> str:
        analyses_text = ""
        for a in cloud_analyses:
            analyses_text += (
                f"\n--- {a.provider.upper()} ---\n"
                f"Summary: {a.summary}\n"
                f"Sentiment: {a.sentiment}\n"
                f"Risk: {a.risk_score}\n"
                f"Confidence: {a.confidence}\n"
            )
        return (
            "You are the Judge in a Hybrid Intelligence Pipeline. "
            "You receive cloud-tier analyses and make the final decision in a private, isolated environment.\n\n"
            "Market data:\n"
            f"{json.dumps(market_data, indent=2, ensure_ascii=False)}\n\n"
            "Cloud-tier analyses:\n"
            f"{analyses_text}\n"
            "Based on the above, provide your final verdict. Respond ONLY with valid JSON:\n"
            '{"decision": "YES|NO|ABSTAIN", "reasoning": "...", '
            '"final_score": 0.0, "action": "BUY|SELL|HOLD|SKIP"}'
        )

    def _parse_verdict(self, raw: str) -> JudgeVerdict:
        try:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                cleaned = "\n".join(lines)
            parsed = json.loads(cleaned)
            return JudgeVerdict(
                decision=parsed.get("decision", "ABSTAIN"),
                reasoning=parsed.get("reasoning", ""),
                final_score=float(parsed.get("final_score", 0.0)),
                action=parsed.get("action", "SKIP"),
                raw_response=raw,
            )
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Failed to parse judge response: %s", exc)
            return JudgeVerdict(
                decision="ABSTAIN",
                reasoning=f"Parse error: {exc}",
                final_score=0.0,
                action="SKIP",
                raw_response=raw,
            )

    async def judge(
        self, market_data: Dict[str, Any], cloud_analyses: List[CloudAnalysis]
    ) -> JudgeVerdict:
        prompt = self._build_judge_prompt(market_data, cloud_analyses)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": config.LOCAL_TEMPERATURE},
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=config.LOCAL_TIMEOUT),
                ) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        logger.error("Ollama returned %d: %s", resp.status, body[:200])
                        return JudgeVerdict(
                            decision="ABSTAIN",
                            reasoning=f"Ollama error: {resp.status}",
                            final_score=0.0,
                            action="SKIP",
                        )
                    data = await resp.json()
                    raw = data.get("response", "")
                    return self._parse_verdict(raw)
        except Exception as exc:
            logger.error("Ollama connection failed: %s", exc)
            return JudgeVerdict(
                decision="ABSTAIN",
                reasoning=f"Connection error: {exc}",
                final_score=0.0,
                action="SKIP",
            )


class HybridPipeline:
    """Two-tier pipeline: cloud tier for analysis, local tier for final verdict."""

    def __init__(self):
        self.cloud = CloudTier()
        self.local = LocalTier()

    async def process_market(self, market_data: Dict[str, Any]) -> PipelineResult:
        market_id = market_data.get("id", "unknown")
        logger.info("Processing market %s through hybrid pipeline", market_id)
        cloud_analyses = await self.cloud.analyze(market_data)
        logger.info("Received %d cloud analyses for market %s", len(cloud_analyses), market_id)
        verdict = await self.local.judge(market_data, cloud_analyses)
        logger.info("Judge verdict for %s: %s (%s)", market_id, verdict.decision, verdict.action)
        return PipelineResult(
            market_id=market_id,
            cloud_analyses=cloud_analyses,
            verdict=verdict,
        )

    async def process_batch(self, markets: List[Dict[str, Any]]) -> List[PipelineResult]:
        tasks = [self.process_market(m) for m in markets]
        return await asyncio.gather(*tasks, return_exceptions=False)

import asyncio
from dataclasses import dataclass
from typing import Dict, Any, List

@dataclass
class CloudAnalysis:
    # ... (rest of the class)

@dataclass
class JudgeVerdict:
    # ... (rest of the class)

@dataclass
class PipelineResult:
    # ... (rest of the class)

class CloudTier:
    """Primary scanning, filtering and summarization tier using cloud LLMs."""

    def __init__(self, max_concurrent: int = config.CLOUD_MAX_CONCURRENT):
        # ... (rest of the class)

    async def _call_openai_compat(self, provider_name: str, prompt: str, session: aiohttp.ClientSession):
        # ... (rest of the method)

    async def _call_gemini(self, prompt: str, session: aiohttp.ClientSession) -> str:
        # ... (rest of the method)

    def _build_analysis_prompt(self, market_data: Dict[str, Any]) -> str:
        # ... (rest of the method)

    def _parse_cloud_response(self, provider: str, raw: str) -> CloudAnalysis:
        # ... (rest of the method)

    async def _analyze_single(self, provider_name: str, market_data: Dict[str, Any], session: aiohttp.ClientSession):
        # ... (rest of the method)

    async def analyze(self, market_data: Dict[str, Any]) -> List[CloudAnalysis]:
        # ... (rest of the method)

class LocalTier:
    """Judge tier using local Ollama for final decision in isolated environment."""

    def __init__(self, base_url: str = config.LOCAL_OLLAMA_BASE_URL, model: str = config.LOCAL_JUDGE_MODEL):
        # ... (rest of the class)

    def _build_judge_prompt(self, market_data: Dict[str, Any], cloud_analyses: List[CloudAnalysis]):
        # ... (rest of the method)

    def _parse_verdict(self, raw: str) -> JudgeVerdict:
        # ... (rest of the method)

    async def judge(self, market_data: Dict[str, Any], cloud_analyses: List[CloudAnalysis]):
        # ... (rest of the method)

class HybridPipeline:
    """Two-tier pipeline: cloud tier for analysis, local tier for final verdict."""

    def __init__(self):
        self.cloud_tier = CloudTier()
        self.local_tier = LocalTier()

    async def process_market(self, market_data: Dict[str, Any]) -> PipelineResult:
        cloud_analyses = await self.cloud_tier.analyze(market_data)
        verdict = await self.local_tier.judge(market_data, cloud_analyses)
        return PipelineResult(cloud_analyses, verdict)

    async def process_batch(self, markets: List[Dict[str, Any]]) -> List[PipelineResult]:
        results = []
        for market in markets:
            result = await self.process_market(market)
            results.append(result)
        return results

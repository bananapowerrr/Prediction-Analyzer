from __future__ import annotations

import asyncio
import json
import logging
from typing import Dict, List

from agents.pipeline import HybridPipeline, PipelineResult

logger = logging.getLogger(__name__)


async def run_agent(agent, context: Dict) -> Dict:
    return await agent(context)


async def gather_agents(agents: List[callable], context: Dict) -> Dict:
    results = await asyncio.gather(*[run_agent(agent, context) for agent in agents])
    return {
        "analyst": results[0],
        "critic": results[1],
        "judge": results[2],
    }


async def run_pipeline_on_markets(markets: List[Dict]) -> List[PipelineResult]:
    pipeline = HybridPipeline()
    return await pipeline.process_batch(markets)


async def main():
    pipeline = HybridPipeline()
    sample_market = {
        "id": "test-market-1",
        "question": "Will ETH exceed $5000 by end of 2026?",
        "liquidity": 50000.0,
        "spread": 0.02,
        "volume_24h": 12000.0,
    }
    result = await pipeline.process_market(sample_market)
    print(json.dumps({
        "market_id": result.market_id,
        "analyses_count": len(result.cloud_analyses),
        "verdict": {
            "decision": result.verdict.decision if result.verdict else None,
            "reasoning": result.verdict.reasoning if result.verdict else None,
            "action": result.verdict.action if result.verdict else None,
        } if result.verdict else None,
    }, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())

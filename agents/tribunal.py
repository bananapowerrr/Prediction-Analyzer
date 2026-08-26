import asyncio
import json
from typing import Dict, List

async def run_agent(agent, context):
    return await agent(context)

async def gather_agents(agents: List[callable], context: Dict) -> Dict:
    results = await asyncio.gather(*[run_agent(agent, context) for agent in agents])
    return {
        "analyst": results[0],
        "critic": results[1],
        "judge": results[2]
    }

async def main():
    # Пример агентов
    async def analyst(context):
        return {"analyst": "Analysis result"}

    async def critic(context):
        return {"critic": "Critic result"}

    async def judge(context):
        return {"judge": "Judgment result"}

    context = {"key": "value"}
    verdict = await gather_agents([analyst, critic, judge], context)
    print(json.dumps(verdict, indent=4))

if __name__ == "__main__":
    asyncio.run(main())

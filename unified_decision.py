from dataclasses import dataclass
from typing import List, Dict, Any
from agents.pipeline import CloudAnalysis, JudgeVerdict

@dataclass
class UnifiedDecision:
    cloud_analyses: List[Dict[str, Any]]
    judge_verdict: Dict[str, Any]
    final_decision: str
    reasoning: str

    def __post_init__(self):
        self.cloud_analyses = [CloudAnalysis(**analysis) for analysis in self.cloud_analyses]
        self.judge_verdict = JudgeVerdict(**self.judge_verdict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cloud_analyses": [analysis.to_dict() for analysis in self.cloud_analyses],
            "judge_verdict": self.judge_verdict.to_dict(),
            "final_decision": self.final_decision,
            "reasoning": self.reasoning
        }

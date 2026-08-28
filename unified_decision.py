from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from agents.pipeline import CloudAnalysis, JudgeVerdict

@dataclass
class UnifiedDecision:
    cloud_analyses: List[Dict[str, Any]]
    judge_verdict: Dict[str, Any] = None
    final_decision: str = ""
    reasoning: str = ""

    def __post_init__(self):
        converted = []
        for analysis in self.cloud_analyses:
            if isinstance(analysis, dict):
                try:
                    converted.append(CloudAnalysis(**analysis))
                except TypeError:
                    converted.append(analysis)
            else:
                converted.append(analysis)
        self.cloud_analyses = converted
        if isinstance(self.judge_verdict, dict):
            try:
                self.judge_verdict = JudgeVerdict(**self.judge_verdict)
            except TypeError:
                pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cloud_analyses": [a.to_dict() if isinstance(a, CloudAnalysis) else a for a in self.cloud_analyses],
            "judge_verdict": self.judge_verdict.to_dict() if isinstance(self.judge_verdict, JudgeVerdict) else self.judge_verdict,
            "final_decision": self.final_decision,
            "reasoning": self.reasoning
        }

    def _analysis_decision(self, analysis) -> Optional[str]:
        if isinstance(analysis, CloudAnalysis):
            return getattr(analysis, "decision", None) or getattr(analysis, "action", None)
        if isinstance(analysis, dict):
            return analysis.get("decision") or analysis.get("action")
        return getattr(analysis, "decision", None)

    def decide(self) -> str:
        """Возвращает решение по большинству голосов.

        При нехватке данных (пустой/недостаточный набор анализов, либо
        непредвиденная ошибка обработки) возвращает hold/skip без возбуждения
        исключения.
        """
        try:
            analyses = self.cloud_analyses or []
            decisions = [self._analysis_decision(a) for a in analyses]
            decisions = [d for d in decisions if d]

            if not decisions:
                return "skip"

            counts: Dict[str, int] = {}
            for d in decisions:
                counts[d] = counts.get(d, 0) + 1
            best = max(counts.values())
            majority = [d for d in decisions if counts[d] == best]
            for d in decisions:
                if d in majority:
                    return d
            return "hold"
        except Exception:
            return "hold"

def pipeline_decide(market: Dict[str, Any], signal_action: str, risk_ok: bool) -> Dict[str, Any]:
    """
    Определяет действие на основе анализа и вердикта.

    :param market: Словарь с данными рынка.
    :param signal_action: Действие, полученное от сигнальной системы.
    :param risk_ok: Флаг, указывающий на допустимость риска.
    :return: Словарь с ключами action, execute (bool) и reason (str).
    """
    decision = {
        "action": signal_action,
        "execute": False,
        "reason": "Недостаточно данных для принятия решения"
    }

    # Пример логики для принятия решения
    if risk_ok:
        decision["execute"] = True
        decision["reason"] = "Риск допустим, действие разрешено"

    return decision

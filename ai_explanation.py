class AIExplanation:
    def __init__(self, summary, risk_factors):
        self.summary = summary
        self.risk_factors = risk_factors

    def __str__(self):
        return f"Summary: {self.summary}\nRisk Factors: {self.risk_factors}"

    def to_dict(self):
        return {
            "summary": self.summary,
            "risk_factors": self.risk_factors
        }

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

def format_explanation(market_question: str, action: str, confidence: float) -> str:
    """
    Форматирует объяснение для арбитража на русском языке.

    :param market_question: Вопрос рынка
    :param action: Действие (например, "Buy" или "Sell")
    :param confidence: Уверенность в действиях
    :return: Строка-пояснение
    """
    explanation = f"Для вопроса рынка '{market_question}' рекомендуется {action}."
    explanation += f"\nУверенность: {confidence:.2f}%."
    return explanation

def format_explanations(items: list[tuple]) -> list[str]:
    """
    Форматирует список объяснений для арбитража на русском языке.

    :param items: Список кортежей (вопрос рынка, действие, уверенность)
    :return: Список строк-пояснений
    """
    explanations = []
    for market_question, action, confidence in items:
        explanation = format_explanation(market_question, action, confidence)
        explanations.append(explanation)
    return explanations

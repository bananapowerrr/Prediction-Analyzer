import unittest
from ai_explanation import format_explanation, format_explanations

CONF_PREFIX = "Уверенность: "


class TestAIConfPhrase(unittest.TestCase):

    def _conf_line(self, confidence):
        text = format_explanation("Вопрос рынка", "Buy", confidence)
        for line in text.splitlines():
            if line.startswith(CONF_PREFIX):
                return line
        self.fail("Строка уверенности не найдена в объяснении")

    def test_confidence_phrase_present(self):
        self.assertIn(CONF_PREFIX, format_explanation("Q", "Buy", 0.5))

    def test_confidence_phrase_value_format(self):
        line = self._conf_line(0.95)
        self.assertEqual(line, "Уверенность: 0.95%.")

    def test_confidence_phrase_two_decimals(self):
        line = self._conf_line(0.5)
        self.assertEqual(line, "Уверенность: 0.50%.")

    def test_confidence_phrase_rounding(self):
        line = self._conf_line(0.999)
        self.assertEqual(line, "Уверенность: 1.00%.")

    def test_confidence_phrase_zero(self):
        self.assertEqual(self._conf_line(0.0), "Уверенность: 0.00%.")

    def test_confidence_phrase_one(self):
        self.assertEqual(self._conf_line(1.0), "Уверенность: 1.00%.")

    def test_confidence_phrase_contains_dot_percent(self):
        line = self._conf_line(0.75)
        self.assertTrue(line.endswith("%."))

    def test_confidence_phrase_action_and_question_kept(self):
        text = format_explanation("Пойдёт ли дождь?", "Sell", 0.1234)
        self.assertIn("Пойдёт ли дождь?", text)
        self.assertIn("Sell", text)
        self.assertIn("Уверенность: 0.12%.", text)

    def test_confidence_phrase_uses_fraction_not_percent(self):
        line = self._conf_line(0.95)
        self.assertNotIn("95.00%", line)

    def test_format_explanations_contains_confidence_phrases(self):
        items = [
            ("Вопрос А", "Buy", 0.90),
            ("Вопрос Б", "Sell", 0.40),
        ]
        result = format_explanations(items)
        self.assertEqual(len(result), 2)
        self.assertTrue(all("Уверенность:" in text for text in result))


if __name__ == "__main__":
    unittest.main()

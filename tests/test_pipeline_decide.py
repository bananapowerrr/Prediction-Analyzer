# создано диспетчером для привязки Aider

import unittest
from unittest.mock import Mock
from agents.pipeline import CloudAnalysis, JudgeVerdict, PipelineResult
from unified_decision import UnifiedDecision

class TestPipelineDecide(unittest.TestCase):

    def test_pipeline_decide_with_cloud_analysis(self):
        cloud_analysis = CloudAnalysis(provider="AWS", decision="approve")
        judge_verdict = JudgeVerdict(decision="approve")
        unified_decision = UnifiedDecision(cloud_analyses=[cloud_analysis.to_dict()], judge_verdict=judge_verdict.to_dict())

        result = unified_decision.to_dict()
        self.assertIn("cloud_analyses", result)
        self.assertIn("judge_verdict", result)
        self.assertEqual(result["cloud_analyses"][0]["provider"], "AWS")
        self.assertEqual(result["judge_verdict"]["decision"], "approve")

    def test_pipeline_decide_with_reject_cloud_analysis(self):
        cloud_analysis = CloudAnalysis(provider="AWS", decision="reject")
        judge_verdict = JudgeVerdict(decision="approve")
        unified_decision = UnifiedDecision(cloud_analyses=[cloud_analysis.to_dict()], judge_verdict=judge_verdict.to_dict())

        result = unified_decision.to_dict()
        self.assertIn("cloud_analyses", result)
        self.assertIn("judge_verdict", result)
        self.assertEqual(result["cloud_analyses"][0]["provider"], "AWS")
        self.assertEqual(result["judge_verdict"]["decision"], "approve")

    def test_pipeline_decide_with_empty_cloud_analyses(self):
        judge_verdict = JudgeVerdict(decision="approve")
        unified_decision = UnifiedDecision(cloud_analyses=[], judge_verdict=judge_verdict.to_dict())

        result = unified_decision.to_dict()
        self.assertIn("cloud_analyses", result)
        self.assertIn("judge_verdict", result)
        self.assertEqual(result["cloud_analyses"], [])
        self.assertEqual(result["judge_verdict"]["decision"], "approve")

if __name__ == '__main__':
    unittest.main()

import unittest
from telemetry import Telemetry

class TestTelemetryCounter(unittest.TestCase):
    def setUp(self):
        self.telemetry = Telemetry()

    def test_inc(self):
        self.telemetry.inc("counter")
        self.assertEqual(self.telemetry.get("counter"), 1)

    def test_get(self):
        self.telemetry.inc("counter")
        self.assertEqual(self.telemetry.get("counter"), 1)

    def test_reset_all(self):
        self.telemetry.inc("counter")
        self.telemetry.reset_all()
        self.assertEqual(self.telemetry.get("counter"), 0)

if __name__ == '__main__':
    unittest.main()

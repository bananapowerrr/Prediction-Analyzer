import unittest
from agents.echo import EchoAgent

class TestEchoAgent(unittest.TestCase):
    def test_echo(self):
        agent = EchoAgent()
        response = agent.process("Hello, World!")
        self.assertEqual(response, "Hello, World!")

if __name__ == '__main__':
    unittest.main()

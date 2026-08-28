import unittest
from state_manager import StateManager

class TestStateManager(unittest.TestCase):
    def test_remember_markets(self):
        state_manager = StateManager()
        state_manager.remember_markets(['market1', 'market2'])
        self.assertIn('market1', state_manager.get_state()['remembered_markets'])
        self.assertIn('market2', state_manager.get_state()['remembered_markets'])

    def test_seen_recently(self):
        state_manager = StateManager()
        state_manager.seen_recently('market1')
        self.assertIn('market1', state_manager.get_state()['seen_recently'])

    def test_clear(self):
        state_manager = StateManager()
        state_manager.remember_markets(['market1', 'market2'])
        state_manager.seen_recently('market1')
        state_manager.clear()
        self.assertEqual(state_manager.get_state()['remembered_markets'], [])
        self.assertEqual(state_manager.get_state()['seen_recently'], [])

if __name__ == '__main__':
    unittest.main()

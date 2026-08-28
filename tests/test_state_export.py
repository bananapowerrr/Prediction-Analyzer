import unittest
from unittest.mock import patch
from state_manager import StateManager

class TestStateManager(unittest.TestCase):
    @patch('state_manager.StateManager._create_table')
    def test_create_table(self, mock_create_table):
        state_manager = StateManager('test.db')
        state_manager._create_table()
        mock_create_table.assert_called_once()

    @patch('state_manager.StateManager.clear')
    def test_clear(self, mock_clear):
        state_manager = StateManager('test.db')
        state_manager.clear()
        mock_clear.assert_called_once()

    @patch('state_manager.StateManager.close')
    def test_close(self, mock_close):
        state_manager = StateManager('test.db')
        state_manager.close()
        mock_close.assert_called_once()

if __name__ == '__main__':
    unittest.main()

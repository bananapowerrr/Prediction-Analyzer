import unittest
from unittest.mock import patch
from position_cap import PositionCap

class TestPositionCap(unittest.TestCase):
    @patch('position_cap.get_capital')
    def test_position_size(self, mock_get_capital):
        mock_get_capital.return_value = 1000
        position_cap = PositionCap()
        position_size = position_cap.calculate_position_size(0.25)
        self.assertEqual(position_size, 250)

if __name__ == '__main__':
    unittest.main()

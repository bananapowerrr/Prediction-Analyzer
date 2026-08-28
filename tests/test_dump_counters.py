import unittest
from unittest.mock import patch, mock_open
from prediction_analyzer.dump_counters import dump_counters

class TestDumpCounters(unittest.TestCase):
    @patch('prediction_analyzer.dump_counters.get_counters')
    def test_dump_counters(self, mock_get_counters):
        # Arrange
        mock_get_counters.return_value = {'counter1': 10, 'counter2': 20}
        expected_output = "counter1: 10\ncounter2: 20\n"

        # Act
        with patch('builtins.open', mock_open(read_data='')) as mock_file:
            dump_counters('path/to/file.txt')

        # Assert
        mock_file.assert_called_once_with('path/to/file.txt', 'w')
        mock_file().write.assert_called_once_with(expected_output)

if __name__ == '__main__':
    unittest.main()

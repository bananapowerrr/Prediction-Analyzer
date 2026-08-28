import unittest
from unittest.mock import patch

def notify(message):
    print(message)

class TestNotify(unittest.TestCase):
    @patch('builtins.print')
    def test_notify(self, mock_print):
        notify("Test message")
        mock_print.assert_called_once_with("Test message")

if __name__ == '__main__':
    unittest.main()

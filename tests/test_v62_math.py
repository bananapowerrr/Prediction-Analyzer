import unittest
from utils.v62_math import add

class TestMathOperations(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(10, 5), 15)

if __name__ == '__main__':
    unittest.main()

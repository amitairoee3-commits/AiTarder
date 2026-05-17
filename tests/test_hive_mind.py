import unittest
from src.hive_mind import HiveMind

class TestHiveMind(unittest.TestCase):
    def test_initialization(self):
        hm = HiveMind()
        self.assertIsNotNone(hm)

if __name__ == '__main__':
    unittest.main()

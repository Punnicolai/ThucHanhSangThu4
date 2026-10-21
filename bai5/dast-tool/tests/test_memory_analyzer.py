import unittest

from memory_analyzer import MemoryAnalyzer


class TestMemoryAnalyzer(unittest.TestCase):
    def test_check_overflow(self):
        analyzer = MemoryAnalyzer()
        self.assertTrue(analyzer.check_overflow(2**64))
        self.assertTrue(analyzer.check_overflow(-(2**63) - 1))
        self.assertFalse(analyzer.check_overflow(100))
        self.assertFalse(analyzer.check_overflow(True))

    def test_check_memory_leaks_returns_list(self):
        self.assertIsInstance(MemoryAnalyzer().check_memory_leaks(), list)


if __name__ == "__main__":
    unittest.main()

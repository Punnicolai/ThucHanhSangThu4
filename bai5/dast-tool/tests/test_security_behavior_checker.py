import tempfile
import unittest
from pathlib import Path

from security_behavior_checker import SecurityBehaviorChecker


class TestSecurityBehaviorChecker(unittest.TestCase):
    def test_detects_calls_in_source(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "sample.py"
            source.write_text(
                "eval('1')\nos.system('echo hi')\n", encoding="utf-8"
            )
            findings = SecurityBehaviorChecker(source).suspicious_calls()
        self.assertEqual(len(findings), 2)
        self.assertIn("eval at line 1", findings[0])


if __name__ == "__main__":
    unittest.main()

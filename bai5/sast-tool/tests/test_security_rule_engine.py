import json
import tempfile
import unittest
from pathlib import Path

from sast_tool.security_rule_engine import SecurityRuleEngine


class TestSecurityRuleEngine(unittest.TestCase):
    def test_applies_severity_without_mutating_input(self):
        with tempfile.TemporaryDirectory() as directory:
            rules_path = Path(directory) / "rules.json"
            rules_path.write_text(
                json.dumps([{"type": "Use of eval", "severity": "high"}]),
                encoding="utf-8",
            )
            engine = SecurityRuleEngine(rules_path)
            issue = {"type": "Use of eval", "message": "unsafe", "lineno": 1}
            results = engine.evaluate([issue], [issue])

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["severity"], "high")
        self.assertNotIn("severity", issue)


if __name__ == "__main__":
    unittest.main()

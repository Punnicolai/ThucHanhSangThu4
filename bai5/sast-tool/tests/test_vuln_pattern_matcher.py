import unittest

from sast_tool.vuln_pattern_matcher import VulnPatternMatcher


class TestVulnPatternMatcher(unittest.TestCase):
    def test_detects_hardcoded_password_and_pickle(self):
        issues = VulnPatternMatcher().match(
            'password = "secret"\nimport pickle\n'
        )
        self.assertEqual(len(issues), 2)
        self.assertEqual([issue["lineno"] for issue in issues], [1, 2])

    def test_accepts_custom_patterns(self):
        matcher = VulnPatternMatcher(
            [{"pattern": r"TODO", "message": "Incomplete work."}]
        )
        self.assertEqual(
            matcher.match("# TODO")[0]["message"], "Incomplete work."
        )


if __name__ == "__main__":
    unittest.main()

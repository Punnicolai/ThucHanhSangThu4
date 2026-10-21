import unittest

from sast_tool.ast_analyzer import ASTAnalyzer


class TestASTAnalyzer(unittest.TestCase):
    def test_detects_dangerous_calls_with_locations(self):
        issues = ASTAnalyzer().analyze(
            "value = eval('1')\nos.system('true')\n"
        )
        self.assertEqual(
            [issue["type"] for issue in issues],
            ["Use of eval", "Use of os.system"],
        )
        self.assertEqual([issue["lineno"] for issue in issues], [1, 2])

    def test_reports_invalid_python(self):
        with self.assertRaises(SyntaxError):
            ASTAnalyzer().analyze("def broken(:")


if __name__ == "__main__":
    unittest.main()

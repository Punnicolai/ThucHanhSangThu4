import tempfile
import unittest
from pathlib import Path

from sast_tool.code_quality_checker import CodeQualityChecker


class TestCodeQualityChecker(unittest.TestCase):
    def test_metrics_include_complexity_and_security_smells(self):
        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "sample.py"
            source_path.write_text(
                "def sample(value):\n"
                "    if value:\n"
                "        return eval(value)\n"
                "    return None\n",
                encoding="utf-8",
            )
            metrics = CodeQualityChecker().metrics(source_path)

        self.assertEqual(metrics["cyclomatic_complexity"]["sample"], 2)
        self.assertEqual(metrics["security_smell_count"], 1)
        self.assertEqual(metrics["security_smell_density"], 0.25)

    def test_check_reports_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            CodeQualityChecker().check("does-not-exist.py")


if __name__ == "__main__":
    unittest.main()

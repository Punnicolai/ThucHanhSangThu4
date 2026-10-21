import json
import tempfile
import unittest
from pathlib import Path

from sast_tool.sarif_reporter import SarifReporter


class TestSarifReporter(unittest.TestCase):
    def test_writes_valid_sarif_locations_and_severity(self):
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "nested" / "report.sarif"
            SarifReporter().generate_report(
                [
                    {
                        "type": "Use of eval",
                        "message": "Unsafe call",
                        "lineno": 3,
                        "col_offset": 4,
                        "severity": "high",
                    }
                ],
                output_path,
                "sample.py",
            )
            report = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(report["version"], "2.1.0")
        result = report["runs"][0]["results"][0]
        self.assertEqual(result["level"], "error")
        region = result["locations"][0]["physicalLocation"]["region"]
        self.assertEqual(region["startColumn"], 5)


if __name__ == "__main__":
    unittest.main()

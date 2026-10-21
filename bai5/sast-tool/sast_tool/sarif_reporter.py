import json
from pathlib import Path


class SarifReporter:
    """Write findings as a SARIF 2.1.0 JSON log."""

    def generate_report(
        self,
        issues: list[dict],
        output_file: str | Path = "report.sarif",
        analyzed_file: str | Path = "input.py",
        quality_metrics: dict | None = None,
    ) -> None:
        rules = {}
        results = []
        for issue in issues:
            rule_id = issue["type"]
            severity = issue.get("severity", "warning").lower()
            level = {
                "critical": "error",
                "high": "error",
                "medium": "warning",
                "low": "note",
            }.get(severity, "warning")
            rules.setdefault(
                rule_id,
                {
                    "id": rule_id,
                    "shortDescription": {"text": rule_id},
                    "defaultConfiguration": {"level": level},
                },
            )
            location = {
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": str(analyzed_file).replace("\\", "/")
                    },
                }
            }
            region = {}
            if "lineno" in issue:
                region["startLine"] = max(1, int(issue["lineno"]))
            if "col_offset" in issue:
                region["startColumn"] = max(1, int(issue["col_offset"]) + 1)
            if region:
                location["physicalLocation"]["region"] = region
            results.append(
                {
                    "ruleId": rule_id,
                    "level": level,
                    "message": {"text": issue["message"]},
                    "locations": [location],
                }
            )

        run = {
            "tool": {
                "driver": {
                    "name": "PySAST",
                    "version": "1.0.0",
                    "rules": list(rules.values()),
                }
            },
            "results": results,
        }
        if quality_metrics is not None:
            run["properties"] = {"qualityMetrics": quality_metrics}

        report = {
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "version": "2.1.0",
            "runs": [run],
        }
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

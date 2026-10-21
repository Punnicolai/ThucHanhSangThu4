import json
from pathlib import Path


class SecurityRuleEngine:
    """Apply configurable severity rules to analyzer findings."""

    def __init__(self, rules_file: str | Path | None = None):
        if rules_file is None:
            rules_file = (
                Path(__file__).parent.parent / "rules" / "default_rules.json"
            )
        with open(rules_file, encoding="utf-8") as rules_stream:
            self.rules = json.load(rules_stream)
        if not isinstance(self.rules, list):
            raise ValueError("Security rules must be a JSON list.")

    def evaluate(
        self, ast_issues: list[dict], pattern_issues: list[dict]
    ) -> list[dict]:
        issues = []
        seen = set()
        for issue in [*ast_issues, *pattern_issues]:
            for rule in self.rules:
                if rule.get("type") != issue.get("type"):
                    continue
                result = dict(issue)
                result["severity"] = rule.get("severity", "medium")
                key = (
                    result.get("type"),
                    result.get("message"),
                    result.get("lineno"),
                    result.get("col_offset"),
                )
                if key not in seen:
                    seen.add(key)
                    issues.append(result)
        return issues

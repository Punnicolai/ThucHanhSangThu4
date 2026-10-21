import re


class VulnPatternMatcher:
    """Detect simple security smells with configurable regular expressions."""

    DEFAULT_PATTERNS = (
        {
            "pattern": r"\bpassword\s*=\s*(['\"])(?!REPLACE_ME\b)[^'\"]+\1",
            "message": "Hardcoded password detected.",
        },
        {
            "pattern": r"^\s*(?:import\s+pickle\b|from\s+pickle\s+import\b)",
            "message": (
                "Usage of pickle can be unsafe when loading untrusted data."
            ),
        },
    )

    def __init__(self, patterns: list[dict] | None = None):
        self.patterns = (
            patterns if patterns is not None else list(self.DEFAULT_PATTERNS)
        )
        for pattern in self.patterns:
            if "pattern" not in pattern or "message" not in pattern:
                raise ValueError(
                    "Each pattern must define 'pattern' and 'message'."
                )
            re.compile(pattern["pattern"])

    def match(self, code: str) -> list[dict]:
        issues = []
        line_offsets = [0]
        line_offsets.extend(match.end() for match in re.finditer("\n", code))

        for pattern in self.patterns:
            for match in re.finditer(pattern["pattern"], code, re.MULTILINE):
                line_index = code.count("\n", 0, match.start())
                issues.append(
                    {
                        "type": "Pattern Match",
                        "message": pattern["message"],
                        "lineno": line_index + 1,
                        "col_offset": match.start() - line_offsets[line_index],
                    }
                )
        return sorted(
            issues, key=lambda issue: (issue["lineno"], issue["col_offset"])
        )

import ast


class ASTAnalyzer:
    """Find dangerous calls in Python source without executing it."""

    _DANGEROUS_CALLS = {
        "eval": (
            "Use of eval",
            "Use of eval() is dangerous and should be avoided.",
        ),
        "exec": ("Use of exec", "Use of exec() can execute arbitrary code."),
        "system": (
            "Use of os.system",
            "Use of os.system() can execute shell commands.",
        ),
    }

    def analyze(self, code: str) -> list[dict]:
        tree = ast.parse(code)
        issues = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            else:
                continue

            finding = self._DANGEROUS_CALLS.get(name)
            if finding is not None:
                issue_type, message = finding
                issues.append(
                    {
                        "type": issue_type,
                        "message": message,
                        "lineno": node.lineno,
                        "col_offset": node.col_offset,
                    }
                )
        return sorted(
            issues, key=lambda issue: (issue["lineno"], issue["col_offset"])
        )

import ast
from pathlib import Path


class SecurityBehaviorChecker:
    """Find suspicious Python calls in a source file without executing it."""

    _SUSPICIOUS_NAMES = {"eval", "exec", "system"}

    def __init__(self, source_file: str | Path | None = None):
        self.source_file = (
            Path(source_file) if source_file is not None else Path(__file__)
        )

    def suspicious_calls(self) -> list[str]:
        source = self.source_file.read_text(encoding="utf-8")
        tree = ast.parse(source)
        suspicious = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            else:
                continue
            if name in self._SUSPICIOUS_NAMES:
                suspicious.append(f"{name} at line {node.lineno}")
        return suspicious

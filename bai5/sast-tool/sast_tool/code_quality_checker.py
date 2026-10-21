import ast
import re
import subprocess
import sys
from importlib.util import find_spec
from pathlib import Path


class CodeQualityChecker:
    """Collect Flake8 findings and security-oriented source metrics."""

    _FLAKE8_LINE = re.compile(r"^(.*?):(\d+):(\d+):\s+([A-Z]\d+)\s+(.*)$")

    def check(self, filepath: str | Path) -> list[dict]:
        filepath = Path(filepath)
        if not filepath.is_file():
            raise FileNotFoundError(filepath)
        if find_spec("flake8") is None:
            raise RuntimeError(
                "Flake8 is required. Install it with "
                "'python -m pip install -r sast-tool\\requirements.txt'."
            )

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "flake8",
                "--format=%(path)s:%(row)d:%(col)d: %(code)s %(text)s",
                str(filepath),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode not in (0, 1):
            raise RuntimeError(f"Flake8 failed: {result.stderr.strip()}")

        issues = []
        for line in result.stdout.splitlines():
            match = self._FLAKE8_LINE.match(line)
            if match is None:
                raise RuntimeError(f"Could not parse Flake8 output: {line}")
            _, lineno, col_offset, code, message = match.groups()
            issues.append(
                {
                    "type": "Lint Issue",
                    "message": f"{code} {message}",
                    "lineno": int(lineno),
                    "col_offset": int(col_offset) - 1,
                }
            )
        return issues

    def metrics(self, filepath: str | Path) -> dict:
        filepath = Path(filepath)
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source)
        functions = [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        dependencies = sum(
            isinstance(node, (ast.Import, ast.ImportFrom))
            for node in ast.walk(tree)
        )
        line_count = max(1, len(source.splitlines()))
        security_smells = sum(
            isinstance(node, ast.Call)
            and (
                (
                    isinstance(node.func, ast.Name)
                    and node.func.id in {"eval", "exec"}
                )
                or (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "system"
                )
            )
            for node in ast.walk(tree)
        )
        return {
            "cyclomatic_complexity": {
                node.name: 1
                + sum(
                    isinstance(
                        child,
                        (
                            ast.If,
                            ast.For,
                            ast.AsyncFor,
                            ast.While,
                            ast.ExceptHandler,
                        ),
                    )
                    for child in ast.walk(node)
                )
                for node in functions
            },
            "function_length": {
                node.name: node.end_lineno - node.lineno + 1
                for node in functions
            },
            "maximum_nesting_depth": self._maximum_nesting_depth(tree),
            "dependency_count": dependencies,
            "security_smell_count": security_smells,
            "security_smell_density": security_smells / line_count,
        }

    @staticmethod
    def _maximum_nesting_depth(tree: ast.AST) -> int:
        branch_types = (
            ast.If,
            ast.For,
            ast.AsyncFor,
            ast.While,
            ast.Try,
            ast.With,
            ast.AsyncWith,
        )

        def visit(node: ast.AST, depth: int) -> int:
            current = depth + int(isinstance(node, branch_types))
            return max(
                [
                    current,
                    *(
                        visit(child, current)
                        for child in ast.iter_child_nodes(node)
                    ),
                ]
            )

        return visit(tree, 0)

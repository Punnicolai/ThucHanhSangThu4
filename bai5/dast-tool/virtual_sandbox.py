import shlex
import subprocess
import sys
import tempfile
from pathlib import Path


class VirtualSandbox:
    """Run a narrowly allowlisted demo command in a temporary directory."""

    def __init__(self):
        self._temporary_directory = tempfile.TemporaryDirectory(
            prefix="dast-sandbox-"
        )
        self.temp_dir = Path(self._temporary_directory.name)

    def run_isolated(self, command: str | list[str]) -> tuple[str, str]:
        if isinstance(command, str):
            parts = shlex.split(command)
        elif isinstance(command, list) and all(
            isinstance(part, str) for part in command
        ):
            parts = command
        else:
            raise TypeError("Command must be a string or a list of strings.")

        if not parts or parts[0].lower() != "echo":
            raise ValueError("The sandbox allows only the echo command.")
        if any("\x00" in part for part in parts):
            raise ValueError("Command arguments cannot contain null bytes.")

        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; print(' '.join(sys.argv[1:]))",
                *parts[1:],
            ],
            cwd=self.temp_dir,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Sandbox command failed: {result.stderr.strip()}"
            )
        return result.stdout, result.stderr

    def close(self) -> None:
        self._temporary_directory.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

import subprocess

from pydantic import Field

from .base import BaseMethod


class RunCommand(BaseMethod):
    """Run a shell command and return its output."""

    command: str = Field(description="Shell command to execute")
    timeout: int = Field(default=30, description="Timeout in seconds")

    def call(self) -> str:
        try:
            result = subprocess.run(
                self.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            out = result.stdout.strip()
            err = result.stderr.strip()
            if result.returncode != 0:
                return f"Exit {result.returncode}\n{err or out}"
            return out or "(no output)"
        except subprocess.TimeoutExpired:
            return f"Command timed out after {self.timeout}s"
        except Exception as e:
            return f"Error: {e}"

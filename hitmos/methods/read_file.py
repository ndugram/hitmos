from pathlib import Path

from pydantic import Field

from .base import BaseMethod


class ReadFile(BaseMethod):
    """Read the full contents of a file."""

    path: str = Field(description="File path to read")

    def call(self) -> str:
        p = Path(self.path)
        if not p.exists():
            return f"File not found: {self.path}"
        return p.read_text(encoding="utf-8")

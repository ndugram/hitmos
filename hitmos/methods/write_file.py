from pathlib import Path

from pydantic import Field

from .base import BaseMethod


class WriteFile(BaseMethod):
    """Create or overwrite a file with the given content."""

    path: str = Field(description="File path (relative to cwd or absolute)")
    content: str = Field(description="Full file content to write")

    def call(self) -> str:
        p = Path(self.path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.content, encoding="utf-8")
        return f"Written {len(self.content)} chars to {self.path}"

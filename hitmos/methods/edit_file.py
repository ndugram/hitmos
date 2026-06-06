from pathlib import Path

from pydantic import Field

from .base import BaseMethod


class EditFile(BaseMethod):
    """Replace the first occurrence of old_string with new_string in a file."""

    path: str = Field(description="File path to edit")
    old_string: str = Field(description="Exact string to find and replace")
    new_string: str = Field(description="Replacement string")

    def call(self) -> str:
        p = Path(self.path)
        if not p.exists():
            return f"File not found: {self.path}"
        text = p.read_text(encoding="utf-8")
        if self.old_string not in text:
            return f"String not found in {self.path}"
        p.write_text(text.replace(self.old_string, self.new_string, 1), encoding="utf-8")
        return f"Edited {self.path}"

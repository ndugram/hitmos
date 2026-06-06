from pathlib import Path

from pydantic import Field

from .base import BaseMethod


class ListDirectory(BaseMethod):
    """List files and subdirectories at the given path."""

    path: str = Field(default=".", description="Directory path (default: current directory)")

    def call(self) -> str:
        p = Path(self.path)
        if not p.exists():
            return f"Path not found: {self.path}"
        items = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        if not items:
            return "(empty)"
        return "\n".join(f"{'dir ' if x.is_dir() else 'file'} {x.name}" for x in items)

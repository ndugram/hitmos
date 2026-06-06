from pathlib import Path

from pydantic import Field

from .base import BaseMethod


class DeleteFile(BaseMethod):
    """Delete a file or empty directory at the given path."""

    path: str = Field(description="File or directory path to delete")

    def call(self) -> str:
        p = Path(self.path)
        if not p.exists():
            return f"Not found: {self.path}"
        if p.is_dir():
            try:
                p.rmdir()
                return f"Deleted directory {self.path}"
            except OSError:
                return f"Directory not empty: {self.path}"
        p.unlink()
        return f"Deleted {self.path}"

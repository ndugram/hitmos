from __future__ import annotations

from pathlib import Path


class ProjectContext:
    _IGNORE_DIRS = frozenset({
        ".git", "__pycache__", ".venv", "venv", "env",
        "node_modules", "dist", "build", ".pytest_cache",
        ".mypy_cache", ".ruff_cache", "eggs", ".eggs",
        ".tox", "htmlcov", ".idea", ".vscode",
    })
    _IGNORE_EXTS = frozenset({
        ".pyc", ".pyo", ".pyd", ".so", ".dylib", ".dll",
        ".jpg", ".jpeg", ".png", ".gif", ".ico", ".svg", ".webp",
        ".pdf", ".zip", ".tar", ".gz", ".bz2", ".whl", ".egg",
        ".db", ".sqlite", ".sqlite3", ".bin", ".pkl",
    })
    _PRIORITY_NAMES = frozenset({
        "README.md", "README.rst", "README.txt",
        "pyproject.toml", "package.json", "Cargo.toml",
        "setup.py", "setup.cfg", "requirements.txt",
        "Makefile", "docker-compose.yml", "Dockerfile",
        ".env.example",
    })
    MAX_FILE_BYTES = 25_000
    MAX_TOTAL_BYTES = 120_000

    def __init__(self, cwd: Path) -> None:
        self.cwd = cwd

    def build(self) -> tuple[str, int]:
        """Returns (context_string, size_in_kb)."""
        parts: list[str] = []

        tree = self._tree()
        if tree:
            parts.append(f"Project structure ({self.cwd}):\n{tree}")

        total = sum(len(p) for p in parts)
        for path in self._collect():
            if total >= self.MAX_TOTAL_BYTES:
                parts.append("(context limit reached — more files exist)")
                break
            text = self._read(path)
            if text is None:
                continue
            rel = str(path.relative_to(self.cwd))
            block = f"--- {rel} ---\n{text}"
            parts.append(block)
            total += len(block)

        context = "\n\n".join(parts)
        return context, len(context) // 1024

    def _tree(self) -> str:
        lines: list[str] = []
        self._walk_tree(self.cwd, "", lines, 0)
        return "\n".join(lines)

    def _walk_tree(self, path: Path, prefix: str, lines: list[str], depth: int) -> None:
        if depth > 4:
            return
        try:
            children = sorted(
                [p for p in path.iterdir() if self._visible(p)],
                key=lambda p: (p.is_file(), p.name.lower()),
            )
        except PermissionError:
            return
        for i, child in enumerate(children):
            is_last = i == len(children) - 1
            lines.append(f"{prefix}{'└── ' if is_last else '├── '}{child.name}")
            if child.is_dir():
                self._walk_tree(child, prefix + ("    " if is_last else "│   "), lines, depth + 1)

    def _visible(self, path: Path) -> bool:
        name = path.name
        if name.startswith(".") and name not in {".env.example"}:
            return False
        if path.is_dir() and name in self._IGNORE_DIRS:
            return False
        if path.is_file() and path.suffix in self._IGNORE_EXTS:
            return False
        return True

    def _collect(self) -> list[Path]:
        priority: list[Path] = []
        others: list[Path] = []
        for path in self._rglob():
            (priority if path.name in self._PRIORITY_NAMES else others).append(path)
        return priority + sorted(others, key=lambda p: str(p))

    def _rglob(self) -> list[Path]:
        result: list[Path] = []
        for path in self.cwd.rglob("*"):
            if not path.is_file():
                continue
            rel_parts = path.relative_to(self.cwd).parts
            if any(
                p in self._IGNORE_DIRS or (p.startswith(".") and p != ".env.example")
                for p in rel_parts[:-1]
            ):
                continue
            if path.suffix in self._IGNORE_EXTS:
                continue
            result.append(path)
        return result

    def _read(self, path: Path) -> str | None:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            if not text.strip():
                return None
            if len(text) > self.MAX_FILE_BYTES:
                text = text[: self.MAX_FILE_BYTES] + "\n... (truncated)"
            return text
        except Exception:
            return None

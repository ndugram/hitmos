from pathlib import Path


def get_cwd_display() -> str:
    cwd = Path.cwd()
    try:
        rel = cwd.relative_to(Path.home())
        return f"~/{rel}" if str(rel) != "." else "~"
    except ValueError:
        return str(cwd)

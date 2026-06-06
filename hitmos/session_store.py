from __future__ import annotations

from datetime import datetime

import orjson

from .constants import SESSIONS_DIR


class SessionStore:
    def __init__(self) -> None:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    def new_id(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def save(self, session_id: str, messages: list[dict], model: str) -> None:
        data: dict = {
            "id": session_id,
            "model": model,
            "saved_at": datetime.now().isoformat(),
            "messages": messages,
        }
        (SESSIONS_DIR / f"{session_id}.json").write_bytes(
            orjson.dumps(data, option=orjson.OPT_INDENT_2)
        )
        (SESSIONS_DIR / "last").write_text(session_id, encoding="utf-8")

    def load_last(self) -> tuple[str, list[dict], str, str] | None:
        """Returns (session_id, messages, model, saved_at) or None."""
        last_path = SESSIONS_DIR / "last"
        if not last_path.exists():
            return None
        session_id = last_path.read_text(encoding="utf-8").strip()
        return self._load(session_id)

    def _load(self, session_id: str) -> tuple[str, list[dict], str, str] | None:
        path = SESSIONS_DIR / f"{session_id}.json"
        if not path.exists():
            return None
        try:
            data = orjson.loads(path.read_bytes())
            return (
                data["id"],
                data.get("messages", []),
                data.get("model", ""),
                data.get("saved_at", ""),
            )
        except Exception:
            return None

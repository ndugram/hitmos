import tomllib


from pydantic_settings import BaseSettings, SettingsConfigDict

from .constants import CONFIG_DIR, CONFIG_FILE, DEFAULT_MODEL
from .exceptions import AuthError


class _EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")

    open_token: str = ""
    openrouter_api_key: str = ""


class ConfigManager:
    def __init__(self) -> None:
        self._env = _EnvSettings()
        self._file_config: dict = self._load_file()

    def _load_file(self) -> dict:
        if not CONFIG_FILE.exists():
            return {}
        try:
            with CONFIG_FILE.open("rb") as f:
                return tomllib.load(f)
        except Exception:
            return {}

    def resolve_token(self) -> str:
        token = (
            self._env.open_token
            or self._env.openrouter_api_key
            or self._file_config.get("api_key", "")
        )
        if not token:
            raise AuthError(
                "No API key found.\n\n"
                "  Set env:   export OPEN_TOKEN=sk-or-xxx\n"
                "  Or run:    hitmos login"
            )
        return token

    def get_model(self) -> str:
        return self._file_config.get("model", DEFAULT_MODEL)

    def save_token(self, token: str) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = self._load_file()
        data["api_key"] = token
        self._write_file(data)

    def save_model(self, model: str) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = self._load_file()
        data["model"] = model
        self._write_file(data)

    def _write_file(self, data: dict) -> None:
        lines = []
        for key, value in data.items():
            if isinstance(value, str):
                lines.append(f'{key} = "{value}"')
            else:
                lines.append(f"{key} = {value}")
        CONFIG_FILE.write_text("\n".join(lines) + "\n")

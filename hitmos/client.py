from collections.abc import AsyncGenerator
from dataclasses import dataclass, field

import orjson
from fasthttp import AsyncSession

from .constants import APP_TITLE, HTTP_REFERER, OPENROUTER_CHAT_URL
from .exceptions import APIError, AuthError, NetworkError, RateLimitError
from .methods import ALL_TOOLS


@dataclass
class ToolCallRequest:
    id: str
    name: str
    arguments: str


@dataclass
class UsageInfo:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost: float = 0.0


class OpenRouterClient:
    def __init__(self, token: str, model: str) -> None:
        self._token = token
        self._model = model

    @property
    def model(self) -> str:
        return self._model

    @model.setter
    def model(self, value: str) -> None:
        self._model = value

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "HTTP-Referer": HTTP_REFERER,
            "X-Title": APP_TITLE,
        }

    async def stream_chat(
        self,
        messages: list[dict],
        use_tools: bool = True,
    ) -> AsyncGenerator[str | list[ToolCallRequest] | UsageInfo, None]:
        payload_dict: dict = {
            "model": self._model,
            "messages": messages,
            "stream": True,
            "max_tokens": 2048,
        }
        if use_tools:
            payload_dict["tools"] = ALL_TOOLS
            payload_dict["tool_choice"] = "auto"

        payload = orjson.dumps(payload_dict)
        pending: dict[int, dict] = {}
        usage: UsageInfo | None = None

        try:
            async with AsyncSession(security=False, timeout=120.0) as session:
                raw = session._ensure_open()
                async with raw.stream(
                    "POST",
                    OPENROUTER_CHAT_URL,
                    headers=self._headers(),
                    content=payload,
                    timeout=120.0,
                ) as resp:
                    await self._check_status(resp)
                    async for line in resp.aiter_lines():
                        token = self._parse_sse(line, pending)
                        if isinstance(token, UsageInfo):
                            usage = token
                        elif token is not None:
                            yield token
        except (AuthError, RateLimitError, APIError):
            raise
        except Exception as exc:
            msg = str(exc).lower()
            if any(k in msg for k in ("connect", "timeout", "timed out", "network")):
                raise NetworkError(str(exc)) from exc
            raise NetworkError(f"Request failed: {exc}") from exc

        if pending:
            yield [
                ToolCallRequest(id=v["id"], name=v["name"], arguments=v["arguments"])
                for v in sorted(pending.values(), key=lambda x: x.get("index", 0))
            ]

        if usage:
            yield usage

    @staticmethod
    async def _check_status(resp: object) -> None:
        code: int = resp.status_code  # type: ignore[attr-defined]
        if code == 401:
            raise AuthError("Invalid API key.  Run: hitmos login")
        if code == 429:
            raise RateLimitError("Rate limit exceeded. Try again later.")
        if code >= 400:
            body = await resp.aread()  # type: ignore[attr-defined]
            try:
                err = orjson.loads(body)
                msg = err.get("error", {}).get("message", f"HTTP {code}")
            except Exception:
                msg = f"HTTP {code}"
            raise APIError(msg)

    @staticmethod
    def _parse_sse(line: str, pending: dict[int, dict]) -> str | UsageInfo | None:
        if not line.startswith("data: "):
            return None
        data = line[6:]
        if data.strip() == "[DONE]":
            return None
        try:
            chunk = orjson.loads(data)

            try:
                delta = chunk["choices"][0]["delta"]
                if content := delta.get("content"):
                    return content
                for tc in delta.get("tool_calls", []):
                    idx = tc.get("index", 0)
                    if idx not in pending:
                        pending[idx] = {"index": idx, "id": "", "name": "", "arguments": ""}
                    if tc.get("id"):
                        pending[idx]["id"] = tc["id"]
                    fn = tc.get("function", {})
                    if fn.get("name"):
                        pending[idx]["name"] = fn["name"]
                    if args := fn.get("arguments"):
                        pending[idx]["arguments"] += args
            except (KeyError, IndexError):
                pass

            if u := chunk.get("usage"):
                return UsageInfo(
                    prompt_tokens=u.get("prompt_tokens", 0),
                    completion_tokens=u.get("completion_tokens", 0),
                    cost=float(u.get("cost") or 0.0),
                )

            return None
        except orjson.JSONDecodeError:
            return None

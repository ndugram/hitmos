from .constants import SYSTEM_PROMPT


class ChatSession:
    def __init__(self, system_prompt: str | None = None) -> None:
        self._messages: list[dict] = []
        self._system = system_prompt or SYSTEM_PROMPT

    def add_user(self, content: str) -> None:
        self._messages.append({"role": "user", "content": content})

    def add_assistant(self, content: str) -> None:
        self._messages.append({"role": "assistant", "content": content})

    def add_raw(self, message: dict) -> None:
        self._messages.append(message)

    def clear(self) -> None:
        self._messages.clear()

    def reset(self) -> None:
        self._messages.clear()

    def load_messages(self, messages: list[dict]) -> None:
        self._messages = list(messages)

    def pop_last(self) -> None:
        if self._messages:
            self._messages.pop()

@property
    def messages(self) -> list[dict]:
        return [{"role": "system", "content": self._system}] + self._messages

    @property
    def raw_messages(self) -> list[dict]:
        return list(self._messages)

    @property
    def is_empty(self) -> bool:
        return len(self._messages) == 0

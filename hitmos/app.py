import asyncio
from collections.abc import AsyncGenerator

from .chat import ChatSession
from .client import OpenRouterClient, ToolCallRequest, UsageInfo
from .commands import CommandHandler, CommandResult, CommandType
from .config import ConfigManager
from .constants import SYSTEM_PROMPT
from .exceptions import AuthError, HitmosError
from .methods import dispatch
from .session_store import SessionStore
from .ui import ConsoleUI


class HitmosApp:
    def __init__(self) -> None:
        self._config = ConfigManager()
        self._ui = ConsoleUI()
        self._commands = CommandHandler()
        self._session: ChatSession | None = None
        self._client: OpenRouterClient | None = None
        self._store = SessionStore()
        self._session_id: str = self._store.new_id()
        self._usage = UsageInfo()

    def run(self, resume: bool = False) -> None:
        try:
            token = self._config.resolve_token()
        except AuthError as e:
            self._ui.show_error(str(e))
            raise SystemExit(1)

        model = self._config.get_model()
        self._client = OpenRouterClient(token, model)

        system_prompt, ctx_kb = self._build_system_prompt()
        self._session = ChatSession(system_prompt=system_prompt)

        resumed_at: str | None = None
        if resume:
            loaded = self._store.load_last()
            if loaded:
                sid, messages, saved_model, saved_at = loaded
                self._session_id = sid
                self._session.load_messages(messages)
                if saved_model:
                    self._client.model = saved_model
                    model = saved_model
                resumed_at = saved_at
            else:
                self._ui.show_info("No saved session found. Starting fresh.")

        self._ui.show_welcome(model, ctx_kb, resumed_at=resumed_at)

        try:
            asyncio.run(self._loop())
        except KeyboardInterrupt:
            self._ui.show_exit()

    async def _loop(self) -> None:
        assert self._client is not None
        assert self._session is not None

        while True:
            try:
                text = await self._ui.get_input()
            except (KeyboardInterrupt, EOFError):
                self._ui.show_exit()
                return

            text = text.strip()
            if not text:
                continue

            result = self._commands.parse(text)
            if result is not None:
                should_exit = await self._handle_command(result)
                if should_exit:
                    return
            else:
                await self._handle_message(text)

    def _build_system_prompt(self) -> tuple[str, int]:
        return SYSTEM_PROMPT, 0

    async def _handle_command(self, result: CommandResult) -> bool:
        assert self._client is not None
        assert self._session is not None

        match result.type:
            case CommandType.HELP:
                self._ui.show_help()
            case CommandType.CLEAR:
                self._session.clear()
                self._ui.show_info("History cleared.")
            case CommandType.RESET:
                self._session.reset()
                self._ui.show_info("Context reset.")
            case CommandType.MODEL:
                if result.arg:
                    self._client.model = result.arg
                    self._config.save_model(result.arg)
                    self._ui.show_success(f"Model: {result.arg}")
                else:
                    selected = await self._ui.show_model_picker(self._client.model)
                    if selected:
                        self._client.model = selected
                        self._config.save_model(selected)
                        self._ui.show_success(f"Model: {selected}")
            case CommandType.COST:
                self._ui.show_cost(self._usage)
            case CommandType.COMPACT:
                await self._compact()
            case CommandType.EXIT:
                self._ui.show_exit()
                return True
        return False

    async def _handle_message(self, text: str) -> None:
        assert self._client is not None
        assert self._session is not None

        self._session.add_user(text)

        try:
            while True:
                tool_calls: list[ToolCallRequest] = []

                async def _text_gen() -> AsyncGenerator[str, None]:
                    async for item in self._client.stream_chat(  # type: ignore[union-attr]
                        self._session.messages  # type: ignore[union-attr]
                    ):
                        if isinstance(item, list):
                            tool_calls.extend(item)
                        elif isinstance(item, UsageInfo):
                            self._usage.prompt_tokens += item.prompt_tokens
                            self._usage.completion_tokens += item.completion_tokens
                            self._usage.cost += item.cost
                        else:
                            yield item

                full_response = await self._ui.stream_response(_text_gen())

                if not tool_calls:
                    if full_response:
                        self._session.add_assistant(full_response)
                    break

                self._session.add_raw({
                    "role": "assistant",
                    "content": full_response or None,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.name, "arguments": tc.arguments},
                        }
                        for tc in tool_calls
                    ],
                })

                for tc in tool_calls:
                    self._ui.show_tool_call(tc.name, tc.arguments)
                    result = dispatch(tc.name, tc.arguments)
                    self._ui.show_tool_result(result)
                    self._session.add_raw({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })

        except HitmosError as e:
            self._session.pop_last()
            self._ui.show_error(str(e))
            return
        except Exception as e:
            self._session.pop_last()
            self._ui.show_error(f"Unexpected error: {e}")
            return

        self._store.save(self._session_id, self._session.raw_messages, self._client.model)

    async def _compact(self) -> None:
        assert self._session is not None
        assert self._client is not None

        raw = self._session.raw_messages
        if not raw:
            self._ui.show_info("Nothing to compact.")
            return

        before_chars = sum(len(str(m.get("content") or "")) for m in raw)

        summary_messages = [
            {"role": "system", "content": "You are a conversation summarizer. Be concise and precise."},
            {
                "role": "user",
                "content": (
                    "Summarize the following conversation. "
                    "Preserve all key decisions, code snippets, technical details, and context. "
                    "Format as a compact summary that can replace the full conversation history:\n\n"
                    + "\n".join(
                        f"{m['role'].upper()}: {m.get('content') or ''}"
                        for m in raw
                        if m.get("content")
                    )
                ),
            },
        ]

        self._ui.show_info("Compacting…")

        async def _gen() -> AsyncGenerator[str, None]:
            async for item in self._client.stream_chat(summary_messages, use_tools=False):  # type: ignore[union-attr]
                if isinstance(item, str):
                    yield item

        summary = await self._ui.stream_response(_gen())

        if not summary:
            self._ui.show_error("Failed to generate summary.")
            return

        self._session.clear()
        self._session.add_user(f"[Compacted context — previous conversation summary]\n{summary}")
        self._session.add_assistant("Got it, I have the context from our previous conversation.")

        after_chars = len(summary)
        reduction = int((1 - after_chars / max(before_chars, 1)) * 100)
        self._ui.show_success(f"Compacted — ~{reduction}% reduction in context size")

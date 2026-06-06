import asyncio
from collections.abc import AsyncGenerator

import orjson
import questionary
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style as PTStyle
from questionary import Style as QStyle
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .constants import APP_TITLE, AVAILABLE_MODELS, COMMANDS
from .utils import get_cwd_display

# ── questionary picker style ──────────────────────────────────────────────────
_PICKER_STYLE = QStyle([
    ("qmark",        "fg:#888888"),
    ("question",     "fg:#888888"),
    ("answer",       "fg:#00d7af bold"),
    ("pointer",      "fg:#00d7af bold"),
    ("highlighted",  "fg:#00d7af"),
    ("selected",     "fg:#00d7af"),
    ("separator",    "fg:#444444"),
    ("instruction",  "fg:#444444"),
    ("text",         ""),
])

# ── prompt input style ────────────────────────────────────────────────────────
_INPUT_STYLE = PTStyle.from_dict({
    "prompt":                               "bold",
    "completion-menu.completion":           "bg:#1e1e1e #888888",
    "completion-menu.completion.current":   "bg:#00d7af #000000 bold",
    "completion-menu.meta.completion":      "bg:#1a1a1a #555555",
    "completion-menu.meta.completion.current": "bg:#00875f #000000",
    "scrollbar.background":                 "bg:#2a2a2a",
    "scrollbar.button":                     "bg:#555555",
})

_COMMAND_COMPLETIONS = ["/help", "/clear", "/reset", "/model", "/exit"]


class _HitmosCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        if text.lower().startswith("/model "):
            typed = text[7:]
            for model_id, desc in AVAILABLE_MODELS:
                if model_id.startswith(typed):
                    yield Completion(
                        model_id,
                        start_position=-len(typed),
                        display=model_id,
                        display_meta=desc,
                    )

        elif text.startswith("/") and " " not in text:
            for cmd in _COMMAND_COMPLETIONS:
                if cmd.startswith(text):
                    yield Completion(cmd, start_position=-len(text))


class ConsoleUI:
    def __init__(self) -> None:
        self.console = Console(highlight=False)
        self._session: PromptSession = PromptSession(
            completer=_HitmosCompleter(),
            complete_while_typing=False,
            style=_INPUT_STYLE,
        )

    def show_welcome(self, model: str, ctx_kb: int = 0) -> None:
        self.console.print()
        self.console.print(
            Panel(
                Text.from_markup(
                    f"[bold]✻  Welcome to {APP_TITLE}[/bold]\n\n"
                    "[dim]/help for commands[/dim]"
                ),
                border_style="dim",
                padding=(1, 2),
            )
        )
        self.console.print()
        self.console.print(f" [dim]◆[/dim] [dim]{get_cwd_display()}[/dim]")
        self.console.print(f" [dim]◆[/dim] [dim]{model}[/dim]")
        if ctx_kb > 0:
            self.console.print(f" [dim]◆[/dim] [dim]context {ctx_kb} KB[/dim]")
        self.console.print()

    def show_help(self) -> None:
        table = Table(show_header=False, box=None, padding=(0, 2, 0, 0))
        table.add_column(style="bold cyan", no_wrap=True)
        table.add_column(style="dim")
        for cmd, desc in COMMANDS.items():
            table.add_row(cmd, desc)
        self.console.print()
        self.console.print(table)
        self.console.print()

    async def show_model_picker(self, current: str) -> str | None:
        self.console.print()

        choices = [
            questionary.Choice(
                title=f"{model_id:<48} {desc}",
                value=model_id,
            )
            for model_id, desc in AVAILABLE_MODELS
        ]

        default = next((c for c in choices if c.value == current), choices[0])

        try:
            result = await questionary.select(
                "Select model  (↑↓ navigate, Enter confirm, Ctrl+C cancel)",
                choices=choices,
                default=default,
                style=_PICKER_STYLE,
                use_shortcuts=False,
                use_arrow_keys=True,
            ).ask_async()
        except KeyboardInterrupt:
            result = None

        self.console.print()
        return result

    def show_error(self, message: str) -> None:
        self.console.print()
        lines = message.split("\n")
        self.console.print(f" [bold red]✖[/bold red] {lines[0]}")
        for line in lines[1:]:
            if line:
                self.console.print(f"   {line}")
        self.console.print()

    def show_info(self, message: str) -> None:
        self.console.print()
        self.console.print(f" [dim]{message}[/dim]")
        self.console.print()

    def show_success(self, message: str) -> None:
        self.console.print()
        self.console.print(f" [bold green]✓[/bold green] {message}")
        self.console.print()

    async def stream_response(self, token_gen: AsyncGenerator[str, None]) -> str:
        self.console.print()
        buffer = ""

        async for first in token_gen:
            buffer = first
            break
        else:
            return buffer

        MAX_CHARS = 24_000
        truncated = False
        interrupted = False

        with Live(
            Markdown(buffer),
            console=self.console,
            refresh_per_second=15,
            vertical_overflow="visible",
        ) as live:
            try:
                async for token in token_gen:
                    buffer += token
                    live.update(Markdown(buffer))
                    if len(buffer) >= MAX_CHARS:
                        truncated = True
                        break
            except (KeyboardInterrupt, asyncio.CancelledError):
                interrupted = True
            finally:
                await token_gen.aclose()

        if truncated:
            self.console.print()
            self.console.print(" [dim]Response truncated.[/dim]")
        self.console.print()
        if interrupted:
            self.console.print(" [dim]Interrupted.[/dim]")
            self.console.print()
        return buffer

    async def get_input(self) -> str:
        return await self._session.prompt_async(
            FormattedText([("class:prompt", "> ")]),
        )

    def show_tool_call(self, name: str, arguments: str) -> None:
        try:
            args = orjson.loads(arguments)
            summary = "  ".join(f"[dim]{k}[/dim] {str(v)[:60]}" for k, v in args.items())
        except Exception:
            summary = arguments[:80]
        self.console.print(f" [bold cyan]⚙[/bold cyan]  [cyan]{name}[/cyan]  {summary}")

    def show_tool_result(self, result: str) -> None:
        first_line = result.split("\n")[0]
        preview = first_line[:80] + ("…" if len(result) > 80 else "")
        self.console.print(f"   [dim]→ {preview}[/dim]")
        self.console.print()

    def show_exit(self) -> None:
        self.console.print()
        self.console.print(" [dim]Goodbye.[/dim]")
        self.console.print()

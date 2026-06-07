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
    "prompt":                               "#00d7af bold",
    "prompt-cwd":                           "#555555",
    "completion-menu.completion":           "bg:#1e1e1e #888888",
    "completion-menu.completion.current":   "bg:#00d7af #000000 bold",
    "completion-menu.meta.completion":      "bg:#1a1a1a #555555",
    "completion-menu.meta.completion.current": "bg:#00875f #000000",
    "scrollbar.background":                 "bg:#2a2a2a",
    "scrollbar.button":                     "bg:#555555",
})

_COMMAND_COMPLETIONS = ["/help", "/clear", "/reset", "/model", "/cost", "/compact", "/exit"]


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

    def show_welcome(
        self,
        model: str,
        ctx_kb: int = 0,
        resumed_at: str | None = None,
        hitmos: bool = False,
    ) -> None:
        from datetime import datetime

        self.console.print()
        if resumed_at:
            try:
                dt = datetime.fromisoformat(resumed_at)
                label = dt.strftime("%b %d, %H:%M")
            except ValueError:
                label = resumed_at
            title = f"[bold]✻  {APP_TITLE}[/bold] [dim]· resuming session from {label}[/dim]"
        else:
            title = f"[bold]✻  Welcome to {APP_TITLE}[/bold]"

        self.console.print(
            Panel(
                Text.from_markup(f"{title}\n\n[dim]/help for commands[/dim]"),
                border_style="dim",
                padding=(1, 2),
            )
        )
        self.console.print()
        self.console.print(f" [dim]◆[/dim] [dim]{get_cwd_display()}[/dim]")
        self.console.print(f" [dim]◆[/dim] [dim]{model}[/dim]")
        if hitmos:
            self.console.print(f" [dim]◆[/dim] [dim].hitmos loaded ({ctx_kb} KB)[/dim]")
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

    @staticmethod
    def _is_repeating(buffer: str, chunk: int = 300, window: int = 3000) -> bool:
        if len(buffer) < chunk * 2:
            return False
        tail = buffer[-chunk:]
        return tail in buffer[-(window + chunk):-chunk]

    async def stream_response(self, token_gen: AsyncGenerator[str, None]) -> str:
        buffer = ""

        first_token: str | None = None
        with self.console.status("[dim]Thinking…[/dim]", spinner="dots"):
            async for tok in token_gen:
                first_token = tok
                break

        if first_token is None:
            return buffer

        self.console.print()
        buffer = first_token
        self.console.file.write(first_token)
        self.console.file.flush()

        MAX_CHARS = 24_000
        truncated = False
        interrupted = False
        looping = False

        try:
            async for token in token_gen:
                buffer += token
                self.console.file.write(token)
                self.console.file.flush()
                if len(buffer) >= MAX_CHARS:
                    truncated = True
                    break
                if len(buffer) % 400 == 0 and self._is_repeating(buffer):
                    looping = True
                    break
        except (KeyboardInterrupt, asyncio.CancelledError):
            interrupted = True
        finally:
            await token_gen.aclose()

        self.console.print()
        if looping:
            self.console.print(" [bold yellow]⚠[/bold yellow] [dim]Loop detected — stopped.[/dim]")
        elif truncated:
            self.console.print(" [dim]Response truncated.[/dim]")
        if interrupted:
            self.console.print(" [dim]Interrupted.[/dim]")

        return buffer

    async def get_input(self) -> str:
        cwd = get_cwd_display()
        return await self._session.prompt_async(
            FormattedText([
                ("class:prompt-cwd", f"{cwd} "),
                ("class:prompt", "> "),
            ]),
        )

    def show_tool_call(self, name: str, arguments: str) -> None:
        try:
            args = orjson.loads(arguments)
            first_val = str(next(iter(args.values()), "")) if args else ""
            arg_display = first_val[:70]
        except Exception:
            arg_display = arguments[:70]
        self.console.print(f"\n [bold #cc8800]⎿[/bold #cc8800] [bold]{name}[/bold]([dim]{arg_display}[/dim])")

    def show_tool_result(self, result: str) -> None:
        lines = [ln for ln in result.split("\n") if ln.strip()]
        for line in lines[:3]:
            self.console.print(f"   [dim]{line[:100]}[/dim]")
        if len(lines) > 3:
            self.console.print(f"   [dim]… +{len(lines) - 3} lines[/dim]")
        self.console.print()

    def show_cost(self, usage: object) -> None:
        from .client import UsageInfo
        u: UsageInfo = usage  # type: ignore[assignment]
        total = u.prompt_tokens + u.completion_tokens
        self.console.print()
        if total == 0:
            self.console.print(" [dim]No usage data yet.[/dim]")
            self.console.print()
            return
        self.console.print(f" [dim]◆[/dim] prompt tokens      [bold]{u.prompt_tokens:,}[/bold]")
        self.console.print(f" [dim]◆[/dim] completion tokens  [bold]{u.completion_tokens:,}[/bold]")
        self.console.print(f" [dim]◆[/dim] total tokens       [bold]{total:,}[/bold]")
        if u.cost > 0:
            self.console.print(f" [dim]◆[/dim] cost               [bold green]${u.cost:.6f}[/bold green]")
        else:
            self.console.print(" [dim]◆[/dim] cost               [dim]n/a[/dim]")
        self.console.print()

    def show_response_meta(self, usage: object) -> None:
        from .client import UsageInfo
        u: UsageInfo = usage  # type: ignore[assignment]
        total = u.prompt_tokens + u.completion_tokens
        if total == 0:
            return
        tk = f"{total / 1000:.1f}k" if total >= 1000 else str(total)
        cost_str = f" · [dim]${u.cost:.4f}[/dim]" if u.cost > 0 else ""
        self.console.print(f" [dim]· {tk} tokens{cost_str}[/dim]")
        self.console.print()

    def show_exit(self) -> None:
        self.console.print()
        self.console.print(" [dim]Goodbye.[/dim]")
        self.console.print()

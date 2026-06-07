import asyncio
import shutil
import subprocess
import sys

import typer
from rich.console import Console
from rich.prompt import Prompt

app = typer.Typer(
    name="hitmos",
    help="Hitmos — AI terminal assistant",
    add_completion=False,
    no_args_is_help=False,
)

console = Console()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    resume: bool = typer.Option(False, "--resume", "-r", help="Resume last saved session"),
) -> None:
    """Start interactive Hitmos session."""
    if ctx.invoked_subcommand is None:
        from .app import HitmosApp

        HitmosApp().run(resume=resume)


@app.command("self-update")
def self_update() -> None:
    """Update hitmos to the latest version from PyPI."""
    from fasthttp import AsyncSession

    from .constants import VERSION

    async def _fetch_latest() -> str:
        async with AsyncSession(timeout=10.0) as session:
            resp = await session.get("https://pypi.org/pypi/hitmos/json")
            return resp.json()["info"]["version"]

    def _ver(v: str) -> tuple[int, ...]:
        try:
            return tuple(int(x) for x in v.split("."))
        except ValueError:
            return (0,)

    console.print()
    with console.status("[dim]Checking PyPI...[/dim]"):
        try:
            latest: str = asyncio.run(_fetch_latest())
        except Exception as exc:
            console.print(f"  [bold red]✖[/bold red]  Cannot reach PyPI: {exc}")
            console.print()
            raise typer.Exit(1)

    if _ver(latest) <= _ver(VERSION):
        console.print(
            f"  [bold green]✓[/bold green]  Already up to date [dim]({VERSION})[/dim]"
        )
        console.print()
        return

    console.print(
        f"  [bold]Update available:[/bold] {VERSION} → [bold green]{latest}[/bold green]"
    )
    console.print()

    uv = shutil.which("uv")
    if uv:
        result = subprocess.run(
            [uv, "tool", "upgrade", "hitmos"],
            capture_output=True,
        )
        if result.returncode != 0:
            result = subprocess.run([uv, "pip", "install", "--upgrade", "hitmos"])
        else:
            console.print()
    else:
        result = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "hitmos"])
        console.print()

    if result.returncode == 0:
        console.print(
            f"  [bold green]✓[/bold green]  Updated to [bold]{latest}[/bold]"
        )
    else:
        console.print("  [bold red]✖[/bold red]  Update failed.")
        raise typer.Exit(1)
    console.print()


@app.command("login")
def login() -> None:
    """Save OpenRouter API key to ~/.hitmos/config.toml."""
    from .config import ConfigManager

    console.print()
    console.print("  [bold]Hitmos Login[/bold]")
    console.print()

    api_key = Prompt.ask("  Paste your OpenRouter API key", password=True)
    api_key = api_key.strip()

    if not api_key:
        console.print("  [bold red]✖[/bold red]  No API key provided.")
        raise typer.Exit(1)

    ConfigManager().save_token(api_key)

    console.print()
    console.print(
        "  [bold green]✓[/bold green]  API key saved to [dim]~/.hitmos/config.toml[/dim]"
    )
    console.print()

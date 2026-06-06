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
def main(ctx: typer.Context) -> None:
    """Start interactive Hitmos session."""
    if ctx.invoked_subcommand is None:
        from .app import HitmosApp

        HitmosApp().run()


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

"""
Lulu CLI. Entry point registered in pyproject.toml as `lulu`.
"""

from __future__ import annotations

import sys

import typer
from rich.console import Console
from rich.table import Table

from lulu import registry
from lulu.engine import ChatSession

app = typer.Typer(
    name="lulu",
    help="Run large language models locally. (Name pending appeal.)",
    no_args_is_help=True,
)
console = Console()


@app.command()
def pull(name: str = typer.Argument(..., help="Model alias, e.g. 'llama3.1'")):
    """Download a model into the local cache."""
    if name not in registry.KNOWN_MODELS:
        console.print(f"[red]Unknown model '{name}'.[/red] Known models:")
        for known_name, info in registry.KNOWN_MODELS.items():
            console.print(f"  [bold]{known_name}[/bold] — {info['description']}")
        raise typer.Exit(code=1)

    console.print(f"Pulling [bold]{name}[/bold] ...")
    entry = registry.pull(name)
    size_gb = entry.size_bytes / (1024 ** 3)
    console.print(f"[green]Done.[/green] Saved to {entry.path} ({size_gb:.1f} GB)")


@app.command("list")
def list_models():
    """List locally downloaded models."""
    models = registry.list_models()
    if not models:
        console.print("No models downloaded yet. Try [bold]lulu pull llama3.1[/bold].")
        return

    table = Table(title="Local models")
    table.add_column("Name", style="bold")
    table.add_column("Size")
    table.add_column("Path")
    for m in models:
        size_gb = m.size_bytes / (1024 ** 3)
        table.add_row(m.name, f"{size_gb:.1f} GB", m.path)
    console.print(table)


@app.command()
def rm(name: str = typer.Argument(..., help="Model name to remove")):
    """Remove a locally downloaded model."""
    if registry.remove(name):
        console.print(f"[green]Removed[/green] {name}")
    else:
        console.print(f"[yellow]No such model:[/yellow] {name}")
        raise typer.Exit(code=1)


@app.command()
def run(
    name: str = typer.Argument(..., help="Model name (must already be pulled)"),
    n_ctx: int = typer.Option(4096, help="Context window size"),
    n_gpu_layers: int = typer.Option(0, help="Layers to offload to GPU (0 = CPU only)"),
    system: str = typer.Option(None, help="Optional system prompt"),
):
    """Start an interactive chat session with a local model."""
    entry = registry.get(name)
    if entry is None:
        console.print(f"[red]Model '{name}' not found locally.[/red] Run [bold]lulu pull {name}[/bold] first.")
        raise typer.Exit(code=1)

    console.print(f"Loading [bold]{name}[/bold] ...")
    with ChatSession(
        model_path=entry.path,
        n_ctx=n_ctx,
        n_gpu_layers=n_gpu_layers,
        system_prompt=system,
    ) as session:
        console.print(f"[dim]{session.model_description}[/dim]")
        console.print("Type your message and press Enter. Ctrl+D to quit.\n")

        while True:
            try:
                user_input = console.input("[bold cyan]>>> [/bold cyan]")
            except (EOFError, KeyboardInterrupt):
                console.print("\nBye!")
                break

            if not user_input.strip():
                continue

            def _on_token(token: str) -> bool:
                sys.stdout.write(token)
                sys.stdout.flush()
                return True

            session.send(user_input, on_token=_on_token)
            print()  # newline after the streamed reply


def main():
    app()


if __name__ == "__main__":
    main()

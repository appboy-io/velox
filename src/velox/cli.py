"""Velox CLI — YAML-driven Gatling performance testing."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import typer
from rich.console import Console

from velox.parser import parse_test_file, ValidationError

app = typer.Typer(
    name="velox",
    help="Velox — YAML-driven Gatling performance testing CLI.",
)
console = Console()


def _get_sample_yaml_path() -> Path:
    return Path(__file__).parent / "templates" / "sample_test.yaml"


@app.command()
def run(
    test_file: str,
    base_url: str = typer.Option(None, "--base-url", help="Override base URL"),
    users: int = typer.Option(None, "--users", help="Override user count"),
) -> None:
    """Run a performance test from a YAML definition."""
    from velox.orchestrator import orchestrate_run

    path = Path(test_file)
    passed = orchestrate_run(
        test_file=path,
        base_url_override=base_url,
        users_override=users,
    )
    if not passed:
        raise typer.Exit(code=1)


@app.command()
def validate(test_file: str) -> None:
    """Validate a YAML test definition without running."""
    path = Path(test_file)
    try:
        definition = parse_test_file(path)
        console.print(f"[green]✓[/green] {path.name} is valid")
        console.print(f"  Name: {definition.name}")
        console.print(f"  Steps: {len(definition.flow)}")
        console.print(f"  Users: {definition.config.users}")
    except FileNotFoundError:
        console.print(f"[red]✗[/red] File not found: {path}")
        raise typer.Exit(code=1)
    except ValidationError as e:
        console.print(f"[red]✗[/red] Validation failed: {e}")
        raise typer.Exit(code=1)


@app.command()
def init() -> None:
    """Scaffold a sample YAML test file."""
    dest = Path("velox-sample.yaml")
    if dest.exists():
        console.print(f"[yellow]![/yellow] {dest} already exists, skipping")
        return
    source = _get_sample_yaml_path()
    shutil.copy(source, dest)
    console.print(f"[green]✓[/green] Created {dest}")
    console.print("  Edit it with your API details, then run: velox run velox-sample.yaml")


@app.command()
def report() -> None:
    """View results from the last test run."""
    results_dir = Path("results")
    if not results_dir.exists():
        console.print("[yellow]No results found. Run a test first:[/yellow] velox run test.yaml")
        raise typer.Exit(code=1)

    # Find most recent results directory
    result_dirs = sorted(results_dir.iterdir(), reverse=True)
    if not result_dirs:
        console.print("[yellow]No results found.[/yellow]")
        raise typer.Exit(code=1)

    latest = result_dirs[0] / "reports" / "report.md"
    if latest.exists():
        console.print(latest.read_text())
    else:
        console.print(f"[yellow]No report found in {result_dirs[0]}[/yellow]")

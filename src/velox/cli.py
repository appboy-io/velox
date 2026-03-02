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
    from velox.runner import GatlingRunError

    path = Path(test_file)
    try:
        passed = orchestrate_run(
            test_file=path,
            base_url_override=base_url,
            users_override=users,
        )
    except GatlingRunError as e:
        console.print(f"  ├─ [red]✗ {e}[/red]")
        detail = e.stderr.strip() or e.stdout.strip() if hasattr(e, 'stdout') else e.stderr.strip()
        if detail:
            console.print(f"  └─ [dim]{detail}[/dim]")
        raise typer.Exit(code=1)
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


CI_PLATFORMS = {
    "github": (".github/workflows/velox.yml", "ci/github.yml"),
    "circle": (".circleci/config.yml", "ci/circle.yml"),
    "bitbucket": ("bitbucket-pipelines.yml", "ci/bitbucket.yml"),
}


@app.command()
def init(
    ci: str = typer.Option(None, "--ci", help="Generate CI/CD workflow: github, circle, or bitbucket"),
) -> None:
    """Scaffold a sample YAML test file and optionally a CI/CD workflow."""
    # Always create sample YAML
    dest = Path("velox-sample.yaml")
    if dest.exists():
        console.print(f"[yellow]![/yellow] {dest} already exists, skipping")
    else:
        source = _get_sample_yaml_path()
        shutil.copy(source, dest)
        console.print(f"[green]✓[/green] Created {dest}")

    # Optionally create CI workflow
    if ci:
        ci = ci.lower()
        if ci not in CI_PLATFORMS:
            console.print(f"[red]✗[/red] Unknown CI platform: {ci}. Use: github, circle, or bitbucket")
            raise typer.Exit(code=1)

        dest_path, template_name = CI_PLATFORMS[ci]
        dest_file = Path(dest_path)
        dest_file.parent.mkdir(parents=True, exist_ok=True)

        template_source = Path(__file__).parent / "templates" / template_name
        shutil.copy(template_source, dest_file)
        console.print(f"[green]✓[/green] Created {dest_file}")
        console.print(f"  Set TARGET_URL in your CI/CD environment variables")
    elif ci is None:
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

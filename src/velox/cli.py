import typer

app = typer.Typer(
    name="velox",
    help="YAML-driven Gatling performance testing CLI.",
)


@app.command()
def run(test_file: str) -> None:
    """Run a performance test from a YAML definition."""
    typer.echo(f"Running test: {test_file}")


@app.command()
def validate(test_file: str) -> None:
    """Validate a YAML test definition without running."""
    typer.echo(f"Validating: {test_file}")


@app.command()
def init() -> None:
    """Scaffold a sample YAML test file."""
    typer.echo("Initializing sample test file...")


@app.command()
def report() -> None:
    """View results from the last test run."""
    typer.echo("Showing last report...")

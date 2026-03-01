import pytest
from typer.testing import CliRunner

from velox.cli import app


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def invoke(cli_runner):
    def _invoke(*args):
        return cli_runner.invoke(app, list(args))
    return _invoke

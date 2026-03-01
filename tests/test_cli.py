import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from velox.cli import app

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def runner():
    return CliRunner()


class TestValidateCommand:
    def test_valid_file(self, runner):
        result = runner.invoke(app, ["validate", str(FIXTURES / "valid_test.yaml")])
        assert result.exit_code == 0
        assert "valid" in result.stdout.lower() or "✓" in result.stdout

    def test_invalid_file(self, runner):
        result = runner.invoke(app, ["validate", str(FIXTURES / "invalid_no_flow.yaml")])
        assert result.exit_code != 0

    def test_file_not_found(self, runner):
        result = runner.invoke(app, ["validate", "/nonexistent/test.yaml"])
        assert result.exit_code != 0


class TestInitCommand:
    def test_creates_sample_file(self, runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0
        sample = tmp_path / "velox-sample.yaml"
        assert sample.exists()


class TestRunCommand:
    @patch("velox.orchestrator.orchestrate_run")
    def test_run_calls_orchestrator(self, mock_orch, runner):
        mock_orch.return_value = True  # all thresholds passed
        result = runner.invoke(app, ["run", str(FIXTURES / "valid_test.yaml")])
        assert result.exit_code == 0
        mock_orch.assert_called_once()

    @patch("velox.orchestrator.orchestrate_run")
    def test_run_nonzero_on_threshold_failure(self, mock_orch, runner):
        mock_orch.return_value = False  # thresholds failed
        result = runner.invoke(app, ["run", str(FIXTURES / "valid_test.yaml")])
        assert result.exit_code != 0

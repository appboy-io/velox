"""End-to-end integration test with mocked Gatling execution."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from velox.cli import app

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_gatling(tmp_path):
    """Set up a mock Gatling environment."""
    gatling_home = tmp_path / "gatling"
    bin_dir = gatling_home / "bin"
    bin_dir.mkdir(parents=True)
    gatling_bin = bin_dir / "gatling.sh"
    gatling_bin.write_text("#!/bin/sh\necho mock")
    gatling_bin.chmod(0o755)
    return gatling_home


class TestEndToEnd:
    @patch("velox.orchestrator.push_results")
    @patch("velox.orchestrator.get_current_branch", return_value="feature/test")
    @patch("velox.orchestrator.GatlingRunner")
    def test_validate_then_run(self, mock_runner_cls, mock_branch, mock_push, runner, mock_gatling, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        # Step 1: Validate
        result = runner.invoke(app, ["validate", str(FIXTURES / "valid_test.yaml")])
        assert result.exit_code == 0

        # Step 2: Mock the Gatling runner to produce a simulation.log
        mock_runner = MagicMock()
        mock_runner.gatling_home = mock_gatling
        mock_runner_cls.return_value = mock_runner

        def fake_run(simulation_class, results_dir):
            results_dir.mkdir(parents=True, exist_ok=True)
            sim_log = results_dir / "test-run" / "simulation.log"
            sim_log.parent.mkdir(parents=True, exist_ok=True)
            sim_log.write_text(
                "RUN\tvelox\ttest\t1709312400000\t \t3.9.5\n"
                "GROUP\tCheckout Flow\t1709312400000\t1709312401500\t1500\tOK\n"
                "REQUEST\tCheckout Flow\tLogin\t1709312400000\t1709312400150\tOK\n"
                "REQUEST\tCheckout Flow\tGet Products\t1709312400200\t1709312400420\tOK\n"
            )
            return MagicMock(returncode=0)

        mock_runner.run.side_effect = fake_run

        # Step 3: Run
        result = runner.invoke(app, ["run", str(FIXTURES / "valid_test.yaml")])
        assert result.exit_code == 0

        # Step 4: Verify reports were generated
        results_dirs = list(Path("results").iterdir())
        assert len(results_dirs) == 1
        report_dir = results_dirs[0] / "reports"
        assert (report_dir / "report.json").exists()
        assert (report_dir / "report.md").exists()

    def test_init_then_validate(self, runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        # Init
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0
        assert (tmp_path / "velox-sample.yaml").exists()

        # Validate the generated sample
        result = runner.invoke(app, ["validate", "velox-sample.yaml"])
        assert result.exit_code == 0

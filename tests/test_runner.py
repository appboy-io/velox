import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from velox.runner import GatlingRunner, GatlingNotFoundError, GatlingRunError


class TestGatlingRunner:
    def test_find_gatling_from_env(self, monkeypatch, tmp_path):
        gatling_bin = tmp_path / "gatling.sh"
        gatling_bin.write_text("#!/bin/sh\necho gatling")
        gatling_bin.chmod(0o755)
        monkeypatch.setenv("GATLING_HOME", str(tmp_path))
        runner = GatlingRunner()
        assert runner.gatling_home == tmp_path

    def test_gatling_not_found_raises(self, monkeypatch):
        monkeypatch.delenv("GATLING_HOME", raising=False)
        with pytest.raises(GatlingNotFoundError):
            GatlingRunner()

    @patch("velox.runner.subprocess.run")
    def test_run_simulation(self, mock_run, monkeypatch, tmp_path):
        gatling_bin = tmp_path / "bin" / "gatling.sh"
        gatling_bin.parent.mkdir(parents=True)
        gatling_bin.write_text("#!/bin/sh\necho gatling")
        gatling_bin.chmod(0o755)
        monkeypatch.setenv("GATLING_HOME", str(tmp_path))

        mock_run.return_value = MagicMock(returncode=0, stdout="done", stderr="")

        runner = GatlingRunner()
        results_dir = tmp_path / "results"
        sim_file = tmp_path / "Simulation.scala"
        sim_file.write_text("class Test {}")

        result = runner.run(
            simulation_class="TestSimulation",
            results_dir=results_dir,
        )
        assert result.returncode == 0
        mock_run.assert_called_once()

    @patch("velox.runner.subprocess.run")
    def test_run_failure_raises(self, mock_run, monkeypatch, tmp_path):
        gatling_bin = tmp_path / "bin" / "gatling.sh"
        gatling_bin.parent.mkdir(parents=True)
        gatling_bin.write_text("#!/bin/sh\necho gatling")
        gatling_bin.chmod(0o755)
        monkeypatch.setenv("GATLING_HOME", str(tmp_path))

        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")

        runner = GatlingRunner()
        with pytest.raises(GatlingRunError):
            runner.run(
                simulation_class="TestSimulation",
                results_dir=tmp_path / "results",
            )

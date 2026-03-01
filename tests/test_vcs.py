import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from velox.vcs import push_results, get_current_branch


class TestGetCurrentBranch:
    @patch("velox.vcs.subprocess.run")
    def test_returns_branch_name(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="feature/checkout\n"
        )
        assert get_current_branch() == "feature/checkout"

    @patch("velox.vcs.subprocess.run")
    def test_strips_whitespace(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="  main \n"
        )
        assert get_current_branch() == "main"


class TestPushResults:
    @patch("velox.vcs.subprocess.run")
    def test_push_creates_branch_and_commits(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        results_dir = tmp_path / "results"
        results_dir.mkdir()
        (results_dir / "report.json").write_text("{}")
        (results_dir / "report.md").write_text("# Report")

        push_results(
            results_dir=results_dir,
            branch_suffix="-perf-results",
            remote="origin",
            current_branch="feature/checkout",
        )

        # Should have run git commands
        assert mock_run.call_count >= 3  # checkout, add, commit, push

    @patch("velox.vcs.subprocess.run")
    def test_branch_name_format(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        results_dir = tmp_path / "results"
        results_dir.mkdir()
        (results_dir / "report.json").write_text("{}")

        push_results(
            results_dir=results_dir,
            branch_suffix="-perf-results",
            remote="origin",
            current_branch="feature/login",
        )

        # Check the branch name in the checkout command
        checkout_calls = [
            c for c in mock_run.call_args_list
            if "checkout" in str(c)
        ]
        assert any("feature/login-perf-results" in str(c) for c in checkout_calls)

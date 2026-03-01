"""VCS results push for Velox."""

from __future__ import annotations

import subprocess
from pathlib import Path


def get_current_branch() -> str:
    """Get the current git branch name."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def push_results(
    results_dir: Path,
    branch_suffix: str,
    remote: str,
    current_branch: str,
) -> None:
    """Push results directory to a VCS branch."""
    target_branch = f"{current_branch}{branch_suffix}"

    def _run(cmd: list[str]) -> None:
        subprocess.run(cmd, capture_output=True, text=True, check=True)

    # Stash any current changes
    _run(["git", "stash", "--include-untracked"])

    try:
        # Try to checkout existing results branch, or create new one
        try:
            _run(["git", "checkout", target_branch])
        except subprocess.CalledProcessError:
            _run(["git", "checkout", "--orphan", target_branch])
            _run(["git", "rm", "-rf", "."])

        # Copy results into the branch
        _run(["git", "add", str(results_dir)])
        _run(["git", "commit", "-m", f"perf: add results from {current_branch}"])
        _run(["git", "push", remote, target_branch])

    finally:
        # Return to original branch
        _run(["git", "checkout", current_branch])
        try:
            _run(["git", "stash", "pop"])
        except subprocess.CalledProcessError:
            pass  # no stash to pop

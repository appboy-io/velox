"""Gatling subprocess launcher."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


class GatlingNotFoundError(Exception):
    """Raised when Gatling installation cannot be found."""


class GatlingRunError(Exception):
    """Raised when Gatling exits with a non-zero code."""

    def __init__(self, message: str, returncode: int, stderr: str, stdout: str = ""):
        super().__init__(message)
        self.returncode = returncode
        self.stderr = stderr
        self.stdout = stdout


@dataclass
class GatlingResult:
    """Result of a Gatling simulation run."""

    returncode: int
    stdout: str
    stderr: str
    results_dir: Path


class GatlingRunner:
    """Manages Gatling subprocess execution."""

    def __init__(self) -> None:
        gatling_home = os.environ.get("GATLING_HOME")
        if not gatling_home:
            raise GatlingNotFoundError(
                "GATLING_HOME environment variable is not set. "
                "Please install Gatling and set GATLING_HOME."
            )
        self.gatling_home = Path(gatling_home)

    def run(
        self,
        simulation_class: str,
        results_dir: Path,
    ) -> GatlingResult:
        """Run a Gatling simulation."""
        results_dir.mkdir(parents=True, exist_ok=True)

        gatling_bin = self.gatling_home / "bin" / "gatling.sh"
        if not gatling_bin.exists():
            gatling_bin = self.gatling_home / "bin" / "gatling.bat"

        cmd = [
            str(gatling_bin),
            "--run-mode", "local",
            "--simulation", simulation_class,
            "--results-folder", str(results_dir),
            "--no-reports",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise GatlingRunError(
                f"Gatling exited with code {result.returncode}",
                returncode=result.returncode,
                stderr=result.stderr,
                stdout=result.stdout,
            )

        return GatlingResult(
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            results_dir=results_dir,
        )

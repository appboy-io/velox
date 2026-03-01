"""Parser for Gatling simulation.log files."""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RequestRecord:
    """A single request record from simulation.log."""

    name: str
    start_ms: int
    end_ms: int
    status: str

    @property
    def response_time_ms(self) -> int:
        return self.end_ms - self.start_ms


@dataclass
class SimulationMetrics:
    """Parsed metrics from a Gatling simulation run."""

    requests: list[RequestRecord] = field(default_factory=list)
    group_name: str | None = None
    group_duration_ms: int | None = None

    def _response_times(self) -> list[int]:
        return [r.response_time_ms for r in self.requests]

    def _percentile(self, times: list[int], pct: float) -> int:
        if not times:
            return 0
        sorted_times = sorted(times)
        idx = int(len(sorted_times) * pct / 100)
        idx = min(idx, len(sorted_times) - 1)
        return sorted_times[idx]

    def overall_stats(self) -> dict:
        """Compute aggregate statistics across all requests."""
        times = self._response_times()
        if not times:
            return {"mean": 0, "p50": 0, "p75": 0, "p95": 0, "p99": 0, "errorRate": 0.0}

        error_count = sum(1 for r in self.requests if r.status != "OK")
        return {
            "mean": int(statistics.mean(times)),
            "p50": self._percentile(times, 50),
            "p75": self._percentile(times, 75),
            "p95": self._percentile(times, 95),
            "p99": self._percentile(times, 99),
            "errorRate": round(error_count / len(self.requests) * 100, 2),
        }

    def request_stats(self) -> list[dict]:
        """Compute per-request statistics."""
        stats_by_name: dict[str, list[RequestRecord]] = {}
        for req in self.requests:
            stats_by_name.setdefault(req.name, []).append(req)

        result = []
        for name, records in stats_by_name.items():
            times = [r.response_time_ms for r in records]
            error_count = sum(1 for r in records if r.status != "OK")
            result.append({
                "name": name,
                "mean": int(statistics.mean(times)),
                "p50": self._percentile(times, 50),
                "p75": self._percentile(times, 75),
                "p95": self._percentile(times, 95),
                "p99": self._percentile(times, 99),
                "errorRate": round(error_count / len(records) * 100, 2),
            })
        return result


def parse_simulation_log(path: Path) -> SimulationMetrics:
    """Parse a Gatling simulation.log file into structured metrics."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Simulation log not found: {path}")

    metrics = SimulationMetrics()

    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if not parts:
            continue

        record_type = parts[0]

        if record_type == "REQUEST" and len(parts) >= 7:
            metrics.requests.append(
                RequestRecord(
                    name=parts[3],
                    start_ms=int(parts[4]),
                    end_ms=int(parts[5]),
                    status=parts[6],
                )
            )
        elif record_type == "GROUP" and len(parts) >= 7:
            metrics.group_name = parts[3]
            start = int(parts[4])
            end = int(parts[5])
            metrics.group_duration_ms = end - start

    return metrics

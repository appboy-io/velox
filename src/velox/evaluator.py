"""Threshold evaluation for Velox test results."""

from __future__ import annotations

from dataclasses import dataclass, field

from velox.models import Threshold


@dataclass
class ThresholdResult:
    """Result of threshold evaluation."""

    passed: bool
    failures: list[str] = field(default_factory=list)


def evaluate_thresholds(
    stats: dict,
    threshold: Threshold | None,
) -> ThresholdResult:
    """Evaluate metrics against threshold definitions."""
    if threshold is None:
        return ThresholdResult(passed=True)

    failures = []

    checks = [
        ("p50", threshold.p50_ms),
        ("p75", threshold.p75_ms),
        ("p95", threshold.p95_ms),
        ("p99", threshold.p99_ms),
    ]

    for metric_name, limit in checks:
        if limit is not None and metric_name in stats:
            actual = stats[metric_name]
            if actual > limit:
                failures.append(
                    f"{metric_name}: {actual}ms exceeded threshold of {limit}ms"
                )

    if threshold.error_rate_pct is not None and "errorRate" in stats:
        actual_rate = stats["errorRate"]
        if actual_rate > threshold.error_rate_pct:
            failures.append(
                f"Error rate: {actual_rate}% exceeded threshold of {threshold.error_rate_pct}%"
            )

    return ThresholdResult(
        passed=len(failures) == 0,
        failures=failures,
    )

"""Report generators for Velox test results."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from velox.evaluator import ThresholdResult
from velox.models import TestConfig, Threshold


def generate_json_report(data: dict, output_path: Path) -> None:
    """Generate a JSON report file."""
    report = {
        "testName": data["test_name"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {
            "users": data["config"].users,
            "rampUp": data["config"].rampUp,
            "duration": data["config"].duration,
        },
        "overall": {
            **data["overall_stats"],
            "thresholdPassed": data["overall_threshold_result"].passed,
        },
        "steps": [],
    }

    for req_stat in data["request_stats"]:
        name = req_stat["name"]
        step_result = data["step_threshold_results"].get(name)
        report["steps"].append({
            **req_stat,
            "thresholdPassed": step_result.passed if step_result else True,
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )


def _bar(value: int, max_value: int, width: int = 30) -> str:
    """Generate an ASCII bar."""
    if max_value == 0:
        return ""
    filled = int(value / max_value * width)
    return "█" * filled + "░" * (width - filled)


def generate_markdown_report(data: dict, output_path: Path) -> None:
    """Generate a Markdown report file with tables and ASCII charts."""
    lines: list[str] = []
    overall = data["overall_stats"]
    threshold_result: ThresholdResult = data["overall_threshold_result"]
    status = "✓ PASS" if threshold_result.passed else "✗ FAIL"

    lines.append(f"# {data['test_name']} — Performance Report")
    lines.append("")
    lines.append(f"**Status:** {status}")
    lines.append(f"**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"**Users:** {data['config'].users} | "
                 f"**Ramp-up:** {data['config'].rampUp} | "
                 f"**Duration:** {data['config'].duration}")
    lines.append("")

    # Overall metrics table
    lines.append("## Overall Metrics")
    lines.append("")
    threshold_def = data.get("overall_threshold")
    threshold_col = ""
    if threshold_def and threshold_def.p95_ms:
        threshold_col = f"{threshold_def.p95_ms}ms"
    lines.append("| Metric | Value | Threshold |")
    lines.append("|--------|-------|-----------|")
    lines.append(f"| Mean | {overall['mean']}ms | |")
    lines.append(f"| P50 | {overall['p50']}ms | |")
    lines.append(f"| P75 | {overall['p75']}ms | |")
    lines.append(f"| P95 | {overall['p95']}ms | {threshold_col} |")
    lines.append(f"| P99 | {overall['p99']}ms | |")
    error_threshold = ""
    if threshold_def and threshold_def.error_rate_pct is not None:
        error_threshold = f"{threshold_def.error_rate_pct}%"
    lines.append(f"| Error Rate | {overall['errorRate']}% | {error_threshold} |")
    lines.append("")

    if threshold_result.failures:
        lines.append("### Failures")
        for f in threshold_result.failures:
            lines.append(f"- ✗ {f}")
        lines.append("")

    # Per-step breakdown
    lines.append("## Step Breakdown")
    lines.append("")
    lines.append("| Step | Mean | P50 | P75 | P95 | P99 | Error Rate | Status |")
    lines.append("|------|------|-----|-----|-----|-----|------------|--------|")
    for req_stat in data["request_stats"]:
        name = req_stat["name"]
        step_result = data["step_threshold_results"].get(name)
        step_status = "✓" if (not step_result or step_result.passed) else "✗"
        lines.append(
            f"| {name} "
            f"| {req_stat['mean']}ms "
            f"| {req_stat['p50']}ms "
            f"| {req_stat['p75']}ms "
            f"| {req_stat['p95']}ms "
            f"| {req_stat['p99']}ms "
            f"| {req_stat['errorRate']}% "
            f"| {step_status} |"
        )
    lines.append("")

    # ASCII latency chart
    lines.append("## Latency Distribution")
    lines.append("")
    lines.append("```")
    max_p99 = max((r["p99"] for r in data["request_stats"]), default=1)
    for req_stat in data["request_stats"]:
        bar = _bar(req_stat["p95"], max_p99)
        lines.append(f"{req_stat['name']:20s} | {bar} {req_stat['p95']}ms (p95)")
    lines.append("```")
    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")

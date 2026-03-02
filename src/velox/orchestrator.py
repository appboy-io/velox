"""Orchestrates the full Velox test run pipeline."""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console

from velox.evaluator import evaluate_thresholds, ThresholdResult
from velox.generator import generate_simulation, _to_class_name
from velox.interpolation import resolve_env_vars
from velox.log_parser import parse_simulation_log
from velox.models import TestDefinition
from velox.parser import parse_test_file
from velox.reporter import generate_json_report, generate_markdown_report
from velox.runner import GatlingRunner
from velox.vcs import get_current_branch, push_results

console = Console()


def orchestrate_run(
    test_file: Path,
    base_url_override: str | None = None,
    users_override: int | None = None,
) -> bool:
    """Run the full pipeline. Returns True if all thresholds pass."""
    # 1. Parse and validate
    console.print(f"[bold]● Loading:[/bold] {test_file.name}")
    definition = parse_test_file(test_file)

    if base_url_override:
        definition.baseUrl = base_url_override
    if users_override:
        definition.config.users = users_override

    console.print(f"  ├─ Users: {definition.config.users} | "
                  f"Ramp-up: {definition.config.rampUp} | "
                  f"Duration: {definition.config.duration}")

    # 2. Resolve environment variables
    variables = resolve_env_vars(definition.variables)

    # 3. Generate Gatling simulation
    console.print("  ├─ Generating Gatling simulation...")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    slug = definition.name.lower().replace(" ", "-")
    work_dir = Path("results") / f"{timestamp}-{slug}"
    sim_dir = work_dir / "simulations"
    sim_dir.mkdir(parents=True, exist_ok=True)

    class_name = _to_class_name(definition.name)
    sim_file = sim_dir / f"{class_name}Simulation.scala"
    generate_simulation(definition, output_path=sim_file)

    # 4. Run Gatling
    console.print("  ├─ Launching Gatling...")
    runner = GatlingRunner()
    gatling_results_dir = work_dir / "gatling-output"
    runner.run(
        simulation_class=f"velox.generated.{class_name}Simulation",
        simulations_dir=sim_dir,
        results_dir=gatling_results_dir,
    )

    # 5. Find and parse simulation.log
    sim_logs = list(gatling_results_dir.rglob("simulation.log"))
    if not sim_logs:
        console.print("  ├─ [red]✗ No simulation.log found[/red]")
        return False

    metrics = parse_simulation_log(sim_logs[0])

    # 6. Evaluate thresholds
    overall_stats = metrics.overall_stats()
    request_stats = metrics.request_stats()

    overall_result = evaluate_thresholds(overall_stats, definition.threshold)

    step_results: dict[str, ThresholdResult] = {}
    for step in definition.flow:
        if step.threshold:
            matching = [r for r in request_stats if r["name"] == step.name]
            if matching:
                step_results[step.name] = evaluate_thresholds(
                    matching[0], step.threshold
                )

    # 7. Print results
    console.print("  │")
    for req_stat in request_stats:
        name = req_stat["name"]
        step_res = step_results.get(name)
        icon = "✓" if (not step_res or step_res.passed) else "✗"
        threshold_info = ""
        step_def = next((s for s in definition.flow if s.name == name), None)
        if step_def and step_def.threshold and step_def.threshold.p95_ms:
            threshold_info = f"  (threshold: {step_def.threshold.p95})"
        color = "green" if icon == "✓" else "red"
        console.print(
            f"  ├─ [{color}]{icon} {name:20s} p95: {req_stat['p95']}ms{threshold_info}[/{color}]"
        )

    console.print("  │")
    overall_icon = "✓" if overall_result.passed else "✗"
    overall_color = "green" if overall_result.passed else "red"
    console.print(
        f"  ├─ [{overall_color}]{overall_icon} Overall Flow    "
        f"p95: {overall_stats['p95']}ms[/{overall_color}]"
    )
    console.print(
        f"  ├─ [{overall_color}]{overall_icon} Error Rate      "
        f"{overall_stats['errorRate']}%[/{overall_color}]"
    )

    # 8. Generate reports
    report_dir = work_dir / "reports"
    report_data = {
        "test_name": definition.name,
        "config": definition.config,
        "overall_stats": overall_stats,
        "request_stats": request_stats,
        "overall_threshold_result": overall_result,
        "step_threshold_results": step_results,
        "overall_threshold": definition.threshold,
    }

    generate_json_report(report_data, report_dir / "report.json")
    generate_markdown_report(report_data, report_dir / "report.md")

    # Copy Gatling HTML report if it exists
    html_reports = list(gatling_results_dir.rglob("index.html"))
    if html_reports:
        html_dest = report_dir / "html"
        shutil.copytree(html_reports[0].parent, html_dest, dirs_exist_ok=True)

    console.print(f"  ├─ Reports: ./{report_dir}")

    # 9. Push results if configured
    if definition.results.push:
        current_branch = get_current_branch()
        push_results(
            results_dir=report_dir,
            branch_suffix=definition.results.branchSuffix,
            remote=definition.results.remote,
            current_branch=current_branch,
        )
        target = f"{current_branch}{definition.results.branchSuffix}"
        console.print(
            f"  └─ Pushed to: {definition.results.remote}/{target}"
        )
    else:
        console.print("  └─ Done")

    all_passed = overall_result.passed and all(
        r.passed for r in step_results.values()
    )
    return all_passed

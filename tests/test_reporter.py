import json
import pytest
from pathlib import Path

from velox.reporter import generate_json_report, generate_markdown_report
from velox.models import TestConfig, Threshold
from velox.evaluator import ThresholdResult


@pytest.fixture
def sample_report_data():
    return {
        "test_name": "Checkout Flow",
        "config": TestConfig(users=100, rampUp="30s", duration="5m"),
        "overall_stats": {
            "mean": 1350, "p50": 1200, "p75": 1500,
            "p95": 1800, "p99": 2100, "errorRate": 0.3,
        },
        "request_stats": [
            {"name": "Login", "mean": 135, "p50": 120, "p75": 150, "p95": 180, "p99": 200, "errorRate": 0.0},
            {"name": "Get Products", "mean": 280, "p50": 250, "p75": 280, "p95": 310, "p99": 350, "errorRate": 0.0},
        ],
        "overall_threshold_result": ThresholdResult(passed=True),
        "step_threshold_results": {
            "Login": ThresholdResult(passed=True),
            "Get Products": ThresholdResult(passed=True),
        },
        "overall_threshold": Threshold(p95="2s", errorRate="1%"),
    }


class TestJsonReport:
    def test_generates_valid_json(self, sample_report_data, tmp_path):
        output = tmp_path / "report.json"
        generate_json_report(sample_report_data, output)
        assert output.exists()
        data = json.loads(output.read_text())
        assert data["testName"] == "Checkout Flow"
        assert data["overall"]["p95"] == 1800
        assert len(data["steps"]) == 2

    def test_includes_threshold_status(self, sample_report_data, tmp_path):
        output = tmp_path / "report.json"
        generate_json_report(sample_report_data, output)
        data = json.loads(output.read_text())
        assert data["overall"]["thresholdPassed"] is True


class TestMarkdownReport:
    def test_generates_markdown_file(self, sample_report_data, tmp_path):
        output = tmp_path / "report.md"
        generate_markdown_report(sample_report_data, output)
        assert output.exists()
        content = output.read_text()
        assert "Checkout Flow" in content
        assert "Login" in content

    def test_includes_summary_table(self, sample_report_data, tmp_path):
        output = tmp_path / "report.md"
        generate_markdown_report(sample_report_data, output)
        content = output.read_text()
        assert "|" in content  # markdown table
        assert "p95" in content.lower() or "P95" in content

    def test_includes_pass_fail_status(self, sample_report_data, tmp_path):
        output = tmp_path / "report.md"
        generate_markdown_report(sample_report_data, output)
        content = output.read_text()
        assert "PASS" in content or "pass" in content or "✓" in content

    def test_includes_ascii_chart(self, sample_report_data, tmp_path):
        output = tmp_path / "report.md"
        generate_markdown_report(sample_report_data, output)
        content = output.read_text()
        # ASCII bar chars
        assert "█" in content or "▓" in content or "#" in content

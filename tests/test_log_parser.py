import pytest
from pathlib import Path

from velox.log_parser import parse_simulation_log, SimulationMetrics


FIXTURES = Path(__file__).parent / "fixtures"


class TestParseSimulationLog:
    def test_parse_requests(self):
        metrics = parse_simulation_log(FIXTURES / "simulation.log")
        assert len(metrics.requests) == 4
        assert metrics.requests[0].name == "Login"
        assert metrics.requests[0].response_time_ms == 180

    def test_parse_group(self):
        metrics = parse_simulation_log(FIXTURES / "simulation.log")
        assert metrics.group_name == "Checkout Flow"
        assert metrics.group_duration_ms == 2500

    def test_overall_stats(self):
        metrics = parse_simulation_log(FIXTURES / "simulation.log")
        stats = metrics.overall_stats()
        assert "mean" in stats
        assert "p50" in stats
        assert "p95" in stats
        assert stats["errorRate"] == 0.0

    def test_per_request_stats(self):
        metrics = parse_simulation_log(FIXTURES / "simulation.log")
        request_stats = metrics.request_stats()
        assert len(request_stats) == 4
        login_stats = request_stats[0]
        assert login_stats["name"] == "Login"
        assert login_stats["mean"] == 180

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            parse_simulation_log(Path("/nonexistent/simulation.log"))

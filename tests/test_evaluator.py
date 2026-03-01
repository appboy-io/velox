import pytest

from velox.models import Threshold
from velox.evaluator import evaluate_thresholds, ThresholdResult


class TestEvaluateThresholds:
    def test_all_pass(self):
        stats = {"p95": 180, "errorRate": 0.5}
        threshold = Threshold(p95="200ms", errorRate="1%")
        result = evaluate_thresholds(stats, threshold)
        assert result.passed is True
        assert len(result.failures) == 0

    def test_p95_fails(self):
        stats = {"p95": 250, "errorRate": 0.5}
        threshold = Threshold(p95="200ms", errorRate="1%")
        result = evaluate_thresholds(stats, threshold)
        assert result.passed is False
        assert any("p95" in f for f in result.failures)

    def test_error_rate_fails(self):
        stats = {"p95": 180, "errorRate": 2.5}
        threshold = Threshold(errorRate="1%")
        result = evaluate_thresholds(stats, threshold)
        assert result.passed is False
        assert any("error" in f.lower() for f in result.failures)

    def test_no_threshold_always_passes(self):
        stats = {"p95": 9999, "errorRate": 99.0}
        result = evaluate_thresholds(stats, None)
        assert result.passed is True

    def test_partial_threshold(self):
        stats = {"p95": 180, "errorRate": 5.0}
        threshold = Threshold(p95="200ms")
        result = evaluate_thresholds(stats, threshold)
        assert result.passed is True  # only p95 checked

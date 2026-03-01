import pytest

from velox.models import (
    FlowStep,
    TestConfig,
    TestDefinition,
    Threshold,
    ResultsConfig,
)


class TestThreshold:
    def test_parse_milliseconds(self):
        t = Threshold(p95="200ms")
        assert t.p95_ms == 200

    def test_parse_seconds(self):
        t = Threshold(p95="2s")
        assert t.p95_ms == 2000

    def test_parse_error_rate(self):
        t = Threshold(errorRate="1%")
        assert t.error_rate_pct == 1.0

    def test_no_thresholds_is_valid(self):
        t = Threshold()
        assert t.p95_ms is None
        assert t.error_rate_pct is None


class TestFlowStep:
    def test_minimal_step(self):
        step = FlowStep(name="Login", method="POST", path="/auth/login")
        assert step.name == "Login"
        assert step.method == "POST"
        assert step.headers == {}
        assert step.body is None
        assert step.extract == {}

    def test_step_with_all_fields(self):
        step = FlowStep(
            name="Login",
            method="POST",
            path="/auth/login",
            headers={"Content-Type": "application/json"},
            body={"username": "test", "password": "pass"},
            extract={"token": "$.accessToken"},
            threshold=Threshold(p95="200ms"),
        )
        assert step.extract["token"] == "$.accessToken"
        assert step.threshold.p95_ms == 200


class TestTestConfig:
    def test_defaults(self):
        config = TestConfig()
        assert config.users == 1
        assert config.rampUp == "0s"
        assert config.duration == "30s"

    def test_custom_values(self):
        config = TestConfig(users=100, rampUp="30s", duration="5m")
        assert config.users == 100


class TestResultsConfig:
    def test_defaults(self):
        config = ResultsConfig()
        assert config.push is False
        assert config.branchSuffix == "-perf-results"
        assert config.remote == "origin"


class TestTestDefinition:
    def test_minimal_definition(self):
        defn = TestDefinition(
            name="Simple Test",
            baseUrl="https://example.com",
            flow=[
                FlowStep(name="Get Home", method="GET", path="/"),
            ],
        )
        assert defn.name == "Simple Test"
        assert len(defn.flow) == 1
        assert defn.config.users == 1

    def test_full_definition(self):
        defn = TestDefinition(
            name="Checkout Flow",
            baseUrl="https://api.example.com",
            config=TestConfig(users=100, rampUp="30s", duration="5m"),
            variables={"apiKey": "${ENV.API_KEY}"},
            flow=[
                FlowStep(name="Login", method="POST", path="/auth/login"),
                FlowStep(name="Get Products", method="GET", path="/products"),
            ],
            threshold=Threshold(p95="2s", errorRate="1%"),
            results=ResultsConfig(push=True),
        )
        assert defn.variables["apiKey"] == "${ENV.API_KEY}"
        assert defn.threshold.p95_ms == 2000
        assert defn.results.push is True

    def test_requires_name(self):
        with pytest.raises(Exception):
            TestDefinition(
                baseUrl="https://example.com",
                flow=[FlowStep(name="X", method="GET", path="/")],
            )

    def test_requires_at_least_one_step(self):
        with pytest.raises(Exception):
            TestDefinition(
                name="Empty",
                baseUrl="https://example.com",
                flow=[],
            )

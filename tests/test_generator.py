import pytest
from pathlib import Path

from velox.models import (
    FlowStep,
    TestConfig,
    TestDefinition,
    Threshold,
)
from velox.generator import generate_simulation


@pytest.fixture
def simple_definition():
    return TestDefinition(
        name="Simple Test",
        baseUrl="https://example.com",
        config=TestConfig(users=10, rampUp="5s", duration="30s"),
        flow=[
            FlowStep(name="Get Home", method="GET", path="/"),
        ],
    )


@pytest.fixture
def full_definition():
    return TestDefinition(
        name="Checkout Flow",
        baseUrl="https://api.example.com",
        config=TestConfig(users=100, rampUp="30s", duration="5m"),
        flow=[
            FlowStep(
                name="Login",
                method="POST",
                path="/auth/login",
                headers={"Content-Type": "application/json"},
                body={"username": "testuser", "password": "testpass"},
                extract={"token": "$.accessToken"},
                threshold=Threshold(p95="200ms"),
            ),
            FlowStep(
                name="Get Products",
                method="GET",
                path="/products",
                headers={"Authorization": "Bearer ${token}"},
                threshold=Threshold(p95="300ms"),
            ),
        ],
        threshold=Threshold(p95="2s", errorRate="1%"),
    )


class TestGenerateSimulation:
    def test_generates_valid_scala(self, simple_definition):
        code = generate_simulation(simple_definition)
        assert "class SimpleTestSimulation" in code
        assert "https://example.com" in code
        assert 'http("Get Home")' in code
        assert ".get" in code.lower() or '.httpRequest("GET"' in code

    def test_includes_scenario_setup(self, simple_definition):
        code = generate_simulation(simple_definition)
        assert "setUp(" in code
        assert "rampUsers(10)" in code
        assert "during(5" in code or "5)" in code

    def test_includes_post_with_body(self, full_definition):
        code = generate_simulation(full_definition)
        assert "post(" in code.lower() or '.httpRequest("POST"' in code
        assert "testuser" in code

    def test_includes_jsonpath_extraction(self, full_definition):
        code = generate_simulation(full_definition)
        assert "accessToken" in code
        assert "jsonPath" in code or "jsonpath" in code.lower()

    def test_includes_scenario_for_flow(self, full_definition):
        code = generate_simulation(full_definition)
        assert "scenario(" in code

    def test_writes_to_file(self, simple_definition, tmp_path):
        output = tmp_path / "Simulation.scala"
        code = generate_simulation(simple_definition, output_path=output)
        assert output.exists()
        assert output.read_text() == code

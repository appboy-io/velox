# Velox Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a YAML-driven Python CLI that generates Gatling load test simulations, runs them, reports results (JSON + HTML + Markdown), and optionally pushes results to a VCS branch.

**Architecture:** Python CLI parses YAML test definitions via Pydantic, renders Gatling simulation code through Jinja2 templates, launches Gatling as a subprocess, parses results from simulation.log, evaluates thresholds, generates reports, and optionally pushes to a git results branch.

**Tech Stack:** Python 3.10+, Pydantic v2, Jinja2, Typer, PyYAML, jsonpath-ng, Gatling (external)

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/velox/__init__.py`
- Create: `src/velox/cli.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `.gitignore`
- Create: `README.md`

**Step 1: Create pyproject.toml with dependencies**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "velox"
version = "0.1.0"
description = "YAML-driven Gatling performance testing CLI"
requires-python = ">=3.10"
dependencies = [
    "typer>=0.9.0",
    "pydantic>=2.0.0",
    "pyyaml>=6.0",
    "jinja2>=3.1.0",
    "jsonpath-ng>=1.5.0",
    "rich>=13.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-tmp-files>=0.0.2",
]

[project.scripts]
velox = "velox.cli:app"

[tool.hatch.build.targets.wheel]
packages = ["src/velox"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

**Step 2: Create directory structure**

```bash
mkdir -p src/velox tests
```

**Step 3: Create `src/velox/__init__.py`**

```python
"""Velox — YAML-driven Gatling performance testing CLI."""

__version__ = "0.1.0"
```

**Step 4: Create minimal `src/velox/cli.py`**

```python
import typer

app = typer.Typer(
    name="velox",
    help="YAML-driven Gatling performance testing CLI.",
)


@app.command()
def run(test_file: str) -> None:
    """Run a performance test from a YAML definition."""
    typer.echo(f"Running test: {test_file}")


@app.command()
def validate(test_file: str) -> None:
    """Validate a YAML test definition without running."""
    typer.echo(f"Validating: {test_file}")


@app.command()
def init() -> None:
    """Scaffold a sample YAML test file."""
    typer.echo("Initializing sample test file...")


@app.command()
def report() -> None:
    """View results from the last test run."""
    typer.echo("Showing last report...")
```

**Step 5: Create `tests/__init__.py` and `tests/conftest.py`**

```python
# tests/__init__.py
```

```python
# tests/conftest.py
import pytest
from typer.testing import CliRunner

from velox.cli import app


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def invoke(cli_runner):
    def _invoke(*args):
        return cli_runner.invoke(app, list(args))
    return _invoke
```

**Step 6: Create `.gitignore`**

```
__pycache__/
*.pyc
*.egg-info/
dist/
build/
.venv/
venv/
.pytest_cache/
.coverage
htmlcov/
results/
*.generated.scala
```

**Step 7: Create `README.md`**

```markdown
# Velox

YAML-driven Gatling performance testing CLI. Latin for "swift."

## Quick Start

```bash
pip install -e ".[dev]"
velox init
velox run test.yaml
```
```

**Step 8: Install dependencies and verify**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
velox --help
```

**Step 9: Commit**

```bash
git add -A
git commit -m "feat: scaffold velox project with CLI skeleton and dev tooling"
```

---

### Task 2: Pydantic Models for YAML Schema

**Files:**
- Create: `src/velox/models.py`
- Create: `tests/test_models.py`

**Step 1: Write the failing tests**

```python
# tests/test_models.py
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
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_models.py -v
```

Expected: FAIL — `velox.models` does not exist

**Step 3: Implement the models**

```python
# src/velox/models.py
"""Pydantic models for Velox YAML test definitions."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


def _parse_duration_ms(value: str) -> int:
    """Parse a duration string like '200ms' or '2s' into milliseconds."""
    match = re.match(r"^(\d+(?:\.\d+)?)(ms|s|m)$", value.strip())
    if not match:
        raise ValueError(f"Invalid duration format: {value!r}. Use '200ms', '2s', or '1m'.")
    amount = float(match.group(1))
    unit = match.group(2)
    if unit == "ms":
        return int(amount)
    if unit == "s":
        return int(amount * 1000)
    if unit == "m":
        return int(amount * 60_000)
    raise ValueError(f"Unknown unit: {unit}")


def _parse_percentage(value: str) -> float:
    """Parse a percentage string like '1%' into a float."""
    match = re.match(r"^(\d+(?:\.\d+)?)%$", value.strip())
    if not match:
        raise ValueError(f"Invalid percentage format: {value!r}. Use '1%' or '0.5%'.")
    return float(match.group(1))


class Threshold(BaseModel):
    """Threshold definition for pass/fail evaluation."""

    p50: str | None = None
    p75: str | None = None
    p95: str | None = None
    p99: str | None = None
    errorRate: str | None = None

    @property
    def p50_ms(self) -> int | None:
        return _parse_duration_ms(self.p50) if self.p50 else None

    @property
    def p75_ms(self) -> int | None:
        return _parse_duration_ms(self.p75) if self.p75 else None

    @property
    def p95_ms(self) -> int | None:
        return _parse_duration_ms(self.p95) if self.p95 else None

    @property
    def p99_ms(self) -> int | None:
        return _parse_duration_ms(self.p99) if self.p99 else None

    @property
    def error_rate_pct(self) -> float | None:
        return _parse_percentage(self.errorRate) if self.errorRate else None


class FlowStep(BaseModel):
    """A single HTTP request step in a test flow."""

    name: str
    method: str
    path: str
    headers: dict[str, str] = Field(default_factory=dict)
    body: dict[str, Any] | None = None
    extract: dict[str, str] = Field(default_factory=dict)
    threshold: Threshold | None = None

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        v = v.upper()
        if v not in ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"):
            raise ValueError(f"Unsupported HTTP method: {v}")
        return v


class TestConfig(BaseModel):
    """Load test configuration."""

    users: int = 1
    rampUp: str = "0s"
    duration: str = "30s"

    @property
    def ramp_up_seconds(self) -> int:
        return _parse_duration_ms(self.rampUp) // 1000

    @property
    def duration_seconds(self) -> int:
        return _parse_duration_ms(self.duration) // 1000


class ResultsConfig(BaseModel):
    """VCS results push configuration."""

    push: bool = False
    branchSuffix: str = "-perf-results"
    remote: str = "origin"


class TestDefinition(BaseModel):
    """Top-level YAML test definition."""

    name: str
    baseUrl: str
    config: TestConfig = Field(default_factory=TestConfig)
    variables: dict[str, str] = Field(default_factory=dict)
    flow: list[FlowStep]
    threshold: Threshold | None = None
    results: ResultsConfig = Field(default_factory=ResultsConfig)

    @model_validator(mode="after")
    def validate_flow_not_empty(self) -> "TestDefinition":
        if len(self.flow) == 0:
            raise ValueError("flow must contain at least one step")
        return self
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_models.py -v
```

Expected: All PASS

**Step 5: Commit**

```bash
git add src/velox/models.py tests/test_models.py
git commit -m "feat: add Pydantic models for YAML test definition schema"
```

---

### Task 3: YAML Parser and Validator

**Files:**
- Create: `src/velox/parser.py`
- Create: `tests/test_parser.py`
- Create: `tests/fixtures/valid_test.yaml`
- Create: `tests/fixtures/minimal_test.yaml`
- Create: `tests/fixtures/invalid_no_flow.yaml`

**Step 1: Create test fixture YAML files**

```yaml
# tests/fixtures/valid_test.yaml
name: "Checkout Flow"
baseUrl: "https://api.example.com"

config:
  users: 100
  rampUp: "30s"
  duration: "5m"

variables:
  apiKey: "test-key-123"

flow:
  - name: "Login"
    method: POST
    path: "/auth/login"
    headers:
      Content-Type: "application/json"
    body:
      username: "testuser"
      password: "testpass"
    extract:
      token: "$.accessToken"
    threshold:
      p95: "200ms"

  - name: "Get Products"
    method: GET
    path: "/products"
    headers:
      Authorization: "Bearer ${token}"
    threshold:
      p95: "300ms"

threshold:
  p95: "2s"
  errorRate: "1%"

results:
  push: true
  branchSuffix: "-perf-results"
  remote: "origin"
```

```yaml
# tests/fixtures/minimal_test.yaml
name: "Simple GET"
baseUrl: "https://example.com"
flow:
  - name: "Homepage"
    method: GET
    path: "/"
```

```yaml
# tests/fixtures/invalid_no_flow.yaml
name: "Bad Test"
baseUrl: "https://example.com"
flow: []
```

**Step 2: Write the failing tests**

```python
# tests/test_parser.py
import pytest
from pathlib import Path

from velox.parser import parse_test_file, parse_yaml_string, ValidationError

FIXTURES = Path(__file__).parent / "fixtures"


class TestParseTestFile:
    def test_parse_valid_file(self):
        defn = parse_test_file(FIXTURES / "valid_test.yaml")
        assert defn.name == "Checkout Flow"
        assert defn.config.users == 100
        assert len(defn.flow) == 2
        assert defn.flow[0].extract["token"] == "$.accessToken"
        assert defn.threshold.p95_ms == 2000

    def test_parse_minimal_file(self):
        defn = parse_test_file(FIXTURES / "minimal_test.yaml")
        assert defn.name == "Simple GET"
        assert defn.config.users == 1
        assert len(defn.flow) == 1

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            parse_test_file(Path("/nonexistent/test.yaml"))

    def test_invalid_empty_flow(self):
        with pytest.raises(ValidationError):
            parse_test_file(FIXTURES / "invalid_no_flow.yaml")


class TestParseYamlString:
    def test_parse_string(self):
        yaml_str = """
name: "Inline Test"
baseUrl: "https://example.com"
flow:
  - name: "Step 1"
    method: GET
    path: "/"
"""
        defn = parse_yaml_string(yaml_str)
        assert defn.name == "Inline Test"

    def test_invalid_yaml_syntax(self):
        with pytest.raises(ValidationError):
            parse_yaml_string("not: valid: yaml: [[[")

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            parse_yaml_string("name: test\n")
```

**Step 3: Run tests to verify they fail**

```bash
pytest tests/test_parser.py -v
```

Expected: FAIL — `velox.parser` does not exist

**Step 4: Implement the parser**

```python
# src/velox/parser.py
"""YAML parser and validator for Velox test definitions."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError as PydanticValidationError

from velox.models import TestDefinition


class ValidationError(Exception):
    """Raised when a YAML test definition is invalid."""

    def __init__(self, message: str, errors: list | None = None):
        super().__init__(message)
        self.errors = errors or []


def parse_test_file(path: Path) -> TestDefinition:
    """Parse and validate a YAML test definition file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Test file not found: {path}")

    text = path.read_text(encoding="utf-8")
    return parse_yaml_string(text)


def parse_yaml_string(yaml_str: str) -> TestDefinition:
    """Parse and validate a YAML string into a TestDefinition."""
    try:
        data = yaml.safe_load(yaml_str)
    except yaml.YAMLError as e:
        raise ValidationError(f"Invalid YAML syntax: {e}") from e

    if not isinstance(data, dict):
        raise ValidationError("YAML must be a mapping at the top level")

    try:
        return TestDefinition(**data)
    except PydanticValidationError as e:
        raise ValidationError(
            f"Invalid test definition: {e.error_count()} error(s)",
            errors=e.errors(),
        ) from e
```

**Step 5: Run tests to verify they pass**

```bash
pytest tests/test_parser.py -v
```

Expected: All PASS

**Step 6: Commit**

```bash
git add src/velox/parser.py tests/test_parser.py tests/fixtures/
git commit -m "feat: add YAML parser with Pydantic validation"
```

---

### Task 4: Variable Interpolation

**Files:**
- Create: `src/velox/interpolation.py`
- Create: `tests/test_interpolation.py`

**Step 1: Write the failing tests**

```python
# tests/test_interpolation.py
import os
import pytest

from velox.interpolation import interpolate_string, interpolate_variables, resolve_env_vars


class TestResolveEnvVars:
    def test_resolve_env_var(self, monkeypatch):
        monkeypatch.setenv("API_KEY", "secret123")
        variables = {"apiKey": "${ENV.API_KEY}"}
        resolved = resolve_env_vars(variables)
        assert resolved["apiKey"] == "secret123"

    def test_non_env_var_unchanged(self):
        variables = {"token": "static-value"}
        resolved = resolve_env_vars(variables)
        assert resolved["token"] == "static-value"

    def test_missing_env_var_raises(self):
        variables = {"apiKey": "${ENV.NONEXISTENT_VAR_XYZ}"}
        with pytest.raises(ValueError, match="NONEXISTENT_VAR_XYZ"):
            resolve_env_vars(variables)


class TestInterpolateString:
    def test_simple_substitution(self):
        result = interpolate_string(
            "Bearer ${token}",
            {"token": "abc123"},
        )
        assert result == "Bearer abc123"

    def test_multiple_substitutions(self):
        result = interpolate_string(
            "/cart/${cartId}/checkout?user=${userId}",
            {"cartId": "42", "userId": "7"},
        )
        assert result == "/cart/42/checkout?user=7"

    def test_no_substitution_needed(self):
        result = interpolate_string("/products", {})
        assert result == "/products"

    def test_undefined_variable_raises(self):
        with pytest.raises(ValueError, match="unknown"):
            interpolate_string("${unknown}", {})


class TestInterpolateVariables:
    def test_interpolate_step_headers(self):
        context = {"token": "abc123"}
        headers = {"Authorization": "Bearer ${token}"}
        result = interpolate_variables(headers, context)
        assert result["Authorization"] == "Bearer abc123"

    def test_interpolate_step_path(self):
        context = {"cartId": "42"}
        result = interpolate_string("/cart/${cartId}/checkout", context)
        assert result == "/cart/42/checkout"
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_interpolation.py -v
```

Expected: FAIL — `velox.interpolation` does not exist

**Step 3: Implement interpolation**

```python
# src/velox/interpolation.py
"""Variable interpolation for Velox test definitions."""

from __future__ import annotations

import os
import re


ENV_PATTERN = re.compile(r"\$\{ENV\.(\w+)\}")
VAR_PATTERN = re.compile(r"\$\{(\w+)\}")


def resolve_env_vars(variables: dict[str, str]) -> dict[str, str]:
    """Resolve ${ENV.VAR_NAME} references in variable values."""
    resolved = {}
    for key, value in variables.items():
        match = ENV_PATTERN.fullmatch(value)
        if match:
            env_name = match.group(1)
            env_value = os.environ.get(env_name)
            if env_value is None:
                raise ValueError(
                    f"Environment variable {env_name} is not set "
                    f"(referenced by variable '{key}')"
                )
            resolved[key] = env_value
        else:
            resolved[key] = value
    return resolved


def interpolate_string(template: str, context: dict[str, str]) -> str:
    """Replace ${varName} placeholders in a string with context values."""

    def replacer(match: re.Match) -> str:
        var_name = match.group(1)
        if var_name not in context:
            raise ValueError(
                f"Undefined variable: {var_name}. "
                f"Available: {', '.join(sorted(context.keys())) or '(none)'}"
            )
        return context[var_name]

    return VAR_PATTERN.sub(replacer, template)


def interpolate_variables(
    mapping: dict[str, str], context: dict[str, str]
) -> dict[str, str]:
    """Interpolate all values in a string dict."""
    return {key: interpolate_string(value, context) for key, value in mapping.items()}
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_interpolation.py -v
```

Expected: All PASS

**Step 5: Commit**

```bash
git add src/velox/interpolation.py tests/test_interpolation.py
git commit -m "feat: add variable interpolation with env var support"
```

---

### Task 5: Jinja2 Template Engine — Gatling Simulation Generation

**Files:**
- Create: `src/velox/templates/simulation.scala.j2`
- Create: `src/velox/generator.py`
- Create: `tests/test_generator.py`

**Step 1: Write the failing tests**

```python
# tests/test_generator.py
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

    def test_includes_group_for_flow(self, full_definition):
        code = generate_simulation(full_definition)
        assert "group(" in code

    def test_writes_to_file(self, simple_definition, tmp_path):
        output = tmp_path / "Simulation.scala"
        code = generate_simulation(simple_definition, output_path=output)
        assert output.exists()
        assert output.read_text() == code
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_generator.py -v
```

Expected: FAIL — `velox.generator` does not exist

**Step 3: Create the Jinja2 template**

```scala
{# src/velox/templates/simulation.scala.j2 #}
package velox.generated

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import scala.concurrent.duration._

class {{ class_name }}Simulation extends Simulation {

  val httpProtocol = http
    .baseUrl("{{ base_url }}")

  val scn = scenario("{{ scenario_name }}")
    .group("{{ scenario_name }}") {
      {% for step in steps %}
      exec(
        http("{{ step.name }}")
          .{{ step.method | lower }}("{{ step.path }}")
          {% if step.headers %}
          {% for key, value in step.headers.items() %}
          .header("{{ key }}", "{{ value }}")
          {% endfor %}
          {% endif %}
          {% if step.body %}
          .body(StringBody("""{{ step.body_json }}""")).asJson
          {% endif %}
          {% if step.extractions %}
          {% for var_name, json_path in step.extractions.items() %}
          .check(jsonPath("{{ json_path }}").saveAs("{{ var_name }}"))
          {% endfor %}
          {% endif %}
      )
      {% if not loop.last %}
      .pause(1)
      {% endif %}
      {% endfor %}
    }

  setUp(
    scn.inject(rampUsers({{ users }}).during({{ ramp_up_seconds }}))
  ).protocols(httpProtocol)
    .maxDuration({{ duration_seconds }}.seconds)
}
```

**Step 4: Implement the generator**

```python
# src/velox/generator.py
"""Gatling simulation code generator using Jinja2 templates."""

from __future__ import annotations

import json
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from velox.models import FlowStep, TestDefinition

TEMPLATES_DIR = Path(__file__).parent / "templates"


def _to_class_name(name: str) -> str:
    """Convert a test name to a valid Scala class name."""
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", name)
    return cleaned.title().replace(" ", "")


def _prepare_step(step: FlowStep) -> dict:
    """Prepare a flow step for template rendering."""
    data = {
        "name": step.name,
        "method": step.method,
        "path": step.path,
        "headers": step.headers,
        "body": step.body is not None,
        "body_json": json.dumps(step.body) if step.body else "",
        "extractions": step.extract,
    }
    return data


def generate_simulation(
    definition: TestDefinition,
    output_path: Path | None = None,
) -> str:
    """Generate a Gatling simulation Scala file from a test definition."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("simulation.scala.j2")

    context = {
        "class_name": _to_class_name(definition.name),
        "base_url": definition.baseUrl,
        "scenario_name": definition.name,
        "steps": [_prepare_step(step) for step in definition.flow],
        "users": definition.config.users,
        "ramp_up_seconds": definition.config.ramp_up_seconds,
        "duration_seconds": definition.config.duration_seconds,
    }

    code = template.render(**context)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(code, encoding="utf-8")

    return code
```

**Step 5: Run tests to verify they pass**

```bash
pytest tests/test_generator.py -v
```

Expected: All PASS

**Step 6: Commit**

```bash
git add src/velox/generator.py src/velox/templates/ tests/test_generator.py
git commit -m "feat: add Jinja2-based Gatling simulation code generator"
```

---

### Task 6: Gatling Subprocess Launcher

**Files:**
- Create: `src/velox/runner.py`
- Create: `tests/test_runner.py`

**Step 1: Write the failing tests**

```python
# tests/test_runner.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from velox.runner import GatlingRunner, GatlingNotFoundError, GatlingRunError


class TestGatlingRunner:
    def test_find_gatling_from_env(self, monkeypatch, tmp_path):
        gatling_bin = tmp_path / "gatling.sh"
        gatling_bin.write_text("#!/bin/sh\necho gatling")
        gatling_bin.chmod(0o755)
        monkeypatch.setenv("GATLING_HOME", str(tmp_path))
        runner = GatlingRunner()
        assert runner.gatling_home == tmp_path

    def test_gatling_not_found_raises(self, monkeypatch):
        monkeypatch.delenv("GATLING_HOME", raising=False)
        with pytest.raises(GatlingNotFoundError):
            GatlingRunner()

    @patch("velox.runner.subprocess.run")
    def test_run_simulation(self, mock_run, monkeypatch, tmp_path):
        gatling_bin = tmp_path / "bin" / "gatling.sh"
        gatling_bin.parent.mkdir(parents=True)
        gatling_bin.write_text("#!/bin/sh\necho gatling")
        gatling_bin.chmod(0o755)
        monkeypatch.setenv("GATLING_HOME", str(tmp_path))

        mock_run.return_value = MagicMock(returncode=0, stdout="done", stderr="")

        runner = GatlingRunner()
        results_dir = tmp_path / "results"
        sim_file = tmp_path / "Simulation.scala"
        sim_file.write_text("class Test {}")

        result = runner.run(
            simulation_class="TestSimulation",
            simulations_dir=tmp_path,
            results_dir=results_dir,
        )
        assert result.returncode == 0
        mock_run.assert_called_once()

    @patch("velox.runner.subprocess.run")
    def test_run_failure_raises(self, mock_run, monkeypatch, tmp_path):
        gatling_bin = tmp_path / "bin" / "gatling.sh"
        gatling_bin.parent.mkdir(parents=True)
        gatling_bin.write_text("#!/bin/sh\necho gatling")
        gatling_bin.chmod(0o755)
        monkeypatch.setenv("GATLING_HOME", str(tmp_path))

        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")

        runner = GatlingRunner()
        with pytest.raises(GatlingRunError):
            runner.run(
                simulation_class="TestSimulation",
                simulations_dir=tmp_path,
                results_dir=tmp_path / "results",
            )
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_runner.py -v
```

Expected: FAIL — `velox.runner` does not exist

**Step 3: Implement the runner**

```python
# src/velox/runner.py
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

    def __init__(self, message: str, returncode: int, stderr: str):
        super().__init__(message)
        self.returncode = returncode
        self.stderr = stderr


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
        simulations_dir: Path,
        results_dir: Path,
    ) -> GatlingResult:
        """Run a Gatling simulation."""
        results_dir.mkdir(parents=True, exist_ok=True)

        gatling_bin = self.gatling_home / "bin" / "gatling.sh"
        if not gatling_bin.exists():
            gatling_bin = self.gatling_home / "bin" / "gatling.bat"

        cmd = [
            str(gatling_bin),
            "--simulation", simulation_class,
            "--simulations-folder", str(simulations_dir),
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
            )

        return GatlingResult(
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            results_dir=results_dir,
        )
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_runner.py -v
```

Expected: All PASS

**Step 5: Commit**

```bash
git add src/velox/runner.py tests/test_runner.py
git commit -m "feat: add Gatling subprocess launcher"
```

---

### Task 7: Simulation Log Parser

**Files:**
- Create: `src/velox/log_parser.py`
- Create: `tests/test_log_parser.py`
- Create: `tests/fixtures/simulation.log`

**Step 1: Create a sample simulation.log fixture**

Gatling's simulation.log uses a tab-separated format. Key line types:

```
# tests/fixtures/simulation.log
RUN	velox.generated.CheckoutFlowSimulation	checkoutflow	1709312400000	 	3.9.5
USER	Checkout Flow	START	1709312400000	0
GROUP	Checkout Flow	1	Checkout Flow	1709312400000	1709312402500	OK
REQUEST	Checkout Flow	1	Login	1709312400000	1709312400180	OK
REQUEST	Checkout Flow	1	Get Products	1709312400200	1709312400450	OK
REQUEST	Checkout Flow	1	Add to Cart	1709312400460	1709312400650	OK
REQUEST	Checkout Flow	1	Checkout	1709312400660	1709312400970	OK
USER	Checkout Flow	END	1709312402500	0
```

**Step 2: Write the failing tests**

```python
# tests/test_log_parser.py
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
```

**Step 3: Run tests to verify they fail**

```bash
pytest tests/test_log_parser.py -v
```

Expected: FAIL — `velox.log_parser` does not exist

**Step 4: Implement the log parser**

```python
# src/velox/log_parser.py
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
```

**Step 5: Run tests to verify they pass**

```bash
pytest tests/test_log_parser.py -v
```

Expected: All PASS

**Step 6: Commit**

```bash
git add src/velox/log_parser.py tests/test_log_parser.py tests/fixtures/simulation.log
git commit -m "feat: add Gatling simulation.log parser"
```

---

### Task 8: Threshold Evaluator

**Files:**
- Create: `src/velox/evaluator.py`
- Create: `tests/test_evaluator.py`

**Step 1: Write the failing tests**

```python
# tests/test_evaluator.py
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
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_evaluator.py -v
```

Expected: FAIL — `velox.evaluator` does not exist

**Step 3: Implement the evaluator**

```python
# src/velox/evaluator.py
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
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_evaluator.py -v
```

Expected: All PASS

**Step 5: Commit**

```bash
git add src/velox/evaluator.py tests/test_evaluator.py
git commit -m "feat: add threshold evaluator for pass/fail metrics"
```

---

### Task 9: Report Generator (JSON + Markdown)

**Files:**
- Create: `src/velox/reporter.py`
- Create: `tests/test_reporter.py`

**Step 1: Write the failing tests**

```python
# tests/test_reporter.py
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
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_reporter.py -v
```

Expected: FAIL — `velox.reporter` does not exist

**Step 3: Implement the reporter**

```python
# src/velox/reporter.py
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
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_reporter.py -v
```

Expected: All PASS

**Step 5: Commit**

```bash
git add src/velox/reporter.py tests/test_reporter.py
git commit -m "feat: add JSON and Markdown report generators"
```

---

### Task 10: VCS Results Pusher

**Files:**
- Create: `src/velox/vcs.py`
- Create: `tests/test_vcs.py`

**Step 1: Write the failing tests**

```python
# tests/test_vcs.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from velox.vcs import push_results, get_current_branch


class TestGetCurrentBranch:
    @patch("velox.vcs.subprocess.run")
    def test_returns_branch_name(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="feature/checkout\n"
        )
        assert get_current_branch() == "feature/checkout"

    @patch("velox.vcs.subprocess.run")
    def test_strips_whitespace(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="  main \n"
        )
        assert get_current_branch() == "main"


class TestPushResults:
    @patch("velox.vcs.subprocess.run")
    def test_push_creates_branch_and_commits(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        results_dir = tmp_path / "results"
        results_dir.mkdir()
        (results_dir / "report.json").write_text("{}")
        (results_dir / "report.md").write_text("# Report")

        push_results(
            results_dir=results_dir,
            branch_suffix="-perf-results",
            remote="origin",
            current_branch="feature/checkout",
        )

        # Should have run git commands
        assert mock_run.call_count >= 3  # checkout, add, commit, push

    @patch("velox.vcs.subprocess.run")
    def test_branch_name_format(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        results_dir = tmp_path / "results"
        results_dir.mkdir()
        (results_dir / "report.json").write_text("{}")

        push_results(
            results_dir=results_dir,
            branch_suffix="-perf-results",
            remote="origin",
            current_branch="feature/login",
        )

        # Check the branch name in the checkout command
        checkout_calls = [
            c for c in mock_run.call_args_list
            if "checkout" in str(c)
        ]
        assert any("feature/login-perf-results" in str(c) for c in checkout_calls)
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_vcs.py -v
```

Expected: FAIL — `velox.vcs` does not exist

**Step 3: Implement the VCS pusher**

```python
# src/velox/vcs.py
"""VCS results push for Velox."""

from __future__ import annotations

import subprocess
from pathlib import Path


def get_current_branch() -> str:
    """Get the current git branch name."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def push_results(
    results_dir: Path,
    branch_suffix: str,
    remote: str,
    current_branch: str,
) -> None:
    """Push results directory to a VCS branch."""
    target_branch = f"{current_branch}{branch_suffix}"

    def _run(cmd: list[str]) -> None:
        subprocess.run(cmd, capture_output=True, text=True, check=True)

    # Stash any current changes
    _run(["git", "stash", "--include-untracked"])

    try:
        # Try to checkout existing results branch, or create new one
        try:
            _run(["git", "checkout", target_branch])
        except subprocess.CalledProcessError:
            _run(["git", "checkout", "--orphan", target_branch])
            _run(["git", "rm", "-rf", "."])

        # Copy results into the branch
        _run(["git", "add", str(results_dir)])
        _run(["git", "commit", "-m", f"perf: add results from {current_branch}"])
        _run(["git", "push", remote, target_branch])

    finally:
        # Return to original branch
        _run(["git", "checkout", current_branch])
        try:
            _run(["git", "stash", "pop"])
        except subprocess.CalledProcessError:
            pass  # no stash to pop
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_vcs.py -v
```

Expected: All PASS

**Step 5: Commit**

```bash
git add src/velox/vcs.py tests/test_vcs.py
git commit -m "feat: add VCS results push to branch with suffix"
```

---

### Task 11: CLI Commands — Wire Everything Together

**Files:**
- Modify: `src/velox/cli.py`
- Create: `src/velox/orchestrator.py`
- Create: `tests/test_cli.py`
- Create: `src/velox/templates/sample_test.yaml`

**Step 1: Write the failing tests**

```python
# tests/test_cli.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from velox.cli import app

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def runner():
    return CliRunner()


class TestValidateCommand:
    def test_valid_file(self, runner):
        result = runner.invoke(app, ["validate", str(FIXTURES / "valid_test.yaml")])
        assert result.exit_code == 0
        assert "valid" in result.stdout.lower() or "✓" in result.stdout

    def test_invalid_file(self, runner):
        result = runner.invoke(app, ["validate", str(FIXTURES / "invalid_no_flow.yaml")])
        assert result.exit_code != 0

    def test_file_not_found(self, runner):
        result = runner.invoke(app, ["validate", "/nonexistent/test.yaml"])
        assert result.exit_code != 0


class TestInitCommand:
    def test_creates_sample_file(self, runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0
        sample = tmp_path / "velox-sample.yaml"
        assert sample.exists()


class TestRunCommand:
    @patch("velox.cli.orchestrate_run")
    def test_run_calls_orchestrator(self, mock_orch, runner):
        mock_orch.return_value = True  # all thresholds passed
        result = runner.invoke(app, ["run", str(FIXTURES / "valid_test.yaml")])
        assert result.exit_code == 0
        mock_orch.assert_called_once()

    @patch("velox.cli.orchestrate_run")
    def test_run_nonzero_on_threshold_failure(self, mock_orch, runner):
        mock_orch.return_value = False  # thresholds failed
        result = runner.invoke(app, ["run", str(FIXTURES / "valid_test.yaml")])
        assert result.exit_code != 0
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_cli.py -v
```

Expected: FAIL

**Step 3: Create sample test YAML template**

```yaml
# src/velox/templates/sample_test.yaml
name: "Sample API Test"
baseUrl: "https://jsonplaceholder.typicode.com"

config:
  users: 5
  rampUp: "10s"
  duration: "30s"

flow:
  - name: "List Posts"
    method: GET
    path: "/posts"
    threshold:
      p95: "500ms"

  - name: "Get Single Post"
    method: GET
    path: "/posts/1"
    extract:
      userId: "$.userId"
    threshold:
      p95: "300ms"

  - name: "Get User"
    method: GET
    path: "/users/${userId}"

threshold:
  p95: "1s"
  errorRate: "5%"

results:
  push: false
```

**Step 4: Implement the orchestrator**

```python
# src/velox/orchestrator.py
"""Orchestrates the full Velox test run pipeline."""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console

from velox.evaluator import evaluate_thresholds, ThresholdResult
from velox.generator import generate_simulation
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

    sim_file = sim_dir / "Simulation.scala"
    generate_simulation(definition, output_path=sim_file)

    # 4. Run Gatling
    console.print("  ├─ Launching Gatling...")
    runner = GatlingRunner()
    gatling_results_dir = work_dir / "gatling-output"
    runner.run(
        simulation_class="velox.generated." + sim_file.stem + "Simulation",
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
```

**Step 5: Update the CLI**

```python
# src/velox/cli.py
"""Velox CLI — YAML-driven Gatling performance testing."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import typer
from rich.console import Console

from velox.parser import parse_test_file, ValidationError

app = typer.Typer(
    name="velox",
    help="Velox — YAML-driven Gatling performance testing CLI.",
)
console = Console()


def _get_sample_yaml_path() -> Path:
    return Path(__file__).parent / "templates" / "sample_test.yaml"


@app.command()
def run(
    test_file: str,
    base_url: str = typer.Option(None, "--base-url", help="Override base URL"),
    users: int = typer.Option(None, "--users", help="Override user count"),
) -> None:
    """Run a performance test from a YAML definition."""
    from velox.orchestrator import orchestrate_run

    path = Path(test_file)
    passed = orchestrate_run(
        test_file=path,
        base_url_override=base_url,
        users_override=users,
    )
    if not passed:
        raise typer.Exit(code=1)


@app.command()
def validate(test_file: str) -> None:
    """Validate a YAML test definition without running."""
    path = Path(test_file)
    try:
        definition = parse_test_file(path)
        console.print(f"[green]✓[/green] {path.name} is valid")
        console.print(f"  Name: {definition.name}")
        console.print(f"  Steps: {len(definition.flow)}")
        console.print(f"  Users: {definition.config.users}")
    except FileNotFoundError:
        console.print(f"[red]✗[/red] File not found: {path}")
        raise typer.Exit(code=1)
    except ValidationError as e:
        console.print(f"[red]✗[/red] Validation failed: {e}")
        raise typer.Exit(code=1)


@app.command()
def init() -> None:
    """Scaffold a sample YAML test file."""
    dest = Path("velox-sample.yaml")
    if dest.exists():
        console.print(f"[yellow]![/yellow] {dest} already exists, skipping")
        return
    source = _get_sample_yaml_path()
    shutil.copy(source, dest)
    console.print(f"[green]✓[/green] Created {dest}")
    console.print("  Edit it with your API details, then run: velox run velox-sample.yaml")


@app.command()
def report() -> None:
    """View results from the last test run."""
    results_dir = Path("results")
    if not results_dir.exists():
        console.print("[yellow]No results found. Run a test first:[/yellow] velox run test.yaml")
        raise typer.Exit(code=1)

    # Find most recent results directory
    result_dirs = sorted(results_dir.iterdir(), reverse=True)
    if not result_dirs:
        console.print("[yellow]No results found.[/yellow]")
        raise typer.Exit(code=1)

    latest = result_dirs[0] / "reports" / "report.md"
    if latest.exists():
        console.print(latest.read_text())
    else:
        console.print(f"[yellow]No report found in {result_dirs[0]}[/yellow]")
```

**Step 6: Run tests to verify they pass**

```bash
pytest tests/test_cli.py -v
```

Expected: All PASS

**Step 7: Run full test suite**

```bash
pytest -v
```

Expected: All tests PASS

**Step 8: Commit**

```bash
git add src/velox/cli.py src/velox/orchestrator.py src/velox/templates/sample_test.yaml tests/test_cli.py
git commit -m "feat: wire CLI commands with full orchestration pipeline"
```

---

### Task 12: End-to-End Integration Test

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write integration test (mocked Gatling)**

```python
# tests/test_integration.py
"""End-to-end integration test with mocked Gatling execution."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from velox.cli import app

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_gatling(tmp_path):
    """Set up a mock Gatling environment."""
    gatling_home = tmp_path / "gatling"
    bin_dir = gatling_home / "bin"
    bin_dir.mkdir(parents=True)
    gatling_bin = bin_dir / "gatling.sh"
    gatling_bin.write_text("#!/bin/sh\necho mock")
    gatling_bin.chmod(0o755)
    return gatling_home


class TestEndToEnd:
    @patch("velox.orchestrator.GatlingRunner")
    def test_validate_then_run(self, mock_runner_cls, runner, mock_gatling, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        # Step 1: Validate
        result = runner.invoke(app, ["validate", str(FIXTURES / "valid_test.yaml")])
        assert result.exit_code == 0

        # Step 2: Mock the Gatling runner to produce a simulation.log
        mock_runner = MagicMock()
        mock_runner_cls.return_value = mock_runner

        def fake_run(simulation_class, simulations_dir, results_dir):
            results_dir.mkdir(parents=True, exist_ok=True)
            sim_log = results_dir / "test-run" / "simulation.log"
            sim_log.parent.mkdir(parents=True, exist_ok=True)
            sim_log.write_text(
                "RUN\tvelox\ttest\t1709312400000\t \t3.9.5\n"
                "GROUP\tCheckout Flow\t1\tCheckout Flow\t1709312400000\t1709312401500\tOK\n"
                "REQUEST\tCheckout Flow\t1\tLogin\t1709312400000\t1709312400150\tOK\n"
                "REQUEST\tCheckout Flow\t1\tGet Products\t1709312400200\t1709312400420\tOK\n"
            )
            return MagicMock(returncode=0)

        mock_runner.run.side_effect = fake_run

        # Step 3: Run
        result = runner.invoke(app, ["run", str(FIXTURES / "valid_test.yaml")])
        assert result.exit_code == 0

        # Step 4: Verify reports were generated
        results_dirs = list(Path("results").iterdir())
        assert len(results_dirs) == 1
        report_dir = results_dirs[0] / "reports"
        assert (report_dir / "report.json").exists()
        assert (report_dir / "report.md").exists()

    def test_init_then_validate(self, runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        # Init
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0
        assert (tmp_path / "velox-sample.yaml").exists()

        # Validate the generated sample
        result = runner.invoke(app, ["validate", "velox-sample.yaml"])
        assert result.exit_code == 0
```

**Step 2: Run the integration test**

```bash
pytest tests/test_integration.py -v
```

Expected: All PASS

**Step 3: Run full suite one final time**

```bash
pytest -v --tb=short
```

Expected: All tests PASS

**Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add end-to-end integration tests"
```

---

## Execution Summary

| Task | Component | Files |
|------|-----------|-------|
| 1 | Project scaffolding | pyproject.toml, cli.py, conftest.py, .gitignore, README.md |
| 2 | Pydantic models | models.py, test_models.py |
| 3 | YAML parser | parser.py, test_parser.py, fixtures/ |
| 4 | Variable interpolation | interpolation.py, test_interpolation.py |
| 5 | Jinja2 template engine | generator.py, simulation.scala.j2, test_generator.py |
| 6 | Gatling subprocess launcher | runner.py, test_runner.py |
| 7 | Simulation log parser | log_parser.py, test_log_parser.py |
| 8 | Threshold evaluator | evaluator.py, test_evaluator.py |
| 9 | Report generator | reporter.py, test_reporter.py |
| 10 | VCS results pusher | vcs.py, test_vcs.py |
| 11 | CLI wiring + orchestrator | cli.py, orchestrator.py, sample_test.yaml, test_cli.py |
| 12 | Integration tests | test_integration.py |

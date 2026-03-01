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

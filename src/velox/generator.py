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

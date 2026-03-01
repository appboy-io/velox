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

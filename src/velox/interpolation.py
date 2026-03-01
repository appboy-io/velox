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

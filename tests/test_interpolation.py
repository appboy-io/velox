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

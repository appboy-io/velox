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

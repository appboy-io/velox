import pytest
from pathlib import Path
from typer.testing import CliRunner

from velox.cli import app


@pytest.fixture
def runner():
    return CliRunner()


class TestInitCi:
    def test_github(self, runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["init", "--ci", "github"])
        assert result.exit_code == 0
        generated = tmp_path / ".github" / "workflows" / "velox.yml"
        assert generated.exists()
        content = generated.read_text()
        assert "ghcr.io/appboy-io/velox" in content
        assert "TARGET_URL" in content

    def test_circle(self, runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["init", "--ci", "circle"])
        assert result.exit_code == 0
        generated = tmp_path / ".circleci" / "config.yml"
        assert generated.exists()
        content = generated.read_text()
        assert "ghcr.io/appboy-io/velox" in content

    def test_bitbucket(self, runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["init", "--ci", "bitbucket"])
        assert result.exit_code == 0
        generated = tmp_path / "bitbucket-pipelines.yml"
        assert generated.exists()
        content = generated.read_text()
        assert "ghcr.io/appboy-io/velox" in content

    def test_invalid_platform(self, runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["init", "--ci", "jenkins"])
        assert result.exit_code != 0

    def test_init_without_ci_still_works(self, runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0
        assert (tmp_path / "velox-sample.yaml").exists()

    def test_init_with_ci_also_creates_sample_yaml(self, runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["init", "--ci", "github"])
        assert result.exit_code == 0
        assert (tmp_path / "velox-sample.yaml").exists()
        assert (tmp_path / ".github" / "workflows" / "velox.yml").exists()

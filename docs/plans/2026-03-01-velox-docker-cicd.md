# Velox Docker & CI/CD Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ship a Docker image with Gatling + Velox pre-installed to GHCR on tagged releases, and add `velox init --ci` to scaffold CI/CD workflow files for GitHub Actions, CircleCI, and Bitbucket Pipelines.

**Architecture:** Dockerfile based on Eclipse Temurin JRE with Python and Gatling installed. GitHub Actions release workflow builds and pushes on `v*` tags. CLI `init` command extended with `--ci` flag that copies platform-specific workflow templates.

**Tech Stack:** Docker, GitHub Actions, GHCR, Gatling 3.9.5, Python 3.10+

---

### Task 1: Dockerfile

**Files:**
- Create: `Dockerfile`
- Create: `.dockerignore`

**Step 1: Create `.dockerignore`**

```
.venv/
venv/
__pycache__/
*.pyc
*.egg-info/
.git/
.worktrees/
results/
.pytest_cache/
htmlcov/
.coverage
```

**Step 2: Create `Dockerfile`**

```dockerfile
FROM eclipse-temurin:21-jre-jammy

ARG GATLING_VERSION=3.9.5
ARG PYTHON_VERSION=3.10

# Install Python
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 python3-pip python3-venv unzip curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Gatling
RUN curl -fsSL https://repo1.maven.org/maven2/io/gatling/highcharts/gatling-charts-highcharts-bundle/${GATLING_VERSION}/gatling-charts-highcharts-bundle-${GATLING_VERSION}-bundle.zip \
        -o /tmp/gatling.zip && \
    unzip /tmp/gatling.zip -d /opt && \
    mv /opt/gatling-charts-highcharts-bundle-${GATLING_VERSION} /opt/gatling && \
    rm /tmp/gatling.zip

ENV GATLING_HOME=/opt/gatling
ENV PATH="${GATLING_HOME}/bin:${PATH}"

# Install Velox
WORKDIR /app
COPY pyproject.toml .
COPY src/ src/
RUN pip3 install --no-cache-dir --break-system-packages .

WORKDIR /tests
ENTRYPOINT ["velox"]
```

**Step 3: Build and verify locally**

```bash
docker build -t velox:local .
docker run --rm velox:local --help
```

Expected: Velox help output prints

**Step 4: Commit**

```bash
git add Dockerfile .dockerignore
git commit -m "feat: add Dockerfile with Gatling and Velox pre-installed"
```

---

### Task 2: GitHub Actions Release Workflow

**Files:**
- Create: `.github/workflows/release.yml`

**Step 1: Create the release workflow**

```yaml
# .github/workflows/release.yml
name: Release Docker Image

on:
  push:
    tags:
      - "v*"

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract version from tag
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=raw,value=latest

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
```

**Step 2: Commit**

```bash
mkdir -p .github/workflows
git add .github/workflows/release.yml
git commit -m "ci: add GitHub Actions release workflow for GHCR"
```

---

### Task 3: CI Template Files

**Files:**
- Create: `src/velox/templates/ci/github.yml`
- Create: `src/velox/templates/ci/circle.yml`
- Create: `src/velox/templates/ci/bitbucket.yml`

**Step 1: Create GitHub Actions template**

```yaml
# src/velox/templates/ci/github.yml
name: Performance Test

on:
  workflow_dispatch:
  workflow_call:

jobs:
  perf-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Velox Performance Test
        run: |
          docker run --rm \
            -v ${{ github.workspace }}/tests:/tests \
            -e TARGET_URL=${{ vars.TARGET_URL }} \
            ghcr.io/appboy-io/velox run /tests/perf.yaml
```

**Step 2: Create CircleCI template**

```yaml
# src/velox/templates/ci/circle.yml
version: 2.1

jobs:
  perf-test:
    docker:
      - image: ghcr.io/appboy-io/velox
    environment:
      TARGET_URL: "https://your-app.example.com"
    steps:
      - checkout
      - run:
          name: Run Velox Performance Test
          command: velox run tests/perf.yaml
```

**Step 3: Create Bitbucket Pipelines template**

```yaml
# src/velox/templates/ci/bitbucket.yml
pipelines:
  custom:
    perf-test:
      - step:
          name: Run Velox Performance Test
          image: ghcr.io/appboy-io/velox
          script:
            - velox run tests/perf.yaml
```

**Step 4: Commit**

```bash
git add src/velox/templates/ci/
git commit -m "feat: add CI/CD workflow templates for GitHub, CircleCI, and Bitbucket"
```

---

### Task 4: Extend `init` Command with `--ci` Flag

**Files:**
- Create: `tests/test_cli_ci.py`
- Modify: `src/velox/cli.py`

**Step 1: Write the failing tests**

```python
# tests/test_cli_ci.py
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
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_cli_ci.py -v
```

Expected: FAIL — `--ci` option does not exist

**Step 3: Update `src/velox/cli.py` — modify `init` command**

Replace the existing `init` function with:

```python
CI_PLATFORMS = {
    "github": (".github/workflows/velox.yml", "ci/github.yml"),
    "circle": (".circleci/config.yml", "ci/circle.yml"),
    "bitbucket": ("bitbucket-pipelines.yml", "ci/bitbucket.yml"),
}


@app.command()
def init(
    ci: str = typer.Option(None, "--ci", help="Generate CI/CD workflow: github, circle, or bitbucket"),
) -> None:
    """Scaffold a sample YAML test file and optionally a CI/CD workflow."""
    # Always create sample YAML
    dest = Path("velox-sample.yaml")
    if dest.exists():
        console.print(f"[yellow]![/yellow] {dest} already exists, skipping")
    else:
        source = _get_sample_yaml_path()
        shutil.copy(source, dest)
        console.print(f"[green]✓[/green] Created {dest}")

    # Optionally create CI workflow
    if ci:
        ci = ci.lower()
        if ci not in CI_PLATFORMS:
            console.print(f"[red]✗[/red] Unknown CI platform: {ci}. Use: github, circle, or bitbucket")
            raise typer.Exit(code=1)

        dest_path, template_name = CI_PLATFORMS[ci]
        dest_file = Path(dest_path)
        dest_file.parent.mkdir(parents=True, exist_ok=True)

        template_source = Path(__file__).parent / "templates" / template_name
        shutil.copy(template_source, dest_file)
        console.print(f"[green]✓[/green] Created {dest_file}")
        console.print(f"  Set TARGET_URL in your CI/CD environment variables")
    elif ci is None:
        console.print("  Edit it with your API details, then run: velox run velox-sample.yaml")
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_cli_ci.py -v
```

Expected: All PASS

**Step 5: Run full test suite**

```bash
pytest -v --tb=short
```

Expected: All tests PASS (including existing tests — verify `init` without `--ci` still works)

**Step 6: Commit**

```bash
git add src/velox/cli.py tests/test_cli_ci.py
git commit -m "feat: extend init command with --ci flag for workflow scaffolding"
```

---

### Task 5: Docker Build Verification

**Step 1: Build the Docker image locally**

```bash
docker build -t velox:local .
```

Expected: Build succeeds

**Step 2: Verify Velox CLI works inside container**

```bash
docker run --rm velox:local --help
docker run --rm velox:local validate /app/src/velox/templates/sample_test.yaml
```

Expected: Help output prints, validation succeeds

**Step 3: Verify Gatling is available inside container**

```bash
docker run --rm --entrypoint sh velox:local -c 'echo $GATLING_HOME && ls $GATLING_HOME/bin/'
```

Expected: Shows `/opt/gatling` and lists `gatling.sh`

**Step 4: Push and tag release**

```bash
git push origin master
git tag v0.1.0
git push origin v0.1.0
```

Expected: GitHub Actions release workflow triggers and pushes image to `ghcr.io/appboy-io/velox:v0.1.0` and `ghcr.io/appboy-io/velox:latest`

---

## Execution Summary

| Task | Component | Files |
|------|-----------|-------|
| 1 | Dockerfile | Dockerfile, .dockerignore |
| 2 | Release workflow | .github/workflows/release.yml |
| 3 | CI templates | templates/ci/github.yml, circle.yml, bitbucket.yml |
| 4 | CLI `--ci` flag | cli.py, test_cli_ci.py |
| 5 | Docker build verification | (manual verification) |

# Velox

YAML-driven Gatling performance testing CLI.

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org)

## What It Does

Define performance tests in YAML instead of writing Scala — Velox generates and runs Gatling simulations under the hood for realistic load generation. Built-in thresholds, reporting, and CI/CD integration let you go from zero to load test in minutes.

## Quick Start

```bash
pip install velox
velox init
# edit velox-sample.yaml with your API details
velox run velox-sample.yaml
```

## YAML Example

```yaml
name: "Sample API Test"
baseUrl: "https://jsonplaceholder.typicode.com"    # target server

config:
  users: 5           # concurrent virtual users
  rampUp: "10s"      # time to ramp up to full load
  duration: "30s"    # total test duration

flow:                # sequence of HTTP requests each user executes
  - name: "List Posts"
    method: GET
    path: "/posts"
    threshold:
      p95: "500ms"   # per-request latency threshold

  - name: "Get Single Post"
    method: GET
    path: "/posts/1"
    extract:
      userId: "$.userId"   # JSONPath extraction for chaining requests
    threshold:
      p95: "300ms"

  - name: "Get User"
    method: GET
    path: "/users/${userId}"   # variable interpolation from extracted values

threshold:           # global thresholds applied to the entire test
  p95: "1s"
  errorRate: "5%"

results:             # result storage options
  push: false        # push results to a dedicated VCS branch
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `velox run <file>` | Run a performance test |
| `velox validate <file>` | Validate YAML without running |
| `velox init` | Scaffold a sample test file |
| `velox init --ci <platform>` | Generate CI/CD workflow (`github`, `circle`, `bitbucket`) |
| `velox report` | View results from last run |

Override flags for `run`:

- `--base-url <url>` — Override the base URL defined in YAML
- `--users <n>` — Override the virtual user count

## Docker

```bash
docker pull ghcr.io/appboy-io/velox
docker run --rm -v $(pwd)/tests:/tests ghcr.io/appboy-io/velox run /tests/perf.yaml
```

## CI/CD

Scaffold a workflow for your platform:

```bash
velox init --ci github    # also: circle, bitbucket
```

Example generated GitHub Actions workflow:

```yaml
# .github/workflows/velox.yml
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

## Features

- Variable interpolation with `${var}` syntax
- Environment variable support via `$ENV{VAR}`
- JSONPath response extraction (`$.field`)
- Per-request and global thresholds (p95, error rate)
- Markdown and JSON report generation
- VCS results push to dedicated branch

## Development

```bash
git clone https://github.com/appboy-io/velox.git
cd velox
pip install -e ".[dev]"
pytest
```

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.

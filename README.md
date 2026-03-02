<p align="center">
  <img src="logo.svg" alt="Velox" width="192" height="192">
</p>

<h1 align="center">Velox</h1>

<p align="center">YAML-driven Gatling performance testing CLI.</p>

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org)

## What It Does

Define performance tests in YAML instead of writing Scala — Velox generates and runs Gatling simulations under the hood for realistic load generation. Built-in thresholds, reporting, and CI/CD integration let you go from zero to load test in minutes.

## Quick Start

```bash
docker pull ghcr.io/appboy-io/velox

# scaffold a sample test
docker run --rm -v $(pwd):/tests ghcr.io/appboy-io/velox init

# edit velox-sample.yaml with your API details, then run
docker run --rm -v $(pwd):/tests ghcr.io/appboy-io/velox run /tests/velox-sample.yaml
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
    threshold:
      p95: "300ms"

threshold:           # global thresholds applied to the entire test
  p95: "1s"
  errorRate: "5%"

results:             # result storage options
  push: false        # push results to a dedicated VCS branch
```

### Using API Keys and Request Bodies

```yaml
name: "Authenticated API Test"
baseUrl: "$ENV{BASE_URL}"              # read from environment variable

flow:
  - name: "Create Resource"
    method: POST
    path: "/api/resources"
    headers:
      Authorization: "Bearer $ENV{API_KEY}"
    body:
      name: "test-resource"
      type: "benchmark"
    extract:
      id: "$.id"                       # extract id from response
    threshold:
      p95: "800ms"

  - name: "Get Resource"
    method: GET
    path: "/api/resources/${id}"       # use extracted value
    headers:
      Authorization: "Bearer $ENV{API_KEY}"
    threshold:
      p95: "300ms"
```

Run with environment variables:

```bash
docker run --rm \
  -v $(pwd):/tests \
  -e BASE_URL=https://api.example.com \
  -e API_KEY=your-key \
  ghcr.io/appboy-io/velox run /tests/auth-test.yaml
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

# run a test
docker run --rm -v $(pwd):/tests ghcr.io/appboy-io/velox run /tests/perf.yaml

# validate without running
docker run --rm -v $(pwd):/tests ghcr.io/appboy-io/velox validate /tests/perf.yaml

# override users and base URL
docker run --rm -v $(pwd):/tests ghcr.io/appboy-io/velox run /tests/perf.yaml --users 10 --base-url https://staging.example.com
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

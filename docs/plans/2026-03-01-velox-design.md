# Velox — Design Document

**Date:** 2026-03-01
**Status:** Approved

## Overview

Velox is a YAML-driven CLI tool that generates and runs Gatling load tests. It makes performance testing approachable enough for project managers to write test definitions, while being powerful enough for CI/CD pipeline integration.

**Name origin:** Latin for "swift/rapid"

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
│  YAML Test   │───▶│  Python CLI   │───▶│ Jinja2 Templates │───▶│  Generated   │
│  Definition  │    │  (validate +  │    │ (Gatling Scala)  │    │  Simulation  │
└─────────────┘    │   orchestrate)│    └─────────────────┘    └──────┬───────┘
                   └──────┬───────┘                                   │
                          │                                           ▼
                   ┌──────▼───────┐    ┌─────────────────┐    ┌──────────────┐
                   │   Reporter    │◀───│  Gatling Engine  │◀───│  Subprocess  │
                   │ (MD+JSON+HTML)│    │  (load testing)  │    │   Launcher   │
                   └──────┬───────┘    └─────────────────┘    └──────────────┘
                          │
                   ┌──────▼───────┐
                   │  VCS Pusher   │
                   │ (git branch)  │
                   └──────────────┘
```

**Components:**

- **Python CLI** — Entry point. Parses YAML via Pydantic, validates, orchestrates everything.
- **Template Engine** — Jinja2 templates that produce Gatling simulation `.scala` files.
- **Subprocess Launcher** — Invokes Gatling with the generated simulation.
- **Reporter** — Parses Gatling output into JSON, generates Markdown with ASCII charts, keeps HTML reports.
- **VCS Pusher** — Commits results to a `{branch}-perf-results` git branch using a configured token/remote.

## Approach

**Template-based code generation** was chosen over AST-based codegen or direct Gatling SDK integration because:

- Jinja2 templates are easy to read, debug, and extend
- Adding new Gatling features means adding template snippets, not rewriting codegen logic
- Pydantic gives strong YAML validation with clear error messages
- Clean separation: Python handles orchestration, Gatling handles load
- Most approachable for open-source contributors

## YAML Schema

```yaml
# test-checkout-flow.yaml
name: "Checkout Flow"
baseUrl: "https://api.example.com"

config:
  users: 100            # concurrent virtual users
  rampUp: "30s"         # ramp-up period
  duration: "5m"        # total test duration

variables:
  apiKey: "${ENV.API_KEY}"

flow:
  - name: "Login"
    method: POST
    path: "/auth/login"
    headers:
      Content-Type: "application/json"
    body:
      username: "testuser"
      password: "testpass"
    extract:
      token: "$.accessToken"     # JSONPath extraction
    threshold:
      p95: "200ms"

  - name: "Get Products"
    method: GET
    path: "/products"
    headers:
      Authorization: "Bearer ${token}"
    threshold:
      p95: "300ms"

  - name: "Add to Cart"
    method: POST
    path: "/cart"
    headers:
      Authorization: "Bearer ${token}"
    body:
      productId: "SKU-001"
      quantity: 1
    extract:
      cartId: "$.cartId"

  - name: "Checkout"
    method: POST
    path: "/cart/${cartId}/checkout"
    headers:
      Authorization: "Bearer ${token}"

threshold:
  p95: "2s"
  errorRate: "1%"

results:
  push: true
  branchSuffix: "-perf-results"   # appended to current branch name
  remote: "origin"
```

### Design Decisions

- **Flat, readable structure** — approachable for non-developers (PMs, QA)
- **`extract`** enables response chaining via JSONPath (JSON responses only for v1)
- **Per-step `threshold`** is optional; **flow-level `threshold`** catches overall regressions
- **`${variable}`** syntax for interpolation — familiar, no code required
- **GraphQL** is supported natively (POST with `query`/`variables` body fields, JSONPath on response)
- Gatling's `group` construct wraps the entire flow for aggregate timing

### GraphQL Example

```yaml
  - name: "Fetch User Profile"
    method: POST
    path: "/graphql"
    headers:
      Authorization: "Bearer ${token}"
      Content-Type: "application/json"
    body:
      query: |
        query GetUser($id: ID!) {
          user(id: $id) {
            name
            email
          }
        }
      variables:
        id: "${userId}"
    extract:
      userName: "$.data.user.name"
```

## Reporting

### Report Artifacts

Each test run produces three artifacts:

1. **JSON** — Machine-readable metrics for programmatic consumption
2. **HTML** — Gatling's native HTML report for deep dives
3. **Markdown** — Summary with tables and ASCII charts, viewable in any VCS

### JSON Report Structure

```json
{
  "testName": "Checkout Flow",
  "timestamp": "2026-03-01T14:30:00Z",
  "config": { "users": 100, "rampUp": "30s", "duration": "5m" },
  "overall": {
    "p50": 1200, "p75": 1500, "p95": 1800, "p99": 2100,
    "mean": 1350, "errorRate": 0.3,
    "thresholdPassed": true
  },
  "steps": [
    {
      "name": "Login",
      "p50": 120, "p75": 150, "p95": 180,
      "mean": 135, "errorRate": 0.0,
      "thresholdPassed": true
    }
  ]
}
```

### Markdown Report

- Summary table with pass/fail status and overall metrics
- Per-step breakdown table with threshold comparison
- ASCII bar charts for latency distribution
- Historical trend if previous runs exist on the results branch

### Threshold Evaluation

- CLI exits with **non-zero exit code** on threshold failure (CI/CD-friendly)
- Threshold failures are clearly called out in Markdown report and CLI output
- Per-step and overall thresholds are evaluated independently

## VCS Results Push

- Results are committed to `{current-branch}-perf-results`
- Provider-agnostic: uses standard `git push` with a configured remote
- Requires an app token configured for authentication
- All three report artifacts (JSON, HTML, Markdown) are committed

## CLI Interface

```bash
velox run checkout-flow.yaml                # run a test
velox run test.yaml --base-url https://staging.example.com --users 50  # with overrides
velox validate checkout-flow.yaml           # validate YAML without running
velox init                                  # scaffold a sample YAML test file
velox report                                # view results from last run
```

### CLI Output

```
● Running: Checkout Flow
  ├─ Users: 100 | Ramp-up: 30s | Duration: 5m
  ├─ Generating Gatling simulation...
  ├─ Launching Gatling...
  │
  ├─ ✓ Login           p95: 180ms  (threshold: 200ms)
  ├─ ✓ Get Products    p95: 250ms  (threshold: 300ms)
  ├─ ✓ Add to Cart     p95: 190ms
  ├─ ✓ Checkout        p95: 310ms
  │
  ├─ ✓ Overall Flow    p95: 1.8s   (threshold: 2s)
  ├─ ✓ Error Rate      0.3%        (threshold: 1%)
  │
  ├─ Reports: ./results/2026-03-01-checkout-flow/
  └─ Pushed to: origin/feature/checkout-perf-results
```

## Constraints & Scope (v1)

- HTTP responses assumed to be JSON only (XML and other formats in future versions)
- Variable extraction via JSONPath only
- Gatling must be installed separately (or bundled via a future `velox setup` command)
- Python 3.10+ required

## Tech Stack

- **Python 3.10+** — CLI and orchestration
- **Pydantic** — YAML validation and schema enforcement
- **Jinja2** — Gatling simulation code generation
- **Click or Typer** — CLI framework
- **Gatling** — Load test execution (subprocess)

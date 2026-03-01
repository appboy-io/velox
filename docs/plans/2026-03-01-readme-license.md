# README & License Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Apache 2.0 license files and rewrite the README with comprehensive project documentation.

**Architecture:** Three new files (LICENSE, NOTICE, updated README.md) plus a one-line addition to pyproject.toml. No code changes.

**Tech Stack:** Markdown, Apache 2.0 license text

---

### Task 1: Add Apache 2.0 License and NOTICE

**Files:**
- Create: `LICENSE`
- Create: `NOTICE`
- Modify: `pyproject.toml:8` (add license field)

**Step 1: Create `LICENSE`**

Use the standard Apache License 2.0 full text from https://www.apache.org/licenses/LICENSE-2.0.txt

**Step 2: Create `NOTICE`**

```
Velox
Copyright 2026 Bryan Riley

Licensed under the Apache License, Version 2.0.
```

**Step 3: Add license to `pyproject.toml`**

Add `license = "Apache-2.0"` after the `description` line in `[project]`:

```toml
description = "YAML-driven Gatling performance testing CLI"
license = "Apache-2.0"
```

**Step 4: Commit**

```bash
git add LICENSE NOTICE pyproject.toml
git commit -m "chore: add Apache 2.0 license and NOTICE file"
```

---

### Task 2: Rewrite README.md

**Files:**
- Modify: `README.md`

**Step 1: Replace README.md with full content**

The README should contain these sections in order:

1. **Title block:**
   - `# Velox` heading
   - One-line description: "YAML-driven Gatling performance testing CLI"
   - Badges: License (Apache 2.0), Python (3.10+)

2. **What it does** (2-3 sentences):
   - Define performance tests in YAML instead of Scala
   - Gatling runs under the hood for realistic load generation
   - Built-in thresholds, reporting, and CI/CD integration

3. **Quick Start:**
   ```bash
   pip install velox
   velox init
   # edit velox-sample.yaml with your API details
   velox run velox-sample.yaml
   ```

4. **YAML Example:** Use the full contents of `src/velox/templates/sample_test.yaml` as a fenced code block. Add brief inline comments explaining each section (baseUrl, config, flow with steps, threshold, results).

5. **CLI Commands** table:

   | Command | Description |
   |---------|-------------|
   | `velox run <file>` | Run a performance test |
   | `velox validate <file>` | Validate YAML without running |
   | `velox init` | Scaffold a sample test file |
   | `velox init --ci <platform>` | Generate CI/CD workflow (github, circle, bitbucket) |
   | `velox report` | View results from last run |

   Include `--base-url` and `--users` override flags for `run`.

6. **Docker:**
   ```bash
   docker pull ghcr.io/appboy-io/velox
   docker run --rm -v $(pwd)/tests:/tests ghcr.io/appboy-io/velox run /tests/perf.yaml
   ```

7. **CI/CD:**
   - Mention `velox init --ci github|circle|bitbucket`
   - Show one short example (GitHub Actions) of what gets generated

8. **Features** bullet list:
   - Variable interpolation with `${var}` syntax
   - Environment variable support via `$ENV{VAR}`
   - JSONPath response extraction (`$.field`)
   - Per-request and global thresholds (p95, error rate)
   - Markdown and JSON report generation
   - VCS results push to dedicated branch

9. **Development:**
   ```bash
   git clone https://github.com/appboy-io/velox.git
   cd velox
   pip install -e ".[dev]"
   pytest
   ```

10. **License:**
    - "Apache 2.0 — see [LICENSE](LICENSE) for details."

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: rewrite README with comprehensive project documentation"
```

---

## Execution Summary

| Task | Component | Files |
|------|-----------|-------|
| 1 | License + NOTICE | LICENSE, NOTICE, pyproject.toml |
| 2 | README rewrite | README.md |

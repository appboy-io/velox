# README & License Design

**Goal:** Add a comprehensive README and Apache 2.0 license to Velox.

## License

- **License:** Apache 2.0
- **Copyright:** Bryan Riley
- **Files:** `LICENSE` (full Apache 2.0 text), `NOTICE` (project name + copyright)
- **pyproject.toml:** Add `license = "Apache-2.0"`

## README Structure

1. **Title + tagline** — "Velox" with one-line description, badges (license, Python version)
2. **What it does** — 2-3 sentences: YAML-driven perf testing, Gatling under the hood, no Scala needed
3. **Quick Start** — pip install, `velox init`, `velox run`
4. **YAML example** — sample test file showing config format (baseUrl, config, flow, threshold, results)
5. **CLI Commands** — `run`, `validate`, `init`, `report` with brief descriptions
6. **Docker** — pull from GHCR, run with volume mount
7. **CI/CD** — `velox init --ci github|circle|bitbucket` with brief example
8. **Features** — bullet list: variable interpolation, JSONPath extraction, threshold pass/fail, Markdown/JSON reports, VCS result push
9. **Development** — clone, install dev deps, run tests
10. **License** — Apache 2.0 one-liner with link

## Audience

Both QA/DevOps engineers and backend developers. No comparison table with alternatives — focus purely on Velox.

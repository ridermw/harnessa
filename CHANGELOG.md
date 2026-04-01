# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.2.0] — 2026-03-30

### Added
- Comprehensive skill rewrite (`SKILL.md`: 86→332 lines) with role separation protocol, anti-people-pleasing rules, and structured agent handoff format
- Comprehensive install guide (`INSTALL.md`: 74→234 lines) with verification steps, best practices, troubleshooting, and uninstall instructions
- Showcase app rebuilt as proper full-stack application (32 files: Express + React + Vite + Tailwind + sql.js) — AI Code Review Dashboard
- `showcase/BUILD_LOG.md` documenting how the Planner→Generator→Evaluator trio built the showcase app end-to-end
- Complete experimental results (`RESULTS.md`) — 0 pending markers, all 12 article claims + 3 Harnessa hypotheses evaluated with verdicts
- Benchmark results: solo vs trio across 5 benchmarks (10 runs total) with per-iteration score tracking
- Runner scripts (`run-benchmark.sh`, `run-all-benchmarks.sh`, `analyze-results.sh`) for automated benchmark execution
- Copilot CLI skill (`/harnessa` command) — GAN-inspired 3-agent pipeline usable in any repo
- Installation instructions (`INSTALL.md`) with per-project, global, and runner script options
- Evaluator JSON extraction hardening (3-strategy parser: direct, brace-matching, code-block extraction)

## [Unreleased]

### Added
- `website/` web-keynote presentation site for **The Adversarial Architecture** with full-screen scenes, hash/deep-link navigation, appendix overlay, and GitHub Pages-friendly static build output
- GitHub Pages workflow (`.github/workflows/presentation-pages.yml`) to build and deploy the presentation microsite from the repo
- Presentation source artifacts in `presentation/` plus the supporting narrative plan in `docs/PRESENTATION_PLAN.md`

## [0.1.0] — 2026-03-26

### Added
- CLI with `run`, `replay`, `report`, `list` commands
- 3-agent pipeline: Planner, Generator, Evaluator with subprocess isolation
- Cross-model evaluator comparison (run two models independently)
- Evaluator Goodhart mitigations: rubber-stamp detection, refusal-to-be-negative handling, fallback grading
- Score reconciliation with conservative disagreement handling
- 12 Pydantic telemetry models (9 data models + 3 enums) with atomic JSON writes
- Pluggable criteria YAML with `backend` and `fullstack` defaults
- Markdown report generation with solo-vs-trio comparison
- Benchmark difficulty auto-calibration (too_easy/too_hard/in_zone classification)
- Replay mode: re-evaluate saved artifacts with updated evaluator prompts
- IsolationManager: git sparse-checkout excluding `_eval/` from generator
- ToolWrapper: logs all subprocess invocations for telemetry
- PortAllocator: non-overlapping port ranges per benchmark
- 5 benchmark repos:
  - small-bugfix-python (CLI arg parser ± sign bug)
  - small-feature-typescript (retry with exponential backoff)
  - small-bugfix-go (HTTP server connection pool race condition)
  - medium-feature-python (FastAPI TODO app tags feature)
  - medium-feature-fullstack (React+Express real-time notifications)
- 178 tests with full mocking (no API calls required)
- PROJECT_SPEC.md, ARCHITECTURE.md, design doc, test plan, CEO review, eng review
- README.md — project overview with architecture diagram and related reading
- CONTRIBUTING.md — contribution guidelines
- LICENSE — MIT license

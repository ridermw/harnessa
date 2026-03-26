# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

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

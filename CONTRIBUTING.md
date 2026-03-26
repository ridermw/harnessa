# Contributing to Harnessa

Thank you for your interest in contributing to Harnessa! This project is equal parts framework-building, research, and documentation — contributions to any of those areas are welcome.

## Getting Started

1. Read [PROJECT_SPEC.md](PROJECT_SPEC.md) — it's the project bible and covers the architecture, principles, success criteria, and telemetry spec
2. Read [docs/ARTICLE_REFERENCE.md](docs/ARTICLE_REFERENCE.md) — the Anthropic article that inspired this project
3. Check the open issues for areas that need work

## What We're Building

Harnessa is a GAN-inspired multi-agent harness with three roles (Planner, Generator, Evaluator). The project has three equally important tracks:

### 1. Framework (the harness itself)
- Orchestrator that coordinates the three agents
- File-based communication between agents
- Sprint contract negotiation
- Pluggable grading criteria

### 2. Telemetry & Testing
- Structured telemetry for every run (timing, cost, scores, bugs)
- 4-level testing pyramid (mechanics → quality → calibration → economics)
- A/B comparison tooling (harness vs solo agent)

### 3. Documentation & Research
- Well-documented experiments with reproducible results
- Evaluator calibration logs and tuning history
- Analysis of which harness components are load-bearing

## How to Contribute

### Reporting Issues
- Include which track the issue relates to (framework, telemetry, docs)
- For framework bugs, include the run manifest if available
- For evaluator calibration issues, include the evaluator's output and your assessment of what it should have been

### Code Changes
1. Fork the repo and create a branch from `main`
2. Make your changes
3. Ensure telemetry schemas are respected (changes to telemetry format need discussion first)
4. Write or update tests as appropriate
5. Submit a PR with a clear description of what and why

### Documentation
- Keep PROJECT_SPEC.md in sync with implementation
- Experiment write-ups go in `docs/experiments/`
- Evaluator calibration data goes in `tests/calibration/`

## Design Principles

These are non-negotiable. See PROJECT_SPEC.md for the full list, but the critical ones for contributors:

1. **Telemetry is first-class.** Every claim about quality improvement must be backed by data.
2. **Communication via files, not memory.** Every decision, score, bug, and contract must be written to disk.
3. **A/B everything.** The solo agent run is always the control group.
4. **Discernment over approval.** The evaluator's default posture is skepticism.

## Code of Conduct

Be respectful, constructive, and assume good intent. We're exploring novel territory — disagreement about approaches is expected and healthy.

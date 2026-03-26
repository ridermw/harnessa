# CLAUDE.md — Harnessa Project Guide

## What This Is
Harnessa is a GAN-inspired multi-agent harness framework. It orchestrates 3 AI agents
(Planner → Generator → Evaluator) to produce software that's categorically better than
what a solo agent achieves, with telemetry proving it.

Based on: https://www.anthropic.com/engineering/harness-design-long-running-apps

## Quick Commands
```bash
# Install (editable, with dev deps)
pip install -e ".[dev]"

# Run tests
pytest

# Run a benchmark (requires ANTHROPIC_API_KEY or OPENAI_API_KEY)
harnessa run small-bugfix-python --mode trio
harnessa run small-bugfix-python --mode solo

# Compare solo vs trio
harnessa report <run-id>

# Re-evaluate with updated criteria
harnessa replay <run-id>

# List available benchmarks
harnessa list
```

## Architecture
```
src/harnessa/
├── cli.py              # Typer CLI entry point (run, replay, report, list)
├── config.py           # RunConfig Pydantic model + RunMode enum
├── orchestrator.py     # Pipeline lifecycle (planner→generator→evaluator→retry)
├── response_adapter.py # LiteLLM response normalization
├── reconciler.py       # Cross-model score reconciliation
├── replay.py           # Re-evaluate saved artifacts
├── agents/
│   ├── base.py         # BaseAgent abstract class
│   ├── planner.py      # Expands prompts into specs
│   ├── generator.py    # Implements specs into code
│   ├── evaluator.py    # Skeptical grading with Goodhart mitigations
│   └── isolation.py    # Filesystem boundaries, ToolWrapper, PortAllocator
├── telemetry/
│   ├── models.py       # 12 Pydantic schemas (9 models + 3 enums) for run data
│   └── collector.py    # Metric collection + atomic JSON writes
├── criteria/
│   └── loader.py       # YAML criteria loader + validator
└── reporting/
    ├── markdown.py     # Run reports, solo-vs-trio comparison
    └── difficulty.py   # Benchmark difficulty classification
```

## Key Design Decisions
- **Subprocess isolation**: Agents run as separate processes. Generator CANNOT see `_eval/` directory (Goodhart mitigation via git sparse-checkout)
- **File-based communication**: Agents write files, orchestrator reads them. Atomic writes (tmp + rename + .done marker)
- **Cross-model evaluation**: Two different LLM models grade independently; disagreements are signal
- **Skeptical evaluator**: Anti-people-pleasing prompting, rubber-stamp detection, refusal handling
- **Telemetry first**: Every run produces structured JSON with timing, cost, scores, bugs, model versions

## Benchmarks
5 benchmark repos in `benchmarks/`, each with:
- Real code with a seeded bug or missing feature
- `TASK.md` — the prompt given to the harness
- `tests/` — visible tests (some failing)
- `_eval/` — hidden acceptance tests (evaluator-only)
- `_eval/fixtures/` — expected output for deterministic verification

Benchmarks:
- `small-bugfix-python` — CLI arg parser ± sign bug
- `small-feature-typescript` — retry with exponential backoff
- `small-bugfix-go` — HTTP server connection pool race condition
- `medium-feature-python` — FastAPI TODO app tags feature
- `medium-feature-fullstack` — React+Express real-time notifications

## Criteria
YAML criteria files in `criteria/`:
- `backend.yaml` — backend-focused grading criteria
- `fullstack.yaml` — full-stack grading criteria

## Testing
```bash
pytest                    # All tests (178 test functions)
pytest tests/test_cli.py  # Just CLI tests
pytest -k "evaluator"     # Tests matching pattern
```

All LLM calls are mocked in tests — no API keys needed to run the test suite.

## Coding Conventions
- Python 3.12+, type hints everywhere
- Pydantic v2 with `model_config = {"strict": True}`
- All classes have docstrings
- Atomic file writes for agent communication
- Mock LLM calls in tests — never make real API calls in tests

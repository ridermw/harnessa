# Harnessa V1 — Implementation Plan

## Approach
CLI benchmark harness (`harnessa run <benchmark> --mode solo|trio`) proving the 3-agent pattern (Planner → Generator → Evaluator) with hard telemetry numbers. Subprocess isolation. Cross-model evaluator comparison. 5 benchmarks across Python/TypeScript/Go spanning small (15-30 min) and medium (60-90 min) tasks.

## Source Documents
- `PROJECT_SPEC.md` — project bible (architecture, telemetry spec, success criteria)
- `docs/designs/v1-cli-benchmark-harness.md` — approved V1 design doc
- `docs/ARTICLE_REFERENCE.md` — Anthropic article (foundational reference)
- `docs/ARCHITECTURE.md` — technical architecture deep-dive
- `~/.gstack/projects/harnessa/ceo-plans/2026-03-26-v1-cli-benchmark-harness.md` — CEO plan with scope decisions

## Architecture Decision: Subprocess Isolation

```
  harnessa run benchmark-3 --mode trio --evaluator-models claude,gpt
       │
       ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                    ORCHESTRATOR (Python)                     │
  │                                                             │
  │  1. Load criteria YAML (criteria/backend.yaml)              │
  │  2. Prepare benchmark working tree (exclude _eval/)         │
  │                                                             │
  │  PLANNER (subprocess)                                       │
  │    sees: prompt only                                        │
  │    writes: spec.md                                          │
  │                          ▼                                  │
  │  GENERATOR (subprocess)                                     │
  │    sees: spec.md + working tree (no _eval/, no criteria)    │
  │    writes: code (git committed)                             │
  │                          ▼                                  │
  │  EVALUATOR A (subprocess, Claude)  ──┐                     │
  │  EVALUATOR B (subprocess, GPT)    ──┤ cross-model          │
  │    sees: code + _eval/ + criteria    │ comparison           │
  │    writes: scores + bugs             │                      │
  │                          ┌───────────┘                      │
  │                          ▼                                  │
  │  SCORE RECONCILER                                           │
  │    agreement → high confidence                              │
  │    disagreement → signal for calibration                    │
  │                          ▼                                  │
  │  PASS → telemetry + artifact snapshot                       │
  │  FAIL → feedback to GENERATOR (max 3 iterations)            │
  └─────────────────────────────────────────────────────────────┘
```

## Accepted Scope Expansions (from CEO review)
1. Cross-model evaluator comparison (`--evaluator-models`)
2. Benchmark difficulty auto-calibration
3. Replay mode (`harnessa replay <run-id>`)
4. Pluggable criteria YAML (`--criteria backend`)
5. Tool/skill usage telemetry (wrapper approach)

## Implementation Todos

### Phase 1: Scaffold
- `scaffold-cli` — Typer CLI with `run`, `replay`, `report` commands
- `scaffold-orchestrator` — Orchestrator class managing subprocess lifecycle
- `scaffold-telemetry` — Pydantic models for run manifest, per-benchmark metrics
- `scaffold-criteria` — YAML loader + validator for criteria definitions

### Phase 2: Agents
- `agent-planner` — Planner subprocess: takes prompt, writes spec.md
- `agent-generator` — Generator subprocess: reads spec, writes code, git commits
- `agent-evaluator` — Evaluator subprocess: runs tests, grades criteria, files bugs
- `agent-isolation` — Filesystem boundary enforcement (_eval/ exclusion, tool wrapper)

### Phase 3: Benchmarks
- `benchmark-small-bugfix-python` — Python CLI arg parser bug
- `benchmark-small-feature-typescript` — TS retry() with exponential backoff
- `benchmark-small-bugfix-go` — Go HTTP server race condition
- `benchmark-medium-feature-python` — FastAPI TODO app tags feature
- `benchmark-medium-feature-fullstack` — React+Express notifications system

### Phase 4: Evaluator Calibration
- `evaluator-calibration` — Golden set testing, false-positive rate measurement
- `evaluator-cross-model` — Dual-model evaluation and score reconciliation
- `evaluator-refusal-handling` — Detect and handle "model refuses to be negative"

### Phase 5: Reporting & Analysis
- `reporting-markdown` — Per-run markdown report with solo-vs-trio comparison
- `reporting-difficulty` — Benchmark difficulty scoring and calibration recommendations
- `replay-mode` — Re-evaluate saved artifacts with updated evaluator prompts

## Failure Modes (from design doc + CEO review + eng review)
- Max 3 evaluator iterations per benchmark
- API errors: exponential backoff (10s/30s/90s), 3 retries, then FAILED
- Docker timeout: 10 min per command
- Evaluator rubber-stamping: flag if all scores ≥ 9
- **Evaluator refusal**: detect when model refuses to give negative scores. Mitigation: re-prompt or switch model.
- Global timeout: small 45 min, medium 120 min
- Goodhart mitigation: hidden _eval/ tests (enforced via git sparse-checkout), fixture comparison, diff quality check
- **Max tokens truncation**: ResponseAdapter detects truncation, triggers retry with shorter prompt
- **Evaluator Playwright failure**: fallback to test-suite-only grading with `degraded_evaluation: true` flag
- **File partial write**: atomic writes (write-to-temp + rename + .done marker) prevent corruption
- **Port collision**: assigned port ranges per benchmark (8001-8010 for bench 1, 8011-8020 for bench 2, etc.)
- **Subprocess orphan**: signal handler on Ctrl+C kills all child PIDs, cleanup on orchestrator exit
- **Cross-run contamination**: each run gets a fresh git worktree, no shared state

## Experimental Rigor (from Codex outside voice)
- Minimum 3 runs per benchmark per mode (report mean + stddev, not single results)
- Preregistered primary metric: evaluator pass rate + test pass rate (defined before first run)
- Model/version pinning in run manifest (LiteLLM model string locked per experiment)
- Budget parity enforced: solo gets same token budget as trio's total
- Fresh git worktree per run (hermetic reset, no cache/artifact leakage)
- Randomized execution order (solo vs trio, benchmark order) to control for time-of-day/provider drift

## Architecture Additions (from eng review)
- **BaseAgent class**: shared subprocess lifecycle (launch, LiteLLM call, response parsing, status writing, telemetry)
- **RunConfig Pydantic model**: centralized config passed through pipeline (cli flags → orchestrator → agents)
- **ResponseAdapter**: normalizes LiteLLM responses across providers to canonical Pydantic model
- **.status file protocol**: agents write running/error/done status, orchestrator polls for fast-fail
- **Retry ownership**: API retries = orchestrator (3 attempts, backoff), iteration retries = eval-driven (max 3)
- **Resource limits**: preexec_fn with rlimit for memory/CPU per subprocess (POSIX, macOS supported)
- **Evaluator health check**: verify evaluator can start containers/access network before run begins

## Success Criteria
1. All 5 benchmarks complete in both solo and trio mode without human intervention
2. Telemetry shows where trio wins AND where it doesn't (honest)
3. Evaluator false-positive rate < 20% (calibration gate)
4. Evaluator catches > 50% of real bugs (calibration gate)
5. Evaluator consistency: ±1 per criterion on same artifact
6. Cross-model evaluator agreement > 70%
7. Tool usage telemetry captures which skills/tools helped vs. didn't
8. Results reproducible: 3+ runs of same benchmark produce scores within ±1.5 stddev
9. Model versions pinned and recorded in every run manifest

## NOT in Scope
- HTML telemetry dashboard (skipped — markdown reports sufficient for V1)
- GitHub/Jira/Linear integration (Phase 2)
- Self-calibrating topology selection (Phase 2)
- Benchmark marketplace (Phase 2+)
- UI of any kind
- Docker-mandatory isolation (optional, local-process with rlimits is default)
- Statistical significance testing (V1 establishes baselines; V2 adds proper hypothesis testing)

## What Already Exists
- PROJECT_SPEC.md — comprehensive spec with telemetry schemas, grading criteria, success tiers
- ARCHITECTURE.md — agent lifecycle, communication protocol, grading criteria YAML format
- Design doc — 5 concrete benchmarks, solo mode spec, failure modes, Goodhart mitigation

## Dream State Delta
V1 leaves us with: proof (or disproof) that the 3-agent pattern works across task sizes, a CLI tool that runs benchmarks, and telemetry data showing where the pattern adds value. The 12-month ideal (quality operating system, self-calibrating, pluggable into any workflow) requires V1's data to guide architectural decisions — this is the right foundation.

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 1 | CLEAR | 5 proposals, 4 accepted, 0 deferred |
| Codex Review | `/codex review` | Independent 2nd opinion | 0 | — | — |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 1 | CLEAR | 18 issues, 6 critical gaps, all resolved |
| Design Review | `/plan-design-review` | UI/UX gaps | 0 | — | N/A (no UI) |

**VERDICT:** CEO + ENG CLEARED — ready to implement. Run `/ship` when done.

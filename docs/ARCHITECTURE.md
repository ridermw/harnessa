# Architecture

> Technical deep-dive into how Harnessa's three-agent system works. For the project vision and success criteria, see [PROJECT_SPEC.md](../PROJECT_SPEC.md).

## System Overview

```
Human Prompt (1-4 sentences)
         │
         ▼
   ┌──────────┐
   │  Planner  │  Expands prompt → full product spec
   └─────┬────┘
         │ spec.md
         ▼
   ┌──────────┐     ┌──────────────┐
   │Generator │◀───▶│  Evaluator   │  Sprint contract negotiation
   └─────┬────┘     └──────┬───────┘
         │                  │
         │ builds code      │ tests live app via Playwright
         │                  │ grades against criteria
         │                  │ files bugs with code references
         │                  │
         │◀─────────────────┘  feedback loop (N iterations)
         │
         ▼
   Final Application + Telemetry
```

## Agent Lifecycle

### Phase 1: Planning

The Planner receives the raw human prompt and produces:

1. **`planner/spec.md`** — Full product specification with features, user stories, data models
2. **`planner/design-direction.md`** — Visual design language (when applicable)

The Planner is instructed to:
- Be ambitious about scope (dream bigger than the user)
- Focus on product context and high-level technical design
- Avoid granular implementation details (errors cascade)
- Identify opportunities for AI-native features

### Phase 2: Contract Negotiation

For each sprint (or build phase), the Generator and Evaluator negotiate:

1. Generator writes **`contracts/sprint-N-proposal.md`** — What it will build, how success is verified
2. Evaluator reviews and writes **`contracts/sprint-N-agreement.md`** — Approved criteria, adjusted expectations
3. They iterate until agreement (typically 1-2 rounds)

This bridges the gap between high-level user stories and testable implementation.

### Phase 3: Build

The Generator implements against the agreed contract:
- Works one feature at a time within a sprint
- Uses git to checkpoint work
- Self-evaluates before handing off to QA (first-pass, not final word)

### Phase 4: Evaluation

The Evaluator:
1. Launches the running application
2. Interacts with it via Playwright MCP — navigates, clicks, fills forms, screenshots
3. Grades each criterion from the sprint contract
4. Files specific bugs with file/line references
5. Produces pass/fail verdict

If any criterion falls below its hard threshold → sprint fails → feedback returns to Generator.

### Phase 5: Iteration

The Generator reads evaluation feedback and decides:
- **Refine** — Scores trending well, continue current direction
- **Pivot** — Approach isn't working, try a fundamentally different strategy

This cycle repeats (typically 3-8 iterations per run) until all criteria pass or iteration limit is reached.

## Communication Protocol

All inter-agent communication happens through files on disk:

```
runs/{run-id}/
├── planner/
│   ├── spec.md                    # Product specification
│   └── design-direction.md        # Visual design language
├── contracts/
│   ├── sprint-1-proposal.md       # Generator's proposal
│   ├── sprint-1-agreement.md      # Evaluator's review + agreement
│   ├── sprint-2-proposal.md
│   └── sprint-2-agreement.md
├── evaluations/
│   ├── sprint-1-eval.md           # Scores + justifications
│   ├── sprint-1-bugs.md           # Bug reports
│   ├── sprint-2-eval.md
│   └── sprint-2-bugs.md
└── telemetry/
    ├── run-manifest.json          # Overall run metadata
    ├── sprint-1-metrics.json      # Per-sprint timing, cost, scores
    ├── sprint-2-metrics.json
    └── quality-trend.json         # Score evolution across iterations
```

### Why Files?

- **Audit trail** — Every decision is recorded and inspectable
- **Resumability** — A crashed run can be picked up from the last written file
- **Human oversight** — A human can read any file at any point to understand what's happening
- **Clean boundaries** — No shared state, no race conditions, no memory leaks between agents

## Grading Criteria System

Criteria are pluggable and project-type-specific. Each criterion defines:

```yaml
name: "Product Depth"
weight: HIGH          # HIGH, MEDIUM, LOW
threshold: 6          # Minimum score (1-10) to pass
description: |
  Are features fully realized or stubbed out?
  Do interactions have real depth?
few_shot_examples:
  - score: 3
    justification: "Button renders but clicking does nothing. Feature is a facade."
  - score: 7
    justification: "Core flow works. Edge cases unhandled but main path is solid."
  - score: 9
    justification: "Feature works as a user would expect. Error states handled. Feels complete."
```

The few-shot examples are critical for calibrating the Evaluator's judgment and preventing score drift.

## Context Management Strategy

Two approaches, depending on model capability:

### Context Resets (for models with context anxiety)
- Clear context window entirely between sprints
- Structured handoff artifact carries state to next agent instance
- Clean slate eliminates premature wrap-up behavior

### Compaction (for models without context anxiety)
- SDK handles automatic compaction as context grows
- Agent runs as one continuous session across the whole build
- Simpler, but requires the model to maintain coherence natively

The choice depends on which model is being used. Test both; measure which produces better output.

## Telemetry Architecture

Telemetry is collected at three granularities:

### Per-Agent (real-time)
- Token counts (in/out)
- Wall-clock duration
- Cost calculation

### Per-Sprint (after each eval cycle)
- Criterion scores with justifications
- Bug count (found / fixed)
- Contract negotiation rounds
- Iteration number

### Per-Run (aggregate)
- Total cost and duration
- Quality trend (scores over iterations)
- Final pass/fail per criterion
- A/B comparison data (if solo run exists)

All telemetry is written to JSON files in `runs/{run-id}/telemetry/` — see PROJECT_SPEC.md for the full schema.

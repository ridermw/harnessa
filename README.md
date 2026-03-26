# Harnessa

A GAN-inspired multi-agent harness framework for orchestrating AI agents that build software better together than any single agent can alone.

## What Is This?

Harnessa is an open-source framework built on research from [Anthropic's harness design work](https://www.anthropic.com/engineering/harness-design-long-running-apps). It implements a three-agent architecture — **Planner**, **Generator**, **Evaluator** — where adversarial tension between the builder and the critic drives output quality far beyond what a solo agent achieves.

Think of it like a GAN for software: the Generator builds, the Evaluator tears it apart, and the feedback loop drives both toward better outcomes. The Planner ensures they're building the right thing in the first place.

## Why?

A single AI agent building software hits two walls:

1. **It loses coherence** as context grows — and some models prematurely wrap up work ("context anxiety")
2. **It can't judge its own work** — agents reliably praise mediocre output, even when bugs are obvious

Separating generation from evaluation breaks through both. The evidence from Anthropic's experiments:

| Approach | Duration | Cost | Result |
|----------|----------|------|--------|
| Solo agent | 20 min | $9 | Core feature broken |
| 3-agent harness | 6 hr | $200 | 16-feature app, working core, polished UI |

Not incrementally better — **categorically different**.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Orchestrator                       │
│                                                       │
│   ┌──────────┐    ┌──────────┐    ┌──────────────┐   │
│   │ Planner  │───▶│Generator │◀──▶│  Evaluator   │   │
│   │          │    │          │    │              │   │
│   │ Expands  │    │ Builds   │    │ Tests live   │   │
│   │ prompt   │    │ features │    │ app, grades  │   │
│   │ into     │    │ in       │    │ against      │   │
│   │ full     │    │ sprints  │    │ criteria,    │   │
│   │ spec     │    │          │    │ files bugs   │   │
│   └──────────┘    └──────────┘    └──────────────┘   │
│                                                       │
│   ┌─────────────────────────────────────────────┐     │
│   │              Telemetry Layer                 │     │
│   │  Timing · Cost · Scores · Bugs · Trends     │     │
│   └─────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────┘
```

**Planner** — Turns 1-4 sentence prompts into ambitious product specs. Focuses on *what*, not *how*.

**Generator** — Implements the spec in sprints. Negotiates "sprint contracts" with the Evaluator before coding. Uses git for checkpointing.

**Evaluator** — Interacts with the live running application (via Playwright). Grades against criteria with hard thresholds. Skeptical by default. Files specific, actionable bugs.

Agents communicate through **files on disk** — every decision, score, and bug report is written down, creating a full audit trail.

## Key Concepts

### Sprint Contracts
Before each sprint, the Generator and Evaluator negotiate what "done" looks like. This bridges the gap between high-level spec and testable implementation without over-specifying too early.

### Grading Criteria
Subjective quality becomes gradable through concrete criteria. The framework ships with defaults for frontend and full-stack work, and supports custom criteria per project type. Criteria wording directly steers the Generator's output — they're not just measurement, they're guidance.

### Adversarial Feedback Loop
The Evaluator's feedback flows back to the Generator as input for the next iteration. The Generator decides: refine the current direction, or pivot entirely. 5-15 iterations per run, with scores trending upward before plateauing.

### Telemetry
Every run produces structured telemetry: timing, cost, scores, bugs, and quality trends. Claims about improvement are backed by data.

## Documentation

| Document | Purpose |
|----------|---------|
| [PROJECT_SPEC.md](PROJECT_SPEC.md) | Complete project specification — the "bible" for this repo |
| [docs/ARTICLE_REFERENCE.md](docs/ARTICLE_REFERENCE.md) | Full text of the Anthropic article that inspired this project |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Technical architecture deep-dive |

## Project Status

🚧 **Early stage** — This project is part speculation, part framework-building, and part rigorous telemetry/testing infrastructure. We're building the harness, the test suite to prove it works, and the documentation to explain why.

## Related Reading

- [Harness Design for Long-Running Apps](https://www.anthropic.com/engineering/harness-design-long-running-apps) — The Anthropic article this project is based on
- [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) — Earlier 2-agent harness work
- [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — Foundational agent design principles
- [Context Engineering for AI Agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — Context window management
- [Claude Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview) — Orchestration layer
- [Generative Adversarial Networks](https://en.wikipedia.org/wiki/Generative_adversarial_network) — The ML paradigm inspiring the architecture

## License

[MIT](LICENSE)

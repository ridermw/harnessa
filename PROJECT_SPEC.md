# Harnessa — GAN-Inspired Multi-Agent Harness Framework

> **One-line pitch:** A framework for orchestrating three adversarial AI agents — Planner, Generator, Evaluator — that produce software far exceeding what any single agent achieves alone, with the telemetry to prove it.

---

## Source Material & Foundational Reference

**Primary article:** [Harness Design for Long-Running Apps](https://www.anthropic.com/engineering/harness-design-long-running-apps)
— Prithvi Rajasekaran, Anthropic Labs, 2025

**Related prior art from article:**
- [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) — earlier 2-agent (initializer + coder) harness work
- [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — Anthropic's foundational "simplest solution possible" philosophy
- [Context Engineering for AI Agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — context window management strategies
- [Claude Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview) — orchestration layer used in the original experiments
- [Frontend Design Skill](https://github.com/anthropics/claude-code/blob/main/plugins/frontend-design/skills/frontend-design/SKILL.md) — design criteria that drove the evaluator's taste
- [Generative Adversarial Networks (GANs)](https://en.wikipedia.org/wiki/Generative_adversarial_network) — the ML paradigm inspiring the architecture

---

## Why This Exists

### The Problem

A single AI agent building software exhibits two persistent failure modes:

1. **Context degradation** — As the context window fills, coherence drops. Some models exhibit "context anxiety," prematurely wrapping up work as they approach perceived limits. Compaction (summarizing earlier conversation) doesn't fully solve this because it doesn't give the agent a clean slate.

2. **Self-evaluation failure** — When asked to judge their own work, agents reliably praise it — even when quality is obviously mediocre to a human observer. This is especially pronounced for subjective tasks (design, UX) but persists even on verifiable tasks. An agent will identify a real bug, then talk itself into deciding it's not a big deal and approve the work anyway.

### The Insight

Separating the agent doing the work from the agent judging it is a **strong lever**. The separation doesn't eliminate leniency on its own, but tuning a standalone evaluator to be skeptical is far more tractable than making a generator critical of its own work. Once external feedback exists, the generator has something concrete to iterate against.

This maps directly to how the GAN paradigm works in machine learning: a generator produces output, a discriminator judges it, and the adversarial tension between them drives both toward higher quality.

### The Evidence

From the article's experiments:

| Approach | Duration | Cost | Outcome |
|----------|----------|------|---------|
| Solo agent (Opus 4.5) | 20 min | $9 | Core feature broken, poor layout, no workflow guidance |
| 3-agent harness (Opus 4.5) | 6 hr | $200 | 16-feature spec, working core, AI integration, polished UI |
| Simplified harness (Opus 4.6) | 3 hr 50 min | $125 | Full DAW with agent-driven composition, 3 QA rounds |

The harness output was categorically different — not incrementally better, but qualitatively in a different tier.

---

## The Three Roles

### 1. Planner (The Architect)

**Purpose:** Transform a minimal human prompt (1-4 sentences) into an ambitious, comprehensive product specification.

**Key behaviors:**
- Expands scope ambitiously — the planner should dream bigger than the user
- Focuses on **product context and high-level technical design**, NOT granular implementation details
- Avoids specifying implementation paths that could cascade errors downstream
- Defines deliverables and user stories, lets the Generator figure out the path
- Optionally identifies opportunities for AI-native features within the spec

**What it produces:**
- Full product spec with feature list, user stories, and data models
- Visual design language / design direction
- Sprint decomposition (when sprints are used) or feature priority ordering
- Success criteria that the Evaluator will later grade against

**Critical principle:** If the planner tries to specify granular technical details upfront and gets something wrong, the errors cascade into downstream implementation. Constrain on *what*, not *how*.

### 2. Generator (The Builder)

**Purpose:** Implement the spec faithfully, working in focused sprints or continuous sessions.

**Key behaviors:**
- Works one feature at a time (sprint-based) or in a continuous session (for more capable models)
- Self-evaluates at the end of each sprint before handing off to QA (a first-pass check, not the final word)
- Negotiates **sprint contracts** with the Evaluator before coding — agreeing on what "done" looks like
- Makes strategic decisions based on evaluator feedback: refine the current direction if scores are trending well, or pivot entirely if the approach isn't working
- Uses version control (git) to checkpoint work

**What it produces:**
- Working code committed in logical chunks
- Sprint contract proposals (what will be built, how success will be verified)
- Self-evaluation notes before QA handoff

### 3. Evaluator (The Critic)

**Purpose:** Test the running application like a real user would and grade it against criteria that encode both objective correctness and subjective quality.

**Key behaviors:**
- **Interacts with the live application** (via Playwright MCP or equivalent) — navigates pages, clicks buttons, fills forms, screenshots results
- Grades against predefined criteria with hard thresholds — any criterion below threshold = sprint fails
- Provides specific, actionable feedback with file/line references when possible
- Resists the urge to be lenient — explicitly prompted for skepticism
- Calibrated with few-shot examples of good/bad scores to prevent drift

**What it produces:**
- Per-criterion scores with detailed justifications
- Bug reports with reproduction steps and code references
- Pass/fail verdict per sprint or per evaluation round
- Aggregate quality trends across iterations

**Critical principle:** Out of the box, Claude is a poor QA agent. Tuning the evaluator is an iterative process — read the evaluator's logs, find examples where its judgment diverges from yours, update its prompt to solve for those. It takes several rounds before the evaluator grades reasonably.

---

## Communication Architecture

Agents communicate through **files**, not conversation threading:

```
planner/
  spec.md                    # Full product specification
  design-direction.md        # Visual/UX design language

contracts/
  sprint-{N}-proposal.md     # Generator's proposal for sprint N
  sprint-{N}-agreement.md    # Evaluator's review + agreed contract
  
evaluations/
  sprint-{N}-eval.md         # Evaluator's grading + feedback
  sprint-{N}-bugs.md         # Specific bugs found
  
telemetry/
  run-manifest.json          # Overall run metadata
  sprint-{N}-metrics.json    # Per-sprint timing, cost, scores
  quality-trend.json         # Score progression across sprints
```

One agent writes a file; another reads it and responds either within that file or with a new file. This provides:
- Full audit trail of all agent decisions
- Human-readable state at any point in the run
- Clean handoff boundaries between roles
- Resumability if a run is interrupted

---

## Grading Criteria Framework

The article establishes two sets of criteria. This framework should support defining **custom criteria per project type**, but these are the proven defaults:

### For Frontend / Design Work

| Criterion | Weight | What it measures |
|-----------|--------|------------------|
| **Design Quality** | HIGH | Does it feel like a coherent whole? Colors, typography, layout, imagery combine into a distinct mood and identity. |
| **Originality** | HIGH | Evidence of custom decisions vs. template layouts, library defaults, AI-generated patterns. Penalize "AI slop" (purple gradients over white cards). |
| **Craft** | MEDIUM | Technical execution: typography hierarchy, spacing consistency, color harmony, contrast ratios. Competence check. |
| **Functionality** | MEDIUM | Can users understand the interface, find actions, complete tasks without guessing? |

### For Full-Stack Applications

| Criterion | Weight | What it measures |
|-----------|--------|------------------|
| **Product Depth** | HIGH | Are features fully realized or stubbed out? Do interactions have real depth? |
| **Functionality** | HIGH | Does the application actually work when a real user clicks through it? |
| **Visual Design** | MEDIUM | Consistent visual identity, appropriate use of space, professional polish. |
| **Code Quality** | MEDIUM | Clean architecture, appropriate abstractions, maintainability. |

### Calibration Process

1. Write initial criteria with descriptive language (this language directly steers the generator)
2. Run the evaluator on known-good and known-bad examples
3. Compare evaluator scores against your own human judgment
4. Where they diverge, update the prompt with few-shot examples showing correct scoring
5. Repeat until the evaluator's taste matches yours

**Insight from the article:** The wording of criteria matters more than you'd expect. Phrases like "museum quality" pushed designs toward a particular aesthetic convergence. The criteria aren't just measurement — they're steering.

---

## What a WORKPLAN.md Would Show

A Harnessa WORKPLAN.md is the operational plan for a single harness run. It bridges the gap between "here's what we want to build" and "here's exactly how the three agents will coordinate."

```markdown
# WORKPLAN: [Project Name]

## Prompt
> [The 1-4 sentence human prompt that kicks off the run]

## Planner Output Summary
- Features planned: [N]
- Sprints defined: [N]  
- AI features identified: [list]
- Design direction: [brief description]

## Sprint Schedule

### Sprint 1: [Feature Name]
- **Contract status:** [proposed | under review | agreed]
- **Generator status:** [not started | in progress | complete | handed to QA]
- **Evaluator status:** [not started | reviewing | passed | failed]
- **Scores:** Design [X/10] | Originality [X/10] | Craft [X/10] | Function [X/10]
- **Iteration:** [1 of max N]
- **Bugs found:** [N] | **Bugs fixed:** [N]

### Sprint 2: ...
[repeat]

## Quality Trend
| Sprint | Avg Score | Pass/Fail | Iterations | Duration | Cost |
|--------|-----------|-----------|------------|----------|------|
| 1      |           |           |            |          |      |
| 2      |           |           |            |          |      |

## Run Totals
- **Total duration:** 
- **Total cost:** 
- **Total iterations (including QA loops):**
- **Final aggregate score:**
```

---

## Testing Success: How We Know It's Working

This is where Harnessa diverges from the article into a rigorous testing and telemetry framework. The article proves the concept works; Harnessa proves it *to you, every time*.

### Level 1: Harness Mechanics (Does the framework run?)

| Test | Method | Pass Criteria |
|------|--------|---------------|
| Planner produces valid spec | Schema validation of spec.md | All required sections present, >3 features defined |
| Generator receives spec | File existence check | Generator reads spec.md before generating code |
| Sprint contracts are negotiated | File exchange verification | Both proposal and agreement files exist per sprint |
| Evaluator receives working app | Process/port check | Application is running and accessible before eval begins |
| Evaluator produces scores | Schema validation of eval output | All criteria scored, justifications non-empty |
| Feedback loop completes | File flow verification | Generator reads eval feedback and produces updated code |
| Run completes end-to-end | Exit code + manifest check | run-manifest.json written with status: complete |

### Level 2: Quality Improvement (Does the adversarial loop help?)

| Test | Method | Pass Criteria |
|------|--------|---------------|
| Scores improve over iterations | Trend analysis on quality-trend.json | Average score at iteration N > iteration 1 |
| Evaluator catches real bugs | Human spot-check of eval bugs | >50% of evaluator-reported bugs are genuine |
| Generator fixes flagged issues | Diff analysis pre/post eval | Code changes address specific eval feedback items |
| Harness > Solo agent | A/B comparison run | Harness output scores higher on same criteria by same evaluator |

### Level 3: Evaluator Calibration (Is the critic trustworthy?)

| Test | Method | Pass Criteria |
|------|--------|---------------|
| Evaluator isn't rubber-stamping | Score distribution analysis | Mean score < 8/10; at least 20% of sprints fail first attempt |
| Evaluator finds bugs humans find | Golden-set testing | Present known-buggy app; evaluator identifies >70% of planted bugs |
| Evaluator doesn't hallucinate bugs | False positive rate | <20% of reported bugs are non-issues |
| Evaluator is consistent | Repeat scoring | Same app scored twice produces scores within ±1 per criterion |
| Evaluator aligns with human taste | Preference correlation | On ranked outputs, evaluator ordering matches human ordering >70% |

### Level 4: Economic Viability (Is the cost worth it?)

| Test | Method | Pass Criteria |
|------|--------|---------------|
| Quality/cost ratio improves | Track across runs | Score-per-dollar trending upward over framework versions |
| Duration is predictable | Variance analysis | Run duration within 2x of estimate for given project type |
| Token waste is minimized | Token breakdown per agent | No agent uses >60% of total tokens; evaluator < 15% |

---

## Telemetry Specification

Every harness run produces structured telemetry. This is non-negotiable — the framework is as much about observability as it is about orchestration.

### Run Manifest (`telemetry/run-manifest.json`)

```json
{
  "run_id": "uuid",
  "started_at": "ISO-8601",
  "completed_at": "ISO-8601",
  "prompt": "original human prompt",
  "model": "claude-opus-4.6",
  "harness_version": "0.1.0",
  "status": "complete | failed | interrupted",
  "agents": {
    "planner": {
      "duration_seconds": 282,
      "tokens_in": 12400,
      "tokens_out": 8900,
      "cost_usd": 0.46
    },
    "generator": {
      "duration_seconds": 7620,
      "tokens_in": 340000,
      "tokens_out": 180000,
      "cost_usd": 71.08,
      "sprints_completed": 5,
      "iterations_total": 8
    },
    "evaluator": {
      "duration_seconds": 528,
      "tokens_in": 45000,
      "tokens_out": 22000,
      "cost_usd": 3.24,
      "bugs_found": 12,
      "bugs_confirmed_fixed": 9,
      "pass_rate": 0.6
    }
  },
  "quality_scores": {
    "final": { "design": 7, "originality": 6, "craft": 8, "functionality": 7 },
    "trend": [
      { "iteration": 1, "avg": 5.2 },
      { "iteration": 2, "avg": 6.8 },
      { "iteration": 3, "avg": 7.0 }
    ]
  },
  "total_cost_usd": 124.70,
  "total_duration_seconds": 13800
}
```

### Per-Sprint Metrics (`telemetry/sprint-{N}-metrics.json`)

```json
{
  "sprint": 1,
  "feature": "Project Dashboard & Management",
  "contract_negotiation_rounds": 2,
  "build_duration_seconds": 1800,
  "eval_duration_seconds": 120,
  "iteration": 1,
  "scores": {
    "product_depth": 6,
    "functionality": 4,
    "visual_design": 7,
    "code_quality": 8
  },
  "verdict": "fail",
  "bugs": [
    {
      "id": "bug-001",
      "severity": "high",
      "description": "Delete button removes project without confirmation dialog",
      "file": "src/components/Dashboard.tsx",
      "line": 142,
      "status": "fixed"
    }
  ],
  "generator_tokens": { "in": 68000, "out": 34000 },
  "evaluator_tokens": { "in": 9000, "out": 4400 }
}
```

### Quality Trend (`telemetry/quality-trend.json`)

Tracks score evolution across all iterations for regression detection and improvement visualization.

---

## Key Principles (Carry These Forward)

### From the Article

1. **"Find the simplest solution possible, and only increase complexity when needed."** — Every harness component encodes an assumption about what the model can't do on its own. Stress-test those assumptions. They go stale as models improve.

2. **Re-examine the harness when a new model lands.** Strip away pieces that are no longer load-bearing. Add new pieces to achieve greater capability that wasn't possible before. The evaluator is not a fixed yes/no decision — it's worth the cost when the task sits beyond what the current model does reliably solo.

3. **Criteria wording directly steers output.** The grading criteria aren't just measurement — they shape what the generator produces. Choose words with intent.

4. **The space of interesting harness combinations doesn't shrink as models improve — it moves.** The interesting work is to keep finding the next novel combination.

5. **Sprint contracts bridge spec and implementation.** The spec is intentionally high-level. Contracts negotiate what "done" looks like per chunk, preventing the generator from building the wrong thing without over-specifying implementation early.

### For This Project Specifically

6. **Telemetry is first-class.** Every claim about quality improvement must be backed by data. The framework without telemetry is just opinion.

7. **The evaluator is the hardest agent to build well.** Plan to spend most of the calibration time here. Read its logs. Find where its judgment diverges from yours. Fix the prompt. Repeat.

8. **Discernment over approval.** The evaluator's default posture must be skepticism. Configure it to fail generously at first and tighten over time, rather than starting lenient and hoping to add rigor later.

9. **Communication via files, not memory.** Every decision, score, bug, and contract must be written to disk. This enables audit, resumability, and human oversight at any point.

10. **A/B everything.** The solo agent run is always the control group. If the harness can't demonstrably beat it, the harness is overhead.

---

## What Success Looks Like

### Minimum Viable Success
- A harness that takes a 1-4 sentence prompt and produces a working multi-feature application
- The evaluator catches bugs that the generator missed (verified by human spot-check)
- Quality scores trend upward across iterations within a run
- Telemetry captures the full story of every run

### Strong Success  
- Harness output is **categorically better** than solo agent output on the same prompt (not incrementally — in a different tier)
- The evaluator's taste is calibrated enough that a human reviewing its scores says "yeah, that's about right" >70% of the time
- The framework is reusable across project types (frontend, full-stack, CLI tools) with criteria swapped
- Cost and duration are predictable enough to plan around

### Exceptional Success
- The adversarial loop produces **creative leaps** — outputs that surprise even the human operator (like the article's 3D museum gallery on iteration 10)
- The evaluator becomes a genuine bottleneck that the generator has to work hard to satisfy
- The telemetry reveals patterns about which types of feedback produce the largest quality jumps
- Other developers can use the framework on their own projects with minimal configuration

---

## Repo Structure (Planned)

```
harnessa/
├── PROJECT_SPEC.md            # This file — the project bible
├── WORKPLAN.md                # Active run workplan (generated per run)
├── README.md                  # User-facing quick start
├── src/
│   ├── orchestrator/          # Run coordinator — launches agents, manages lifecycle
│   ├── planner/               # Planner agent config, prompts, output handling
│   ├── generator/             # Generator agent config, prompts, sprint management
│   ├── evaluator/             # Evaluator agent config, criteria, calibration data
│   ├── contracts/             # Sprint contract negotiation logic
│   ├── telemetry/             # Metrics collection, trend analysis, reporting
│   └── criteria/              # Pluggable grading criteria definitions
├── templates/
│   ├── criteria/              # Default criteria sets (frontend, fullstack, CLI)
│   └── prompts/               # Agent prompt templates
├── telemetry/                 # Output directory for run telemetry data
├── runs/                      # Output directory for agent communication files
│   └── {run-id}/
│       ├── planner/
│       ├── contracts/
│       ├── evaluations/
│       └── telemetry/
└── tests/
    ├── harness/               # Framework mechanics tests
    ├── calibration/           # Evaluator calibration golden sets
    └── integration/           # End-to-end run tests
```

---

## Glossary

| Term | Definition |
|------|------------|
| **Harness** | The orchestration framework surrounding the model — prompts, agent topology, communication patterns, and lifecycle management |
| **GAN-inspired** | Architecture where a generator and evaluator (discriminator) create adversarial tension that drives quality upward |
| **Sprint contract** | A negotiated agreement between Generator and Evaluator defining what "done" looks like for a chunk of work, established before implementation begins |
| **Context anxiety** | Model behavior where it prematurely wraps up work as it approaches perceived context limits |
| **Context reset** | Clearing the context window entirely and starting a fresh agent with a structured handoff artifact (vs. compaction, which summarizes in-place) |
| **Compaction** | Summarizing earlier conversation in-place so the same agent can continue on shortened history |
| **AI slop** | Telltale generic patterns in AI output — purple gradients, white cards, safe template layouts, stock components |
| **Calibration** | The iterative process of aligning the evaluator's judgments with human preferences through prompt tuning and few-shot examples |
| **Load-bearing** | A harness component that actively contributes to output quality; components should be re-evaluated when models improve |
| **Telemetry** | Structured data capturing timing, cost, scores, bugs, and decisions across every harness run |

---

*This document is the source of truth for the Harnessa project. Any new session should read this file first to understand the project's goals, architecture, principles, and success criteria.*

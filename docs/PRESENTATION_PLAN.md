# Plan: PowerPoint Presentation — The Adversarial Architecture

## Problem
Create a professional PowerPoint deck for a 15-minute talk to engineering leadership.
Focus: theory (Anthropic article) → implementation (multi-agent architecture) → evidence (experimental data) → industry landscape.
Harnessa is the test harness used to verify results — not the focus of the talk.
Includes demo section and showcase app story.

## Approach
1. Design a slide-by-slide content doc (this plan) capturing every slide's title, content, speaker notes, and visual direction
2. Build the deck programmatically using `python-pptx` with a clean, professional design
3. Output: `presentation/harnessa-deck.pptx`

## Todos
- `design-doc` — Write the complete slide-by-slide design document
- `build-deck` — Implement the PowerPoint using python-pptx
- `verify-output` — Open/validate the generated file

---

## Slide-by-Slide Design Document

### Design System
- **Color palette:** Dark navy (#1B2A4A) primary, teal accent (#2EC4B6), white text, light gray (#F0F0F0) backgrounds for data slides
- **Semantic colors:**
  - Solo/fail/danger: Muted coral (#E07A5F) — used for solo scores, FAIL badges, negative deltas
  - Trio/pass/success: Teal (#2EC4B6) — used for trio scores, PASS badges, positive deltas
  - Neutral/tie: Medium gray (#8B8B8B) — ties, inconclusive verdicts
  - Highlight/emphasis: Warm amber (#F2CC8F) — key numbers, delta callouts, "the headline"
  - Background dark: Navy (#1B2A4A) — title slides, quote slides, section transitions
  - Background light: Off-white (#F8F8F8) — data slides, tables, diagrams
- **Typography:** Clean sans-serif (Calibri or Segoe UI), large titles (32pt), body (18-20pt), data (14-16pt)
- **Slide type templates:**
  - **Title/Section slides:** Dark navy background, centered title (36pt white), subtitle (20pt teal). Used for: slides 1, section transitions.
  - **Data comparison slides:** Light background, left-aligned title, data visualization takes 70% of space, key insight callout in amber below. Used for: slides 10-14.
  - **Diagram slides:** Dark or light background depending on density. Diagram is the hero (80% of space). Minimal text below. Used for: slides 5, 6, 15.
  - **Text/insight slides:** Left-aligned title, 3 items max, generous line spacing (1.5x). Each item is bold lead + supporting sentence. Used for: slides 2, 3, 17, 19.
  - **Quote slides:** Dark background, large centered quote (24pt, italic, teal), attribution below (14pt, white). Used for: slides 22 (closing).
  - **Demo slides:** Dark background simulating terminal, monospace font for code, light text. Used for: slide 20.
- **Layout:** Left-aligned titles, generous whitespace, one idea per slide
- **Data viz:** Tables use semantic colors (solo=coral row bg, trio=teal row bg). No table borders — use alternating row colors and whitespace. Bar fills proportional to scores.
- **Text density rule:** Max 40 words of body text per slide (excluding tables/code). If it needs more, split the slide.
- **Projector safety:** All text on light backgrounds must be navy (#1B2A4A), never gray. Teal accent on light backgrounds should be darkened to (#229E92) for projector visibility.
- **Transitions:** Cut only (no fades, dissolves, or animations between slides). Within slides, elements can have a simple fade-in for build reveals. No fly-ins, bounces, or spins.
- **Code/terminal font:** JetBrains Mono or Consolas (never Courier New). 16pt minimum for readability on shared screens.
- **Slide count target:** 22 slides + appendix for 15 minutes (~40 sec/slide average). Pacing note: data slides (10-14) and demo (20) will need ~60 sec each; context slides (15-16) should be ~30 sec each to compensate. Rehearse to verify.

---

### SECTION 1: THE PROBLEM (Slides 1-4)

#### Slide 1 — Title Slide
**Title:** The Adversarial Architecture
**Subtitle:** Why the best AI output comes from agents that disagree
**Footer:** Matthew Williams — Senior SWE (MSFT) · 2026-04-01 · Based on Anthropic Labs research by Prithvi Rajasekaran
**Visual:** Clean, dark navy background. Minimal. Project logo or abstract geometric pattern suggesting adversarial tension.

#### Slide 2 — The Ceiling
**Title:** AI Agents Hit Two Walls
**Content:**
- **Wall 1: Context degradation** — As the context window fills, coherence drops. Some models exhibit "context anxiety," prematurely wrapping up work.
- **Wall 2: Self-evaluation failure** — When asked to judge their own work, agents reliably praise it — even when quality is obviously mediocre.
- Pull quote (bottom): *"I watched it identify legitimate issues, then talk itself into deciding they weren't a big deal and approve the work anyway."* — Anthropic Labs
**Visual:** Two-panel layout — but NOT symmetric. Left panel is larger (60%), showing a simple descending staircase graphic (3 steps going down, labeled "Attempt 1 → Attempt 5 → Attempt N") representing declining quality. Right panel (40%) shows a speech bubble: "This looks great! Ship it." over a red error trace. The Anthropic quote sits in a dark strip at the bottom, full-width, smaller type. Avoid: two equal-sized boxes.
**Speaker Notes:** This is the starting point. Anthropic published research in 2025 showing these two failure modes are persistent across models. The first is well-known — context window limits. The second is more insidious — agents are bad at self-criticism. This matters because it means single-agent coding has a quality ceiling that more tokens can't break through.

#### Slide 3 — The Insight
**Title:** What if the Builder and the Critic Were Different Agents?
**Content:**
- Inspired by GANs (Generative Adversarial Networks) from ML
- Generator builds → Evaluator tears it apart → Feedback drives improvement
- Separation doesn't eliminate leniency — but makes it *tractable* to fix
- Add a Planner to ensure they build the right thing
**Visual:** Simple 3-box diagram: Planner → Generator ↔ Evaluator with arrows. The ↔ arrow is thick/emphasized to show the adversarial feedback loop.
**Speaker Notes:** The insight from Anthropic's Prithvi Rajasekaran: tuning a standalone evaluator to be skeptical is far more tractable than making a generator critical of its own work. This maps to GANs in ML — generator produces, discriminator judges, adversarial tension drives both higher. We add a Planner to expand scope and provide structure.

#### Slide 4 — Anthropic's Evidence
**Title:** The Article That Started This
**Content:**

| Approach | Duration | Cost | Result |
|----------|----------|------|--------|
| Solo agent (Opus 4.5) | 20 min | $9 | Core feature broken, poor layout |
| 3-agent harness (Opus 4.5) | 6 hr | $200 | 16-feature app, working core, polished UI |
| Simplified harness (Opus 4.6) | 3 hr 50 min | $125 | Full DAW, 3 QA rounds |

- Not incrementally better — **categorically different**
- Source: "Harness Design for Long-Running Apps" — Anthropic Labs, 2025
**Visual:** Comparison table with the solo row in red/muted and the harness rows in green/bright. Bold the key phrase "categorically different."
**Speaker Notes:** Anthropic's own experiments showed the gap isn't marginal — it's a different tier of output entirely. But they published the concept, not a reusable framework. We wanted to build it, test it independently, and prove whether the claims hold.

---

### SECTION 2: THE ARCHITECTURE (Slides 5-9)

#### Slide 5 — Three Agents, One Pipeline
**Title:** The Architecture — Three Agents, One Pipeline
**Content:**
```
┌──────────────────────────────────────────────┐
│              ORCHESTRATOR                     │
│                                               │
│  ┌────────┐   ┌──────────┐   ┌────────────┐  │
│  │Planner │──▶│Generator │◀─▶│ Evaluator  │  │
│  │        │   │          │   │            │  │
│  │Expands │   │Builds    │   │Tests live  │  │
│  │prompt  │   │features  │   │app, grades │  │
│  │into    │   │in        │   │against     │  │
│  │spec    │   │sprints   │   │criteria    │  │
│  └────────┘   └──────────┘   └────────────┘  │
│                                               │
│  ┌───────────────────────────────────────┐    │
│  │         Telemetry Layer               │    │
│  │ Timing · Cost · Scores · Bugs · Trends│    │
│  └───────────────────────────────────────┘    │
└──────────────────────────────────────────────┘
```
- Planner: 1-4 sentence prompt → full product spec (WHAT, not HOW)
- Generator: Implements spec, negotiates sprint contracts, iterates on feedback
- Evaluator: Grades against criteria, files specific bugs, resists leniency
- Telemetry: Every run produces structured data — claims backed by evidence
**Visual:** NOT a rendered ASCII diagram. Build a real diagram with 3 colored rounded rectangles (Planner=blue-gray, Generator=teal, Evaluator=coral) connected by directional arrows. The Generator↔Evaluator arrow should be thicker and have a circular loop icon. Telemetry bar runs full-width at bottom in a darker shade. Each agent box has a one-line role description inside. White text on colored backgrounds. No drop shadows, no gradients on boxes — flat, confident colors.
**Speaker Notes:** This is the core. The Planner takes a brief human prompt and expands it into an ambitious spec — focusing on what to build, not how. The Generator implements it in sprints. The Evaluator tests the live application, grades against criteria, and provides specific, actionable feedback. If it fails, the feedback flows back to the Generator for the next iteration. Everything is tracked by telemetry.

#### Slide 6 — Isolation: Keeping Agents Honest
**Title:** How We Prevent Gaming
**Content:**
- **Generator worktree:** Cannot see hidden acceptance tests (`_eval/`)
  - Prevents Goodhart's Law — if generator could see tests, it would optimize for passing them, not for quality
- **Evaluator worktree:** Full access including hidden tests and fixtures
- **Result:** 11 runs, 0 boundary violations
**Visual:** NOT a symmetric two-panel. Left 70%: a file tree diagram (dark background, monospace font) showing the Generator's view with `_eval/` grayed out and struck through. Right 30%: the Evaluator's view with `_eval/` in green/visible. A vertical dividing line labeled "BOUNDARY" with a lock icon. The asymmetry emphasizes that the Generator's view is deliberately limited.
**Speaker Notes:** This is a Goodhart mitigation — "when a measure becomes a target, it ceases to be a good measure." If the generator could see the acceptance tests, it would optimize for passing them rather than writing genuinely good code. We give it a separate worktree that excludes the hidden tests. The evaluator gets the full picture. In all 11 experimental runs, this boundary was never breached.

#### Slide 7 — The Evaluator: Calibrated Skepticism
**Title:** Building a Critic That Actually Criticizes
**Content:**
- **The Karpathy problem:**
  > *"Used an LLM to improve my argument over 4 hours. Feeling great, so convincing! Fun idea — let's ask it to argue the opposite. LLM demolishes the entire argument. lol"* — Andrej Karpathy
  
  LLMs will argue any direction convincingly. The sycophancy isn't a bug — it's the default. A separate evaluator with hard rules is how you counter it.
- **Anti-people-pleasing rules (hard-coded, added after calibration failures):**
  - Any test fails → functionality ≤ 4
  - No new tests for new functionality → test_coverage ≤ 4
  - Implementation is stub → product_depth ≤ 3
- **Rubber-stamp detection:** All scores ≥ 7 flagged as suspicious
- **Still imperfect:** Before these rules were added, the TS benchmark evaluator gave func=8 with 50% tests failing — sycophancy is hard to kill even with guardrails
**Visual:** The Karpathy quote in a callout box at top (styled conversationally, like a tweet). Below: a concrete "report card" visual showing an actual evaluator output snippet (styled as a dark code block): `{ "functionality": 1, "verdict": "FAIL" }` → next iteration: `{ "functionality": 10, "verdict": "PASS" }`. The anti-people-pleasing rules in a sidebar with checkmark/X icons.
**Speaker Notes:** Andrej Karpathy captured this perfectly — LLMs will argue convincingly that your work is great, then argue equally convincingly that it's terrible. The sycophancy is the default mode. This is exactly why we need a separate evaluator with hard-coded rules, not just "be critical" in the prompt. Our first trio run failed because the evaluator output verbose praise instead of structured scores. We had to add hard guardrails — if tests fail, functionality CANNOT score above 4. We detect rubber-stamping. We calibrate with few-shot examples. It's still not perfect — we saw the evaluator give func=8 with 50% test failures — but it's dramatically better than self-evaluation. The Karpathy lesson: always ask the LLM to argue the opposite direction. That's literally what our evaluator does.

#### Slide 8 — Sprint Contracts
**Title:** Agreeing on "Done" Before Writing Code
**Content:**
- Before each sprint, Generator proposes what it will build
- Evaluator reviews and may add/remove acceptance criteria
- Max 2 negotiation rounds → agreed contract
- **Why:** Bridges the gap between high-level spec and testable implementation
- **Example:** Sprint 3 of the article's game maker had **27 acceptance criteria**

**Visual:** A two-column layout: Generator's proposal on the left, Evaluator's review on the right, with arrows showing the negotiation flow. A handshake icon in the middle.
**Speaker Notes:** Sprint contracts prevent scope misinterpretation. The Planner's spec is intentionally high-level — we want WHAT, not HOW. But the Generator needs to know exactly what "done" looks like before coding. So it proposes a contract, the Evaluator reviews it, and they agree. In the Anthropic article, Sprint 3 of the game maker had 27 individual acceptance criteria that the evaluator tested against.

#### Slide 9 — Communication & Telemetry
**Title:** Files on Disk, Not Chat History
**Content:**
- Agents communicate through files, not conversation threading
  - Copilot skill: `harnessa-spec.md` / `harnessa-gen-report.md` / `harnessa-eval.md` (flat files)
  - Benchmark harness: structured directories — `planner/spec.md`, `contracts/`, `evaluations/`, `telemetry/`
  - Same pattern, two implementations: skill is lightweight, harness adds contracts and telemetry
- **Benefits:** Full audit trail · Human-readable state · Clean handoffs · Resumability
- **Every write is atomic** (crash-safe)
**Visual:** A file tree showing the communication artifacts, with arrows showing the flow between agents.
**Speaker Notes:** All agent communication is through files on disk — not conversation threading. This gives us a full audit trail, human-readable state at every step, and crash safety through atomic writes. The telemetry layer captures everything: timing, scores, bugs, quality trends. The Copilot skill uses flat files (harnessa-spec.md, etc.) for simplicity; the benchmark harness adds structured directories with contracts and detailed telemetry.

---

### SECTION 3: THE EVIDENCE & LANDSCAPE (Slides 10-17)

#### Slide 10 — Experiment Design
**Title:** 5 Benchmarks, 2 Modes, Real Code
**Content:**

| # | Benchmark | Language | Size | Challenge |
|---|-----------|----------|------|-----------|
| 1 | small-bugfix-python | Python | 500 LOC | Fix ± sign bug in arg parser |
| 2 | small-feature-typescript | TypeScript | 800 LOC | Implement retry with backoff |
| 3 | small-bugfix-go | Go | 600 LOC | Fix connection pool race condition |
| 4 | medium-feature-python | Python | 1700 LOC | Add tags to FastAPI TODO app |
| 5 | medium-feature-fullstack | React+Express | 3000 LOC | Real-time notifications (WebSocket) |

- Same model for both modes (claude-sonnet-4 via Copilot CLI)
- Same prompt, same tools, same evaluation criteria
- Hidden `_eval/` acceptance tests + expected output fixtures
- Solo gets one shot; Trio gets feedback loop
**Visual:** Table with language icons. Benchmark sizes shown as a horizontal bar chart.
**Speaker Notes:** We built 5 real benchmarks spanning three languages — Python, TypeScript, Go — and two complexity levels. Each has seeded bugs or missing features, visible tests, AND hidden acceptance tests the generator can't see. Both modes get the exact same model, prompt, and tools. The only variable is the architecture: solo (one shot) vs trio (planner + generator + evaluator feedback loop).

#### Slide 11 — The Headline Result
**Title:** Solo FAIL → Trio PASS
**Content:**
- **Setup:** *We ran the same task — build a real-time notification system — through both architectures. Same model, same prompt, same tools. N=11 total runs across all benchmarks — small sample, but the fullstack result was categorical, not marginal.*
- **Medium Fullstack Benchmark (WebSocket Notifications)**

| | Solo | Trio |
|--|------|------|
| Verdict | **FAIL** | **PASS** |
| Functionality score | 4 / 10 | 8 / 10 |
| Average score | 6.25 | 8.0 |
| Duration | 383s | 619s (1.6x) |

- Solo: WebSocket notification system **broken** — non-functional core feature
- Trio: WebSocket notifications **working** — correct implementation on first attempt
- The planner's 84-second spec gave the generator enough structure to get it right
- **This is the categorical difference the article predicted**
**Visual:** Large before/after comparison. Solo in red/dim, Trio in green/bright. Big bold "+4" on the functionality score. Perhaps a simple pass/fail badge graphic.
**Speaker Notes:** This is the headline. The solo agent produced a broken notification system — functionality score of 4. The trio agent, with an 84-second planning phase, produced working WebSocket notifications on the FIRST attempt — functionality 8. This is not an incremental improvement. The solo output literally doesn't work. The trio output does. This is the categorical difference the Anthropic article described.

#### Slide 12 — The Full Scorecard
**Title:** Trio Won the Tests That Mattered
**Content:**

| Benchmark | Solo | Trio | Winner | Key Insight |
|-----------|------|------|--------|-------------|
| Python bugfix | PASS 8.5 | PASS 9.5 | **Trio** | Evaluator caught issue, gen fixed it |
| TS feature | PASS 8.5 | PASS 8.5 | Tie | Simple task — trio overhead wasted |
| Go race | FAIL 6.75 | FAIL 7.25 | Tie | Too hard for both — race condition |
| Python tags | PASS 8.5 | PASS 8.0 | **Solo** ↑ | Feedback loop: 3.25 → 8.0 (but solo's lenient evaluator scored higher) |
| **Fullstack** | **FAIL 6.25** | **PASS 8.0** | **Trio** | **Categorical difference** |

**Aggregates:**
- Mean functionality: Solo **4.8** → Trio **7.6** (+2.8)
- Verdicts: Solo 3/5 PASS → Trio 4/5 PASS
- Duration: Trio ~1.8x slower (wall-clock)
- Python tags caveat: Solo scored higher numerically, but solo's evaluator was likely lenient (self-evaluation bias) — the trio's harsh evaluator + feedback loop is the intended pattern
**Visual:** NOT a flat table — use a "scorecard" layout. Each benchmark is a horizontal row with: a colored status pill (green PASS / red FAIL), a score bar (filled proportional to score), and the winner tag. The fullstack row is visually enlarged — 2x height, bolder border — making it the unmistakable focal point. Aggregates below in large bold numerals: "4.8 → 7.6" with an upward arrow. No generic table borders — use whitespace to separate rows.
**Speaker Notes:** The full scorecard: trio won decisively on 2 benchmarks, Solo scored higher on Python tags (likely evaluator leniency), and they tied on 2 (one because both failed the hard Go race condition). The mean functionality improvement is +2.8 points — from 4.8 to 7.6. Trio is about 1.8x slower in wall-clock time, but when the alternative is shipping broken code, that's a trade worth making. Notice the pattern: on simple tasks (TypeScript feature), trio adds overhead with no benefit. On complex tasks (fullstack), it's the difference between failure and success. The Python tags result is interesting — the solo evaluator gave 8.5 but may have been lenient, while the trio evaluator started at 3.25 and forced the generator to improve.

#### Slide 13 — Quality Improves Across Iterations
**Title:** The Feedback Loop Works
**Content:**

| Benchmark | Iteration 1 | Iteration 2 | Iteration 3 | Trend |
|-----------|------------|------------|------------|-------|
| Python bugfix | func=1, avg=5.0 (FAIL) | avg 9.5 (PASS) | — | ↑ +4.5 |
| Go race | avg 2.75 | avg 6.5 | avg 7.25 | ↑ +4.5 (plateau) |
| Python tags | avg 3.25 | avg 8.0 (PASS) | — | ↑ +4.75 |

- Evaluator is **harsh** on iteration 1 (avg ~3.7 across multi-iteration runs)
- Generator **dramatically improves** after feedback (avg 8.2 final)
- Go benchmark shows plateauing — 3 iterations wasn't enough for the race condition (ended at 7.25 avg but still FAIL verdict due to func=5)
- **This validates the article's core claim:** scores improve over iterations before plateauing
**Visual:** Real line chart with 3 lines on a dark background. X-axis: Iteration (1, 2, 3). Y-axis: Average Score (0-10). A horizontal dashed line at 7.0 labeled "PASS THRESHOLD." Python bugfix line jumps dramatically (5.0→9.5). Python tags line jumps (3.25→8.0). Go race line rises but FAIL verdict persists (2.75→6.5→7.25 — avg crosses 7 but func stays low). Lines are teal, white, and coral respectively. The pass threshold line creates a clear "above/below" visual story.
**Speaker Notes:** This is the adversarial loop in action. Look at the Python tags benchmark: iteration 1 averaged 3.25 — the evaluator was ruthless. After specific feedback, the generator improved to 8.0 on iteration 2. That's a nearly 5-point jump in one cycle. The Go race condition shows the limit — scores improved from 2.75 to 7.25 across 3 iterations, but it plateaued and never passed. Even the feedback loop can't solve problems beyond the model's capability.

#### Slide 14 — Article Claims: What We Validated
**Title:** 5 Confirmed, 2 Partial, 2 Inconclusive
**Content:**

| Claim | Verdict |
|-------|---------|
| Separating generator/evaluator = strong lever | ✅ Confirmed |
| Scores improve over iterations | ✅ Confirmed |
| Evaluator worth cost only beyond model's solo capability | ✅ Confirmed |
| Solo agents have self-evaluation failure | ✅ Confirmed |
| Claude is a poor QA agent out of the box | ✅ Confirmed |
| Harness output categorically different | ⚠️ Partial — only on complex tasks |
| Planner expands scope beyond solo | ⚠️ Partial — structure > scope |
| Criteria wording steers output | ❓ Inconclusive — needs ablation |
| Harness assumptions go stale with new models | ❓ Inconclusive — single model tested |

**Visual:** NOT a checklist table. Group visually by verdict: a green block of 5 confirmed claims (with ✅), an amber block of 2 partial (⚠️), a gray block of 2 inconclusive (❓). Each block has a subtle background color. Claims are left-aligned text, verdicts are right-aligned badges. The visual grouping tells the story instantly: "mostly confirmed, a few nuances." No table borders — use color blocks.
**Speaker Notes:** We set out to validate the Anthropic article's claims with independent data. Five of nine confirmed outright. The separation lever is real. Scores do improve over iterations. The evaluator is worth the cost, but only when the task is hard enough. Two claims partially confirmed — the categorical difference is real but only for complex tasks; the planner provides structure more than scope expansion. Two remain inconclusive — we need ablation studies and multi-model tests.

#### Slide 15 — The Landscape: Major Labs Are Converging
**Title:** We're Not Alone — This Is an Industry Pattern
**Content:**

| Who | What | Key Insight |
|-----|------|-------------|
| **Anthropic** (Mar 2026) | Harness Design article | Generator + Evaluator loop, GAN-inspired, planner expands scope |
| **Anthropic** Claude Code | Coordinator mode ships anti-sycophancy | *"Do not rubber-stamp weak work"* — baked into the product |
| **OpenAI** Symphony (2026) | Issue tracker → isolated agent workspaces | *"Works best in codebases that have adopted harness engineering"* — Symphony README |
| **Anthropic** C Compiler (Feb 2026) | 16 parallel agents, 100K-line compiler, $20K | *"The testing harness is more important than the agents"* — Anthropic Engineering Blog |
| **Anthropic** Research System (Jun 2025) | Lead agent + subagents | Multi-agent outperformed single-agent by **90.2%** — Anthropic Research |

- **The pattern:** Isolation, structured handoffs, specialized roles, evaluation as architecture
- **The convergence:** Both Anthropic and OpenAI independently arrived at multi-agent orchestration with harness engineering as the foundation
- **From paper to product:** Claude Code's own multi-agent coordinator uses prompt-based instructions like *"Do not rubber-stamp weak work"* — the same anti-sycophancy principle as our evaluator, now shipping in the flagship product
- **The quote:** *"Harness quality is becoming more important than raw model upgrades."*
**Visual:** A timeline or landscape diagram showing these developments converging. Each entry has a lab logo/icon and a one-liner. The quote at bottom is in a dark strip, full-width. NOT a bullet list — use a visual layout that shows convergence (arrows pointing inward, or a timeline with events clustering).
**Speaker Notes:** This is the slide that turns our experiment into an industry trend. Anthropic published the harness design research — and then shipped the same principles directly into Claude Code. Their coordinator mode manages worker agents with explicit anti-sycophancy instructions: "Do not rubber-stamp weak work," "You must understand findings before directing follow-up work." That's the same evaluator calibration we built into our test harness, now in the product itself. OpenAI built Symphony — a daemon that spawns isolated coding agents per issue — and their README explicitly says it works best with harness engineering. Anthropic's C compiler project used 16 parallel agents with the same core insight: the testing harness matters more than the agents themselves. Their research system showed multi-agent outperforms single-agent by 90%. We're all independently arriving at the same conclusion: the architecture around the model matters as much as the model itself.

#### Slide 16 — The Ecosystem: Community Is Building This
**Title:** The Community Is Already Here
**Content:**
- **GStack** (Garry Tan / YC) — The `/codex` "outside voice" skill sends your diff to OpenAI Codex for an **independent second opinion**. Cross-model analysis shows where Claude and Codex agree vs disagree. *This is the cross-model reconciler pattern as a production workflow.*
- **The broader ecosystem:** ClawCompany (productized harness), OpenHands (agent SDK), and builders combining Claude + Codex for independent evaluation
- **The principle:** Disagreements between models aren't noise — they're signal

**What this means:** The pattern is production-ready. GStack ships it as a daily workflow for YC companies.
**Visual:** A network/constellation diagram showing the adversarial pattern at center with connections to related projects. GStack gets a prominent callout box showing the `/review` → `/codex` → cross-model analysis flow.
**Speaker Notes:** The most concrete example is Garry Tan's GStack — the YC CEO's personal engineering toolchain. His /codex skill sends your code to a completely different AI for an independent review. When both Claude and Codex have looked at the same diff, you get a cross-model comparison: where do they agree? Where do they disagree? Disagreements are signal, not noise. This is exactly what our reconciler does — use the lower score when models disagree, flag the gap as a finding. Beyond GStack, ClawCompany productized the Anthropic harness paper, OpenHands provides an agent SDK, and builders everywhere are combining multiple AI models for independent evaluation. This isn't experimental anymore — it's becoming standard practice at the best companies.

#### Slide 17 — The Showcase: Monolith → Rebuild
**Title:** What the Evaluator Catches (That Solo Would Ship)
**Content:**
- **Task:** Build an AI Code Review Dashboard (React + Express + Tailwind)
- **Generator Iteration 1:** 1,206-line TypeScript monolith. CDN React via Babel. Zero tests. No component separation.
  - *A solo agent would have shipped this.*
- **Evaluator Iteration 1:** FAIL. "Unacceptable monolith architecture. Rebuild with proper separation, real components, tests."
- **Generator Iteration 2:** Complete rebuild. +4,335 / -2,973 lines across **36 files**. 6 real components, 4 pages, React Router, 7 tests.
- **Evaluator Iteration 2:** PASS ✅
- **The spec survived both iterations** — WHAT vs HOW separation worked
**Visual:** Two screenshots or code snippets side-by-side: the monolith (iter 1) vs the rebuild (iter 2). Or a dramatic diff stat: "+4,335 / -2,973 lines."
**Speaker Notes:** This is the showcase app — built by the trio pattern itself. The generator's first attempt was a 1,200-line monolith with CDN React. No tests. A solo agent would have shipped that and called it done. But the evaluator said "no" — and gave specific feedback about what needed to change. The second attempt was a complete rebuild: 36 files, real component architecture, router, tests. The diff was massive — over 4,000 lines added, nearly 3,000 removed. The evaluator forced a quality level the generator would never have reached alone.

---

### SECTION 4: IMPLICATIONS & DEMO (Slides 18-22)

#### Slide 18 — When to Use Trio vs Solo
**Title:** It's Not Always Worth It
**Content:**

| Use Trio ✅ | Skip It ❌ |
|-------------|------------|
| Features touching 3+ files | Single-line fixes |
| Unfamiliar bugs with unclear root cause | Formatting / linting |
| Architecture refactors | Dependency updates |
| Full-stack features | Tasks where you already know the fix |
| Anything where "does it actually work?" is uncertain | Simple, well-understood changes |

- **Rule of thumb:** If a solo agent would get it right on the first try, trio is overhead
- **Sweet spot:** Medium complexity (60-90 min tasks) where the model is at the edge of its capability
**Visual:** Two-column layout with checkmarks and X marks. Bold the "sweet spot" callout.
**Speaker Notes:** An important nuance: trio is NOT always better. On simple tasks — our TypeScript benchmark showed this — the trio added overhead with zero quality benefit. The sweet spot is medium-complexity tasks where the model is at the edge of what it can do solo. That's where the evaluator catches real issues and the feedback loop adds genuine value. Think of it like code review — you don't review a one-line typo fix.

#### Slide 19 — Key Learnings Beyond the Article
**Title:** What We Found That the Article Didn't Cover
**Content:**
1. **Planner's value is structure, not scope expansion** — The planner gives the generator a roadmap. On medium tasks, this enables correct first attempts. On small tasks, it's overhead.
2. **Evaluator leniency persists** — Even with anti-people-pleasing rules, the evaluator gave func=8 with 50% tests failing. Hard-coded guardrails help but don't fully solve. This is an honest limitation.
3. **Telemetry makes claims honest** — Every run produces structured JSON. No hand-waving about "it feels better." If you can't measure it, you can't trust it.
**Visual:** Three large statements, each with a single supporting sentence. Generous whitespace. No icons — let the words carry weight.
**Speaker Notes:** These are the things we discovered that go beyond the Anthropic article. The biggest surprise: the planner's value is structural guidance, not scope expansion. We're also honest about limitations — the evaluator leniency problem isn't fully solved. And we back everything with telemetry data, not vibes. [Verbal aside: JSON reliability was an engineering challenge — first trio run failed because the evaluator output prose instead of structured scores. Speed varies — trio was actually faster on one benchmark because the spec helped the generator focus.]

#### Slide 20 — Demo: How It Works
**Title:** One Command, Three Agents
**Content:**
```bash
copilot -p '/harnessa Fix the authentication bug' --allow-all
```

**What happens:**
1. 🧭 **Planner** reads code → writes `harnessa-spec.md` (problem, root cause, approach, acceptance criteria)
2. 🔨 **Generator** reads ONLY spec → implements fix → writes `harnessa-gen-report.md`
3. 🔍 **Evaluator** reads report + diff + hidden tests → grades → writes `harnessa-eval.md` (JSON with scores, verdict, bugs)

Context resets between each phase — each agent gets a clean slate. *(In the benchmark harness, the evaluator also has access to hidden `_eval/` acceptance tests for independent verification.)*
- Open source (MIT) · All benchmarks + telemetry included · Replay mode for re-evaluation
**Visual:** Single terminal command at top, large. Below: a 3-step horizontal flow with icons for each agent phase. Open source badges in footer.
**Fallback:** If live demo fails, have a pre-recorded terminal GIF or screenshot walkthrough of a completed run. Never depend on a live API call in a 15-minute slot.
**Speaker Notes:** [DEMO SECTION] This is where you can show a live demo or walk through a pre-recorded example. One command kicks off the trio. The system runs three phases with context resets — the evaluator never sees the generator's conversation, only its output. Each agent writes structured artifacts that the next agent reads. Everything is open source, all benchmarks are included, and there's a replay mode that lets you re-evaluate saved code with updated criteria without re-running the expensive generator step.

#### Slide 21 — So What? The Strategic Question
**Title:** When Should You Use This?
**Content:**
- **The pattern works.** The evidence says multi-agent architecture produces better output on complex tasks.
- **The cost is manageable.** ~1.8x wall-clock duration — not the 20x of the original Anthropic experiments. *(Note: token costs not measured — Copilot CLI doesn't expose them. Duration is the proxy.)*
- **Models punch above their weight.** *(Industry practice, not tested in our experiments.)* Use the expensive model where it matters (Opus for planning/evaluation) and the fast model where volume matters (Sonnet for building). Anthropic's own `/opusplan` mode does exactly this — Opus in plan mode, Sonnet for everything else. You get Opus-quality architecture with Sonnet-speed execution.
- **The decision framework:**
  - Solo agent gets it right first try → **don't add overhead**
  - Task is at the edge of model capability → **trio catches what solo misses**
  - Shipping broken code has real cost → **trio is insurance**
- **You don't even need a framework.** *(Conjecture — not tested in our experiments.)* The simplest version: a round-robin of models that each take a turn as planner, builder, and evaluator. Claude plans → GPT builds → Gemini evaluates → rotate. Each model's sycophancy biases and blind spots get counterbalanced by the others. One script, three API calls, immediate value.
- **The bigger question:** As models improve, which parts of the harness are load-bearing? The answer changes every model generation. The architecture that adapts wins.
**Visual:** Decision tree or flowchart at top: "Is the task complex?" → Yes → "Trio" / No → "Solo." Middle: a model-tiering diagram showing Opus (brain icon, $$) → Plan + Evaluate, Sonnet (lightning icon, $) → Build. Below: a circular diagram showing 3 models rotating through the 3 roles (Claude → GPT → Gemini, with arrows forming a cycle through Planner → Builder → Evaluator). The "bigger question" is visually separated at the bottom as a forward-looking statement.
**Speaker Notes:** This is the strategic takeaway for leadership. The trio pattern isn't always worth it — our data proves that on simple tasks it adds overhead with zero quality benefit. But on complex tasks, it's the difference between FAIL and PASS. And here's something that makes the economics work even better: you don't need the same model for every role. Anthropic ships an /opusplan mode — Opus handles the planning where deep reasoning matters, Sonnet handles the building where speed and volume matter. You get Opus-quality architecture at Sonnet speed and cost. The multi-agent pattern doesn't just improve quality — it lets you allocate model intelligence where it has the most leverage. For anyone who wants to try this tomorrow: just use a round-robin of different models. Have Claude write the spec, GPT implement it, Gemini evaluate it. Each model has different biases and blind spots, so cross-model evaluation gives you genuinely independent critique. The meta-lesson: every harness component encodes an assumption about model limitations, and those assumptions go stale with every model release. The team that continuously re-evaluates their architecture wins.

#### Slide 22 — The Takeaway
**Title:** The Quality Ceiling is Real. Architecture Breaks Through It.
**Content:**
- When your solo agent ships broken code, the problem isn't the model — **it's the architecture**
- Separating building from evaluation is a **proven, measurable lever**
- *"The space of interesting harness combinations doesn't shrink as models improve. It moves."* — Anthropic Labs

**Footer:** github.com/ridermw/harnessa · MIT License · Benchmarks + telemetry included
**Visual:** The Anthropic quote is large and centered, visually dominant. Title at top is bold. Footer has GitHub link and license — secondary, not the main message. Dark navy background, clean.
**Speaker Notes:** Leave them with this: the quality ceiling for single-agent AI coding is real, we measured it, and architectural patterns break through it. The trio pattern costs 1.8x more time but turns FAIL into PASS on complex tasks. And the Anthropic quote is the forward-looking message — this space evolves with every model generation. The teams that keep experimenting with harness design will build the best software. GitHub link in the footer for anyone who wants to try it or dig into the data.

---

### APPENDIX SLIDES (optional, for Q&A backup)

#### Slide A1 — Full Experiment Matrix
Full table of all 11 runs with run IDs, scores, durations, verdicts.

#### Slide A2 — Evaluator Reliability Metrics
Rubber-stamp detection, refusal-to-be-negative incidents, agreement rates.

#### Slide A3 — Difficulty Classification System
The too_easy / in_zone / too_hard / marginal classification system with all 5 benchmarks plotted.

#### Slide A4 — Grading Criteria Details
Full criteria from backend.yaml and fullstack.yaml with weights, thresholds, and few-shot examples.

#### Slide A5 — Architecture Diagram (Detailed)
Full system diagram with orchestrator, isolation manager, telemetry collector, reporting engine.

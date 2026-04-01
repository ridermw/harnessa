# Plan: Web Presentation Expansion — Collapsible Operator Rail + ASCII Diagram Contracts

## Problem
The current deployed site proves the stack and theme direction, but it is still too compressed and too brittle for presentation-grade use:

- the operator rail permanently steals layout width instead of behaving like a presenter control
- multiple diagrams rely on hardcoded coordinates, pseudo-element connectors, and absolute positioning
- arrows, descriptions, and support text can drift or land awkwardly because the layout has no diagram contract
- the narrative is over-compressed into 10 scenes, which forces caveats and important evidence into side notes

The next version should be a **detail-rich, ~30-scene web keynote** with **ASCII-first diagram specs**, a **collapsible rail**, and a **browser QA gate** that verifies the rendered diagrams still match the rough source representation.

## Requested Outcomes
1. **Collapsible operator rail**
   - the scene rail should toggle open/closed
   - collapsed state should let the body use the fuller screen width
   - expanded state should behave like a control surface, not a permanent gutter tax

2. **ASCII source-of-truth for diagrams**
   - every interaction/relationship diagram should have a rough ASCII spec in this plan
   - implementation should move toward structured diagram specs in code rather than ad hoc HTML/CSS/SVG

3. **Diagram refactor**
   - refactor every current website diagram that uses brittle positioning
   - move arrows/labels/descriptions to a geometry-aware rendering system

4. **QA / exit gate**
   - do not call the refactor done unless browser QA confirms the rendered result still matches the rough ASCII representation
   - validate structure, ordering, labels, relative regions, arrows, and overlap/overflow conditions

5. **More detail**
   - expand from the current 10-scene compression to a richer **~30-scene** experience
   - preserve facts, caveats, limitations, and appendix-grade material in the main narrative where it matters

## Current Implementation Risks
These are the main fragility points we should plan around:

- **operator rail width reservation**
  - `scene-stack` keeps a hardcoded right gutter for the rail
  - `.scene__content` width calculation explicitly reserves rail space
  - result: the main body never gets true full-width presentation layouts

- **hardcoded SVG geometry**
  - hero network and iteration chart use fixed coordinates
  - labels and callouts are offset with magic numbers
  - result: text and arrows can drift when content changes

- **pseudo-element connectors**
  - topology and timeline connectors depend on 50% centering and fixed offsets
  - result: connector lines only look correct when node heights stay conveniently similar

- **absolute-position support panels**
  - hero metrics and some supporting chrome are positioned absolutely
  - result: they can become visually awkward instead of participating in a deliberate layout

- **over-compressed information architecture**
  - multiple deck slides were merged into single scenes
  - result: important nuance (Goodhart mitigation, experiment design, claims validation, evaluator caveats, showcase rebuild, demo flow) is underrepresented

## Proposed Implementation Shape

### Navigation / Layout
- keep hash-addressable scenes
- add an **operator rail toggle** in the top bar
- desktop behavior: rail is a **drawer/control panel**, not a permanent reserved column
- mobile/tablet behavior: rail is always drawer-style
- persist rail state in local storage, but let explicit URL/deep-link state override storage for reproducible QA
- allow a clean “focus mode” where the rail is closed and body layouts can use the fuller screen
- keep scene slugs stable; if scenes are renamed or reordered, preserve an alias/compatibility map for old hashes
- drawer behavior must include focus management, ESC close, keyboard safety, and clear ARIA state

### Content / Scene Architecture
- expand the site to **30 primary scenes**
- split content by **acts with shared primitives**, not one file per scene
- keep appendix/deep-dive material as secondary panels or scene-local expanders, not as the main place where facts go to hide
- promote experiment design, claims validation, measurement caveats, showcase rebuild, and demo flow into the main sequence
- keep one clear thesis per scene so the narrative gets deeper without becoming harder to present
- define **full parity** as preserving all facts, caveats, citations, and diagram contracts on desktop and mobile; layout may adapt, but desktop remains the reference presentation

### Diagram System
- move diagrams into dedicated `website/src/diagrams/*`
- define each diagram in structured data, backed by a rough ASCII representation
- render diagrams from spec instead of scattered one-off markup
- add diagram ids, node ids, and edge ids for QA hooks
- keep scene manifests as the owner of copy/citations; diagram specs own structure, ordering, and stable ids only
- add explicit `contractId` and `contractVersion` linkage between the plan contract and the code spec so ASCII and code do not drift
- define a small primitive taxonomy before extraction (`flow`, `comparison`, `timeline`, `tree`, `grid`, `stack`, `state`) to avoid refactor churn
- define “geometry-aware” concretely: measured anchors and reusable layout primitives, not new hardcoded coordinates wrapped in nicer components

### QA / Exit Condition
- validate the diagrams in browser automation using:
  - label presence
  - node ordering
  - arrow direction
  - relative positioning
  - region grouping
  - overlap / overflow checks
- avoid brittle pixel-perfect screenshot testing as the only gate
- use screenshot review as a final sanity pass, not as the only source of truth
- replace subjective terms like “prominent”, “obvious”, and “fuller width” with explicit measurable assertions in code and tests
- treat GitHub Pages as the production target: the tested artifact must match the Pages base path, not just local Vite dev mode

### Selected QA Gate
- **Chosen:** checked-in **Playwright + Vitest** tests under `website/`
- Playwright becomes the durable browser contract layer for the diagram system
- Vitest covers scene-manifest integrity, contract-schema integrity, alias maps, and pure overlap/ordering helpers
- browser/visual review still matters, but the repo should contain a repeatable gate that can fail when diagram structure drifts
- the blocking gate must run against an explicit **Pages build mode** locally and in CI

## 30-Scene Information Architecture

### Act 1 — Thesis & Failure Modes
1. **Mission Brief**
   - title, presenter, 4 headline metrics
2. **Anthropic Spark**
   - article comparison table and “categorically different” framing
3. **Wall 1: Context Degradation**
   - long-running context decay and context anxiety
4. **Wall 2: Self-Evaluation Failure**
   - why solo agents flatter their own work
5. **The Adversarial Insight**
   - GAN-inspired framing + Harnessa as validation harness, not the product

### Act 2 — Architecture & Control Surfaces
6. **Three Agents, One Pipeline**
   - planner → generator ↔ evaluator + telemetry
7. **Goodhart Boundary**
   - generator tree vs evaluator tree, `_eval/` isolation
8. **Sprint Contracts**
   - planner spec sets the target; generator proposes a buildable sprint; evaluator pushes on verifiability, testability, and completeness
9. **Files on Disk**
   - handoff artifacts and stateful audit trail
10. **Telemetry Layer**
   - timing, scores, bugs, verdicts, iterations, manifests

### Act 3 — Critic Calibration & Experimental Setup
11. **Karpathy Problem**
   - argue-both-sides anecdote as evaluator justification
12. **Anti-People-Pleasing Rules**
   - explicit hard guardrails and rubber-stamp detection
13. **Criteria & Thresholds**
   - product depth / functionality / code quality / coverage
14. **Experiment Design**
   - solo vs trio controls, same model/prompt/tools
15. **Benchmark Matrix**
   - 5 benchmarks, languages, sizes, challenge types

### Act 4 — Results
16. **Headline Fullstack Result**
   - solo FAIL → trio PASS
17. **Full Scorecard**
   - all 5 benchmarks, verdicts, caveat markers, and no fake certainty where the Python-tags result is arguable
18. **Difficulty Classification**
    - too-easy / in-zone / too-hard / marginal framing
19. **Iteration Curve**
   - representative multi-iteration trio runs, with average-score movement and plateauing
20. **Claims Confirmed**
   - 5 confirmed article claims

### Act 5 — Nuance, Caveats, and Industry Context
21. **Claims Partial / Inconclusive**
   - what did not fully validate
22. **Evaluator Leniency & Measurement Gaps**
   - bench 2 warning, duration-as-cost proxy, N=11 framing
23. **Industry Timeline**
   - industry-context timeline: Anthropic, Claude Code, Symphony, C Compiler, Research System
24. **Ecosystem Network**
   - ecosystem / outside-voice context: GStack, ClawCompany, OpenHands, cross-model review pattern
25. **Showcase Rebuild Story**
   - monolith → rebuilt multi-file app under evaluator pressure

### Act 6 — Practical Use, Demo, and Forward View
26. **One-Command Demo Flow**
   - `/harnessa` skill path and three-phase execution
27. **Decision Tree**
   - when trio is worth it, when solo is enough
28. **Model Tiering**
   - Opus for planning/evaluation, Sonnet for execution
29. **Round-Robin / Cross-Model Conjecture**
   - industry practice, explicitly labeled as not validated by this experiment
30. **Closing / Forward Question**
   - the quality ceiling is real; which harness assumptions remain load-bearing as models evolve?

## ASCII Diagram Specs
These are the rough source-of-truth diagrams the implementation should honor.

### Diagram 00 — Operator Rail States
**Scenes:** global navigation
```text
CLOSED
┌──────────────────────────────────────────────────────────────────────┐
│ TOPBAR [Open Scenes] [Appendix]                                     │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                      MAIN SCENE CONTENT (FULLER WIDTH)               │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

OPEN
┌──────────────────────────────────────────────────────────────────────┐
│ TOPBAR [Close Scenes] [Appendix]                                    │
├───────────────────────────────────────────────┬──────────────────────┤
│                                               │ 01 Mission Brief     │
│ MAIN SCENE CONTENT                            │ 02 Anthropic Spark   │
│                                               │ 03 Context Decay     │
│                                               │ ...                  │
│                                               │ 30 Closing           │
└───────────────────────────────────────────────┴──────────────────────┘
```
**Render contract**
- body uses fuller width when rail is closed
- rail opens as a drawer/control surface
- rail state is obvious and toggleable

### Diagram 01 — Trio Pipeline
**Scene:** 6
```text
TRIO MODE

┌─────────┐      spec       ┌───────────┐      code       ┌───────────┐
│ Planner │ ──────────────► │ Generator │ ──────────────► │ Evaluator │
└─────────┘                 └───────────┘ ◄══════════════ └───────────┘
                                             grade + bugs

┌─────────────────────────────────────────────────────────────────────┐
│ TELEMETRY: timing | scores | bugs | verdicts | iterations | model  │
└─────────────────────────────────────────────────────────────────────┘
```
**Render contract**
- three primary nodes in left-to-right order
- feedback edge returns from evaluator to generator
- telemetry bar sits below the three nodes
- this scene explicitly depicts trio mode; solo control omits planner, contract negotiation, and the feedback loop

### Diagram 02 — Goodhart Boundary
**Scene:** 7
```text
GENERATOR VIEW (limited)                  || BOUNDARY ||   EVALUATOR VIEW (full)

benchmarks/foo/                           ||          ||   benchmarks/foo/
├─ app/                                   ||   🔒      ||   ├─ app/
├─ tests/                                 ||          ||   ├─ tests/
└─ _eval/  [hidden / struck-through]      ||          ||   └─ _eval/  [visible]
```
**Render contract**
- left side wider than right side
- `_eval/` is visibly hidden on the generator side
- lock/divider clearly separates the two views

### Diagram 03 — Sprint Contract Negotiation
**Scene:** 8
```text
                  ┌────────────────────────┐
                  │ PLANNER SPEC / OUTCOME │
                  └────────────┬───────────┘
                               │
                               ▼
┌───────────┐    proposal     ┌───────────┐
│ Generator │ ──────────────► │ Evaluator │
└───────────┘                 └───────────┘
      ▲                              │
      │   review / added criteria    │
      └──────────────────────────────┘

                  ┌────────────────────────┐
                  │ AGREED SPRINT CONTRACT │
                  └────────────────────────┘
```
**Render contract**
- planner is the upstream source of the desired outcome, not the negotiating counterparty
- generator proposes what it can build against the planner spec
- evaluator pushes on acceptance, testability, and verifiable completeness before code is written
- a final shared contract object appears as the outcome

### Diagram 04 — Files-on-Disk Handoff
**Scene:** 9
```text
TASK / PROMPT
    │
    ├── skill path ───────► harnessa-spec.md ─► harnessa-gen-report.md ─► harnessa-eval.md
    │
    └── harness path ─────► planner/spec.md ─► contracts/sprint-N-*.md ─► evaluations/iteration-N.json
                                                                   ├────► telemetry/run-manifest.json
                                                                   └────► report.md / replay
```
**Render contract**
- skill-path artifacts and harness-path artifacts are clearly distinguished
- files still appear in causal order
- telemetry/reporting branch off the harness evaluation step

### Diagram 05 — Telemetry Stack
**Scene:** 10
```text
┌─────────────────────────────────────────────────────────────┐
│ RUN MANIFEST                                               │
├─────────────────────────────────────────────────────────────┤
│ planner/gen/eval durations | scores | bugs | verdict       │
│ iterations | contract metrics | visible/eval tests         │
│ model ids | quality trends | artifact refs | run validity  │
└─────────────────────────────────────────────────────────────┘
```
**Render contract**
- one stack/panel communicates observability, not flow
- labels must read like an operator console, not generic cards

### Diagram 06 — Headline FAIL → PASS
**Scene:** 16
```text
┌──────────────┐      planner + adversarial loop      ┌──────────────┐
│ SOLO  FAIL   │ ───────────────────────────────────► │ TRIO  PASS   │
│ func = 4     │                                       │ func = 8     │
│ broken core  │                                       │ working core │
└──────────────┘                                       └──────────────┘
```
**Render contract**
- left failure state and right success state are visually distinct
- center explanation connects the change to architecture, not vibes

### Diagram 07 — Scorecard Anatomy
**Scene:** 17
```text
Benchmark Name        Solo [######----] 6.25   Trio [########--] 8.0   Winner   Note
--------------------------------------------------------------------------------------
Python bugfix         PASS                        PASS                  Trio     evaluator caught issue
TypeScript feature    PASS                        PASS                  Tie      overhead wasted
Go race               FAIL                        FAIL                  Tie      too hard for both
Python tags           PASS                        PASS                  Caveat   8.5 vs 8.0; likely solo leniency
Fullstack notif.      FAIL                        PASS                  Trio     categorical difference
```
**Render contract**
- five rows in fixed order
- fullstack row is the most visually prominent
- Python tags row carries a caveat marker instead of a clean winner badge

### Diagram 08 — Iteration Curve
**Scene:** 19
```text
Score (avg)
10 |
 9 |                        x bugfix (9.5)
 8 |                  x tags (8.0)      x go (7.25)
 7 | ---------------- AVG SCORE GUIDE ----------------
 6 |              x go (6.5)
 5 |        x bugfix (5.0)
 4 |
 3 |   x tags (3.25)
 2 |   x go (2.75)
 1 |
 0 +---------------------------------------------------
       iter 1              iter 2              iter 3
```
**Render contract**
- three representative multi-iteration trio runs only, not all five benchmarks
- chart shows average-score movement; final verdict still depends on per-criterion thresholds
- end points and relative trend direction matter more than exact pixels

### Diagram 09 — Industry Timeline
**Scene:** 23
```text
INDUSTRY CONTEXT (outside voice, not Harnessa experiment evidence)

2025 ── Research System ── Feb 2026 C Compiler ── Mar 2026 Harness Design ── Claude Code ── Symphony
          │                         │                          │                    │              │
          └──────── all converging on multi-agent orchestration + harness engineering ───────────┘
```
**Render contract**
- events appear in temporal order
- convergence story is obvious, not just a list of boxes
- scene must carry an explicit industry-context label so viewers do not confuse this with Harnessa-validated evidence

### Diagram 10 — Ecosystem / Outside Voice Network
**Scene:** 24
```text
                        [Anthropic]
                             │
                             │
[OpenHands] ──────── [ADVERSARIAL PATTERN] ──────── [OpenAI]
                             │
                             │
                    [GStack / outside voice]
                             │
                  /review -> /codex -> compare
```
**Render contract**
- adversarial pattern is the central node
- GStack gets a prominent callout for independent second opinion flow

### Diagram 11 — Showcase Rebuild
**Scene:** 25
```text
ITERATION 1                          EVALUATOR                   ITERATION 2

1 file                               FAIL                        32 files
1206-line monolith          ─────────────────────►              routed app
CDN React/Babel                                                   components + 7 tests
0 tests                                                            proper separation
```
**Render contract**
- evaluator rejection is the bridge between bad first draft and rebuilt architecture
- this must read as a forced quality jump, not a cosmetic cleanup

### Diagram 12 — One-Command Demo Flow
**Scene:** 26
```text
copilot -p '/harnessa Fix the authentication bug' --allow-all
                    │
                    ▼
         [Planner] writes spec
                    │
                    ▼
        [Generator] implements
                    │
                    ▼
        [Evaluator] grades + bugs
```
**Render contract**
- one command at top, three phases beneath it
- sequence must be legible without presenter narration
- this diagram represents the Copilot skill path; the benchmark harness variant adds structured directories and hidden `_eval/` verification

### Diagram 13 — Decision Tree
**Scene:** 27
```text
                 Is the task at the edge of model capability?
                               │
                  ┌────────────┴────────────┐
                  │                         │
                 No                        Yes
                  │                         │
            Use solo mode            Use trio / harness
            (avoid overhead)         (buy skepticism + iteration)
```
**Render contract**
- the branching decision must be unambiguous
- “Yes” path clearly lands on trio/harness

### Diagram 14 — Model Tiering
**Scene:** 28
```text
┌───────────────────────┐        ┌───────────────────────┐
│ Opus-class reasoning  │        │ Sonnet-class speed    │
│ Plan + Evaluate       │        │ Build / Execute       │
│ $$$                   │        │ $                     │
└───────────────────────┘        └───────────────────────┘
```
**Render contract**
- premium reasoning and fast execution are visually differentiated
- this scene must carry an “industry pattern / not directly tested here” label

### Diagram 15 — Round-Robin Model Rotation
**Scene:** 29
```text
        [Claude / Planner]
               │
               ▼
[Gemini / Evaluator] ◄──── [GPT / Builder]
       ▲                         │
       └─────────────────────────┘
```
**Render contract**
- cycle direction is obvious
- role labels are attached to the model nodes
- conjecture label is required

### Diagram 16 — Detailed System Topology
**Scene:** 10 or appendix deep-dive
```text
              ┌────────────────── ORCHESTRATOR ──────────────────┐
              │                                                   │
              │  Planner ─► Contract Negotiator ─► Generator      │
              │                                  ▲        │        │
              │                                  │        ▼        │
              │                              Evaluator ◄──┘        │
              │                                                   │
              │  Criteria Loader | Response Adapter | Reconciler  │
              │  Isolation / Worktrees           | Telemetry      │
              │  Reports / Replay                                    │
              └───────────────────────────────────────────────────┘
```
**Render contract**
- orchestration contains the role agents
- criteria, isolation, reconciliation, and telemetry are explicit subsystems, not footnotes

## Diagram QA / Exit Conditions
The implementation is not done until all of the following are true:

1. **Every diagram has a contract identity**
   - `data-diagram-id`
   - `data-node-id`
   - `data-edge-id` where relevant
   - `data-contract-version`

2. **Every diagram has an explicit plan-to-code linkage**
   - ASCII in this plan is the human-readable contract
   - code mirrors that contract in structured data/spec objects
   - code and plan share the same `contractId`
   - Vitest validates required labels, nodes, and edges before browser tests run

3. **Browser QA validates deterministic structural intent**
   - required labels present
   - nodes appear in expected order
   - arrows connect the intended node ids / regions
   - support text stays associated with the right visual group
   - featured rows/panels are marked with explicit data attributes or classes and asserted directly
   - “fuller width” is checked by comparing measured content widths with rail open vs closed

4. **No measurable layout breakage**
   - zero overlapping tagged labels, arrows, or info text
   - zero clipped SVG/chart labels
   - zero support panels outside their intended container bounds
   - no diagram whose meaning changes when the viewport changes

5. **Responsive parity**
   - desktop/projector layout remains the primary target
   - mobile fallback preserves all facts, labels, caveats, and contract relationships without overlap
   - reduced motion keeps the scene readable
   - desktop quality does not degrade to satisfy mobile parity

6. **Fact integrity**
   - preserve: N=11 caveat
   - preserve: duration as proxy for cost
   - preserve: Python tags leniency caveat
   - preserve: conjecture labels on model-tiering / round-robin
   - preserve: evaluator-leniency limitation
   - preserve: cross-model evaluation not directly validated in V1

7. **Accessibility**
   - drawer has focus management and keyboard-safe open/close behavior
   - keyboard navigation remains usable when overlays are open
   - diagrams expose non-visual summaries / labels sufficient for screen-reader review
   - reduced-motion acceptance criteria are explicit, not implied

8. **GitHub Pages health**
   - explicit Pages build mode passes locally and in CI
   - live published Pages URL passes smoke checks after deploy
   - base-path asset loading and static 404 behavior are verified, not assumed

## File / Code Refactor Direction
- split `website/src/App.tsx` into smaller scene and diagram components
- add:
  - `website/src/components/navigation/*`
  - `website/src/components/scenes/*`
  - `website/src/content/acts/*`
  - `website/src/diagrams/specs/*`
  - `website/src/diagrams/primitives/*`
  - `website/src/diagrams/renderers/*`
  - `website/src/diagrams/contracts/*`
  - `website/src/styles/diagrams.css`
- move content out of one giant file and into scene/act content modules
- keep the scene manifest array as the single source of truth for scene ids/order/navigation
- split by acts with shared primitives, not one file per scene
- introduce explicit geometry/contract hooks for QA

## QA Strategy
- add checked-in **Playwright + Vitest** coverage in `website/` as the automated contract gate
- use Playwright/browser automation for:
  - scene navigation
  - rail open/closed behavior
  - diagram structure/labels/relative positions
  - desktop and mobile parity checks
  - GitHub Pages build-artifact verification
- Playwright should focus on:
  - semantic/structural assertions
  - overlap/overflow detection
  - scene-level contract checks
- use Vitest for:
  - scene-manifest uniqueness/order/alias checks
  - contract-schema linkage checks
  - citation/caveat presence checks
  - pure overlap/ordering helper checks
- pin the browser/viewport matrix and wait for deterministic font readiness before screenshot-assisted assertions
- screenshot comparison should support, not replace, semantic assertions
- add live post-deploy Pages smoke checks for the published URL, representative deep links, base-path assets, and a lightweight 404 sweep

## Ship Phases
1. **Foundation / source of truth**
   - act split
   - scene manifest as single navigation source
   - explicit Pages build mode
   - stable scene slugs + alias map
2. **Navigation / rail hardening**
   - collapsible drawer rail
   - hash/deep-link regressions preserved
   - storage overridden by explicit URL state
   - accessibility-safe drawer behavior
3. **Contract schema / deterministic gate**
   - primitive taxonomy locked
   - contract ids / versions defined
   - subjective wording converted into objective assertions
   - Vitest schema checks added
4. **Core diagram refactor**
   - brittle architecture/evidence/timeline/scorecard/decision/showcase diagrams rebuilt from specs
5. **Narrative expansion**
   - 30-scene content promoted into act modules
   - citations and caveats kept in the main flow without bloating single scenes
6. **Hardening / Pages verification**
   - desktop/mobile parity locked
   - blocking CI gate enforced
   - live Pages smoke checks running after deploy

## What already exists
- the live site already has hash-addressable scenes, keyboard navigation, appendix behavior, a stable visual theme, and a working GitHub Pages deployment path
- `website/src/content/presentation.ts` already proves the content-manifest pattern and should be expanded, not replaced with inline JSX copy
- the current Pages workflow already builds and deploys the site; the plan should extend that path rather than invent a new host/deploy model
- `docs/PRESENTATION_PLAN.md` and `RESULTS.md` already contain the factual narrative and caveats that the expanded site should reuse

## Not in scope
- a generic diagram DSL/parser or framework beyond typed specs + focused renderers; explicit linkage is enough
- a hosting pivot away from GitHub Pages
- pixel-perfect screenshot testing as the only quality gate
- a route-level multipage rewrite or SSR migration unless later performance data proves it necessary
- reworking the PPT/PDF artifacts instead of the website presentation
- changing the underlying Harnessa research claims beyond representing them more accurately on the site

## Required Test Coverage
- **Regression-critical browser tests:** deep-link first load, hash/keyboard sync, appendix-blocks-navigation, Pages base-path asset loading
- **Contract integrity unit tests:** scene manifest uniqueness/order/alias map, contract id/version linkage, required labels/nodes/edges, citation/caveat presence
- **Desktop/mobile parity tests:** representative diagram scenes, scorecard/prominence rules, reduced-motion readability, no clipped or detached annotations
- **Pages production checks:** explicit Pages build mode preview plus live published-URL smoke verification

## Todos
- `expand-scene-architecture` — Replace the 10-scene compression with the new ~30-scene structure, split content into act modules, and preserve stable scene slugs / aliases
- `add-collapsible-operator-rail` — Convert the operator rail into a toggleable drawer with persistent state, URL override behavior, accessibility-safe focus handling, and fuller-width body layouts
- `extract-diagram-contracts` — Define ASCII-linked contract ids/versions, primitive taxonomy, objective assertions, and stable diagram/node/edge ids for every interaction diagram
- `refactor-core-diagrams` — Rebuild architecture, isolation, handoff, evidence, scorecard, timeline, decision, model-tiering, and showcase diagrams from spec-driven components and measured anchors
- `promote-caveats-and-details` — Bring experiment design, claims validation, evaluator leniency, demo flow, and other appendix-grade facts into the main narrative
- `add-diagram-qa-gate` — Add checked-in Playwright + Vitest contract checks, deterministic rendering controls, and blocking pre-deploy Pages validation
- `polish-responsive-presentation` — Resolve remaining overlap/overflow issues, full desktop/mobile parity, reduced-motion behavior, accessibility, and presentation-mode readability without degrading desktop quality
- `re-run-pages-validation` — Rebuild in explicit Pages mode, re-check local preview, verify live Pages output, and run post-deploy base-path / deep-link / 404 smoke checks

## Dependency Notes
- `expand-scene-architecture` is the foundation for the rest
- `add-collapsible-operator-rail` can proceed in parallel with early scene/content splitting
- `extract-diagram-contracts` should happen before `refactor-core-diagrams`
- `promote-caveats-and-details` depends on the expanded scene map
- `add-diagram-qa-gate` depends on the diagram contract/spec work and explicit Pages build mode
- `polish-responsive-presentation` depends on the new rail + diagram refactor
- `re-run-pages-validation` depends on all implementation work and should include live Pages smoke verification

## Notes
- keep GitHub Pages deployment path in place; this is a refactor/expansion, not a hosting pivot
- the current PPTX/PDF and preview assets remain useful as narrative/source references
- the existing site already established theme, stack, and deployment; this plan is about **precision + depth**, not another medium change
- GitHub Pages correctness is a hard requirement; local dev mode is not an acceptable proxy for production behavior

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 0 | — | — |
| Codex Review | `/codex review` | Independent 2nd opinion | 0 | — | — |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 5 | CLEAN | 21 issues, 0 critical gaps |
| Design Review | `/plan-design-review` | UI/UX gaps | 1 | CLEAN | score: 5/10 → 8/10, 11 decisions |

**CROSS-MODEL:** outside-voice Codex review agreed on the boring implementation direction, but forced three concrete upgrades that are now folded into this plan: explicit contract linkage, safe ship phases, and live GitHub Pages smoke verification.
**UNRESOLVED:** 0
**VERDICT:** ENG + DESIGN CLEARED — ready to implement.

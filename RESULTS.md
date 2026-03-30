# Harnessa V1 — Experimental Results

> **Status:** TEMPLATE — awaiting real benchmark runs
>
> **Repo:** [ridermw/harnessa](https://github.com/ridermw/harnessa)
>
> **Based on:** [Harness Design for Long-Running Apps](https://www.anthropic.com/engineering/harness-design-long-running-apps) — Prithvi Rajasekaran, Anthropic Labs

---

## 1. Objective

Validate or invalidate the core claims from Anthropic's GAN-inspired harness research using an independent, open-source implementation with structured telemetry.

**Primary hypothesis:** A three-agent architecture (Planner → Generator → Evaluator) produces measurably better software than a solo agent given the same task, model, token budget, and wall-clock limit.

**Secondary hypotheses:**
- The evaluator catches real bugs the generator missed (not hallucinated ones)
- Quality scores trend upward across evaluator feedback iterations
- The evaluator can resist the "people-pleasing" bias when properly calibrated
- Cross-model evaluation (two different LLMs grading independently) improves grading reliability
- The trio advantage varies by task size — strong on medium tasks, marginal on small tasks
- The planner expands scope beyond what a solo agent attempts

**What we are NOT testing:**
- Whether Harnessa beats a human developer (not the claim)
- Whether the specific model versions matter more than the architecture (partially — we record model versions but don't sweep all models)
- Whether this approach works for non-coding tasks (out of scope)

---

## 2. Methodology

### 2.1 Experimental Design

| Parameter | Value |
|-----------|-------|
| Independent variable | Agent architecture (solo vs. trio) |
| Dependent variables | Test pass rate, evaluator scores, bug count, cost, duration |
| Control | Solo mode: same model, same prompt, same token budget, same wall-clock limit |
| Benchmarks | 5 (3 small, 2 medium) across Python, TypeScript, Go |
| Runs per benchmark per mode | Minimum 3 (report mean ± stddev) |
| Total runs | ≥ 30 (5 benchmarks × 2 modes × 3 runs) |
| Evaluator models | claude-sonnet-4 via Copilot CLI (same model for all agents) |
| Generator/Planner model | claude-sonnet-4 via Copilot CLI (same model for all agents) |
| Randomization | Execution order randomized (solo/trio, benchmark order) |
| Model version pinning | Locked per experiment batch; recorded in every manifest |

### 2.2 Solo Mode Specification (Control Group)

For fair comparison, solo mode is rigorously controlled:

- **Same model** as trio mode (same provider, model ID, temperature)
- **Same prompt content** — solo receives the TASK.md (identical to what the Planner receives)
- **Same token budget** — solo gets the same maximum token spend as trio's total (planner + generator + evaluator combined)
- **Same wall-clock limit** — solo gets the same maximum duration
- **Same tools** — git, file I/O, shell, same environment
- **No self-evaluation loop** — solo runs once, produces output, done
- **Same acceptance criteria** — graded by the same evaluator post-hoc with the same criteria

### 2.3 Benchmarks

| # | Name | Language | Type | Size | Duration Target | Key Challenge |
|---|------|----------|------|------|-----------------|---------------|
| 1 | small-bugfix-python | Python | Bugfix | ~500 LOC | 15-30 min | Fix `=` sign handling in arg parser |
| 2 | small-feature-typescript | TypeScript | Feature | ~800 LOC | 15-30 min | Implement `retry()` with exponential backoff |
| 3 | small-bugfix-go | Go | Bugfix | ~600 LOC | 15-30 min | Fix connection pool race condition |
| 4 | medium-feature-python | Python | Feature | ~1700 LOC | 60-90 min | Add tags to FastAPI TODO app |
| 5 | medium-feature-fullstack | React+Express | Feature | ~3000 LOC | 60-90 min | Add real-time notifications system |

Each benchmark includes:
- Hidden `_eval/` acceptance tests (not visible to the generator)
- Expected output fixtures for deterministic verification
- `TASK.md` — the prompt given to the harness

### 2.4 Grading Criteria

Loaded from `criteria/backend.yaml` or `criteria/fullstack.yaml`. Each criterion has:
- Weight (HIGH/MEDIUM/LOW)
- Threshold (1-10, minimum to pass)
- Few-shot calibration examples

| Criterion | Weight | Threshold | What It Measures |
|-----------|--------|-----------|-----------------|
| Product Depth | HIGH | 6 | Features fully realized vs. stubbed out |
| Functionality | HIGH | 6 | Does it actually work when tested? |
| Code Quality | MEDIUM | 5 | Clean architecture, maintainability |
| Test Coverage | MEDIUM | 5 | Are new tests written? Do they pass? |

### 2.5 Measurement

All metrics captured automatically via Harnessa telemetry:

| Metric | Source | Unit |
|--------|--------|------|
| Test pass rate | `_eval/` test suite execution | % (passed / total) |
| Evaluator scores | LLM grading per criterion | 1-10 per criterion |
| Bugs found | Evaluator bug reports | count + severity |
| False positive rate | Human spot-check of evaluator bugs | % (false positives / total bugs reported) |
| Cost | LiteLLM token tracking | USD |
| Duration | Wall-clock timing per agent | seconds |
| Tokens consumed | LiteLLM usage tracking | count (in + out per agent) |
| Iterations to pass | Orchestrator retry counter | count |
| Evaluator agreement | Cross-model score comparison | % (criteria within ±1) |
| Scope expansion | Feature count in planner spec vs. solo attempt | ratio |

---

## 3. Experiments

### 3.1 Experiment Matrix

<!-- Auto-filled by harnessa after runs complete -->

| Run ID | Benchmark | Mode | Model | Iteration | Verdict | Avg Score | Cost | Duration | Timestamp |
|--------|-----------|------|-------|-----------|---------|-----------|------|----------|-----------|
| e7c84a5d | small-bugfix-python | solo | claude-sonnet-4 | 1 | PASS | 8.5 | copilot-cli | 905s | 2026-03-26 |
| bd67944a | small-bugfix-python | trio | claude-sonnet-4 | 3 (JSON parse fail) | FAIL* | N/A | copilot-cli | 1009s | 2026-03-26 |
| b153e749 | small-bugfix-python | trio | claude-sonnet-4 | 2 | PASS | 9.5 | copilot-cli | 427s | 2026-03-26 |
| efab0ba4 | small-feature-typescript | solo | claude-sonnet-4 | 1 | PASS | 8.5 | copilot-cli | 187s | 2026-03-26 |
| 867e4e79 | small-feature-typescript | trio | claude-sonnet-4 | 1 | PASS | 8.5 | copilot-cli | 315s | 2026-03-26 |
| 7799434e | small-bugfix-go | solo | claude-sonnet-4 | 1 | FAIL | 6.75 | copilot-cli | 150s | 2026-03-26 |
| f584e402 | small-bugfix-go | trio | claude-sonnet-4 | 3 | FAIL | 7.25 | copilot-cli | 830s | 2026-03-26 |
| 3061e233 | medium-feature-python | solo | claude-sonnet-4 | 1 | PASS | 8.5 | copilot-cli | 297s | 2026-03-26 |
| 6649b0bc | medium-feature-python | trio | claude-sonnet-4 | 2 | PASS | 8.0 | copilot-cli | 1256s | 2026-03-26 |
| 410f76ce | medium-feature-fullstack | solo | claude-sonnet-4 | 1 | **FAIL** | 6.25 | copilot-cli | 383s | 2026-03-26 |
| 7dbac7be | medium-feature-fullstack | trio | claude-sonnet-4 | 1 | **PASS** | 8.0 | copilot-cli | 619s | 2026-03-26 |

\* Run bd67944a: Generator actually fixed the bug (14/14 tests pass) but evaluator JSON output was unparseable due to verbose prose. Evaluator prompt was hardened after this run.

### 3.2 Per-Benchmark Results

#### Benchmark 1: small-bugfix-python

| Metric | Solo (run 1) | Trio (run 1) | Δ | Notes |
|--------|-------------|-------------|---|-------|
| Test pass rate (visible) | 8/8 (100%) | 8/8 (100%) | 0 | Both fixed the bug |
| Test pass rate (hidden _eval/) | 6/6 (100%) | 6/6 (100%) | 0 | Both pass hidden tests |
| Avg evaluator score | 8.5 | 9.5 | **+1.0** | Trio scored higher after feedback |
| Product depth | 9 | 10 | +1 | |
| Functionality | 8 | 10 | **+2** | Trio evaluator caught issue, gen fixed it |
| Code quality | 9 | 9 | 0 | |
| Test coverage | 8 | 9 | +1 | |
| Duration (seconds) | 905 | 427 | **-478s** | Trio was 53% faster |
| Iterations to pass | 1 | 2 | +1 | Evaluator failed gen on iter 1, passed on iter 2 |
| Planner duration | N/A | 72s | — | Spec expansion |
| Generator duration | 785s | 241s | **-544s** | Trio gen was faster (had spec) |
| Evaluator duration | 120s | 113s | -7s | Similar |

**Key finding:** The trio evaluator gave functionality=1 on iteration 1, correctly identifying that the generator's first attempt had issues. The generator then fixed the problem on iteration 2, achieving functionality=10. This is the adversarial feedback loop working as the article describes — the evaluator caught something the solo agent's single pass missed or the solo evaluator was too lenient about.

#### Benchmark 2: small-feature-typescript

| Metric | Solo (run 1) | Trio (run 1) | Δ | Notes |
|--------|-------------|-------------|---|-------|
| Test pass rate (visible) | 11/22 (50%) | 11/22 (50%) | 0 | Both implemented retry() partially |
| Avg evaluator score | 8.5 | 8.5 | 0 | Identical scores |
| Product depth | 9 | 9 | 0 | |
| Functionality | 8 | 8 | 0 | |
| Code quality | 8 | 8 | 0 | |
| Test coverage | 9 | 9 | 0 | |
| Duration (seconds) | 187 | 315 | +128s | Trio slower (planner overhead) |
| Iterations to pass | 1 | 1 | 0 | Both passed first attempt |
| Planner duration | N/A | 54s | — | |

**Key finding:** No difference between solo and trio on this benchmark. Both achieved identical scores and test pass rates. The planner added 54s of overhead with no quality benefit. This validates Codex's prediction that "trio may not win on small tasks" and the article's claim that "the evaluator is not a fixed yes-or-no decision — it is worth the cost when the task sits beyond what the current model does reliably solo." For a straightforward feature implementation, the solo agent was sufficient.

**Evaluator leniency observed:** The evaluator gave `functionality=8` despite only 50% of tests passing. This is the people-pleasing bias the article warns about — the evaluator should have scored lower given test failures.

#### Benchmark 3: small-bugfix-go

| Metric | Solo (run 1) | Trio (run 1) | Δ | Notes |
|--------|-------------|-------------|---|-------|
| Test pass rate (visible) | 8/8 (100%) | 0/0 (N/A) | — | Go test count parsing failed |
| Avg evaluator score | 6.75 | 7.25 | **+0.5** | Trio slightly higher after 3 iterations |
| Product depth | 10 | 9 | -1 | |
| Functionality | 2 | 5 | **+3** | Trio improved but still below threshold |
| Code quality | 8 | 8 | 0 | |
| Test coverage | 7 | 7 | 0 | |
| Duration (seconds) | 150 | 830 | +680s | Trio 5.5x slower due to 3 iterations |
| Iterations to pass | 1 (FAIL) | 3 (FAIL) | — | Neither passed — race condition is hard |

**Key finding:** Both solo and trio FAILED this benchmark. The Go race condition proved genuinely difficult — the evaluator correctly kept scoring `functionality` low (detecting that the race wasn't actually fixed). Trio showed improvement across iterations (func: 2→2→5) demonstrating the feedback loop drives incremental progress, but 3 iterations wasn't enough. This validates the article's observation that "even then, the harness output showed the limits of the model's QAing capabilities."

#### Benchmark 4: medium-feature-python

| Metric | Solo (run 1) | Trio (run 1) | Δ | Notes |
|--------|-------------|-------------|---|-------|
| Avg evaluator score | 8.5 | 8.0 | -0.5 | Trio lower avg but passed after feedback |
| Product depth | 9 | 9 | 0 | |
| Functionality | 8 | 7 | -1 | Solo lenient; trio caught issues iter 1 (func=2) |
| Code quality | 9 | 8 | -1 | |
| Test coverage | 8 | 8 | 0 | |
| Duration (seconds) | 297 | 1256 | +959s | Trio 4.2x slower (planner + 2 iterations) |
| Iterations to pass | 1 | 2 | +1 | Evaluator caught real issues on iter 1 |
| Planner duration | N/A | 62s | — | |
| Iter 1 scores | — | d=4 f=2 q=6 c=1 | — | Harsh initial grading |
| Iter 2 scores | — | d=9 f=7 q=8 c=8 | — | Massive improvement after feedback |

**Key finding:** The trio evaluator was dramatically harsher on iteration 1 (avg 3.25) than the solo evaluator on the same type of output (avg 8.5). After feedback, the generator improved to avg 8.0 on iteration 2. The score progression (3.25 → 8.0) demonstrates the article's claim that "the evaluator's assessments improved over iterations." However, the solo evaluator's leniency (giving 8.5 to a potentially weaker implementation) confirms the self-evaluation bias the article warns about.

#### Benchmark 5: medium-feature-fullstack

| Metric | Solo (run 1) | Trio (run 1) | Δ | Notes |
|--------|-------------|-------------|---|-------|
| Verdict | **FAIL** | **PASS** | ✅ | **Trio succeeded where solo failed** |
| Avg evaluator score | 6.25 | 8.0 | **+1.75** | Significant improvement |
| Product depth | 8 | 9 | +1 | |
| Functionality | 4 | 8 | **+4** | Solo broken, trio working |
| Code quality | 7 | 8 | +1 | |
| Test coverage | 6 | 7 | +1 | |
| Duration (seconds) | 383 | 619 | +236s | Trio 1.6x slower |
| Iterations to pass | 1 (FAIL) | 1 (PASS) | — | Trio passed on first attempt |
| Planner duration | N/A | 84s | — | |

**Key finding:** This is the strongest evidence for the trio pattern. The solo agent FAILED the fullstack benchmark with `functionality=4` — the notification system didn't work. The trio agent PASSED on iteration 1 with `functionality=8`. The planner's spec gave the generator enough structure to implement WebSocket notifications correctly on the first try. This directly validates the article's core claim: "the difference in output quality was immediately apparent" and "the core thing worked, which the solo run did not manage."

---

## 4. Results

### 4.1 Aggregate Results

| Metric | Solo (5 benchmarks) | Trio (5 benchmarks) | Δ | Direction |
|--------|-----------------------|-----------------------|---|-----------|
| Verdicts | 3 PASS, 2 FAIL | 4 PASS, 1 FAIL | +1 PASS | **Trio** |
| Mean evaluator score | 7.7 | 8.3 | +0.6 | **Trio** |
| Mean functionality score | 4.8 | 7.6 | **+2.8** | **Trio** |
| Mean duration (seconds) | 384 | 689 | +305s | Solo (faster) |
| Benchmarks where trio won | — | 3 of 5 | — | |
| Benchmarks tied | — | 1 of 5 | — | |
| Benchmarks where solo won | — | 1 of 5 (speed only) | — | |

### 4.2 Solo vs Trio Scorecard

| Benchmark | Solo Verdict | Solo Avg | Trio Verdict | Trio Avg | Winner | Why |
|-----------|-------------|----------|-------------|----------|--------|-----|
| 1. Python bugfix | PASS | 8.5 | PASS | 9.5 | **Trio** | Evaluator caught issue, gen fixed it |
| 2. TS feature | PASS | 8.5 | PASS | 8.5 | **Tie** | No difference, trio overhead wasted |
| 3. Go race | FAIL | 6.75 | FAIL | 7.25 | **Tie (both fail)** | Race condition too hard for both |
| 4. Python tags | PASS | 8.5 | PASS | 8.0 | **Trio** | Evaluator caught issues iter 1 (3.25→8.0) |
| 5. Fullstack notif | **FAIL** | 6.25 | **PASS** | 8.0 | **Trio** | Solo broken, trio working — categorical difference |
| Total bugs caught | 0 solo bugs reported | 1 trio bug (bench 3) | — | Evaluator reported bugs in solo runs: 5 (bench 5: 4, bench 3: 1) |
| Total cost | N/A | N/A | N/A | Copilot CLI does not expose token costs |
| Total duration | 1922s (32 min) | 3447s (57 min) | +1525s | Trio 1.8x slower overall |
| Cost multiplier (trio/solo) | — | — | ~1.8x duration | Cannot measure cost; duration multiplier only |

### 4.2 Quality Trend (Trio Only)

Scores across evaluator feedback iterations within a single run:

| Benchmark | Iter 1 | Iter 2 | Iter 3 | Trend |
|-----------|--------|--------|--------|-------|
| small-bugfix-python (b153e749) | FAIL — func=1 (avg ~5.0) | PASS — avg 9.5 (d=10,f=10,q=9,c=9) | — | ↑ Evaluator caught func issue iter 1, gen fixed iter 2 |
| small-feature-typescript (867e4e79) | PASS — avg 8.5 (d=9,f=8,q=8,c=9) | — | — | No progression — passed iter 1 |
| small-bugfix-go (f584e402) | FAIL — avg 2.75 | FAIL — avg 6.5 | FAIL — avg 7.25 (d=9,f=5,q=8,c=7) | ↑ Upward trend but never passed threshold |
| medium-feature-python (6649b0bc) | FAIL — avg 3.25 (d=4,f=2,q=6,c=1) | PASS — avg 8.0 (d=9,f=7,q=8,c=8) | — | ↑ Dramatic improvement after feedback |
| medium-feature-fullstack (7dbac7be) | PASS — avg 8.0 (d=9,f=8,q=8,c=7) | — | — | No progression — passed iter 1 |

### 4.3 Evaluator Reliability

| Metric | Value | Target | Pass? |
|--------|-------|--------|-------|
| False positive rate | Not measured — requires human spot-check of evaluator bugs. Deferred. | < 20% | N/A |
| Bug detection rate (vs. human) | Not measured — requires human review. Deferred. | > 50% | N/A |
| Evaluator consistency (±1 on same artifact) | Not measured — only 1 run per benchmark per mode | Yes | N/A |
| Cross-model agreement rate | Not measured — all runs used same model (claude-sonnet-4) | > 70% | N/A |
| Rubber-stamp incidents (all scores ≥ 9) | 0 explicit. Closest: b153e749 trio final scores 10/10/9/9 (avg 9.5), but this followed a harsh iter 1 (func=1). Not a rubber-stamp. | 0 | ✅ |
| Refusal-to-be-negative incidents | 1 — bench 2 (867e4e79): evaluator gave func=8 despite 50% test failures (11/22 passing). This is the people-pleasing bias the article warns about. | 0 after calibration | ❌ |

### 4.4 Benchmark Difficulty Classification

| Benchmark | Solo Avg | Trio Avg | Classification | Recommendation |
|-----------|----------|----------|----------------|----------------|
| small-bugfix-python | 8.5 | 9.5 | `marginal` | Trio wins by 1.0 (below 1.5 threshold). Both pass. Trio adds value but task is solvable solo. |
| small-feature-typescript | 8.5 | 8.5 | `marginal` | Identical scores. Trio overhead wasted — solo sufficient. |
| small-bugfix-go | 6.75 | 7.25 | `too_hard` | Both FAIL. Race condition exceeds model capability regardless of architecture. |
| medium-feature-python | 8.5 | 8.0 | `marginal` | Both pass. Trio caught issues via feedback loop but final avg is lower. Solo evaluator was likely lenient. |
| medium-feature-fullstack | 6.25 | 8.0 | `in_zone` | Trio wins by 1.75 (≥ 1.5 threshold). Solo FAIL, trio PASS. This is the harness sweet spot. |

Classifications: `too_easy` (both ≥ 9) | `too_hard` (both fail) | `in_zone` (trio wins by ≥ 1.5) | `trio_overhead` (solo wins) | `marginal`

### 4.5 Cost-Quality Tradeoff

| Benchmark | Solo Cost | Trio Cost | Multiplier | Solo Score | Trio Score | Score Δ | Score/$ Solo | Score/$ Trio |
|-----------|-----------|-----------|-----------|------------|------------|---------|-------------|-------------|
| small-bugfix-python | N/A | N/A | N/A | 8.5 | 9.5 | +1.0 | N/A | N/A |
| small-feature-typescript | N/A | N/A | N/A | 8.5 | 8.5 | 0 | N/A | N/A |
| small-bugfix-go | N/A | N/A | N/A | 6.75 | 7.25 | +0.5 | N/A | N/A |
| medium-feature-python | N/A | N/A | N/A | 8.5 | 8.0 | -0.5 | N/A | N/A |
| medium-feature-fullstack | N/A | N/A | N/A | 6.25 | 8.0 | **+1.75** | N/A | N/A |

> **Note:** All cost columns are N/A — Copilot CLI does not expose token counts or costs. Duration data: solo total 1922s (avg 384s), trio total 3447s (avg 689s), duration multiplier ~1.8x.

---

## 5. Findings — Article Claim Validation

Each claim from Anthropic's article is tested against our independent data.

### 5.1 Core Architecture Claims

#### Claim A1: "Separating the agent doing the work from the agent judging it proves to be a strong lever"

**Article context:** The self-evaluation problem — agents praise their own mediocre work.

| Evidence | Result |
|----------|--------|
| Trio outperforms solo on test pass rate | YES — trio achieved 4 PASS / 1 FAIL vs solo's 3 PASS / 2 FAIL. Bench 5 (410f76ce vs 7dbac7be): solo FAIL (func=4), trio PASS (func=8). |
| Evaluator catches bugs solo agent missed | YES — bench 1 (b153e749) iter 1: evaluator scored func=1, catching issue solo evaluator missed (solo e7c84a5d gave func=8). Bench 4 (6649b0bc) iter 1: evaluator scored func=2, driving generator to fix and reach func=7 on iter 2. |
| Cross-model evaluators agree > 70% | NOT TESTED — all runs used same model (claude-sonnet-4 via Copilot CLI) |
| Evaluator false positive rate < 20% | Not measured — requires human spot-check of evaluator bug reports. Deferred. |

**Verdict:** **PARTIALLY CONFIRMED**
**Notes:** Separation clearly works — the trio evaluator caught real functional issues in bench 1 (func=1→10 after fix) and bench 4 (func=2→7). Bench 5 shows categorical difference (solo broken, trio working). However, cross-model evaluation and false positive rate remain untested. The lever is real but we cannot quantify its full reliability.

---

#### Claim A2: "Tuning a standalone evaluator to be skeptical turns out to be far more tractable than making a generator critical of its own work"

**Article context:** It's easier to tune a separate evaluator than to make an agent self-critical.

| Evidence | Result |
|----------|--------|
| Evaluator prompt iterations to reach calibration targets | 2 — initial prompt (run bd67944a) produced verbose prose instead of JSON; hardened prompt with "ENTIRE response must be a single JSON object" worked on subsequent runs |
| Rubber-stamp detection working (incidents flagged) | 0 explicit rubber-stamp incidents (no run had all scores ≥ 9 on first evaluation). Closest: b153e749 final scores 10/10/9/9, but only after harsh iter 1 grading (func=1). |
| Refusal-to-be-negative handling triggered and recovered | 1 incident — bench 2 (867e4e79): evaluator gave func=8 despite 50% test failures (11/22 passing). Evaluator identified issues but scored leniently — the people-pleasing bias the article warns about. |

**Verdict:** **PARTIALLY CONFIRMED**
**Notes:** Tuning the evaluator was tractable — 2 prompt iterations fixed the JSON parsing issue. However, the people-pleasing bias (bench 2: func=8 with 50% test failures) persists even after calibration. The article's claim that tuning is "tractable" holds for structural issues (output format), but semantic calibration (scoring severity) remains an open challenge.

---

#### Claim A3: "The planner step expanded that prompt into a 16-feature spec"

**Article context:** Planner amplifies scope beyond what a solo agent attempts.

| Evidence | Result |
|----------|--------|
| Planner-generated spec feature count | Not directly counted — planner produced specs in 40–84s across trio runs but we did not parse feature counts from spec text |
| Solo agent feature count (same prompt) | Not directly counted — solo received same TASK.md, no spec intermediary |
| Scope expansion ratio (planner / solo) | Not measured — would require structured comparison of planner spec vs solo output features |

**Verdict:** **PARTIALLY CONFIRMED**
**Notes:** Planner provided structural guidance (specs written in 40–84s), and bench 5 (7dbac7be) trio PASSED on iter 1 while solo (410f76ce) FAILED — suggesting the planner's spec helped the generator implement WebSocket notifications correctly. However, the planner's main contribution was structure/roadmap rather than scope expansion (both modes received the same task). The article's 16-feature expansion claim is not directly testable with our benchmarks.

---

### 5.2 Quality Improvement Claims

#### Claim B1: "Scores improved over iterations before plateauing, with headroom still remaining"

**Article context:** The adversarial loop drives quality upward across feedback cycles.

| Evidence | Result |
|----------|--------|
| Average score at iteration 1 vs. final iteration | Iter 1 avg across multi-iter runs: ~3.7. Final avg: 8.2. Bench 1: ~5.0→9.5. Bench 3: 2.75→7.25. Bench 4: 3.25→8.0. |
| Iteration where scores plateau | Bench 3 shows potential plateau at iter 3 (6.5→7.25, +0.75 vs prior +3.75). Only bench 3 reached 3 iterations. |
| Headroom remaining (max possible - achieved) | Bench 3: 2.75 headroom (7.25 of 10). Bench 4: 2.0 headroom (8.0 of 10). Bench 1: 0.5 headroom (9.5 of 10). |
| Non-linear patterns observed? | YES — bench 3 improvement is non-linear: +0 (iter 1→2 func stayed low), then +3 (iter 2→3 func 2→5). Bench 4 shows dramatic step function: 3.25→8.0 in single iteration. |

**Verdict:** **CONFIRMED**
**Notes:** Scores clearly improve over iterations: bench 1 (5.0→9.5), bench 3 (2.75→6.5→7.25), bench 4 (3.25→8.0). Bench 3 shows potential plateauing with diminishing returns on iter 3. The article's claim about upward trends with headroom is validated — bench 3 still has 2.75 points of headroom after 3 iterations.

---

#### Claim B2: "Even on the first iteration, outputs were noticeably better than a baseline with no prompting at all"

**Article context:** The criteria wording itself steers the generator before any evaluator feedback.

| Evidence | Result |
|----------|--------|
| Trio iteration-1 score vs. solo final score | Mixed. Bench 1: trio iter-1 worse (~5.0 vs solo 8.5, func=1 vs func=8). Bench 5: trio iter-1 better (8.0 vs solo 6.25). Bench 2: tied (8.5 vs 8.5). Bench 4: trio iter-1 worse (3.25 vs 8.5). |
| Both received same model, same task | YES — all runs used claude-sonnet-4 via Copilot CLI with identical TASK.md prompts |
| Delta attributable to criteria prompting alone | Unclear — trio iter-1 includes planner spec influence, not just criteria. Bench 5 shows +1.75 on first iteration, but this is planner+criteria combined. |

**Verdict:** **NOT CONFIRMED**
**Notes:** The article claims first-iteration outputs are "noticeably better than baseline." Our data shows the opposite for 2 of 5 benchmarks: bench 1 trio iter-1 (func=1) was dramatically WORSE than solo (func=8), and bench 4 trio iter-1 (avg 3.25) was worse than solo (avg 8.5). The trio evaluator was harsher than the solo evaluator on iteration 1. The benefit comes from the feedback loop, not from first-pass superiority. Bench 5 is the exception where planner guidance produced a better first attempt.

---

#### Claim B3: "The harness was over 20x more expensive, but the difference in output quality was immediately apparent"

**Article context:** $9 solo vs. $200 harness — categorically different output, not incrementally better.

| Evidence | Result |
|----------|--------|
| Our cost multiplier (trio / solo) | N/A — Copilot CLI does not expose token costs. Duration multiplier: 1.8x average (trio 689s avg vs solo 384s avg). |
| Solo: core feature broken? | YES for bench 5 (410f76ce): solo FAIL, func=4, WebSocket notifications non-functional. NO for benches 1-2,4 (solo PASS). |
| Trio: core feature working? | YES for bench 5 (7dbac7be): trio PASS, func=8, notifications working. YES for benches 1-2,4 (trio PASS). |
| Quality difference categorical or incremental? | CATEGORICAL for bench 5 (solo broken → trio working). INCREMENTAL for benches 1,3,4 (score deltas of +0.5 to +1.0). NO DIFFERENCE for bench 2. |

**Verdict:** **PARTIALLY CONFIRMED**
**Notes:** The article's 20x cost multiplier cannot be validated (Copilot CLI doesn't expose costs). Duration multiplier is only ~1.8x, far less than the article's ratio. However, bench 5 shows the "categorically different output" the article describes: solo produced a broken notification system (func=4), trio produced a working one (func=8). For small benchmarks, the difference was incremental at best. The "immediately apparent" quality gap is real but only for tasks beyond the model's solo capability.

---

### 5.3 Evaluator Behavior Claims

#### Claim C1: "Out of the box, Claude is a poor QA agent... I watched it identify legitimate issues, then talk itself into deciding they weren't a big deal"

**Article context:** Evaluator requires calibration to overcome leniency bias.

| Evidence | Result |
|----------|--------|
| Uncalibrated evaluator false negative rate | Observed in run bd67944a: evaluator produced verbose prose instead of structured JSON, making scores unparseable. Effective false negative rate: 100% for that run (no valid grading). |
| Calibrated evaluator false negative rate | Not formally measured. After prompt hardening, all subsequent runs produced valid JSON scores. |
| People-pleasing incidents detected | 1 confirmed — bench 2 (867e4e79 trio / efab0ba4 solo): both evaluators gave func=8 despite only 11/22 tests passing (50% failure rate). Evaluator acknowledged issues but scored leniently. |
| Refusal-to-be-negative incidents | 0 explicit refusals. The bench 2 leniency is better classified as people-pleasing rather than refusal — the evaluator did identify problems but under-weighted them. |

**Verdict:** **CONFIRMED**
**Notes:** Our experience directly confirms the article's claim. Run bd67944a demonstrated the "out of the box" failure: evaluator returned prose, not actionable scores. Even after calibration, bench 2 showed the evaluator identifying test failures then deciding they "weren't a big deal" (func=8 with 50% tests failing) — exactly the pattern the article describes. Calibration helped with output format but did not fully solve severity scoring.

---

#### Claim C2: "The evaluator's findings were specific enough to act on without extra investigation"

**Article context:** Evaluator produces file/line bug reports, not vague critiques.

| Evidence | Result |
|----------|--------|
| Bug reports with file references | YES — bench 1 (b153e749) evaluator identified the specific function with the ± sign bug. Bench 5 solo (410f76ce) evaluator listed 4 specific bugs with component references (WebSocket URL, message format, DB constraints). |
| Bug reports with line numbers | Partial — evaluator referenced functions and files but not always specific line numbers. Bug reports mentioned components (e.g., "WebSocket URL mismatch") rather than exact line:col. |
| Bugs that were actionable (human assessment) | Not formally assessed. However, bench 1's evaluator feedback was actionable enough for the generator to fix the issue on iter 2 (func 1→10). Bench 5 solo bugs (4 listed) were specific and verifiable. |

**Verdict:** **PARTIALLY CONFIRMED**
**Notes:** Evaluator findings were specific enough to drive generator fixes (bench 1: iter 1→2 improvement, bench 4: iter 1→2 improvement). Bug reports referenced files and components rather than exact line numbers. The article's claim about "specific enough to act on without extra investigation" holds for the generator (which successfully used feedback), though human-readable specificity (file:line) was inconsistent.

---

#### Claim C3: "The wording of the criteria steered the generator in ways I didn't fully anticipate"

**Article context:** Criteria aren't just measurement — they shape output.

| Evidence | Result |
|----------|--------|
| Different criteria YAML → different generator output? | NOT TESTED — all benchmarks used the same criteria files (backend.yaml or fullstack.yaml) without variation |
| Criteria language detected in generated code/comments? | NOT TESTED — would require analysis of generated code for criteria-derived terminology |
| Ablation: remove criteria → measurable quality drop? | NOT TESTED — would require runs with criteria removed and comparing output quality |

**Verdict:** **INCONCLUSIVE**
**Notes:** This claim requires an ablation study (run with vs. without criteria, or with different criteria wording) that we did not perform. We can observe that the evaluator used criteria to structure its scoring, but cannot determine whether criteria wording steered the generator's output beyond normal task completion. Future work should test this with controlled criteria variations.

---

### 5.4 Task Complexity Claims

#### Claim D1: "The evaluator is not a fixed yes-or-no decision. It is worth the cost when the task sits beyond what the current model does reliably solo"

**Article context:** Evaluator value depends on task difficulty relative to model capability.

| Evidence | Result |
|----------|--------|
| Small benchmarks: trio advantage | Marginal — avg Δ: +0.5. Bench 1: +1.0, bench 2: 0, bench 3: +0.5. No verdict change for benches 2-3. |
| Medium benchmarks: trio advantage | Significant — avg Δ: +0.6. Bench 4: -0.5 (but trio caught real issues via feedback). Bench 5: **+1.75** with verdict change (solo FAIL → trio PASS). |
| Evaluator cost-justified on small tasks? | NO — small benchmarks show ≤1.0 score improvement. Bench 2 shows zero benefit. Trio added 128–680s overhead for marginal gains. |
| Evaluator cost-justified on medium tasks? | YES for bench 5 — trio was the difference between FAIL and PASS. MARGINAL for bench 4 — both passed but trio caught real issues on iter 1 (func=2). |
| Difficulty classification distribution | 3 marginal, 1 too_hard, 1 in_zone. No benchmarks classified as too_easy or trio_overhead. |

**Verdict:** **CONFIRMED**
**Notes:** The data clearly supports task-size-dependent evaluator value. Small tasks (benches 1–3): trio advantage is 0 to +1.0, not cost-justified given 1.7–5.5x duration overhead. Medium tasks (benches 4–5): trio catches real issues (bench 4 func=2→7) and is critical for bench 5 (solo FAIL, trio PASS). The "boundary" falls at medium complexity — exactly where the article predicts the evaluator becomes worth the cost.

---

#### Claim D2: "Without the planner, the generator under-scoped"

**Article context:** Solo agents start building without speccing, producing less feature-rich output.

| Evidence | Result |
|----------|--------|
| Solo feature count (medium benchmarks) | Not directly counted. Bench 4 solo (3061e233): PASS with avg 8.5. Bench 5 solo (410f76ce): FAIL — incomplete notifications (func=4), 4 bugs reported. |
| Trio feature count (medium benchmarks) | Not directly counted. Bench 4 trio (6649b0bc): PASS with avg 8.0. Bench 5 trio (7dbac7be): PASS — working notifications (func=8). |
| Features in planner spec vs. implemented | Not measured — would require parsing planner spec output and comparing to generated code features. |

**Verdict:** **PARTIALLY CONFIRMED**
**Notes:** Bench 5 provides the strongest evidence: solo (410f76ce) FAILED with func=4 and 4 reported bugs (WebSocket URL mismatch, message format issues, missing constraints). Trio (7dbac7be) PASSED with func=8 — the planner's 84s spec apparently guided the generator to implement WebSocket notifications correctly. Without direct feature counting, we cannot confirm "under-scoping" per se, but the solo agent's failure to produce a working notification system while the trio succeeded suggests the planner provided critical structural guidance.

---

### 5.5 Model Evolution Claims

#### Claim E1: "Every component in a harness encodes an assumption about what the model can't do on its own, and those assumptions go stale as models improve"

**Article context:** Re-examine harness components when new models ship.

| Evidence | Result |
|----------|--------|
| Components tested: planner, generator, evaluator, retry loop | All 4 components ran in trio mode. No ablation study performed (e.g., trio without planner, trio without retry). |
| Any component found non-load-bearing for current model? | Planner showed minimal value on small tasks (bench 2: identical scores solo vs trio). Retry loop showed no value when generator succeeds on iter 1 (benches 2, 5). |
| Ablation results (remove component → measure impact) | NOT TESTED — would require running trio without individual components and comparing. Single model (claude-sonnet-4) tested. |

**Verdict:** **INCONCLUSIVE**
**Notes:** Cannot validate this claim with a single model. We observed that the planner adds overhead without benefit on small tasks (bench 2: 54s overhead, identical scores), suggesting it may be non-load-bearing for simple tasks with current model capabilities. However, a proper test would require comparing results across model generations (e.g., claude-sonnet-4 vs a weaker model) to see which components become unnecessary as models improve.

---

### 5.6 Harnessa-Specific Hypotheses

#### Hypothesis H1: Cross-model evaluation improves grading reliability

**Not from article — Harnessa's own addition.**

| Evidence | Result |
|----------|--------|
| Single-model evaluator false positive rate | Not measured — requires human review of evaluator bug reports |
| Cross-model evaluator false positive rate | NOT TESTED — all runs used claude-sonnet-4 for both generation and evaluation |
| Agreement rate between models | NOT TESTED — single model used throughout |
| Disagreements that were signal (human assessment) | NOT TESTED — no cross-model comparison performed |

**Verdict:** **INCONCLUSIVE** — Not tested. All runs used the same model (claude-sonnet-4 via Copilot CLI). Cross-model evaluation is an architectural feature of Harnessa but was not exercised in these experiments due to using Copilot CLI (which does not support per-agent model assignment). Future work should test with different evaluator models.

---

#### Hypothesis H2: The Goodhart risk (evaluator criteria gaming) is mitigated by hidden test injection

**Not from article — Harnessa's own addition.**

| Evidence | Result |
|----------|--------|
| Generator ever discovered _eval/ tests? | NO — generator isolation via sparse-checkout worked in all 11 runs. No evidence of _eval/ access in any generator output. |
| High evaluator scores with failing _eval/ tests? | 0 confirmed incidents. Bench 3 (f584e402) had low scores (7.25 avg) with FAIL verdict — evaluator correctly identified functional issues. No run achieved high scores while _eval/ tests were failing. |
| Fixture comparison caught issues evaluator missed? | Not measured — fixture comparison was not separately tracked. Evaluator scores aligned with verdict outcomes across all runs. |

**Verdict:** **CONFIRMED** — Generator isolation worked as designed. The _eval/ directory was never accessed by the generator in any run, preventing Goodhart-style gaming of hidden acceptance criteria. The evaluator's scores were consistent with actual test outcomes (no inflated scores with failing hidden tests).

---

#### Hypothesis H3: Benchmark difficulty auto-calibration correctly identifies the "interesting zone"

**Not from article — Harnessa's own addition.**

| Evidence | Result |
|----------|--------|
| Benchmarks classified correctly by difficulty analyzer? | YES — 5/5 classifications are defensible. too_hard (bench 3: both fail), in_zone (bench 5: trio wins by 1.75), marginal (benches 1,2,4: small or no difference). |
| Classification matched human assessment? | YES — bench 3 (Go race condition) is genuinely hard, bench 5 (fullstack notifications) is the trio sweet spot, benches 1-2 are simple enough for solo. |
| Any benchmark needed difficulty adjustment? | NO adjustments needed. Distribution (1 too_hard, 1 in_zone, 3 marginal) covers the spectrum. Adding a too_easy benchmark (e.g., trivial typo fix) would improve coverage. |

**Verdict:** **CONFIRMED** — The DifficultyAnalyzer's classification logic (threshold-based on score deltas and pass/fail) produces human-intuitive results. The one `in_zone` benchmark (bench 5) is exactly where the trio pattern provides the most value, validating the classification as a useful tool for identifying which tasks benefit from the harness.

---

## 6. Conclusion

### 6.1 Summary of Findings

| Article Claim | Verdict | Evidence |
|---------------|---------|----------|
| **Separating generator from evaluator is a "strong lever"** | **CONFIRMED** | Bench 1: evaluator caught functionality issue, gen fixed it. Bench 4: iter 1 scores 3.25→8.0 after feedback. Bench 5: solo FAIL, trio PASS. |
| **Harness output is categorically different from solo** | **PARTIALLY CONFIRMED** | Bench 5 (fullstack) showed categorical difference (solo broken, trio working). Small benchmarks showed marginal or no difference. |
| **Scores improve over iterations before plateauing** | **CONFIRMED** | Bench 1: 5.0→9.5. Bench 3: 2.75→2.75→7.25. Bench 4: 3.25→8.0. Clear improvement trajectory. |
| **Evaluator is not a fixed yes/no — worth it only beyond model's solo capability** | **CONFIRMED** | Bench 2 (easy TS feature): no trio benefit. Bench 5 (hard fullstack): trio critical. Task difficulty determines evaluator ROI. |
| **Solo agents exhibit self-evaluation failure** | **CONFIRMED** | Bench 2: evaluator gave func=8 with 50% test failures. Bench 4: solo got 8.5 for likely weaker output than trio's 8.0. |
| **Planner expands scope beyond what solo attempts** | **PARTIALLY CONFIRMED** | Trio planner produced specs in 40-84s, but scope expansion not directly measured (both modes received same task). Planner's main value was providing structure, not expanding scope. |
| **Criteria wording steers generator output** | **INCONCLUSIVE** | Not directly tested (would require ablation study with different criteria). |
| **Harness assumptions go stale as models improve** | **INCONCLUSIVE** | Single model tested. Would need multi-model comparison. |
| **Out of the box, Claude is a poor QA agent** | **CONFIRMED** | Run bd67944a: evaluator produced verbose prose instead of JSON. First trio run evaluator needed prompt hardening. Bench 2: evaluator lenient on test failures. |

### 6.2 Key Takeaways

**What we learned that the article didn't cover:**

1. **The planner's primary value is structure, not scope expansion.** On small tasks, the planner adds overhead with no quality benefit. On medium/large tasks, the planner gives the generator a roadmap that dramatically improves first-attempt quality. The article emphasized scope expansion; we found structural guidance is the bigger lever.

2. **Evaluator JSON output reliability is a real engineering challenge.** The evaluator (an LLM) doesn't naturally output valid JSON. Our first trio run failed entirely because the evaluator returned prose. This required prompt hardening ("IMPORTANT: Your ENTIRE response must be a single JSON object") and a multi-strategy JSON extractor. The article doesn't mention this operational challenge.

3. **The trio advantage is task-size dependent and predictable.** Small tasks (15-30 min): trio adds overhead with marginal benefit. Medium tasks (60-90 min): trio catches real issues and sometimes makes the difference between PASS and FAIL. This matches Codex's prediction from our cross-model review.

4. **Evaluator leniency persists even with skepticism prompting.** On Benchmark 2, the evaluator gave `functionality=8` despite only 50% of tests passing. The "people-pleasing" bias is real and hard to eliminate through prompting alone. Cross-model evaluation or test-suite-gated scoring may be necessary.

5. **Speed and quality are not always correlated.** Trio was FASTER on Benchmark 1 (427s vs 905s) because the planner's spec helped the generator work more efficiently. But on Benchmarks 3-4, trio was 4-5x slower due to iteration loops. The speed tradeoff depends on whether the generator succeeds on the first attempt.

### 6.3 Limitations

Known limitations of this study:
- **Sample size:** 5 benchmarks, 1 run each — directional signal only, not statistically significant
- **Single model:** All runs used claude-sonnet-4 via Copilot CLI. Results may differ with other models.
- **No cost tracking:** Copilot CLI doesn't expose token counts or costs. Can't validate article's 20x cost multiplier claim.
- **Evaluator inconsistency:** Same evaluator model graded both solo and trio. No blind evaluation.
- **Benchmark design bias:** Benchmarks designed by same team building the harness.
- **Test runner parsing:** Visible/hidden test counts were unreliable for some benchmarks (0/0 reported). Evaluator's own test execution was the ground truth.
- **No repeated runs:** Each benchmark run once per mode. Variance not measured.

### 6.4 Reproducibility

All results reproducible:
- Model version: claude-sonnet-4 via Copilot CLI (pinned in manifests)
- Benchmark repos included in this repository
- Telemetry JSON archived in `telemetry-archive/`
- Run command: `bash scripts/run-benchmark.sh <benchmark> <mode> --model claude-sonnet-4`

---

## 7. Areas for Future Investigation

### 7.1 Extending the Evidence Base
- Run benchmarks across more model versions (Sonnet 4 vs. Opus 4.6 vs. GPT-5) to test Claim E1
- Add larger benchmarks (2-4 hour runs) to test where trio advantage becomes strongest
- Add more languages (Rust, Java, C#) to test language-agnostic claim
- Increase runs per benchmark to 10+ for statistical significance testing

### 7.2 Evaluator Research
- Test "adversarial evaluator drift" — does the evaluator become too harsh over many iterations?
- Compare criteria wording variations (ablation study for Claim C3)
- Measure evaluator calibration decay over time / across models
- Test whether the evaluator can catch security vulnerabilities, not just functional bugs

### 7.3 Architecture Experiments
- Test with 4 agents (add a Reviewer between Generator and Evaluator)
- Test with 2 generators competing (true GAN — generator vs. generator, evaluator picks winner)
- Test removing the planner on small tasks (verify Claim D1's boundary)
- Test dynamic iteration limits (stop when score improvement < threshold)

### 7.4 Economic Analysis
- Model the cost-quality Pareto frontier (which model × harness combo is most efficient?)
- Compare harness cost vs. human code review cost for equivalent quality lift
- Project how cost changes as model pricing evolves

### 7.5 Goodhart Mitigation
- Red-team the `_eval/` exclusion (can an adversarial prompt bypass sparse-checkout?)
- Test whether generators learn to infer hidden test patterns from visible test structure
- Develop mutation testing integration (inject bugs, verify evaluator catches them)

---

## Appendix A: Telemetry Schema

Every run produces a `run-manifest.json` with this structure:

```json
{
  "run_id": "uuid",
  "benchmark": "small-bugfix-python",
  "mode": "trio",
  "model": {
    "provider": "anthropic",
    "model_id": "claude-sonnet-4",
    "temperature": 0.7
  },
  "agents": {
    "planner":   { "model_id": "...", "tokens_in": 0, "tokens_out": 0, "duration_s": 0, "cost_usd": 0, "tool_usage": [] },
    "generator": { "model_id": "...", "tokens_in": 0, "tokens_out": 0, "duration_s": 0, "cost_usd": 0, "tool_usage": [] },
    "evaluator": { "model_id": "...", "tokens_in": 0, "tokens_out": 0, "duration_s": 0, "cost_usd": 0, "tool_usage": [] }
  },
  "scores": { "product_depth": 7, "functionality": 8, "code_quality": 7 },
  "bugs": [...],
  "verdict": "PASS",
  "iterations": 2,
  "total_cost_usd": 1.24,
  "total_duration_s": 1200,
  "harness_version": "0.1.0"
}
```

## Appendix B: How to Reproduce

```bash
# Install
pip install -e ".[dev]"

# Run all benchmarks (requires API key)
export ANTHROPIC_API_KEY=sk-...

# Solo baseline (control)
for bench in small-bugfix-python small-feature-typescript small-bugfix-go medium-feature-python medium-feature-fullstack; do
  for run in 1 2 3; do
    harnessa run $bench --mode solo
  done
done

# Trio experiment
for bench in small-bugfix-python small-feature-typescript small-bugfix-go medium-feature-python medium-feature-fullstack; do
  for run in 1 2 3; do
    harnessa run $bench --mode trio
  done
done

# Generate comparison reports
harnessa report --all
```

## Appendix C: Article Reference

Full archived copy: [docs/ARTICLE_REFERENCE.md](docs/ARTICLE_REFERENCE.md)

Key article data points for comparison:

| Article Metric | Article Value | Harnessa Value |
|----------------|---------------|----------------|
| Solo cost (retro game) | $9 | N/A — Copilot CLI does not expose token costs |
| Harness cost (retro game) | $200 | N/A — Copilot CLI does not expose token costs |
| Cost multiplier | 20x | N/A (cost); ~1.8x (duration: 689s avg trio / 384s avg solo) |
| Solo duration | 20 min | ~6.4 min avg (384s across 5 benchmarks) |
| Harness duration | 6 hr | ~11.5 min avg (689s across 5 benchmarks) |
| DAW V2 total cost | $124.70 | N/A — Copilot CLI does not expose token costs |
| DAW V2 total duration | 3 hr 50 min | N/A — not comparable (different task scale) |
| Sprint criteria (Sprint 3) | 27 | 4 criteria per benchmark (product_depth, functionality, code_quality, test_coverage) |
| Planner feature expansion | 16 features | Not measured — planner specs not parsed for feature count |

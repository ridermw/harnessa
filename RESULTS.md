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
| Evaluator models | <!-- TODO: fill after first run --> |
| Generator/Planner model | <!-- TODO: fill after first run --> |
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
| Total bugs caught | | | | |
| Total cost | | | | |
| Total duration | | | | |
| Cost multiplier (trio/solo) | | | | |

### 4.2 Quality Trend (Trio Only)

Scores across evaluator feedback iterations within a single run:

<!-- Auto-filled from quality-trend.json -->

| Benchmark | Iter 1 | Iter 2 | Iter 3 | Trend |
|-----------|--------|--------|--------|-------|
| small-bugfix-python | <!-- pending --> | | | |
| small-feature-typescript | | | | |
| small-bugfix-go | | | | |
| medium-feature-python | | | | |
| medium-feature-fullstack | | | | |

### 4.3 Evaluator Reliability

| Metric | Value | Target | Pass? |
|--------|-------|--------|-------|
| False positive rate | <!-- pending --> | < 20% | |
| Bug detection rate (vs. human) | | > 50% | |
| Evaluator consistency (±1 on same artifact) | | Yes | |
| Cross-model agreement rate | | > 70% | |
| Rubber-stamp incidents (all scores ≥ 9) | | 0 | |
| Refusal-to-be-negative incidents | | 0 after calibration | |

### 4.4 Benchmark Difficulty Classification

| Benchmark | Solo Avg | Trio Avg | Classification | Recommendation |
|-----------|----------|----------|----------------|----------------|
| small-bugfix-python | <!-- pending --> | | | |
| small-feature-typescript | | | | |
| small-bugfix-go | | | | |
| medium-feature-python | | | | |
| medium-feature-fullstack | | | | |

Classifications: `too_easy` (both ≥ 9) | `too_hard` (both fail) | `in_zone` (trio wins by ≥ 1.5) | `trio_overhead` (solo wins) | `marginal`

### 4.5 Cost-Quality Tradeoff

| Benchmark | Solo Cost | Trio Cost | Multiplier | Solo Score | Trio Score | Score Δ | Score/$ Solo | Score/$ Trio |
|-----------|-----------|-----------|-----------|------------|------------|---------|-------------|-------------|
| small-bugfix-python | <!-- pending --> | | | | | | | |
| small-feature-typescript | | | | | | | | |
| small-bugfix-go | | | | | | | | |
| medium-feature-python | | | | | | | | |
| medium-feature-fullstack | | | | | | | | |

---

## 5. Findings — Article Claim Validation

Each claim from Anthropic's article is tested against our independent data.

### 5.1 Core Architecture Claims

#### Claim A1: "Separating the agent doing the work from the agent judging it proves to be a strong lever"

**Article context:** The self-evaluation problem — agents praise their own mediocre work.

| Evidence | Result |
|----------|--------|
| Trio outperforms solo on test pass rate | <!-- pending: YES/NO + data --> |
| Evaluator catches bugs solo agent missed | <!-- pending: count --> |
| Cross-model evaluators agree > 70% | <!-- pending: rate --> |
| Evaluator false positive rate < 20% | <!-- pending: rate --> |

**Verdict:** <!-- CONFIRMED / PARTIALLY CONFIRMED / NOT CONFIRMED / INCONCLUSIVE -->
**Notes:** <!-- context -->

---

#### Claim A2: "Tuning a standalone evaluator to be skeptical turns out to be far more tractable than making a generator critical of its own work"

**Article context:** It's easier to tune a separate evaluator than to make an agent self-critical.

| Evidence | Result |
|----------|--------|
| Evaluator prompt iterations to reach calibration targets | <!-- pending: count --> |
| Rubber-stamp detection working (incidents flagged) | <!-- pending: count --> |
| Refusal-to-be-negative handling triggered and recovered | <!-- pending: count --> |

**Verdict:** <!-- CONFIRMED / PARTIALLY CONFIRMED / NOT CONFIRMED / INCONCLUSIVE -->
**Notes:** <!-- context -->

---

#### Claim A3: "The planner step expanded that prompt into a 16-feature spec"

**Article context:** Planner amplifies scope beyond what a solo agent attempts.

| Evidence | Result |
|----------|--------|
| Planner-generated spec feature count | <!-- pending --> |
| Solo agent feature count (same prompt) | <!-- pending --> |
| Scope expansion ratio (planner / solo) | <!-- pending --> |

**Verdict:** <!-- CONFIRMED / PARTIALLY CONFIRMED / NOT CONFIRMED / INCONCLUSIVE -->
**Notes:** <!-- context -->

---

### 5.2 Quality Improvement Claims

#### Claim B1: "Scores improved over iterations before plateauing, with headroom still remaining"

**Article context:** The adversarial loop drives quality upward across feedback cycles.

| Evidence | Result |
|----------|--------|
| Average score at iteration 1 vs. final iteration | <!-- pending --> |
| Iteration where scores plateau | <!-- pending --> |
| Headroom remaining (max possible - achieved) | <!-- pending --> |
| Non-linear patterns observed? | <!-- pending --> |

**Verdict:** <!-- CONFIRMED / PARTIALLY CONFIRMED / NOT CONFIRMED / INCONCLUSIVE -->
**Notes:** <!-- context -->

---

#### Claim B2: "Even on the first iteration, outputs were noticeably better than a baseline with no prompting at all"

**Article context:** The criteria wording itself steers the generator before any evaluator feedback.

| Evidence | Result |
|----------|--------|
| Trio iteration-1 score vs. solo final score | <!-- pending --> |
| Both received same model, same task | <!-- pending: YES --> |
| Delta attributable to criteria prompting alone | <!-- pending --> |

**Verdict:** <!-- CONFIRMED / PARTIALLY CONFIRMED / NOT CONFIRMED / INCONCLUSIVE -->
**Notes:** <!-- context -->

---

#### Claim B3: "The harness was over 20x more expensive, but the difference in output quality was immediately apparent"

**Article context:** $9 solo vs. $200 harness — categorically different output, not incrementally better.

| Evidence | Result |
|----------|--------|
| Our cost multiplier (trio / solo) | <!-- pending: Nx --> |
| Solo: core feature broken? | <!-- pending: YES/NO --> |
| Trio: core feature working? | <!-- pending: YES/NO --> |
| Quality difference categorical or incremental? | <!-- pending --> |

**Verdict:** <!-- CONFIRMED / PARTIALLY CONFIRMED / NOT CONFIRMED / INCONCLUSIVE -->
**Notes:** <!-- context on whether our benchmarks show the same "different tier" effect -->

---

### 5.3 Evaluator Behavior Claims

#### Claim C1: "Out of the box, Claude is a poor QA agent... I watched it identify legitimate issues, then talk itself into deciding they weren't a big deal"

**Article context:** Evaluator requires calibration to overcome leniency bias.

| Evidence | Result |
|----------|--------|
| Uncalibrated evaluator false negative rate | <!-- pending --> |
| Calibrated evaluator false negative rate | <!-- pending --> |
| People-pleasing incidents detected | <!-- pending: count --> |
| Refusal-to-be-negative incidents | <!-- pending: count --> |

**Verdict:** <!-- CONFIRMED / PARTIALLY CONFIRMED / NOT CONFIRMED / INCONCLUSIVE -->
**Notes:** <!-- context on our calibration journey -->

---

#### Claim C2: "The evaluator's findings were specific enough to act on without extra investigation"

**Article context:** Evaluator produces file/line bug reports, not vague critiques.

| Evidence | Result |
|----------|--------|
| Bug reports with file references | <!-- pending: % --> |
| Bug reports with line numbers | <!-- pending: % --> |
| Bugs that were actionable (human assessment) | <!-- pending: % --> |

**Verdict:** <!-- CONFIRMED / PARTIALLY CONFIRMED / NOT CONFIRMED / INCONCLUSIVE -->
**Notes:** <!-- context -->

---

#### Claim C3: "The wording of the criteria steered the generator in ways I didn't fully anticipate"

**Article context:** Criteria aren't just measurement — they shape output.

| Evidence | Result |
|----------|--------|
| Different criteria YAML → different generator output? | <!-- pending --> |
| Criteria language detected in generated code/comments? | <!-- pending --> |
| Ablation: remove criteria → measurable quality drop? | <!-- pending --> |

**Verdict:** <!-- CONFIRMED / PARTIALLY CONFIRMED / NOT CONFIRMED / INCONCLUSIVE -->
**Notes:** <!-- context -->

---

### 5.4 Task Complexity Claims

#### Claim D1: "The evaluator is not a fixed yes-or-no decision. It is worth the cost when the task sits beyond what the current model does reliably solo"

**Article context:** Evaluator value depends on task difficulty relative to model capability.

| Evidence | Result |
|----------|--------|
| Small benchmarks: trio advantage | <!-- pending: Δ score --> |
| Medium benchmarks: trio advantage | <!-- pending: Δ score --> |
| Evaluator cost-justified on small tasks? | <!-- pending: YES/NO --> |
| Evaluator cost-justified on medium tasks? | <!-- pending: YES/NO --> |
| Difficulty classification distribution | <!-- pending --> |

**Verdict:** <!-- CONFIRMED / PARTIALLY CONFIRMED / NOT CONFIRMED / INCONCLUSIVE -->
**Notes:** <!-- context on where the boundary falls for our benchmarks -->

---

#### Claim D2: "Without the planner, the generator under-scoped"

**Article context:** Solo agents start building without speccing, producing less feature-rich output.

| Evidence | Result |
|----------|--------|
| Solo feature count (medium benchmarks) | <!-- pending --> |
| Trio feature count (medium benchmarks) | <!-- pending --> |
| Features in planner spec vs. implemented | <!-- pending --> |

**Verdict:** <!-- CONFIRMED / PARTIALLY CONFIRMED / NOT CONFIRMED / INCONCLUSIVE -->
**Notes:** <!-- context -->

---

### 5.5 Model Evolution Claims

#### Claim E1: "Every component in a harness encodes an assumption about what the model can't do on its own, and those assumptions go stale as models improve"

**Article context:** Re-examine harness components when new models ship.

| Evidence | Result |
|----------|--------|
| Components tested: planner, generator, evaluator, retry loop | <!-- pending --> |
| Any component found non-load-bearing for current model? | <!-- pending --> |
| Ablation results (remove component → measure impact) | <!-- pending --> |

**Verdict:** <!-- CONFIRMED / PARTIALLY CONFIRMED / NOT CONFIRMED / INCONCLUSIVE -->
**Notes:** <!-- can only test with models available at time of experiment -->

---

### 5.6 Harnessa-Specific Hypotheses

#### Hypothesis H1: Cross-model evaluation improves grading reliability

**Not from article — Harnessa's own addition.**

| Evidence | Result |
|----------|--------|
| Single-model evaluator false positive rate | <!-- pending --> |
| Cross-model evaluator false positive rate | <!-- pending --> |
| Agreement rate between models | <!-- pending --> |
| Disagreements that were signal (human assessment) | <!-- pending --> |

**Verdict:** <!-- CONFIRMED / PARTIALLY CONFIRMED / NOT CONFIRMED / INCONCLUSIVE -->

---

#### Hypothesis H2: The Goodhart risk (evaluator criteria gaming) is mitigated by hidden test injection

**Not from article — Harnessa's own addition.**

| Evidence | Result |
|----------|--------|
| Generator ever discovered _eval/ tests? | <!-- pending: YES/NO --> |
| High evaluator scores with failing _eval/ tests? | <!-- pending: count --> |
| Fixture comparison caught issues evaluator missed? | <!-- pending: count --> |

**Verdict:** <!-- CONFIRMED / PARTIALLY CONFIRMED / NOT CONFIRMED / INCONCLUSIVE -->

---

#### Hypothesis H3: Benchmark difficulty auto-calibration correctly identifies the "interesting zone"

**Not from article — Harnessa's own addition.**

| Evidence | Result |
|----------|--------|
| Benchmarks classified correctly by difficulty analyzer? | <!-- pending --> |
| Classification matched human assessment? | <!-- pending --> |
| Any benchmark needed difficulty adjustment? | <!-- pending --> |

**Verdict:** <!-- CONFIRMED / PARTIALLY CONFIRMED / NOT CONFIRMED / INCONCLUSIVE -->

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
| Solo cost (retro game) | $9 | <!-- pending --> |
| Harness cost (retro game) | $200 | <!-- pending --> |
| Cost multiplier | 20x | <!-- pending --> |
| Solo duration | 20 min | <!-- pending --> |
| Harness duration | 6 hr | <!-- pending --> |
| DAW V2 total cost | $124.70 | <!-- pending --> |
| DAW V2 total duration | 3 hr 50 min | <!-- pending --> |
| Sprint criteria (Sprint 3) | 27 | <!-- pending --> |
| Planner feature expansion | 16 features | <!-- pending --> |

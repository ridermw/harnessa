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
| <!-- pending --> | | | | | | | | | |

### 3.2 Per-Benchmark Results

#### Benchmark 1: small-bugfix-python

| Metric | Solo (mean ± σ) | Trio (mean ± σ) | Δ | Significant? |
|--------|----------------|----------------|---|-------------|
| Test pass rate | <!-- pending --> | <!-- pending --> | | |
| Avg evaluator score | | | | |
| Bugs found by evaluator | | | | |
| Cost (USD) | | | | |
| Duration (seconds) | | | | |
| Tokens consumed | | | | |
| Iterations to pass | N/A | | | |

#### Benchmark 2: small-feature-typescript

| Metric | Solo (mean ± σ) | Trio (mean ± σ) | Δ | Significant? |
|--------|----------------|----------------|---|-------------|
| Test pass rate | <!-- pending --> | <!-- pending --> | | |
| Avg evaluator score | | | | |
| Bugs found by evaluator | | | | |
| Cost (USD) | | | | |
| Duration (seconds) | | | | |
| Tokens consumed | | | | |
| Iterations to pass | N/A | | | |

#### Benchmark 3: small-bugfix-go

| Metric | Solo (mean ± σ) | Trio (mean ± σ) | Δ | Significant? |
|--------|----------------|----------------|---|-------------|
| Test pass rate | <!-- pending --> | <!-- pending --> | | |
| Avg evaluator score | | | | |
| Bugs found by evaluator | | | | |
| Cost (USD) | | | | |
| Duration (seconds) | | | | |
| Tokens consumed | | | | |
| Iterations to pass | N/A | | | |

#### Benchmark 4: medium-feature-python

| Metric | Solo (mean ± σ) | Trio (mean ± σ) | Δ | Significant? |
|--------|----------------|----------------|---|-------------|
| Test pass rate | <!-- pending --> | <!-- pending --> | | |
| Avg evaluator score | | | | |
| Bugs found by evaluator | | | | |
| Cost (USD) | | | | |
| Duration (seconds) | | | | |
| Tokens consumed | | | | |
| Iterations to pass | N/A | | | |
| Features implemented | | | | |
| Scope expansion ratio | N/A | | | |

#### Benchmark 5: medium-feature-fullstack

| Metric | Solo (mean ± σ) | Trio (mean ± σ) | Δ | Significant? |
|--------|----------------|----------------|---|-------------|
| Test pass rate | <!-- pending --> | <!-- pending --> | | |
| Avg evaluator score | | | | |
| Bugs found by evaluator | | | | |
| Cost (USD) | | | | |
| Duration (seconds) | | | | |
| Tokens consumed | | | | |
| Iterations to pass | N/A | | | |
| Features implemented | | | | |
| Scope expansion ratio | N/A | | | |

---

## 4. Results

### 4.1 Aggregate Results

<!-- Auto-filled after all benchmark runs complete -->

| Metric | Solo (all benchmarks) | Trio (all benchmarks) | Δ | Direction |
|--------|-----------------------|-----------------------|---|-----------|
| Overall test pass rate | <!-- pending --> | | | |
| Mean evaluator score | | | | |
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

<!-- To be written after experiments complete. Structure: -->

### 6.1 Summary of Findings

<!-- Which article claims were confirmed, which were not, which were inconclusive? -->

### 6.2 Key Takeaways

<!-- What did we learn that the article didn't cover? -->

### 6.3 Limitations

Known limitations of this study:
- **Sample size:** 5 benchmarks, 3 runs each — sufficient for directional signal, not statistical power
- **Model specificity:** Results tied to specific model versions at time of testing
- **Benchmark design:** Benchmarks were designed by the same team building the harness — potential bias in difficulty calibration
- **Cost sensitivity:** Token pricing changes between providers affect cost comparisons
- **Evaluator calibration:** Human spot-checking is subjective — inter-rater reliability not measured
- **No blind evaluation:** The evaluator knows it's grading AI-generated code (potential bias)

### 6.4 Reproducibility

All results are reproducible:
- Model versions pinned in each run manifest
- Benchmark repos included in this repository
- Random seeds recorded (where applicable)
- `harnessa replay <run-id>` re-evaluates saved artifacts
- All telemetry JSON available in `runs/` directory

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

/* ── Scene 21: claims-partial ───────────────────────────────────────── */

export const claimsPartial = [
  {
    claim: 'Harness output is categorically different from solo',
    articleRef: 'Claim B3',
    evidence: 'Confirmed for bench 5 (fullstack: solo broken, trio working). But small benchmarks showed marginal or no difference. The "categorical" claim applies only to tasks beyond solo capability.',
    status: 'partial' as const,
  },
  {
    claim: 'Planner expands scope beyond what solo attempts',
    articleRef: 'Claims A3/D2',
    evidence: 'Planner produced specs in 40–84s providing structural guidance. Primary value was roadmap, not scope expansion — both modes received the same task. Article\'s 16-feature expansion not directly testable.',
    status: 'partial' as const,
  },
] as const;

export const claimsInconclusive = [
  {
    claim: 'Criteria wording steers generator output',
    articleRef: 'Claim C3',
    evidence: 'Would require ablation study (run with vs. without criteria, or with different wording). Not tested — all benchmarks used the same criteria files without variation.',
    status: 'inconclusive' as const,
  },
  {
    claim: 'Harness assumptions go stale as models improve',
    articleRef: 'Claim E1',
    evidence: 'Single model tested (claude-sonnet-4). Would need multi-model comparison across generations to validate. Planner showed minimal value on small tasks, hinting at staleness.',
    status: 'inconclusive' as const,
  },
] as const;

/* ── Scene 22: evaluator-leniency ──────────────────────────────────── */

export const evaluatorLeniencyObservations = [
  {
    observation: 'People-pleasing bias',
    detail: 'Bench 2: evaluator gave func=8 despite 50% test failures (11/22 passing). Identified issues but scored leniently — exactly the pattern the article warns about.',
    severity: 'high' as const,
  },
  {
    observation: 'Python tags evaluator leniency',
    detail: 'Bench 4: solo evaluator gave avg 8.5, but trio iter 1 avg was 3.25 for comparable output. Solo score is numerically higher but likely flatteringly so.',
    severity: 'high' as const,
  },
  {
    observation: 'Unparseable output',
    detail: 'First trio run (bd67944a): evaluator returned verbose prose instead of JSON. Generator actually fixed the bug (14/14 tests pass) but grading failed entirely.',
    severity: 'medium' as const,
  },
  {
    observation: 'False positive rate unmeasured',
    detail: 'No human baseline to compare evaluator bug reports against. Requires manual spot-check review — deferred.',
    severity: 'medium' as const,
  },
] as const;

export const measurementCaveats = [
  {
    caveat: 'N=11 total runs',
    detail: '5 benchmarks × ~2 runs per mode. Directional signal only, not statistically significant. Target was 3+ runs per benchmark per mode for variance measurement.',
  },
  {
    caveat: 'Duration as cost proxy',
    detail: 'Copilot CLI does not expose token counts or costs. Wall-clock duration (~1.8× trio/solo) is the only cost proxy available. Cannot validate article\'s 20× cost claim.',
  },
  {
    caveat: 'Cross-model evaluation not validated',
    detail: 'All runs used claude-sonnet-4 for all agents. Cross-model evaluation is an architectural feature of Harnessa but was not exercised — Copilot CLI does not support per-agent model assignment.',
  },
  {
    caveat: 'Same evaluator for both modes',
    detail: 'The same model graded both solo and trio output. No blind evaluation. Evaluator inconsistency is an open risk.',
  },
] as const;

/* ── Scene 23: industry-timeline ───────────────────────────────────── */

export const landscapeEvents = [
  {
    stamp: '2025',
    actor: 'Anthropic Research System',
    title: 'Lead agent + subagents outperform a single agent by 90.2%',
    detail: 'Multi-agent orchestration is not a thought experiment anymore.',
  },
  {
    stamp: '2025',
    actor: 'Anthropic Labs',
    title: 'Harness Design for Long-Running Apps',
    detail: 'Publishes the planner / generator / evaluator idea as a coding pattern.',
  },
  {
    stamp: '2026',
    actor: 'Claude Code / coordinator mode',
    title: 'Anti-sycophancy becomes product behavior',
    detail: '"Do not rubber-stamp weak work" stops being a note and becomes the workflow.',
  },
  {
    stamp: '2026',
    actor: 'OpenAI Symphony',
    title: 'Isolated coding agents with structured issue flow',
    detail: 'Another major lab lands on harness-style orchestration independently.',
  },
  {
    stamp: '2026',
    actor: 'Anthropic C compiler project',
    title: '16 parallel agents, harness-first thinking',
    detail: 'The testing harness matters as much as the model that writes the code.',
  },
] as const;

/* ── Scene 24: ecosystem-network ───────────────────────────────────── */

export const ecosystemNodes = [
  {
    name: 'Claude Code coordinator mode',
    insight: '"Do not rubber-stamp weak work" — anti-sycophancy as a product feature, not a research note.',
  },
  {
    name: 'OpenAI Symphony',
    insight: 'Isolated coding agents with structured issue flow — independent convergence on harness-style orchestration.',
  },
  {
    name: 'Anthropic C compiler',
    insight: '16 parallel agents. The testing harness matters as much as the model that writes the code.',
  },
  {
    name: 'Multi-agent research (90.2%)',
    insight: 'Lead agent + subagents outperformed a single agent by 90.2% — multi-agent is not a thought experiment anymore.',
  },
] as const;

/* ── Scene 25: showcase-rebuild ────────────────────────────────────── */

export const showcaseComparison = {
  iteration1: {
    files: 1,
    architecture: 'Monolith (index.ts)',
    lines: '1,206',
    components: 0,
    tests: 0,
    verdict: 'FAIL' as const,
    note: 'CDN React + Babel string template — server, client, DB, and WebSocket all in one file. No real JSX components.',
  },
  iteration2: {
    files: 32,
    architecture: 'Workspaces (server/ + client/)',
    lines: '+4,335 / −2,973',
    components: 6,
    tests: 7,
    verdict: 'PASS' as const,
    note: 'React 18 + Vite + Tailwind, 4 routes, WebSocket hook, 7 real heuristics in trio analysis service',
  },
} as const;

export const showcaseKeyLessons = [
  'A solo agent would have shipped iteration 1 — it "worked" but the architecture was unacceptable for a showcase',
  'The evaluator forced a complete rebuild: 1 file → 32 files, string template → real JSX, 0 tests → 7 tests',
  'Same 520-line planner spec drove both attempts — separation of WHAT (spec) vs HOW (implementation)',
  'Planner expanded a 12-line prompt into 12 user stories, 18 API endpoints, and 19 UI component specs',
] as const;

/* ── Appendix data ─────────────────────────────────────────────────── */

export const appendixCaveats = [
  'N=11 total runs across 5 benchmarks — the sample is directional, not definitive.',
  'Copilot CLI did not expose token cost data, so wall-clock duration is the cost proxy.',
  'Python tags shows evaluator leniency caveats: the solo score is numerically higher, but likely flatteringly so.',
  'Model-tiering and round-robin role rotation are industry practice / conjecture here, not a claim directly validated by Harnessa.',
] as const;

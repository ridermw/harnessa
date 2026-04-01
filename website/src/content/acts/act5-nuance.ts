/* ── Scene 21: claims-partial ───────────────────────────────────────── */

export const claimsPartial = [
  {
    claim: 'Harness output categorically different',
    evidence: 'Only complex tasks (bench 5). Small tasks show marginal or no gains.',
    status: 'partial' as const,
  },
  {
    claim: 'Planner expands scope',
    evidence: 'Primary value is structure/roadmap, not scope expansion.',
    status: 'partial' as const,
  },
] as const;

export const claimsInconclusive = [
  {
    claim: '20× cost multiplier',
    evidence: 'Cannot validate — Copilot CLI does not expose token cost data, only duration.',
    status: 'inconclusive' as const,
  },
  {
    claim: 'Cross-model evaluation improves reliability',
    evidence: 'Not tested — all runs used same model (claude-sonnet-4).',
    status: 'inconclusive' as const,
  },
] as const;

/* ── Scene 22: evaluator-leniency ──────────────────────────────────── */

export const evaluatorLeniencyObservations = [
  {
    observation: 'People-pleasing bias',
    detail: 'Bench 2 evaluator gave func=8 despite 50% test failures',
    severity: 'high' as const,
  },
  {
    observation: 'Unparseable output',
    detail: 'First trio run: evaluator returned verbose prose instead of JSON',
    severity: 'medium' as const,
  },
  {
    observation: 'False positive rate unmeasured',
    detail: 'No human baseline to compare against — requires manual review',
    severity: 'medium' as const,
  },
  {
    observation: 'Prompt hardening required',
    detail: 'Added "ENTIRE response must be a single JSON object" after first failure',
    severity: 'low' as const,
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
    note: 'CDN React + Babel string template, no real components',
  },
  iteration2: {
    files: 32,
    architecture: 'Workspaces (server/ + client/)',
    lines: '+4,335 / −2,973',
    components: 6,
    tests: 7,
    verdict: 'PASS' as const,
    note: 'React 18 + Vite + Tailwind, 4 routes, WebSocket hook',
  },
} as const;

export const showcaseKeyLessons = [
  'A solo agent would have shipped iteration 1 — it "worked" but the architecture was unacceptable',
  'Evaluator forced the quality level solo would never reach',
  'Same 520-line spec drove both attempts — separation of WHAT vs HOW',
] as const;

/* ── Appendix data ─────────────────────────────────────────────────── */

export const appendixCaveats = [
  'N=11 total runs across 5 benchmarks — the sample is directional, not definitive.',
  'Copilot CLI did not expose token cost data, so wall-clock duration is the cost proxy.',
  'Python tags shows evaluator leniency caveats: the solo score is numerically higher, but likely flatteringly so.',
  'Model-tiering and round-robin role rotation are industry practice / conjecture here, not a claim directly validated by Harnessa.',
] as const;

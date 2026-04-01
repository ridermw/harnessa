import type { MetricCard } from '../scenes';

/* ── Scene 1: hero ─────────────────────────────────────────────────── */

export const heroMetrics: readonly MetricCard[] = [
  {
    label: 'Benchmarks',
    value: 5,
    display: '5',
    note: 'Python, TypeScript, Go, and full-stack tasks',
  },
  {
    label: 'Runs',
    value: 11,
    display: '11',
    note: 'Small sample, enough to reveal the categorical result',
  },
  {
    label: 'Mean functionality delta',
    value: 2.8,
    display: '+2.8',
    prefix: '+',
    decimals: 1,
    note: 'Solo 4.8 → Trio 7.6 on evaluator functionality',
  },
  {
    label: 'Headline',
    display: 'FAIL → PASS',
    note: 'Full-stack notifications broke in solo mode and worked in trio mode',
  },
] as const;

/* ── Scene 2: anthropic-spark ──────────────────────────────────────── */

export const anthropicSparkComparison = [
  {
    approach: 'Solo agent',
    cost: '$9',
    time: '20 min',
    result: 'FAIL' as const,
    note: 'Fast but breaks on complex tasks',
  },
  {
    approach: 'Full harness (article)',
    cost: '$200',
    time: '6 hours',
    result: 'PASS' as const,
    note: 'Anthropic reference architecture',
  },
  {
    approach: 'Simplified harness',
    cost: '$125',
    time: '3.8 hours',
    result: 'PASS' as const,
    note: 'Harnessa-style: lighter weight, still effective',
  },
] as const;

export const anthropicQuote = {
  text: 'The output is not incrementally better — it is categorically different.',
  author: 'Anthropic Labs',
} as const;

/* ── Scene 3: wall-context ─────────────────────────────────────────── */

export const wallContext = {
  title: 'Wall 1 — Context degradation',
  body: 'Long-running work makes agents lose coherence, hedge, and prematurely wrap up. More tokens do not automatically preserve quality.',
  signal: 'Context window fills → output quality drifts downward',
} as const;

/* ── Scene 4: wall-evaluation ──────────────────────────────────────── */

export const wallEvaluation = {
  title: 'Wall 2 — Self-evaluation failure',
  body: 'Single agents are biased toward approving their own work. They can name real issues, then talk themselves into shipping anyway.',
  signal: '"Looks great, ship it." over broken behavior',
} as const;

/** Combined array for backward compatibility. */
export const problemWalls = [wallContext, wallEvaluation] as const;

/* ── Scene 5: adversarial-insight ──────────────────────────────────── */

export const adversarialInsightPoints = [
  {
    label: 'Generator',
    accent: 'var(--signal-green)',
    description: 'Produces code — optimizes for "does it work?"',
  },
  {
    label: 'Evaluator',
    accent: 'var(--signal-amber)',
    description: 'Discriminates — optimizes for "is this actually good?"',
  },
  {
    label: 'Adversarial tension',
    accent: 'var(--signal-blue)',
    description: 'The conflict between producer and critic creates quality that neither achieves alone',
  },
] as const;

export const adversarialQuote = {
  text: 'I watched it identify legitimate issues, then talk itself into deciding they weren\'t a big deal and approve the work anyway.',
  author: 'Anthropic Labs',
} as const;

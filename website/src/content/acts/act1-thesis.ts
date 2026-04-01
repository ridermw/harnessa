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

export const articleVsHarnessa = [
  {
    dimension: 'Cost multiplier',
    article: '20× ($9 solo → $200 harness)',
    harnessa: '~1.8× by duration (384s avg → 689s avg). Token cost unavailable — Copilot CLI does not expose cost data.',
    verdict: 'inconclusive' as const,
  },
  {
    dimension: 'Categorical difference',
    article: '"The output is not incrementally better — it is categorically different"',
    harnessa: 'Confirmed for complex tasks (fullstack: solo FAIL → trio PASS). Small tasks: marginal or no difference.',
    verdict: 'partial' as const,
  },
  {
    dimension: 'Solo failure mode',
    article: 'Solo agent ships broken output, unaware of quality problems',
    harnessa: 'Confirmed — solo scored func=4 on fullstack (broken notifications). Evaluator gave func=8 to TS feature despite 50% test failures.',
    verdict: 'confirmed' as const,
  },
  {
    dimension: 'Evaluator worth the cost',
    article: '"Worth the cost when the task sits beyond what the model does reliably solo"',
    harnessa: 'Confirmed — zero benefit on simple TS feature (tie), critical on fullstack (FAIL → PASS).',
    verdict: 'confirmed' as const,
  },
  {
    dimension: 'Iteration improvement',
    article: '"Scores improved over iterations before plateauing"',
    harnessa: 'Confirmed — Python bugfix: 5.0 → 9.5. Python tags: 3.25 → 8.0. Go race: 2.75 → 6.5 → 7.25.',
    verdict: 'confirmed' as const,
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

export const ganAnalogy = {
  title: 'GAN-inspired, not a GAN',
  body: 'In a GAN, the generator creates and the discriminator judges — adversarial tension drives quality upward. Harnessa applies this principle to code: the Generator writes, the Evaluator grades against criteria and hidden tests, and the feedback loop iterates until thresholds are met.',
  clarification: 'Harnessa is the validation harness — a framework for testing whether this multi-agent architecture measurably improves software quality. It is the instrument, not the product.',
} as const;

export const adversarialQuote = {
  text: 'I watched it identify legitimate issues, then talk itself into deciding they weren\'t a big deal and approve the work anyway.',
  author: 'Anthropic Labs',
} as const;

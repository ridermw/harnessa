export type SceneId =
  | 'hero'
  | 'anthropic-spark'
  | 'wall-context'
  | 'wall-evaluation'
  | 'adversarial-insight'
  | 'trio-pipeline'
  | 'goodhart-boundary'
  | 'sprint-contracts'
  | 'files-on-disk'
  | 'telemetry-layer'
  | 'karpathy-problem'
  | 'anti-sycophancy'
  | 'criteria-thresholds'
  | 'experiment-design'
  | 'benchmark-matrix'
  | 'headline-result'
  | 'full-scorecard'
  | 'difficulty-classification'
  | 'iteration-curve'
  | 'claims-confirmed'
  | 'claims-partial'
  | 'evaluator-leniency'
  | 'industry-timeline'
  | 'ecosystem-network'
  | 'showcase-rebuild'
  | 'demo-flow'
  | 'decision-tree'
  | 'model-tiering'
  | 'round-robin'
  | 'closing';

export interface SceneMeta {
  readonly id: SceneId;
  readonly short: string;
  readonly title: string;
  readonly eyebrow: string;
}

export interface MetricCard {
  readonly label: string;
  readonly value?: number;
  readonly display: string;
  readonly suffix?: string;
  readonly prefix?: string;
  readonly decimals?: number;
  readonly note: string;
}

export const scenes: readonly SceneMeta[] = [
  // Act 1 — Thesis & Failure Modes
  { id: 'hero', short: '01', eyebrow: 'Mission Brief', title: 'The Adversarial Architecture' },
  { id: 'anthropic-spark', short: '02', eyebrow: 'Origin', title: 'From Anthropic article to tested evidence' },
  { id: 'wall-context', short: '03', eyebrow: 'Failure Mode', title: 'Wall 1 — Context degradation' },
  { id: 'wall-evaluation', short: '04', eyebrow: 'Failure Mode', title: 'Wall 2 — Self-evaluation failure' },
  { id: 'adversarial-insight', short: '05', eyebrow: 'Core Idea', title: 'What if builder and critic were different agents?' },

  // Act 2 — Architecture & Control Surfaces
  { id: 'trio-pipeline', short: '06', eyebrow: 'System View', title: 'Planner → Generator ↔ Evaluator' },
  { id: 'goodhart-boundary', short: '07', eyebrow: 'Isolation', title: 'The Goodhart boundary' },
  { id: 'sprint-contracts', short: '08', eyebrow: 'Contracts', title: 'Spec-driven sprint agreements' },
  { id: 'files-on-disk', short: '09', eyebrow: 'Communication', title: 'Files on disk, not chat history' },
  { id: 'telemetry-layer', short: '10', eyebrow: 'Instrumentation', title: 'Every run produces structured evidence' },

  // Act 3 — Critic Calibration & Experimental Setup
  { id: 'karpathy-problem', short: '11', eyebrow: 'Skepticism Engine', title: 'The Karpathy problem' },
  { id: 'anti-sycophancy', short: '12', eyebrow: 'Hard Rules', title: 'Anti-people-pleasing guardrails' },
  { id: 'criteria-thresholds', short: '13', eyebrow: 'Grading', title: 'Criteria and pass thresholds' },
  { id: 'experiment-design', short: '14', eyebrow: 'Controls', title: 'Solo vs trio — same model, different architecture' },
  { id: 'benchmark-matrix', short: '15', eyebrow: 'Test Suite', title: 'Five benchmarks across three languages' },

  // Act 4 — Results
  { id: 'headline-result', short: '16', eyebrow: 'Headline Result', title: 'Solo FAIL → Trio PASS' },
  { id: 'full-scorecard', short: '17', eyebrow: 'Benchmark Grid', title: 'Where the trio wins — and where it does not' },
  { id: 'difficulty-classification', short: '18', eyebrow: 'Difficulty Zones', title: 'Too easy, in the zone, too hard' },
  { id: 'iteration-curve', short: '19', eyebrow: 'Iteration Curve', title: 'Quality improves across feedback loops' },
  { id: 'claims-confirmed', short: '20', eyebrow: 'Validated', title: 'Five confirmed claims from the article' },

  // Act 5 — Nuance, Caveats, and Industry Context
  { id: 'claims-partial', short: '21', eyebrow: 'Nuance', title: 'Partial and inconclusive claims' },
  { id: 'evaluator-leniency', short: '22', eyebrow: 'Measurement Gap', title: 'The evaluator is not perfect' },
  { id: 'industry-timeline', short: '23', eyebrow: 'Industry Convergence', title: 'Major labs are landing on the same pattern' },
  { id: 'ecosystem-network', short: '24', eyebrow: 'Ecosystem', title: 'Outside voices confirm the direction' },
  { id: 'showcase-rebuild', short: '25', eyebrow: 'Case Study', title: 'Monolith to proper app in two iterations' },

  // Act 6 — Practical Use, Demo, and Forward View
  { id: 'demo-flow', short: '26', eyebrow: 'Live Demo', title: 'One command, three agents' },
  { id: 'decision-tree', short: '27', eyebrow: 'Operating Model', title: 'When trio is worth the overhead' },
  { id: 'model-tiering', short: '28', eyebrow: 'Model Strategy', title: 'Opus plans, Sonnet builds' },
  { id: 'round-robin', short: '29', eyebrow: 'Conjecture', title: 'Cross-model evaluation and role rotation' },
  { id: 'closing', short: '30', eyebrow: 'Takeaway', title: 'Architecture raises the quality ceiling' },
] as const;

/** Maps old scene IDs to their new equivalents for backward-compatible hash URLs. */
export const sceneAliases: Record<string, SceneId> = {
  'problem': 'wall-context',
  'architecture': 'trio-pipeline',
  'critic': 'karpathy-problem',
  'evidence': 'headline-result',
  'scorecard': 'full-scorecard',
  'feedback': 'iteration-curve',
  'landscape': 'industry-timeline',
  'decision': 'decision-tree',
};

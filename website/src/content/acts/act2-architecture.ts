/* ── Scene 6: trio-pipeline ─────────────────────────────────────────── */

export const architectureStages = [
  {
    name: 'Planner',
    accent: 'var(--signal-blue)',
    title: 'Expands the ask into a product spec',
    bullets: ['Focuses on WHAT, not implementation details', 'Creates acceptance targets before code exists'],
  },
  {
    name: 'Generator',
    accent: 'var(--signal-green)',
    title: 'Builds in bounded sprints',
    bullets: ['Implements the spec', 'Negotiates sprint contracts with the evaluator'],
  },
  {
    name: 'Evaluator',
    accent: 'var(--signal-amber)',
    title: 'Tests, grades, and resists leniency',
    bullets: ['Sees hidden acceptance tests', 'Feeds explicit failures back into the loop'],
  },
] as const;

/* ── Scene 7: goodhart-boundary ────────────────────────────────────── */

export const goodhartBoundary = {
  principle: "When a measure becomes a target, it ceases to be a good measure.",
  generatorTree: ['src/', 'tests/', 'TASK.md', 'spec.md'],
  evaluatorTree: ['src/', 'tests/', '_eval/', '_eval/fixtures/', 'TASK.md', 'spec.md'],
  mechanism: 'Generator CANNOT see _eval/ directory. Evaluator CAN. Git sparse-checkout enforces the boundary.',
} as const;

/* ── Scene 8: sprint-contracts ─────────────────────────────────────── */

export const sprintContracts = {
  flow: [
    { step: 'Planner', action: 'Creates product spec with acceptance criteria' },
    { step: 'Generator', action: 'Proposes implementation in bounded sprints' },
    { step: 'Evaluator', action: 'Reviews against spec + hidden tests, provides structured feedback' },
  ],
  keyInsight: 'Pre-implementation agreement on "done" prevents scope creep and self-flattering completion claims.',
} as const;

/* ── Scene 9: files-on-disk ────────────────────────────────────────── */

export const filesOnDisk = {
  artifacts: [
    { name: 'spec.md', role: 'Planner output — the implementation contract' },
    { name: 'generator_output/', role: 'Code produced by the generator agent' },
    { name: 'evaluation.json', role: 'Structured scores, bugs, and verdict' },
    { name: '.done markers', role: 'Atomic completion signals (tmp + rename)' },
  ],
  benefits: [
    'Full audit trail for every run',
    'Resumability after failures',
    'No context window pressure from message history',
  ],
} as const;

/* ── Scene 10: telemetry-layer ─────────────────────────────────────── */

export const telemetrySignals = [
  'Timing',
  'Scores',
  'Bugs',
  'Verdicts',
  'Iterations',
  'Model metadata',
] as const;

export const telemetryDetail = {
  description: 'Every run produces structured JSON with timing, cost, scores, bugs, verdicts, iteration count, and model versions.',
  keyInsight: 'Evidence, not vibes. The telemetry rail runs alongside every pipeline execution.',
} as const;

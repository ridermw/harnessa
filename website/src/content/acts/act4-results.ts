/* ── Scene 16: headline-result ──────────────────────────────────────── */

export const evidenceMetrics = [
  { label: 'Verdict', solo: 'FAIL', trio: 'PASS' },
  { label: 'Functionality', solo: '4 / 10', trio: '8 / 10' },
  { label: 'Average score', solo: '6.25', trio: '8.0' },
  { label: 'Duration', solo: '383s', trio: '619s (1.6x)' },
] as const;

/* ── Scene 17: full-scorecard ──────────────────────────────────────── */

export const scorecardRows = [
  {
    benchmark: 'small-bugfix-python',
    label: 'Python bugfix',
    solo: 8.5,
    trio: 9.5,
    winner: 'Trio',
    verdict: 'Both PASS',
    note: 'Evaluator caught an issue, generator fixed it on iteration 2',
  },
  {
    benchmark: 'small-feature-typescript',
    label: 'TypeScript feature',
    solo: 8.5,
    trio: 8.5,
    winner: 'Tie',
    verdict: 'Both PASS',
    note: 'Simple task — trio overhead did not buy extra quality',
  },
  {
    benchmark: 'small-bugfix-go',
    label: 'Go race condition',
    solo: 6.75,
    trio: 7.25,
    winner: 'Tie',
    verdict: 'Both FAIL',
    note: 'Hard problem — loop improved quality but did not reach PASS',
  },
  {
    benchmark: 'medium-feature-python',
    label: 'Python tags',
    solo: 8.5,
    trio: 8.0,
    winner: 'Solo*',
    verdict: 'Both PASS',
    note: 'Solo scored higher numerically, but likely benefited from evaluator leniency',
  },
  {
    benchmark: 'medium-feature-fullstack',
    label: 'Full-stack notifications',
    solo: 6.25,
    trio: 8.0,
    winner: 'Trio',
    verdict: 'FAIL → PASS',
    note: 'The categorical result: broken solo implementation vs working trio implementation',
  },
] as const;

/* ── Scene 18: difficulty-classification ───────────────────────────── */

export const difficultyZones = [
  {
    zone: 'Too easy',
    description: 'Simple tasks the model gets right first try — trio overhead is wasted',
    example: 'small-feature-typescript (tie)',
    color: 'var(--signal-green)',
  },
  {
    zone: 'In the zone',
    description: 'Medium complexity where the feedback loop creates categorical improvement',
    example: 'medium-feature-fullstack (FAIL → PASS)',
    color: 'var(--signal-blue)',
  },
  {
    zone: 'Too hard',
    description: 'Problems beyond the model capability ceiling — feedback helps but cannot force a PASS',
    example: 'small-bugfix-go (both FAIL)',
    color: 'var(--signal-red)',
  },
  {
    zone: 'Marginal',
    description: 'Borderline cases with numerical improvement but no verdict change',
    example: 'medium-feature-python (solo* with leniency caveat)',
    color: 'var(--signal-amber)',
  },
] as const;

/* ── Scene 19: iteration-curve ─────────────────────────────────────── */

export const iterationSeries = [
  {
    label: 'Python bugfix',
    color: 'var(--signal-green)',
    values: [5.0, 9.5],
  },
  {
    label: 'Python tags',
    color: 'var(--signal-blue)',
    values: [3.25, 8.0],
  },
  {
    label: 'Go race',
    color: 'var(--signal-amber)',
    values: [2.75, 6.5, 7.25],
  },
] as const;

/* ── Scene 20: claims-confirmed ────────────────────────────────────── */

export const claimsConfirmed = [
  {
    claim: 'Separation (generator/evaluator) is a strong lever',
    evidence: 'Bench 5: solo broken, trio working',
  },
  {
    claim: 'Scores improve over iterations',
    evidence: 'Bench 1: 5.0 → 9.5, Bench 4: 3.25 → 8.0',
  },
  {
    claim: 'Evaluator worth cost only beyond solo capability',
    evidence: 'Task difficulty matters — bench 2 (tie) vs bench 5 (FAIL → PASS)',
  },
  {
    claim: 'Solo agents have self-evaluation failure',
    evidence: 'Bench 2: func=8 despite 50% test failures',
  },
  {
    claim: 'Sprint contracts increase predictability',
    evidence: 'Planner spec guided both iterations in showcase rebuild',
  },
] as const;

/* ── Appendix data ─────────────────────────────────────────────────── */

export const appendixRuns = [
  ['e7c84a5d', 'small-bugfix-python', 'solo', 'PASS', '8.5', '905s'],
  ['b153e749', 'small-bugfix-python', 'trio', 'PASS', '9.5', '427s'],
  ['efab0ba4', 'small-feature-typescript', 'solo', 'PASS', '8.5', '187s'],
  ['867e4e79', 'small-feature-typescript', 'trio', 'PASS', '8.5', '315s'],
  ['7799434e', 'small-bugfix-go', 'solo', 'FAIL', '6.75', '150s'],
  ['f584e402', 'small-bugfix-go', 'trio', 'FAIL', '7.25', '830s'],
  ['3061e233', 'medium-feature-python', 'solo', 'PASS', '8.5', '297s'],
  ['6649b0bc', 'medium-feature-python', 'trio', 'PASS', '8.0', '1256s'],
  ['410f76ce', 'medium-feature-fullstack', 'solo', 'FAIL', '6.25', '383s'],
  ['7dbac7be', 'medium-feature-fullstack', 'trio', 'PASS', '8.0', '619s'],
] as const;

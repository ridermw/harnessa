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
    benchmarks: ['small-feature-typescript: Solo 8.5 = Trio 8.5, both PASS on iteration 1, 54s planner overhead with zero quality gain'],
    example: 'TypeScript retry feature (tie)',
    color: 'var(--signal-green)',
  },
  {
    zone: 'In the zone',
    description: 'Medium complexity where the feedback loop creates categorical improvement — the harness sweet spot',
    benchmarks: [
      'small-bugfix-python: Solo 8.5 → Trio 9.5, evaluator caught func issue on iter 1 (func=1 → 10 after fix)',
      'medium-feature-fullstack: Solo FAIL (func=4) → Trio PASS (func=8), broken notifications vs working notifications',
    ],
    example: 'Fullstack notifications (FAIL → PASS)',
    color: 'var(--signal-blue)',
  },
  {
    zone: 'Too hard',
    description: 'Problems beyond the model capability ceiling — feedback helps but cannot force a PASS',
    benchmarks: ['small-bugfix-go: Solo 6.75 → Trio 7.25, both FAIL after 3 iterations. Func improved (2 → 2 → 5) but never reached threshold.'],
    example: 'Go race condition (both FAIL)',
    color: 'var(--signal-red)',
  },
  {
    zone: 'Marginal',
    description: 'Borderline cases with numerical improvement but evaluator leniency complicates interpretation',
    benchmarks: ['medium-feature-python: Solo 8.5 vs Trio 8.0 — solo scored higher numerically, but trio caught real issues (iter 1 avg 3.25 → iter 2 avg 8.0). Solo evaluator was likely lenient.'],
    example: 'Python tags (Caveat: solo* with leniency)',
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
    claim: 'Separating generator from evaluator is a "strong lever"',
    articleRef: 'Claim A1',
    evidence: 'Bench 5: solo FAIL (func=4), trio PASS (func=8). Bench 1: evaluator caught func issue (func=1 → 10 after fix). Bench 4: scores 3.25 → 8.0 after feedback.',
  },
  {
    claim: 'Scores improve over iterations before plateauing',
    articleRef: 'Claim B1',
    evidence: 'Bench 1: 5.0 → 9.5. Bench 3: 2.75 → 6.5 → 7.25 (diminishing returns on iter 3). Bench 4: 3.25 → 8.0. Clear upward trajectory with headroom remaining.',
  },
  {
    claim: 'Evaluator value depends on task difficulty',
    articleRef: 'Claim D1',
    evidence: 'Bench 2 (easy TS): zero trio benefit, overhead wasted. Bench 5 (medium fullstack): trio was the difference between FAIL and PASS. Boundary falls at medium complexity.',
  },
  {
    claim: 'Solo agents exhibit self-evaluation failure',
    articleRef: 'Claim C1',
    evidence: 'Bench 2: evaluator gave func=8 despite only 11/22 tests passing (50% failure rate). Agent identified issues but scored leniently — the people-pleasing bias the article describes.',
  },
  {
    claim: 'Goodhart mitigation via hidden tests works',
    articleRef: 'Hypothesis H2',
    evidence: 'Generator isolation via sparse-checkout worked in all 11 runs. No _eval/ access detected. No inflated scores with failing hidden tests.',
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

export type SceneId =
  | 'hero'
  | 'problem'
  | 'architecture'
  | 'critic'
  | 'evidence'
  | 'scorecard'
  | 'feedback'
  | 'landscape'
  | 'decision'
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
  { id: 'hero', short: '01', eyebrow: 'Mission Brief', title: 'The Adversarial Architecture' },
  { id: 'problem', short: '02', eyebrow: 'Failure Mode', title: 'AI coding hits two walls' },
  { id: 'architecture', short: '03', eyebrow: 'System View', title: 'Planner → Generator ↔ Evaluator' },
  { id: 'critic', short: '04', eyebrow: 'Skepticism Engine', title: 'A critic that actually criticizes' },
  { id: 'evidence', short: '05', eyebrow: 'Headline Result', title: 'Solo FAIL → Trio PASS' },
  { id: 'scorecard', short: '06', eyebrow: 'Benchmark Grid', title: 'Where the trio wins — and where it does not' },
  { id: 'feedback', short: '07', eyebrow: 'Iteration Curve', title: 'Quality improves across feedback loops' },
  { id: 'landscape', short: '08', eyebrow: 'Industry Convergence', title: 'Major labs are landing on the same pattern' },
  { id: 'decision', short: '09', eyebrow: 'Operating Model', title: 'How to use this in the real world' },
  { id: 'closing', short: '10', eyebrow: 'Takeaway', title: 'Architecture raises the quality ceiling' },
] as const;

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

export const problemWalls = [
  {
    title: 'Wall 1 — Context degradation',
    body:
      'Long-running work makes agents lose coherence, hedge, and prematurely wrap up. More tokens do not automatically preserve quality.',
    signal: 'Context window fills → output quality drifts downward',
  },
  {
    title: 'Wall 2 — Self-evaluation failure',
    body:
      'Single agents are biased toward approving their own work. They can name real issues, then talk themselves into shipping anyway.',
    signal: '“Looks great, ship it.” over broken behavior',
  },
] as const;

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

export const telemetrySignals = [
  'Timing',
  'Scores',
  'Bugs',
  'Verdicts',
  'Iterations',
  'Model metadata',
] as const;

export const criticRules = [
  'Any test fails → functionality cannot score above 4',
  'No new tests for new functionality → coverage cannot score above 4',
  'Stubbed implementation → product depth cannot score above 3',
  'All scores ≥ 7 trigger rubber-stamp suspicion',
] as const;

export const evidenceMetrics = [
  { label: 'Verdict', solo: 'FAIL', trio: 'PASS' },
  { label: 'Functionality', solo: '4 / 10', trio: '8 / 10' },
  { label: 'Average score', solo: '6.25', trio: '8.0' },
  { label: 'Duration', solo: '383s', trio: '619s (1.6x)' },
] as const;

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
    detail: '“Do not rubber-stamp weak work” stops being a note and becomes the workflow.',
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

export const useTrio = [
  'Features spanning multiple files or layers',
  'Tasks where “does it actually work?” is uncertain',
  'Medium-complexity work at the edge of model capability',
  'Changes where broken output is more expensive than extra runtime',
] as const;

export const skipTrio = [
  'Single-line fixes or formatting work',
  'Simple tasks the model already gets right first try',
  'Dependency bumps and obvious mechanical edits',
  'Work where the answer is already fully known',
] as const;

export const tieringRoles = [
  {
    model: 'Opus-class reasoning',
    role: 'Plan + evaluate',
    note: 'Use the expensive model where architecture and criticism matter most.',
  },
  {
    model: 'Sonnet-class execution',
    role: 'Build',
    note: 'Use the faster model where volume and iteration matter more than perfect first-principles reasoning.',
  },
] as const;

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

export const appendixCriteria = [
  ['Product depth', 'HIGH', '6', 'Features feel real, not stubbed'],
  ['Functionality', 'HIGH', '6', 'Behavior works under test'],
  ['Code quality', 'MEDIUM', '5', 'Architecture, readability, maintainability'],
  ['Test coverage', 'MEDIUM', '5', 'New behavior includes tests'],
] as const;

export const appendixCaveats = [
  'N=11 total runs across 5 benchmarks — the sample is directional, not definitive.',
  'Copilot CLI did not expose token cost data, so wall-clock duration is the cost proxy.',
  'Python tags shows evaluator leniency caveats: the solo score is numerically higher, but likely flatteringly so.',
  'Model-tiering and round-robin role rotation are industry practice / conjecture here, not a claim directly validated by Harnessa.',
] as const;

export const citations = [
  {
    label: 'Anthropic Labs — Harness Design for Long-Running Apps',
    href: 'https://www.anthropic.com/engineering/harness-design-long-running-apps',
  },
  {
    label: 'Harnessa repository',
    href: 'https://github.com/ridermw/harnessa',
  },
  {
    label: 'RESULTS.md — experimental details',
    href: 'https://github.com/ridermw/harnessa/blob/main/RESULTS.md',
  },
] as const;

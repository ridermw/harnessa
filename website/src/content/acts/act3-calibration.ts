/* ── Scene 11: karpathy-problem ─────────────────────────────────────── */

export const karpathyQuote = {
  text: "Used an LLM to improve my argument over 4 hours. Feeling great, so convincing! Fun idea — let's ask it to argue the opposite. LLM demolishes the entire argument. lol",
  author: 'Andrej Karpathy',
  insight: 'An LLM can argue both sides convincingly. A separate evaluator only works if it is calibrated to refuse empty praise.',
} as const;

/* ── Scene 12: anti-sycophancy ─────────────────────────────────────── */

export const criticRules = [
  'Any test fails → functionality cannot score above 4',
  'No new tests for new functionality → coverage cannot score above 4',
  'Stubbed implementation → product depth cannot score above 3',
  'All scores ≥ 7 trigger rubber-stamp suspicion',
] as const;

/* ── Scene 13: criteria-thresholds ─────────────────────────────────── */

export const criteriaThresholds = [
  { criterion: 'Product depth', weight: 'HIGH' as const, threshold: 6, meaning: 'Features feel real, not stubbed' },
  { criterion: 'Functionality', weight: 'HIGH' as const, threshold: 6, meaning: 'Behavior works under test' },
  { criterion: 'Code quality', weight: 'MEDIUM' as const, threshold: 5, meaning: 'Architecture, readability, maintainability' },
  { criterion: 'Test coverage', weight: 'MEDIUM' as const, threshold: 5, meaning: 'New behavior includes tests' },
] as const;

/** Appendix-format criteria (2D tuple array for backward compat). */
export const appendixCriteria = [
  ['Product depth', 'HIGH', '6', 'Features feel real, not stubbed'],
  ['Functionality', 'HIGH', '6', 'Behavior works under test'],
  ['Code quality', 'MEDIUM', '5', 'Architecture, readability, maintainability'],
  ['Test coverage', 'MEDIUM', '5', 'New behavior includes tests'],
] as const;

/* ── Scene 14: experiment-design ───────────────────────────────────── */

export const experimentDesign = {
  controls: [
    { variable: 'Model', value: 'claude-sonnet-4 (identical)' },
    { variable: 'Tools', value: 'Same Copilot CLI toolset' },
    { variable: 'Prompt', value: 'Same TASK.md per benchmark' },
  ],
  independentVariable: 'Architecture — solo (single agent) vs trio (planner → generator ↔ evaluator)',
  dependentVariables: ['Evaluator score', 'Functionality score', 'Verdict (PASS/FAIL)', 'Duration'],
} as const;

/* ── Scene 15: benchmark-matrix ────────────────────────────────────── */

export const benchmarkMatrix = [
  { id: 'small-bugfix-python', language: 'Python', size: 'Small', type: 'Bugfix', description: 'CLI arg parser ± sign bug' },
  { id: 'small-feature-typescript', language: 'TypeScript', size: 'Small', type: 'Feature', description: 'Retry with exponential backoff' },
  { id: 'small-bugfix-go', language: 'Go', size: 'Small', type: 'Bugfix', description: 'HTTP server connection pool race condition' },
  { id: 'medium-feature-python', language: 'Python', size: 'Medium', type: 'Feature', description: 'FastAPI TODO app tags feature' },
  { id: 'medium-feature-fullstack', language: 'TS/JS', size: 'Medium', type: 'Feature', description: 'React + Express real-time notifications' },
] as const;

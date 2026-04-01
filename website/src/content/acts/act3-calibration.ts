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
  { criterion: 'Product depth', weight: 'HIGH' as const, threshold: 6, meaning: 'Features fully realized vs. stubbed out', calibrationLow: 'Score 3: "Todo app with only add/remove, no persistence"', calibrationHigh: 'Score 8: "Todo app with categories, due dates, priority sorting, SQLite persistence"' },
  { criterion: 'Functionality', weight: 'HIGH' as const, threshold: 6, meaning: 'Does it actually work end-to-end when tested?', calibrationLow: 'Score 2: "API returns 500 on valid POST request"', calibrationHigh: 'Score 8: "All CRUD endpoints work, input validation present, proper error responses"' },
  { criterion: 'Code quality', weight: 'MEDIUM' as const, threshold: 5, meaning: 'Clean architecture, readability, maintainability', calibrationLow: 'Score 2: "Single 500-line file with no functions, global state everywhere"', calibrationHigh: 'Score 9: "Clean module separation, typed interfaces, dependency injection"' },
  { criterion: 'Test coverage', weight: 'MEDIUM' as const, threshold: 5, meaning: 'New behavior includes meaningful tests', calibrationLow: 'Score 1: "No tests at all"', calibrationHigh: 'Score 8: "Unit tests for business logic, integration tests for API, edge case coverage"' },
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
    { variable: 'Model', value: 'claude-sonnet-4 (identical for all agents)' },
    { variable: 'Prompt', value: 'Same TASK.md per benchmark' },
    { variable: 'Tools', value: 'Same Copilot CLI toolset' },
    { variable: 'Token budget', value: 'Same maximum token spend' },
    { variable: 'Wall-clock limit', value: 'Same maximum duration' },
  ],
  independentVariable: 'Architecture — solo (single agent, no feedback loop) vs trio (planner → generator ↔ evaluator)',
  dependentVariables: ['Evaluator score', 'Functionality score', 'Verdict (PASS/FAIL)', 'Duration'],
  coverage: {
    benchmarks: 5,
    languages: 3,
    languageList: ['Python', 'TypeScript', 'Go'],
    totalRuns: 11,
    runsNote: 'N=11 total runs — directional signal, not statistically significant',
  },
} as const;

/* ── Scene 15: benchmark-matrix ────────────────────────────────────── */

export const benchmarkMatrix = [
  { id: 'small-bugfix-python', language: 'Python', size: 'Small', type: 'Bugfix', description: 'CLI arg parser ± sign bug', loc: '~500 LOC', duration: '15–30 min' },
  { id: 'small-feature-typescript', language: 'TypeScript', size: 'Small', type: 'Feature', description: 'Retry with exponential backoff', loc: '~800 LOC', duration: '15–30 min' },
  { id: 'small-bugfix-go', language: 'Go', size: 'Small', type: 'Bugfix', description: 'HTTP server connection pool race condition', loc: '~600 LOC', duration: '15–30 min' },
  { id: 'medium-feature-python', language: 'Python', size: 'Medium', type: 'Feature', description: 'FastAPI TODO app tags feature', loc: '~1,700 LOC', duration: '60–90 min' },
  { id: 'medium-feature-fullstack', language: 'TS/JS', size: 'Medium', type: 'Feature', description: 'React + Express real-time notifications', loc: '~3,000 LOC', duration: '60–90 min' },
] as const;

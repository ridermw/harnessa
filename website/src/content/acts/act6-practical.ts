/* ── Scene 26: demo-flow ───────────────────────────────────────────── */

export const demoFlow = {
  command: "copilot -p '/harnessa Fix the authentication bug' --allow-all",
  phases: [
    { name: 'Planner', artifact: 'harnessa-spec.md', description: 'Reads task, surveys codebase, produces structured spec with acceptance criteria' },
    { name: 'Generator', artifact: 'harnessa-gen-report.md', description: 'Implements spec in bounded sprints, writes code, runs tests, commits changes' },
    { name: 'Evaluator', artifact: 'harnessa-eval.md', description: 'Reads diff + report (NOT the spec), grades against criteria, provides structured feedback or PASS verdict' },
  ],
  note: 'Runs inside any Copilot CLI session. No API keys needed — uses your Copilot subscription.',
  paths: {
    skill: { label: 'Copilot skill (/harnessa)', detail: 'Single session, simulated isolation via context resets between phases. Quick, low-overhead — for everyday use.' },
    harness: { label: 'Full harness (harnessa CLI)', detail: 'Real subprocess isolation, separate processes per agent. Structured telemetry, cross-model evaluation support — for benchmarking and research.' },
  },
} as const;

/* ── Scene 27: decision-tree ───────────────────────────────────────── */

export const useTrio = [
  'Features spanning multiple files or layers',
  'Tasks where "does it actually work?" is uncertain',
  'Medium-complexity work at the edge of model capability',
  'Changes where broken output is more expensive than extra runtime',
] as const;

export const skipTrio = [
  'Single-line fixes or formatting work',
  'Simple tasks the model already gets right first try',
  'Dependency bumps and obvious mechanical edits',
  'Work where the answer is already fully known',
] as const;

/* ── Scene 28: model-tiering ───────────────────────────────────────── */

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

/* ── Scene 29: round-robin ─────────────────────────────────────────── */

export const roundRobinConcepts = [
  {
    concept: 'Cross-model evaluation',
    description: 'Two different LLM models grade independently. Disagreements between models are treated as signal, not noise.',
  },
  {
    concept: 'Role rotation',
    description: 'Rotate which model plays which role across iterations — prevents one model\'s blind spots from dominating the pipeline.',
  },
  {
    concept: 'Reconciliation',
    description: 'When evaluators disagree on a score by more than a threshold, the run gets flagged for review instead of auto-passing.',
  },
] as const;

export const roundRobinCaveat =
  'Industry context, not Harnessa evidence. These concepts are conjecture and industry practice — not directly validated by our experiments. All Harnessa runs used a single model (claude-sonnet-4).' as const;

/* ── Scene 30: closing ─────────────────────────────────────────────── */

export const closingQuote = {
  text: "The space of interesting harness combinations doesn't shrink as models improve. It moves.",
  author: 'Anthropic Labs',
} as const;

/* ── Shared ────────────────────────────────────────────────────────── */

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

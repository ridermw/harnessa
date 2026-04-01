import type { DiagramSpec } from '../types';

export const diagram04FilesHandoff: DiagramSpec = {
  contractId: 'diagram-04-files-handoff',
  contractVersion: 1,
  primitive: 'flow',
  scene: 'files-on-disk',
  title: 'Files-on-Disk Handoff',
  nodes: [
    { id: 'task-prompt', label: 'TASK / PROMPT', type: 'event' },
    // Skill path
    { id: 'skill-spec', label: 'harnessa-spec.md', type: 'artifact', detail: 'skill path' },
    { id: 'skill-gen-report', label: 'harnessa-gen-report.md', type: 'artifact', detail: 'skill path' },
    { id: 'skill-eval', label: 'harnessa-eval.md', type: 'artifact', detail: 'skill path' },
    // Harness path
    { id: 'harness-spec', label: 'planner/spec.md', type: 'artifact', detail: 'harness path' },
    { id: 'harness-contracts', label: 'contracts/sprint-N-*.md', type: 'artifact', detail: 'harness path' },
    { id: 'harness-evals', label: 'evaluations/iteration-N.json', type: 'artifact', detail: 'harness path' },
    { id: 'harness-manifest', label: 'telemetry/run-manifest.json', type: 'artifact', detail: 'harness path' },
    { id: 'harness-report', label: 'report.md / replay', type: 'artifact', detail: 'harness path' },
  ],
  edges: [
    // Skill path
    { id: 'task-to-skill-spec', from: 'task-prompt', to: 'skill-spec', style: 'solid', direction: 'forward' },
    { id: 'skill-spec-to-gen', from: 'skill-spec', to: 'skill-gen-report', style: 'solid', direction: 'forward' },
    { id: 'skill-gen-to-eval', from: 'skill-gen-report', to: 'skill-eval', style: 'solid', direction: 'forward' },
    // Harness path
    { id: 'task-to-harness-spec', from: 'task-prompt', to: 'harness-spec', style: 'solid', direction: 'forward' },
    { id: 'harness-spec-to-contracts', from: 'harness-spec', to: 'harness-contracts', style: 'solid', direction: 'forward' },
    { id: 'harness-contracts-to-evals', from: 'harness-contracts', to: 'harness-evals', style: 'solid', direction: 'forward' },
    { id: 'harness-evals-to-manifest', from: 'harness-evals', to: 'harness-manifest', style: 'solid', direction: 'forward' },
    { id: 'harness-manifest-to-report', from: 'harness-manifest', to: 'harness-report', style: 'solid', direction: 'forward' },
  ],
  regions: [
    {
      id: 'skill-path',
      label: 'Skill Path',
      nodeIds: ['skill-spec', 'skill-gen-report', 'skill-eval'],
      style: 'group',
    },
    {
      id: 'harness-path',
      label: 'Harness Path',
      nodeIds: ['harness-spec', 'harness-contracts', 'harness-evals', 'harness-manifest', 'harness-report'],
      style: 'group',
    },
  ],
  renderHints: {
    layout: 'dual-track',
    direction: 'left-to-right',
  },
} as const;

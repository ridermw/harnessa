import type { DiagramSpec } from '../types';

export const diagram12DemoFlow: DiagramSpec = {
  contractId: 'diagram-12-demo-flow',
  contractVersion: 1,
  primitive: 'flow',
  scene: 'demo-flow',
  title: 'One-Command Demo Flow',
  nodes: [
    { id: 'command', label: "copilot -p '/harnessa Fix the authentication bug' --allow-all", type: 'action' },
    { id: 'planner', label: 'Planner', type: 'agent', accent: 'blue', detail: 'writes spec' },
    { id: 'generator', label: 'Generator', type: 'agent', accent: 'green', detail: 'implements' },
    { id: 'evaluator', label: 'Evaluator', type: 'agent', accent: 'red', detail: 'grades + bugs' },
  ],
  edges: [
    { id: 'command-to-planner', from: 'command', to: 'planner', style: 'solid', direction: 'forward' },
    { id: 'planner-to-generator', from: 'planner', to: 'generator', label: 'spec', style: 'solid', direction: 'forward' },
    { id: 'generator-to-evaluator', from: 'generator', to: 'evaluator', label: 'code', style: 'solid', direction: 'forward' },
  ],
  annotations: [
    { id: 'path-note', text: 'Copilot skill path; harness variant has more structure', position: 'bottom' },
  ],
  renderHints: {
    layout: 'top-to-bottom',
    commandPosition: 'top',
  },
} as const;

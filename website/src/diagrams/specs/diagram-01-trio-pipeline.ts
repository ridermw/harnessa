import type { DiagramSpec } from '../types';

export const diagram01TrioPipeline: DiagramSpec = {
  contractId: 'diagram-01-trio-pipeline',
  contractVersion: 1,
  primitive: 'flow',
  scene: 'trio-pipeline',
  title: 'Trio Pipeline',
  nodes: [
    { id: 'planner', label: 'Planner', type: 'agent', accent: 'blue' },
    { id: 'generator', label: 'Generator', type: 'agent', accent: 'green' },
    { id: 'evaluator', label: 'Evaluator', type: 'agent', accent: 'red' },
  ],
  edges: [
    { id: 'planner-to-generator', from: 'planner', to: 'generator', label: 'spec', style: 'solid', direction: 'forward' },
    { id: 'generator-to-evaluator', from: 'generator', to: 'evaluator', label: 'code', style: 'solid', direction: 'forward' },
    { id: 'evaluator-to-generator', from: 'evaluator', to: 'generator', label: 'grade + bugs', style: 'dashed', direction: 'back' },
  ],
  annotations: [
    { id: 'telemetry-bar', text: 'TELEMETRY', position: 'bottom' },
    { id: 'mode-qualifier', text: 'TRIO MODE', position: 'top' },
  ],
  renderHints: {
    direction: 'left-to-right',
    loopEdge: 'evaluator-to-generator',
  },
} as const;

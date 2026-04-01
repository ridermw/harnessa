import type { DiagramSpec } from '../types';

export const diagram03SprintContract: DiagramSpec = {
  contractId: 'diagram-03-sprint-contract',
  contractVersion: 1,
  primitive: 'cycle',
  scene: 'sprint-contracts',
  title: 'Sprint Contract Negotiation',
  nodes: [
    { id: 'planner-spec', label: 'PLANNER SPEC / OUTCOME', type: 'agent', accent: 'blue' },
    { id: 'generator', label: 'Generator', type: 'agent', accent: 'green' },
    { id: 'evaluator', label: 'Evaluator', type: 'agent', accent: 'red' },
    { id: 'agreed-contract', label: 'AGREED SPRINT CONTRACT', type: 'artifact', accent: 'gold' },
  ],
  edges: [
    { id: 'planner-feeds', from: 'planner-spec', to: 'generator', label: 'feeds into negotiation', style: 'solid', direction: 'forward' },
    { id: 'gen-to-eval', from: 'generator', to: 'evaluator', label: 'proposal', style: 'solid', direction: 'forward' },
    { id: 'eval-to-gen', from: 'evaluator', to: 'generator', label: 'review / added criteria', style: 'dashed', direction: 'back' },
    { id: 'negotiation-output', from: 'evaluator', to: 'agreed-contract', label: 'agreed', style: 'double', direction: 'forward' },
  ],
  renderHints: {
    layout: 'vertical-cycle',
    plannerPosition: 'top',
    contractPosition: 'bottom',
  },
} as const;

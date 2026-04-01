import type { DiagramSpec } from '../types';

export const diagram13DecisionTree: DiagramSpec = {
  contractId: 'diagram-13-decision-tree',
  contractVersion: 1,
  primitive: 'tree',
  scene: 'decision-tree',
  title: 'Decision Tree',
  nodes: [
    { id: 'root-question', label: 'Is the task at the edge of model capability?', type: 'action' },
    { id: 'no-branch', label: 'No', type: 'state' },
    { id: 'yes-branch', label: 'Yes', type: 'state' },
    { id: 'use-solo', label: 'Use solo mode (avoid overhead)', type: 'action', accent: 'blue' },
    { id: 'use-trio', label: 'Use trio/harness (buy skepticism + iteration)', type: 'action', accent: 'green' },
  ],
  edges: [
    { id: 'root-to-no', from: 'root-question', to: 'no-branch', label: 'No', style: 'solid', direction: 'forward' },
    { id: 'root-to-yes', from: 'root-question', to: 'yes-branch', label: 'Yes', style: 'solid', direction: 'forward' },
    { id: 'no-to-solo', from: 'no-branch', to: 'use-solo', style: 'solid', direction: 'forward' },
    { id: 'yes-to-trio', from: 'yes-branch', to: 'use-trio', style: 'solid', direction: 'forward' },
  ],
  renderHints: {
    layout: 'top-to-bottom-tree',
    rootNode: 'root-question',
  },
} as const;

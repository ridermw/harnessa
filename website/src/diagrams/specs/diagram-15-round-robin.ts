import type { DiagramSpec } from '../types';

export const diagram15RoundRobin: DiagramSpec = {
  contractId: 'diagram-15-round-robin',
  contractVersion: 1,
  primitive: 'cycle',
  scene: 'round-robin',
  title: 'Round-Robin Model Rotation',
  nodes: [
    { id: 'claude-planner', label: 'Claude / Planner', type: 'agent', accent: 'blue' },
    { id: 'gpt-builder', label: 'GPT / Builder', type: 'agent', accent: 'green' },
    { id: 'gemini-evaluator', label: 'Gemini / Evaluator', type: 'agent', accent: 'red' },
  ],
  edges: [
    { id: 'claude-to-gpt', from: 'claude-planner', to: 'gpt-builder', style: 'solid', direction: 'forward' },
    { id: 'gpt-to-gemini', from: 'gpt-builder', to: 'gemini-evaluator', style: 'solid', direction: 'forward' },
    { id: 'gemini-to-claude', from: 'gemini-evaluator', to: 'claude-planner', style: 'solid', direction: 'forward' },
  ],
  annotations: [
    { id: 'conjecture-label', text: 'CONJECTURE', position: 'top' },
  ],
  renderHints: {
    layout: 'circular',
    rotation: 'clockwise',
  },
} as const;

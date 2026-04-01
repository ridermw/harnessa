import type { DiagramSpec } from '../types';

export const diagram14ModelTiering: DiagramSpec = {
  contractId: 'diagram-14-model-tiering',
  contractVersion: 1,
  primitive: 'comparison',
  scene: 'model-tiering',
  title: 'Model Tiering',
  nodes: [
    { id: 'opus-class', label: 'Opus-class reasoning', type: 'system', accent: 'gold', detail: 'Plan + Evaluate, $$$' },
    { id: 'sonnet-class', label: 'Sonnet-class speed', type: 'system', accent: 'blue', detail: 'Build / Execute, $' },
  ],
  edges: [],
  annotations: [
    { id: 'caveat', text: 'Industry pattern / not directly tested here', position: 'bottom' },
  ],
  renderHints: {
    layout: 'side-by-side',
    leftAccent: 'gold',
    rightAccent: 'blue',
  },
} as const;

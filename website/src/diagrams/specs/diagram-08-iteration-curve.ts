import type { DiagramSpec } from '../types';

export const diagram08IterationCurve: DiagramSpec = {
  contractId: 'diagram-08-iteration-curve',
  contractVersion: 1,
  primitive: 'flow',
  scene: 'iteration-curve',
  title: 'Iteration Curve',
  nodes: [
    { id: 'iter-1', label: 'iter 1', type: 'event' },
    { id: 'iter-2', label: 'iter 2', type: 'event' },
    { id: 'iter-3', label: 'iter 3', type: 'event' },
    { id: 'bugfix-series', label: 'bugfix', type: 'artifact', detail: 'score series' },
    { id: 'tags-series', label: 'tags', type: 'artifact', detail: 'score series' },
    { id: 'go-series', label: 'go', type: 'artifact', detail: 'score series' },
  ],
  edges: [
    { id: 'iter-1-to-2', from: 'iter-1', to: 'iter-2', style: 'solid', direction: 'forward' },
    { id: 'iter-2-to-3', from: 'iter-2', to: 'iter-3', style: 'solid', direction: 'forward' },
  ],
  annotations: [
    { id: 'y-axis', text: 'Y: Score (avg)', position: 'inline' },
    { id: 'x-axis', text: 'X: Iterations', position: 'bottom' },
    { id: 'avg-guide', text: 'AVG SCORE GUIDE = 7', position: 'inline' },
    { id: 'chart-note', text: 'Shows average-score movement, not final verdict', position: 'bottom' },
  ],
  renderHints: {
    layout: 'chart',
    chartType: 'line',
    guideLine: '7',
  },
} as const;

import type { DiagramSpec } from '../types';

export const diagram07Scorecard: DiagramSpec = {
  contractId: 'diagram-07-scorecard',
  contractVersion: 1,
  primitive: 'grid',
  scene: 'full-scorecard',
  title: 'Scorecard Anatomy',
  nodes: [
    { id: 'python-bugfix', label: 'Python bugfix', type: 'event', detail: 'Winner: Trio' },
    { id: 'typescript-feature', label: 'TypeScript feature', type: 'event', detail: 'Winner: Tie' },
    { id: 'go-race', label: 'Go race condition', type: 'event', detail: 'Winner: Tie' },
    { id: 'python-tags', label: 'Python tags', type: 'event', detail: 'Winner: Caveat — 8.5 vs 8.0, likely solo leniency' },
    { id: 'fullstack-notif', label: 'Fullstack notifications', type: 'event', detail: 'Winner: Trio — categorical' },
  ],
  edges: [],
  annotations: [
    { id: 'grid-header', text: 'Benchmark | Winner | Notes', position: 'top' },
  ],
  renderHints: {
    layout: 'table',
    columns: 'benchmark,winner,notes',
    highlightRow: 'fullstack-notif',
  },
} as const;

import type { DiagramSpec } from '../types';

export const diagram00RailStates: DiagramSpec = {
  contractId: 'diagram-00-rail-states',
  contractVersion: 1,
  primitive: 'comparison',
  scene: 'global',
  title: 'Operator Rail States',
  nodes: [
    { id: 'topbar-closed', label: 'TOPBAR', type: 'system' },
    { id: 'main-closed', label: 'MAIN SCENE CONTENT', type: 'system', detail: 'full-width' },
    { id: 'topbar-open', label: 'TOPBAR', type: 'system' },
    { id: 'main-open', label: 'MAIN SCENE CONTENT', type: 'system' },
    { id: 'scene-rail', label: 'Scene List Rail', type: 'system' },
  ],
  edges: [],
  regions: [
    {
      id: 'closed-state',
      label: 'CLOSED',
      nodeIds: ['topbar-closed', 'main-closed'],
      style: 'container',
    },
    {
      id: 'open-state',
      label: 'OPEN',
      nodeIds: ['topbar-open', 'main-open', 'scene-rail'],
      style: 'container',
    },
  ],
  renderHints: {
    layout: 'side-by-side',
    closedLayout: 'topbar + full-width main',
    openLayout: 'topbar + main + rail',
  },
} as const;

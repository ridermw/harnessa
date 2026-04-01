import type { DiagramSpec } from '../types';

export const diagram02GoodhartBoundary: DiagramSpec = {
  contractId: 'diagram-02-goodhart-boundary',
  contractVersion: 1,
  primitive: 'comparison',
  scene: 'goodhart-boundary',
  title: 'Goodhart Boundary',
  nodes: [
    { id: 'gen-app', label: 'app/', type: 'artifact' },
    { id: 'gen-tests', label: 'tests/', type: 'artifact' },
    { id: 'gen-eval-hidden', label: '_eval/ (hidden)', type: 'artifact', detail: 'not visible to generator' },
    { id: 'eval-app', label: 'app/', type: 'artifact' },
    { id: 'eval-tests', label: 'tests/', type: 'artifact' },
    { id: 'eval-eval', label: '_eval/', type: 'artifact', detail: 'visible to evaluator' },
    { id: 'boundary', label: 'BOUNDARY', type: 'system' },
  ],
  edges: [],
  regions: [
    {
      id: 'generator-view',
      label: 'GENERATOR VIEW (limited)',
      nodeIds: ['gen-app', 'gen-tests', 'gen-eval-hidden'],
      style: 'boundary',
    },
    {
      id: 'evaluator-view',
      label: 'EVALUATOR VIEW (full)',
      nodeIds: ['eval-app', 'eval-tests', 'eval-eval'],
      style: 'boundary',
    },
  ],
  annotations: [
    { id: 'benchmark-path', text: 'benchmarks/foo/', position: 'top' },
  ],
  renderHints: {
    layout: 'side-by-side',
    boundaryStyle: 'dashed-vertical-divider',
    hiddenNodeStyle: 'dimmed',
  },
} as const;

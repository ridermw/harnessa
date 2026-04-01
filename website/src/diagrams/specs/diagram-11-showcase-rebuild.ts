import type { DiagramSpec } from '../types';

export const diagram11ShowcaseRebuild: DiagramSpec = {
  contractId: 'diagram-11-showcase-rebuild',
  contractVersion: 1,
  primitive: 'comparison',
  scene: 'showcase-rebuild',
  title: 'Showcase Rebuild',
  nodes: [
    { id: 'iter-1', label: 'ITERATION 1', type: 'state', accent: 'red', detail: '1 file, 1206-line monolith, CDN React/Babel, 0 tests' },
    { id: 'evaluator-fail', label: 'EVALUATOR FAIL', type: 'action', accent: 'red' },
    { id: 'iter-2', label: 'ITERATION 2', type: 'state', accent: 'green', detail: '32 files, routed app, components + 7 tests, proper separation' },
  ],
  edges: [
    { id: 'iter1-to-fail', from: 'iter-1', to: 'evaluator-fail', style: 'solid', direction: 'forward' },
    { id: 'fail-to-iter2', from: 'evaluator-fail', to: 'iter-2', style: 'solid', direction: 'forward' },
  ],
  renderHints: {
    layout: 'left-center-right',
    bridgeNode: 'evaluator-fail',
  },
} as const;

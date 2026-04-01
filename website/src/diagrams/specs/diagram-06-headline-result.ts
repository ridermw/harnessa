import type { DiagramSpec } from '../types';

export const diagram06HeadlineResult: DiagramSpec = {
  contractId: 'diagram-06-headline-result',
  contractVersion: 1,
  primitive: 'state',
  scene: 'headline-result',
  title: 'Headline FAIL → PASS',
  nodes: [
    { id: 'solo-fail', label: 'SOLO FAIL', type: 'state', accent: 'red', detail: 'func=4, broken core' },
    { id: 'trio-pass', label: 'TRIO PASS', type: 'state', accent: 'green', detail: 'func=8, working core' },
  ],
  edges: [
    { id: 'fail-to-pass', from: 'solo-fail', to: 'trio-pass', label: 'planner + adversarial loop', style: 'double', direction: 'forward' },
  ],
  renderHints: {
    layout: 'left-to-right',
    leftAccent: 'red',
    rightAccent: 'green',
    transitionStyle: 'dramatic',
  },
} as const;

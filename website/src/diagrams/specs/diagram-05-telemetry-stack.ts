import type { DiagramSpec } from '../types';

export const diagram05TelemetryStack: DiagramSpec = {
  contractId: 'diagram-05-telemetry-stack',
  contractVersion: 1,
  primitive: 'stack',
  scene: 'telemetry-layer',
  title: 'Telemetry Stack',
  nodes: [
    { id: 'run-manifest', label: 'RUN MANIFEST', type: 'artifact' },
    { id: 'durations', label: 'planner / gen / eval durations', type: 'artifact' },
    { id: 'scores', label: 'scores', type: 'artifact' },
    { id: 'bugs', label: 'bugs', type: 'artifact' },
    { id: 'verdict', label: 'verdict', type: 'artifact' },
    { id: 'iterations', label: 'iterations', type: 'artifact' },
    { id: 'contract-metrics', label: 'contract metrics', type: 'artifact' },
    { id: 'test-counts', label: 'visible / eval tests', type: 'artifact' },
    { id: 'model-ids', label: 'model ids', type: 'artifact' },
    { id: 'quality-trends', label: 'quality trends', type: 'artifact' },
    { id: 'artifact-refs', label: 'artifact refs', type: 'artifact' },
    { id: 'run-validity', label: 'run validity', type: 'artifact' },
  ],
  edges: [],
  regions: [
    {
      id: 'manifest-panel',
      label: 'RUN MANIFEST',
      nodeIds: [
        'durations', 'scores', 'bugs', 'verdict', 'iterations',
        'contract-metrics', 'test-counts', 'model-ids',
        'quality-trends', 'artifact-refs', 'run-validity',
      ],
      style: 'container',
    },
  ],
  renderHints: {
    layout: 'stacked-vertical',
    panelStyle: 'single-card',
  },
} as const;

import type { DiagramSpec } from '../types';

export const diagram16SystemTopology: DiagramSpec = {
  contractId: 'diagram-16-system-topology',
  contractVersion: 1,
  primitive: 'stack',
  scene: 'telemetry-layer',
  title: 'Detailed System Topology',
  nodes: [
    { id: 'orchestrator', label: 'ORCHESTRATOR', type: 'system' },
    { id: 'planner', label: 'Planner', type: 'agent', accent: 'blue' },
    { id: 'contract-negotiator', label: 'Contract Negotiator', type: 'system' },
    { id: 'generator', label: 'Generator', type: 'agent', accent: 'green' },
    { id: 'evaluator', label: 'Evaluator', type: 'agent', accent: 'red' },
    { id: 'criteria-loader', label: 'Criteria Loader', type: 'system' },
    { id: 'response-adapter', label: 'Response Adapter', type: 'system' },
    { id: 'reconciler', label: 'Reconciler', type: 'system' },
    { id: 'isolation', label: 'Isolation / Worktrees', type: 'system' },
    { id: 'telemetry', label: 'Telemetry', type: 'system' },
    { id: 'reports', label: 'Reports', type: 'artifact' },
    { id: 'replay', label: 'Replay', type: 'artifact' },
  ],
  edges: [
    { id: 'planner-to-negotiator', from: 'planner', to: 'contract-negotiator', style: 'solid', direction: 'forward' },
    { id: 'negotiator-to-generator', from: 'contract-negotiator', to: 'generator', style: 'solid', direction: 'forward' },
    { id: 'generator-to-evaluator', from: 'generator', to: 'evaluator', style: 'solid', direction: 'forward' },
    { id: 'evaluator-to-generator', from: 'evaluator', to: 'generator', label: 'feedback loop', style: 'dashed', direction: 'back' },
  ],
  regions: [
    {
      id: 'agent-layer',
      label: 'Agent Layer',
      nodeIds: ['planner', 'contract-negotiator', 'generator', 'evaluator'],
      style: 'group',
    },
    {
      id: 'infra-layer',
      label: 'Infrastructure',
      nodeIds: ['criteria-loader', 'response-adapter', 'reconciler'],
      style: 'group',
    },
    {
      id: 'platform-layer',
      label: 'Platform',
      nodeIds: ['isolation', 'telemetry'],
      style: 'group',
    },
    {
      id: 'output-layer',
      label: 'Output',
      nodeIds: ['reports', 'replay'],
      style: 'group',
    },
    {
      id: 'orchestrator-container',
      label: 'ORCHESTRATOR',
      nodeIds: [
        'planner', 'contract-negotiator', 'generator', 'evaluator',
        'criteria-loader', 'response-adapter', 'reconciler',
        'isolation', 'telemetry', 'reports', 'replay',
      ],
      style: 'container',
    },
  ],
  renderHints: {
    layout: 'layered-stack',
    containerNode: 'orchestrator',
  },
} as const;

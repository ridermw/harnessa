import type { DiagramSpec } from '../types';

export const diagram10EcosystemNetwork: DiagramSpec = {
  contractId: 'diagram-10-ecosystem-network',
  contractVersion: 1,
  primitive: 'cycle',
  scene: 'ecosystem-network',
  title: 'Ecosystem / Outside Voice Network',
  nodes: [
    { id: 'adversarial-pattern', label: 'ADVERSARIAL PATTERN', type: 'system', accent: 'gold' },
    { id: 'anthropic', label: 'Anthropic', type: 'system' },
    { id: 'openhands', label: 'OpenHands', type: 'system' },
    { id: 'openai', label: 'OpenAI', type: 'system' },
    { id: 'gstack', label: 'GStack / outside voice', type: 'system', detail: '/review → /codex → compare' },
  ],
  edges: [
    { id: 'anthropic-to-center', from: 'anthropic', to: 'adversarial-pattern', style: 'solid', direction: 'forward' },
    { id: 'openhands-to-center', from: 'openhands', to: 'adversarial-pattern', style: 'solid', direction: 'forward' },
    { id: 'openai-to-center', from: 'openai', to: 'adversarial-pattern', style: 'solid', direction: 'forward' },
    { id: 'gstack-to-center', from: 'gstack', to: 'adversarial-pattern', style: 'solid', direction: 'forward' },
  ],
  annotations: [
    { id: 'gstack-callout', text: '/review → /codex → compare', position: 'inline' },
  ],
  renderHints: {
    layout: 'hub-and-spoke',
    centerNode: 'adversarial-pattern',
  },
} as const;

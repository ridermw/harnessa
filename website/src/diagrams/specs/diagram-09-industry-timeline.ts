import type { DiagramSpec } from '../types';

export const diagram09IndustryTimeline: DiagramSpec = {
  contractId: 'diagram-09-industry-timeline',
  contractVersion: 1,
  primitive: 'timeline',
  scene: 'industry-timeline',
  title: 'Industry Timeline',
  nodes: [
    { id: 'research-system', label: '2025 Research System', type: 'event' },
    { id: 'c-compiler', label: 'Feb 2026 C Compiler', type: 'event' },
    { id: 'harness-design', label: 'Mar 2026 Harness Design', type: 'event' },
    { id: 'claude-code', label: 'Claude Code', type: 'event' },
    { id: 'symphony', label: 'Symphony', type: 'event' },
  ],
  edges: [
    { id: 'research-to-compiler', from: 'research-system', to: 'c-compiler', style: 'solid', direction: 'forward' },
    { id: 'compiler-to-harness', from: 'c-compiler', to: 'harness-design', style: 'solid', direction: 'forward' },
    { id: 'harness-to-claude', from: 'harness-design', to: 'claude-code', style: 'solid', direction: 'forward' },
    { id: 'claude-to-symphony', from: 'claude-code', to: 'symphony', style: 'solid', direction: 'forward' },
  ],
  annotations: [
    { id: 'context-label', text: 'INDUSTRY CONTEXT (outside voice)', position: 'top' },
    { id: 'convergence', text: 'Convergence: multiple teams arriving at the same pattern', position: 'bottom' },
  ],
  renderHints: {
    layout: 'horizontal-timeline',
  },
} as const;

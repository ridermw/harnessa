import type { DiagramSpec } from '../types';

function accentColor(accent?: string): string {
  switch (accent) {
    case 'blue': return 'var(--signal-blue)';
    case 'green': return 'var(--signal-green)';
    case 'amber': case 'gold': return 'var(--signal-amber)';
    case 'red': return 'var(--signal-red)';
    default: return 'var(--border)';
  }
}

export function StateDiagram({ spec }: { spec: DiagramSpec }): JSX.Element {
  const isDramatic = spec.renderHints?.transitionStyle === 'dramatic';
  const edge = spec.edges[0];

  // Typically two nodes: before and after state
  const leftNode = spec.nodes[0];
  const rightNode = spec.nodes[1];

  return (
    <div className={`dg-state ${isDramatic ? 'dg-state--dramatic' : ''}`} data-diagram-id={spec.contractId}>
      {leftNode && (
        <div className="dg-state__card dg-state__card--before" data-node-id={leftNode.id} style={{ '--node-accent': accentColor(leftNode.accent) } as React.CSSProperties}>
          <span className="dg-node__type">{leftNode.type ?? 'state'}</span>
          <strong className="dg-node__label">{leftNode.label}</strong>
          {leftNode.detail && <span className="dg-node__detail">{leftNode.detail}</span>}
        </div>
      )}
      {edge && (
        <div className={`dg-state__transition ${edge.style === 'double' ? 'dg-state__transition--double' : ''}`} data-edge-id={edge.id}>
          <div className="dg-state__arrow" aria-hidden="true" />
          {edge.label && <span className="dg-state__label">{edge.label}</span>}
        </div>
      )}
      {rightNode && (
        <div className="dg-state__card dg-state__card--after" data-node-id={rightNode.id} style={{ '--node-accent': accentColor(rightNode.accent) } as React.CSSProperties}>
          <span className="dg-node__type">{rightNode.type ?? 'state'}</span>
          <strong className="dg-node__label">{rightNode.label}</strong>
          {rightNode.detail && <span className="dg-node__detail">{rightNode.detail}</span>}
        </div>
      )}
    </div>
  );
}

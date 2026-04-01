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

export function CycleDiagram({ spec }: { spec: DiagramSpec }): JSX.Element {
  const layout = spec.renderHints?.layout ?? 'circular';
  const isHub = layout === 'hub-and-spoke';
  const centerNodeId = spec.renderHints?.centerNode;
  const topAnnotations = spec.annotations?.filter(a => a.position === 'top') ?? [];
  const bottomAnnotations = spec.annotations?.filter(a => a.position === 'bottom') ?? [];
  const inlineAnnotations = spec.annotations?.filter(a => a.position === 'inline') ?? [];

  if (isHub && centerNodeId) {
    const centerNode = spec.nodes.find(n => n.id === centerNodeId);
    const spokeNodes = spec.nodes.filter(n => n.id !== centerNodeId);

    return (
      <div className="dg-cycle dg-cycle--hub" data-diagram-id={spec.contractId}>
        {topAnnotations.map(a => (
          <div key={a.id} className="dg-annotation dg-annotation--top">{a.text}</div>
        ))}
        <div className="dg-cycle__hub-layout">
          <div className="dg-cycle__spokes">
            {spokeNodes.map(node => {
              const edge = spec.edges.find(e => e.from === node.id || e.to === node.id);
              return (
                <div key={node.id} className="dg-cycle__spoke">
                  <div className="dg-cycle__node" data-node-id={node.id} style={{ '--node-accent': accentColor(node.accent) } as React.CSSProperties}>
                    <span className="dg-node__label">{node.label}</span>
                    {node.detail && <span className="dg-node__detail">{node.detail}</span>}
                  </div>
                  {edge && <div className="dg-cycle__spoke-line" data-edge-id={edge.id} aria-hidden="true" />}
                </div>
              );
            })}
          </div>
          {centerNode && (
            <div className="dg-cycle__center" data-node-id={centerNode.id} style={{ '--node-accent': accentColor(centerNode.accent) } as React.CSSProperties}>
              <span className="dg-node__label">{centerNode.label}</span>
            </div>
          )}
        </div>
        {inlineAnnotations.map(a => (
          <div key={a.id} className="dg-annotation dg-annotation--inline">{a.text}</div>
        ))}
        {bottomAnnotations.map(a => (
          <div key={a.id} className="dg-annotation dg-annotation--bottom">{a.text}</div>
        ))}
      </div>
    );
  }

  // Circular / vertical-cycle layout
  return (
    <div className={`dg-cycle ${layout === 'vertical-cycle' ? 'dg-cycle--vertical' : 'dg-cycle--circular'}`} data-diagram-id={spec.contractId}>
      {topAnnotations.map(a => (
        <div key={a.id} className="dg-annotation dg-annotation--top">{a.text}</div>
      ))}
      <div className="dg-cycle__ring">
        {spec.nodes.map((node, index) => {
          const outEdge = spec.edges.find(e => e.from === node.id);
          return (
            <div key={node.id} className="dg-cycle__step">
              <div className="dg-cycle__node" data-node-id={node.id} style={{ '--node-accent': accentColor(node.accent) } as React.CSSProperties}>
                {node.type && <span className="dg-node__type">{node.type}</span>}
                <span className="dg-node__label">{node.label}</span>
                {node.detail && <span className="dg-node__detail">{node.detail}</span>}
              </div>
              {outEdge && (
                <div className={`dg-cycle__edge ${outEdge.style === 'dashed' ? 'dg-cycle__edge--dashed' : ''} ${outEdge.style === 'double' ? 'dg-cycle__edge--double' : ''}`} data-edge-id={outEdge.id}>
                  <div className="dg-cycle__arrow" aria-hidden="true" />
                  {outEdge.label && <span className="dg-cycle__edge-label">{outEdge.label}</span>}
                </div>
              )}
              {/* Show closing arrow on last node to indicate loop */}
              {index === spec.nodes.length - 1 && !outEdge && spec.edges.find(e => e.from === node.id) && (
                <div className="dg-cycle__loop-indicator" aria-hidden="true" />
              )}
            </div>
          );
        })}
      </div>
      {bottomAnnotations.map(a => (
        <div key={a.id} className="dg-annotation dg-annotation--bottom">{a.text}</div>
      ))}
    </div>
  );
}

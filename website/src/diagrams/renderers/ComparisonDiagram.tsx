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

export function ComparisonDiagram({ spec }: { spec: DiagramSpec }): JSX.Element {
  const regions = spec.regions ?? [];
  const topAnnotations = spec.annotations?.filter(a => a.position === 'top') ?? [];
  const bottomAnnotations = spec.annotations?.filter(a => a.position === 'bottom') ?? [];

  // If we have regions, group nodes by region
  const hasRegions = regions.length >= 2;
  const leftRegion = hasRegions ? regions[0] : null;
  const rightRegion = hasRegions ? regions[1] : null;

  // Nodes not in any region (bridge nodes like "BOUNDARY")
  const regionNodeIds = new Set(regions.flatMap(r => [...r.nodeIds]));
  const bridgeNodes = spec.nodes.filter(n => !regionNodeIds.has(n.id));

  // For non-region comparisons (like model-tiering, showcase-rebuild), split nodes
  const leftNodes = leftRegion
    ? spec.nodes.filter(n => leftRegion.nodeIds.includes(n.id))
    : spec.nodes.filter((_, i) => i < Math.ceil(spec.nodes.length / 2));
  const rightNodes = rightRegion
    ? spec.nodes.filter(n => rightRegion.nodeIds.includes(n.id))
    : spec.nodes.filter((_, i) => i >= Math.ceil(spec.nodes.length / 2));

  // For showcase-rebuild style with a bridge node
  const hasBridge = spec.renderHints?.bridgeNode;
  const bridgeNode = hasBridge ? spec.nodes.find(n => n.id === hasBridge) : null;
  const isBridgeLayout = spec.renderHints?.layout === 'left-center-right';

  return (
    <div className="dg-comparison" data-diagram-id={spec.contractId}>
      {topAnnotations.map(a => (
        <div key={a.id} className="dg-annotation dg-annotation--top">{a.text}</div>
      ))}
      <div className={`dg-comparison__panels ${isBridgeLayout ? 'dg-comparison__panels--three' : ''}`}>
        <div className="dg-comparison__side dg-comparison__side--left">
          {leftRegion && <div className="dg-comparison__region-label">{leftRegion.label}</div>}
          {leftNodes.map(node => (
            <div key={node.id} className={`dg-comparison__node ${spec.renderHints?.hiddenNodeStyle === 'dimmed' && node.detail?.includes('not visible') ? 'dg-comparison__node--dimmed' : ''}`} data-node-id={node.id} style={{ '--node-accent': accentColor(node.accent) } as React.CSSProperties}>
              <span className="dg-node__label">{node.label}</span>
              {node.detail && <span className="dg-node__detail">{node.detail}</span>}
            </div>
          ))}
        </div>

        {isBridgeLayout && bridgeNode ? (
          <div className="dg-comparison__bridge" data-node-id={bridgeNode.id}>
            <span className="dg-node__label">{bridgeNode.label}</span>
            {bridgeNode.detail && <span className="dg-node__detail">{bridgeNode.detail}</span>}
            {spec.edges.map(e => (
              <div key={e.id} className="dg-comparison__edge-arrow" data-edge-id={e.id} />
            ))}
          </div>
        ) : (
          <div className="dg-comparison__divider" aria-hidden="true">
            {bridgeNodes.map(n => (
              <span key={n.id} className="dg-comparison__boundary-label" data-node-id={n.id}>{n.label}</span>
            ))}
          </div>
        )}

        <div className="dg-comparison__side dg-comparison__side--right">
          {rightRegion && <div className="dg-comparison__region-label">{rightRegion.label}</div>}
          {rightNodes.map(node => (
            <div key={node.id} className="dg-comparison__node" data-node-id={node.id} style={{ '--node-accent': accentColor(node.accent) } as React.CSSProperties}>
              <span className="dg-node__label">{node.label}</span>
              {node.detail && <span className="dg-node__detail">{node.detail}</span>}
            </div>
          ))}
        </div>
      </div>
      {bottomAnnotations.map(a => (
        <div key={a.id} className="dg-annotation dg-annotation--bottom">{a.text}</div>
      ))}
    </div>
  );
}

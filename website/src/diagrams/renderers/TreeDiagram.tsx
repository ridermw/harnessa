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

export function TreeDiagram({ spec }: { spec: DiagramSpec }): JSX.Element {
  const rootId = spec.renderHints?.rootNode ?? spec.nodes[0]?.id;
  const rootNode = spec.nodes.find(n => n.id === rootId);

  // Get children edges from root
  const rootEdges = spec.edges.filter(e => e.from === rootId);

  // Build branches: each branch is rootEdge -> intermediate node -> leaf edge -> leaf node
  const branches = rootEdges.map(edge => {
    const intermediate = spec.nodes.find(n => n.id === edge.to);
    const leafEdge = spec.edges.find(e => e.from === edge.to);
    const leaf = leafEdge ? spec.nodes.find(n => n.id === leafEdge.to) : null;
    return { edge, intermediate, leafEdge, leaf };
  });

  return (
    <div className="dg-tree" data-diagram-id={spec.contractId}>
      {rootNode && (
        <div className="dg-tree__root" data-node-id={rootNode.id}>
          <span className="dg-node__label">{rootNode.label}</span>
          {rootNode.detail && <span className="dg-node__detail">{rootNode.detail}</span>}
        </div>
      )}
      <div className="dg-tree__branches">
        {branches.map(({ edge, intermediate, leafEdge, leaf }) => (
          <div key={edge.id} className="dg-tree__branch">
            <div className="dg-tree__edge" data-edge-id={edge.id}>
              {edge.label && <span className="dg-tree__edge-label">{edge.label}</span>}
            </div>
            {intermediate && (
              <div className="dg-tree__node dg-tree__node--intermediate" data-node-id={intermediate.id}>
                <span className="dg-node__label">{intermediate.label}</span>
              </div>
            )}
            {leafEdge && (
              <div className="dg-tree__edge" data-edge-id={leafEdge.id}>
                {leafEdge.label && <span className="dg-tree__edge-label">{leafEdge.label}</span>}
              </div>
            )}
            {leaf && (
              <div className="dg-tree__node dg-tree__node--leaf" data-node-id={leaf.id} style={{ '--node-accent': accentColor(leaf.accent) } as React.CSSProperties}>
                <span className="dg-node__label">{leaf.label}</span>
                {leaf.detail && <span className="dg-node__detail">{leaf.detail}</span>}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

import type { DiagramSpec, DiagramNode, DiagramEdge } from '../types';

function accentColor(accent?: string): string {
  switch (accent) {
    case 'blue': return 'var(--signal-blue)';
    case 'green': return 'var(--signal-green)';
    case 'amber': case 'gold': return 'var(--signal-amber)';
    case 'red': return 'var(--signal-red)';
    default: return 'var(--border)';
  }
}

function nodeById(nodes: readonly DiagramNode[], id: string): DiagramNode | undefined {
  return nodes.find(n => n.id === id);
}

function FlowEdge({ edge }: { edge: DiagramEdge }): JSX.Element {
  const isDashed = edge.style === 'dashed';
  const isBack = edge.direction === 'back';
  const isDouble = edge.style === 'double';

  return (
    <div className={`dg-flow__edge ${isDashed ? 'dg-flow__edge--dashed' : ''} ${isBack ? 'dg-flow__edge--back' : ''} ${isDouble ? 'dg-flow__edge--double' : ''}`} data-edge-id={edge.id}>
      <div className="dg-flow__arrow" aria-hidden="true" />
      {edge.label && <span className="dg-flow__edge-label">{edge.label}</span>}
    </div>
  );
}

export function FlowDiagram({ spec }: { spec: DiagramSpec }): JSX.Element {
  const direction = spec.renderHints?.direction ?? 'left-to-right';
  const isVertical = direction === 'top-to-bottom';

  // Build ordered node sequence from edges (forward edges only)
  const forwardEdges = spec.edges.filter(e => e.direction !== 'back');
  const backEdges = spec.edges.filter(e => e.direction === 'back');

  // Find starting nodes (nodes that appear as "from" but not as "to" in forward edges)
  const toSet = new Set(forwardEdges.map(e => e.to));
  const startNodes = spec.nodes.filter(n => !toSet.has(n.id) && forwardEdges.some(e => e.from === n.id));

  // Build ordered sequence
  const orderedPairs: { node: DiagramNode; edge?: DiagramEdge }[] = [];
  const visited = new Set<string>();

  function walk(nodeId: string) {
    if (visited.has(nodeId)) return;
    visited.add(nodeId);
    const node = nodeById(spec.nodes, nodeId);
    if (!node) return;
    const outEdge = forwardEdges.find(e => e.from === nodeId);
    orderedPairs.push({ node, edge: outEdge });
    if (outEdge) walk(outEdge.to);
  }

  if (startNodes.length > 0) {
    startNodes.forEach(n => walk(n.id));
  } else {
    // Fallback: use nodes in order
    spec.nodes.forEach(n => {
      if (!visited.has(n.id)) orderedPairs.push({ node: n });
    });
  }

  // Any nodes not yet visited
  spec.nodes.forEach(n => {
    if (!visited.has(n.id)) orderedPairs.push({ node: n });
  });

  const topAnnotations = spec.annotations?.filter(a => a.position === 'top') ?? [];
  const bottomAnnotations = spec.annotations?.filter(a => a.position === 'bottom') ?? [];

  return (
    <div className={`dg-flow ${isVertical ? 'dg-flow--vertical' : 'dg-flow--horizontal'}`} data-diagram-id={spec.contractId}>
      {topAnnotations.map(a => (
        <div key={a.id} className="dg-annotation dg-annotation--top">{a.text}</div>
      ))}
      <div className="dg-flow__track">
        {orderedPairs.map(({ node, edge }) => (
          <div key={node.id} className="dg-flow__step">
            <div className="dg-flow__node" data-node-id={node.id} style={{ '--node-accent': accentColor(node.accent) } as React.CSSProperties}>
              {node.type && <span className="dg-node__type">{node.type}</span>}
              <span className="dg-node__label">{node.label}</span>
              {node.detail && <span className="dg-node__detail">{node.detail}</span>}
            </div>
            {edge && <FlowEdge edge={edge} />}
          </div>
        ))}
      </div>
      {backEdges.map(edge => (
        <div key={edge.id} className="dg-flow__back-edge" data-edge-id={edge.id}>
          <div className="dg-flow__back-arrow" aria-hidden="true" />
          {edge.label && <span className="dg-flow__edge-label">{edge.label}</span>}
        </div>
      ))}
      {bottomAnnotations.map(a => (
        <div key={a.id} className="dg-annotation dg-annotation--bottom">{a.text}</div>
      ))}
    </div>
  );
}

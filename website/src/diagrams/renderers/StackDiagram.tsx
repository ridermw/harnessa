import type { DiagramSpec } from '../types';

export function StackDiagram({ spec }: { spec: DiagramSpec }): JSX.Element {
  const regions = spec.regions ?? [];
  const topAnnotations = spec.annotations?.filter(a => a.position === 'top') ?? [];
  const bottomAnnotations = spec.annotations?.filter(a => a.position === 'bottom') ?? [];

  // If there are container regions, render nodes grouped inside them
  const containerRegion = regions.find(r => r.style === 'container');
  const regionNodeIds = new Set(containerRegion?.nodeIds ?? []);

  // Find the "header" node (not in any region, like "RUN MANIFEST")
  const headerNodes = spec.nodes.filter(n => !regionNodeIds.has(n.id));
  const stackNodes = containerRegion
    ? spec.nodes.filter(n => regionNodeIds.has(n.id))
    : spec.nodes;

  return (
    <div className="dg-stack" data-diagram-id={spec.contractId}>
      {topAnnotations.map(a => (
        <div key={a.id} className="dg-annotation dg-annotation--top">{a.text}</div>
      ))}
      {headerNodes.map(node => (
        <div key={node.id} className="dg-stack__header" data-node-id={node.id}>
          <span className="dg-node__label">{node.label}</span>
        </div>
      ))}
      <div className="dg-stack__container">
        {containerRegion && (
          <div className="dg-stack__region-label">{containerRegion.label}</div>
        )}
        <div className="dg-stack__layers">
          {stackNodes.map((node, index) => (
            <div key={node.id} className="dg-stack__layer" data-node-id={node.id} style={{ transitionDelay: `${index * 60}ms` }}>
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

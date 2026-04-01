import type { DiagramSpec } from '../types';

export function TimelineDiagram({ spec }: { spec: DiagramSpec }): JSX.Element {
  const topAnnotations = spec.annotations?.filter(a => a.position === 'top') ?? [];
  const bottomAnnotations = spec.annotations?.filter(a => a.position === 'bottom') ?? [];

  return (
    <div className="dg-timeline" data-diagram-id={spec.contractId}>
      {topAnnotations.map(a => (
        <div key={a.id} className="dg-annotation dg-annotation--top">{a.text}</div>
      ))}
      <div className="dg-timeline__track">
        {spec.nodes.map((node, index) => {
          const edge = spec.edges.find(e => e.from === node.id);
          // Extract timestamp from label (e.g. "Feb 2026 C Compiler" → "Feb 2026")
          const labelParts = node.label.match(/^(\d{4}|[A-Z][a-z]+ \d{4})\s+(.+)$/);
          const stamp = labelParts ? labelParts[1] : '';
          const title = labelParts ? labelParts[2] : node.label;

          return (
            <div key={node.id} className="dg-timeline__item" data-node-id={node.id} style={{ transitionDelay: `${index * 90}ms` }}>
              <div className="dg-timeline__marker" aria-hidden="true" />
              {stamp && <span className="dg-timeline__stamp">{stamp}</span>}
              <div className="dg-timeline__body">
                <strong className="dg-node__label">{title}</strong>
                {node.detail && <span className="dg-node__detail">{node.detail}</span>}
              </div>
              {edge && <div className="dg-timeline__connector" data-edge-id={edge.id} aria-hidden="true" />}
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

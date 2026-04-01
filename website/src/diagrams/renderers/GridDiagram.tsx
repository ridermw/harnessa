import type { DiagramSpec } from '../types';

export function GridDiagram({ spec }: { spec: DiagramSpec }): JSX.Element {
  const topAnnotations = spec.annotations?.filter(a => a.position === 'top') ?? [];
  const bottomAnnotations = spec.annotations?.filter(a => a.position === 'bottom') ?? [];
  const highlightRow = spec.renderHints?.highlightRow;

  // Parse columns from renderHints
  const columns = spec.renderHints?.columns?.split(',') ?? ['item', 'detail'];

  return (
    <div className="dg-grid" data-diagram-id={spec.contractId}>
      {topAnnotations.map(a => (
        <div key={a.id} className="dg-annotation dg-annotation--top dg-grid__header">{a.text}</div>
      ))}
      <div className="dg-grid__rows">
        {spec.nodes.map((node, index) => {
          const isHighlighted = node.id === highlightRow;
          // Split detail by "Winner: " to extract winner and notes
          const detailParts = node.detail?.match(/^Winner:\s*(.+?)(?:\s*[—–-]\s*(.+))?$/);
          const winner = detailParts?.[1] ?? '';
          const notes = detailParts?.[2] ?? '';

          return (
            <div
              key={node.id}
              className={`dg-grid__row ${isHighlighted ? 'dg-grid__row--featured' : ''}`}
              data-node-id={node.id}
              style={{ transitionDelay: `${index * 80}ms` }}
            >
              {columns.includes('benchmark') && (
                <div className="dg-grid__cell dg-grid__cell--label">
                  <span className="dg-node__label">{node.label}</span>
                </div>
              )}
              {columns.includes('winner') && (
                <div className="dg-grid__cell dg-grid__cell--winner">
                  <span className="dg-grid__badge">{winner}</span>
                </div>
              )}
              {columns.includes('notes') && notes && (
                <div className="dg-grid__cell dg-grid__cell--notes">
                  <span className="dg-node__detail">{notes}</span>
                </div>
              )}
              {!columns.includes('benchmark') && (
                <div className="dg-grid__cell dg-grid__cell--label">
                  <span className="dg-node__label">{node.label}</span>
                  {node.detail && <span className="dg-node__detail">{node.detail}</span>}
                </div>
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

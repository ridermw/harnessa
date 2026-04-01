import type { DiagramSpec } from '../types';
import { FlowDiagram } from './FlowDiagram';
import { ComparisonDiagram } from './ComparisonDiagram';
import { TimelineDiagram } from './TimelineDiagram';
import { TreeDiagram } from './TreeDiagram';
import { GridDiagram } from './GridDiagram';
import { StackDiagram } from './StackDiagram';
import { CycleDiagram } from './CycleDiagram';
import { StateDiagram } from './StateDiagram';

const renderers: Record<string, React.ComponentType<{ spec: DiagramSpec }>> = {
  flow: FlowDiagram,
  comparison: ComparisonDiagram,
  timeline: TimelineDiagram,
  tree: TreeDiagram,
  grid: GridDiagram,
  stack: StackDiagram,
  cycle: CycleDiagram,
  state: StateDiagram,
};

export function DiagramRenderer({ spec }: { spec: DiagramSpec }): JSX.Element {
  const Renderer = renderers[spec.primitive];
  if (!Renderer) {
    return <div data-diagram-id={spec.contractId} className="dg-unsupported">Unsupported diagram type: {spec.primitive}</div>;
  }
  return <Renderer spec={spec} />;
}

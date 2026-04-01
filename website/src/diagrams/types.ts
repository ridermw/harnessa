/** Primitive taxonomy for diagram layouts */
export type DiagramPrimitive =
  | 'flow'        // left-to-right or top-to-bottom sequential pipeline
  | 'comparison'  // side-by-side contrast (solo vs trio, before vs after)
  | 'timeline'    // temporal sequence of events
  | 'tree'        // branching decision structure
  | 'grid'        // tabular data (scorecard, matrix)
  | 'stack'       // layered vertical structure (telemetry, topology)
  | 'cycle'       // circular/looping flow (round-robin, feedback)
  | 'state'       // state transition (FAIL → PASS)
  ;

export interface DiagramNode {
  readonly id: string;
  readonly label: string;
  readonly type?: 'agent' | 'artifact' | 'action' | 'state' | 'event' | 'system';
  readonly accent?: string;
  readonly detail?: string;
}

export interface DiagramEdge {
  readonly id: string;
  readonly from: string;  // node id
  readonly to: string;    // node id
  readonly label?: string;
  readonly style?: 'solid' | 'dashed' | 'double' | 'loop';
  readonly direction?: 'forward' | 'back' | 'both';
}

export interface DiagramRegion {
  readonly id: string;
  readonly label: string;
  readonly nodeIds: readonly string[];
  readonly style?: 'boundary' | 'group' | 'container';
}

export interface DiagramSpec {
  readonly contractId: string;       // matches plan ASCII diagram ID
  readonly contractVersion: number;  // bumped when contract changes
  readonly primitive: DiagramPrimitive;
  readonly scene: string;            // scene ID this diagram belongs to
  readonly title: string;
  readonly nodes: readonly DiagramNode[];
  readonly edges: readonly DiagramEdge[];
  readonly regions?: readonly DiagramRegion[];
  readonly annotations?: readonly { id: string; text: string; position: 'top' | 'bottom' | 'inline' }[];
  readonly renderHints?: Record<string, string>;
}

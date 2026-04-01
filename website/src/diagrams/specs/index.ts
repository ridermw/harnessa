import type { DiagramSpec } from '../types';

import { diagram00RailStates } from './diagram-00-rail-states';
import { diagram01TrioPipeline } from './diagram-01-trio-pipeline';
import { diagram02GoodhartBoundary } from './diagram-02-goodhart-boundary';
import { diagram03SprintContract } from './diagram-03-sprint-contract';
import { diagram04FilesHandoff } from './diagram-04-files-handoff';
import { diagram05TelemetryStack } from './diagram-05-telemetry-stack';
import { diagram06HeadlineResult } from './diagram-06-headline-result';
import { diagram07Scorecard } from './diagram-07-scorecard';
import { diagram08IterationCurve } from './diagram-08-iteration-curve';
import { diagram09IndustryTimeline } from './diagram-09-industry-timeline';
import { diagram10EcosystemNetwork } from './diagram-10-ecosystem-network';
import { diagram11ShowcaseRebuild } from './diagram-11-showcase-rebuild';
import { diagram12DemoFlow } from './diagram-12-demo-flow';
import { diagram13DecisionTree } from './diagram-13-decision-tree';
import { diagram14ModelTiering } from './diagram-14-model-tiering';
import { diagram15RoundRobin } from './diagram-15-round-robin';
import { diagram16SystemTopology } from './diagram-16-system-topology';

export {
  diagram00RailStates,
  diagram01TrioPipeline,
  diagram02GoodhartBoundary,
  diagram03SprintContract,
  diagram04FilesHandoff,
  diagram05TelemetryStack,
  diagram06HeadlineResult,
  diagram07Scorecard,
  diagram08IterationCurve,
  diagram09IndustryTimeline,
  diagram10EcosystemNetwork,
  diagram11ShowcaseRebuild,
  diagram12DemoFlow,
  diagram13DecisionTree,
  diagram14ModelTiering,
  diagram15RoundRobin,
  diagram16SystemTopology,
};

/** All diagram specs as an ordered array */
export const allDiagramSpecs: readonly DiagramSpec[] = [
  diagram00RailStates,
  diagram01TrioPipeline,
  diagram02GoodhartBoundary,
  diagram03SprintContract,
  diagram04FilesHandoff,
  diagram05TelemetryStack,
  diagram06HeadlineResult,
  diagram07Scorecard,
  diagram08IterationCurve,
  diagram09IndustryTimeline,
  diagram10EcosystemNetwork,
  diagram11ShowcaseRebuild,
  diagram12DemoFlow,
  diagram13DecisionTree,
  diagram14ModelTiering,
  diagram15RoundRobin,
  diagram16SystemTopology,
] as const;

/** Diagram specs indexed by contractId */
export const diagramSpecMap: ReadonlyMap<string, DiagramSpec> = new Map(
  allDiagramSpecs.map(spec => [spec.contractId, spec])
);

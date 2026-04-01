import type { DiagramSpec } from '../types';

export interface ContractViolation {
  contractId: string;
  type: 'missing-node' | 'orphan-edge' | 'duplicate-id' | 'empty-label' | 'invalid-edge-ref';
  message: string;
}

export function validateSpec(spec: DiagramSpec): ContractViolation[] {
  const violations: ContractViolation[] = [];
  const nodeIds = new Set<string>();

  // Check for duplicate node IDs
  for (const node of spec.nodes) {
    if (nodeIds.has(node.id)) {
      violations.push({
        contractId: spec.contractId,
        type: 'duplicate-id',
        message: `Duplicate node id: "${node.id}"`,
      });
    }
    nodeIds.add(node.id);
  }

  // Check for empty labels on nodes
  for (const node of spec.nodes) {
    if (!node.label.trim()) {
      violations.push({
        contractId: spec.contractId,
        type: 'empty-label',
        message: `Node "${node.id}" has an empty label`,
      });
    }
  }

  // Check edges reference valid nodes
  const edgeIds = new Set<string>();
  for (const edge of spec.edges) {
    if (edgeIds.has(edge.id)) {
      violations.push({
        contractId: spec.contractId,
        type: 'duplicate-id',
        message: `Duplicate edge id: "${edge.id}"`,
      });
    }
    edgeIds.add(edge.id);

    if (!nodeIds.has(edge.from)) {
      violations.push({
        contractId: spec.contractId,
        type: 'invalid-edge-ref',
        message: `Edge "${edge.id}" references unknown from-node: "${edge.from}"`,
      });
    }
    if (!nodeIds.has(edge.to)) {
      violations.push({
        contractId: spec.contractId,
        type: 'invalid-edge-ref',
        message: `Edge "${edge.id}" references unknown to-node: "${edge.to}"`,
      });
    }
  }

  // Check regions reference valid nodes
  if (spec.regions) {
    for (const region of spec.regions) {
      for (const nid of region.nodeIds) {
        if (!nodeIds.has(nid)) {
          violations.push({
            contractId: spec.contractId,
            type: 'invalid-edge-ref',
            message: `Region "${region.id}" references unknown node: "${nid}"`,
          });
        }
      }
    }
  }

  return violations;
}

export function validateAllSpecs(specs: readonly DiagramSpec[]): ContractViolation[] {
  // Check for duplicate contract IDs across all specs
  const contractIds = new Set<string>();
  const violations: ContractViolation[] = [];

  for (const spec of specs) {
    if (contractIds.has(spec.contractId)) {
      violations.push({
        contractId: spec.contractId,
        type: 'duplicate-id',
        message: `Duplicate contractId: "${spec.contractId}"`,
      });
    }
    contractIds.add(spec.contractId);
  }

  return [...violations, ...specs.flatMap(validateSpec)];
}

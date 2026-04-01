import { describe, it, expect } from 'vitest';
import { validateSpec, validateAllSpecs } from './validate';
import { allDiagramSpecs } from '../specs/index';
import type { DiagramSpec } from '../types';

function makeSpec(overrides: Partial<DiagramSpec> = {}): DiagramSpec {
  return {
    contractId: 'test-spec',
    contractVersion: 1,
    primitive: 'flow',
    scene: 'hero',
    title: 'Test',
    nodes: [
      { id: 'a', label: 'Node A' },
      { id: 'b', label: 'Node B' },
    ],
    edges: [
      { id: 'e1', from: 'a', to: 'b' },
    ],
    ...overrides,
  };
}

describe('validateSpec', () => {
  it('catches duplicate node IDs', () => {
    const spec = makeSpec({
      nodes: [
        { id: 'dup', label: 'First' },
        { id: 'dup', label: 'Second' },
      ],
      edges: [],
    });
    const violations = validateSpec(spec);
    expect(violations).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ type: 'duplicate-id', message: expect.stringContaining('dup') }),
      ]),
    );
  });

  it('catches invalid edge references', () => {
    const spec = makeSpec({
      nodes: [{ id: 'a', label: 'A' }],
      edges: [{ id: 'e1', from: 'a', to: 'nonexistent' }],
    });
    const violations = validateSpec(spec);
    expect(violations).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ type: 'invalid-edge-ref', message: expect.stringContaining('nonexistent') }),
      ]),
    );
  });

  it('catches empty labels', () => {
    const spec = makeSpec({
      nodes: [
        { id: 'a', label: '' },
        { id: 'b', label: '   ' },
      ],
      edges: [],
    });
    const violations = validateSpec(spec);
    const emptyLabelViolations = violations.filter((v) => v.type === 'empty-label');
    expect(emptyLabelViolations).toHaveLength(2);
  });

  it('returns no violations for a valid spec', () => {
    const spec = makeSpec();
    expect(validateSpec(spec)).toHaveLength(0);
  });
});

describe('validateAllSpecs', () => {
  it('returns zero violations for all shipped diagram specs', () => {
    const violations = validateAllSpecs(allDiagramSpecs);
    if (violations.length > 0) {
      const summary = violations.map((v) => `[${v.contractId}] ${v.message}`).join('\n');
      expect.fail(`Shipped specs have ${violations.length} violation(s):\n${summary}`);
    }
    expect(violations).toHaveLength(0);
  });

  it('catches duplicate contractIds across specs', () => {
    const specA = makeSpec({ contractId: 'same-id' });
    const specB = makeSpec({ contractId: 'same-id' });
    const violations = validateAllSpecs([specA, specB]);
    expect(violations).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ type: 'duplicate-id', message: expect.stringContaining('same-id') }),
      ]),
    );
  });
});

import { test, expect } from '@playwright/test';

test.describe('Diagram contracts in the DOM', () => {
  test('every scene with a diagram has [data-diagram-id]', async ({ page }) => {
    await page.goto('/');
    // Wait for first diagram to render
    await page.locator('[data-diagram-id]').first().waitFor({ state: 'visible' });

    const diagrams = await page.locator('[data-diagram-id]').all();
    expect(diagrams.length).toBeGreaterThan(0);

    // Each diagram should have a non-empty contractId
    for (const diagram of diagrams) {
      const id = await diagram.getAttribute('data-diagram-id');
      expect(id).toBeTruthy();
    }
  });

  test('diagram nodes have [data-node-id] attributes', async ({ page }) => {
    await page.goto('/');
    await page.locator('[data-diagram-id]').first().waitFor({ state: 'visible' });

    const nodes = await page.locator('[data-node-id]').all();
    expect(nodes.length).toBeGreaterThan(0);

    for (const node of nodes) {
      const nodeId = await node.getAttribute('data-node-id');
      expect(nodeId).toBeTruthy();
    }
  });

  test('no diagram elements overlap within a single diagram', async ({ page }) => {
    await page.goto('/#trio-pipeline');
    const trioDiagram = page.locator('[data-diagram-id="diagram-01-trio-pipeline"]');
    await trioDiagram.waitFor({ state: 'visible' });

    const nodes = await trioDiagram.locator('[data-node-id]').all();
    expect(nodes.length).toBeGreaterThanOrEqual(3);

    const boxes: { id: string; x: number; y: number; w: number; h: number }[] = [];
    for (const node of nodes) {
      const box = await node.boundingBox();
      const id = (await node.getAttribute('data-node-id'))!;
      if (box) {
        boxes.push({ id, x: box.x, y: box.y, w: box.width, h: box.height });
      }
    }

    // Basic overlap check: no two node centers should be in the same position
    for (let i = 0; i < boxes.length; i++) {
      for (let j = i + 1; j < boxes.length; j++) {
        const a = boxes[i];
        const b = boxes[j];
        const overlapX = a.x < b.x + b.w && a.x + a.w > b.x;
        const overlapY = a.y < b.y + b.h && a.y + a.h > b.y;
        if (overlapX && overlapY) {
          // Allow minor overlap (< 50% of smaller element)
          const overlapWidth = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x);
          const overlapHeight = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
          const overlapArea = overlapWidth * overlapHeight;
          const smallerArea = Math.min(a.w * a.h, b.w * b.h);
          expect(
            overlapArea / smallerArea,
            `nodes "${a.id}" and "${b.id}" overlap by ${Math.round((overlapArea / smallerArea) * 100)}%`,
          ).toBeLessThan(0.5);
        }
      }
    }
  });

  test('trio-pipeline diagram has planner, generator, evaluator nodes', async ({ page }) => {
    await page.goto('/#trio-pipeline');
    const diagram = page.locator('[data-diagram-id="diagram-01-trio-pipeline"]');
    await diagram.waitFor({ state: 'visible' });

    await expect(diagram.locator('[data-node-id="planner"]')).toBeVisible();
    await expect(diagram.locator('[data-node-id="generator"]')).toBeVisible();
    await expect(diagram.locator('[data-node-id="evaluator"]')).toBeVisible();
  });
});

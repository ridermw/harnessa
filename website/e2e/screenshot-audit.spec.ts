import { test } from '@playwright/test';

const SCENES = [
  'hero', 'anthropic-spark', 'wall-context', 'wall-evaluation',
  'adversarial-insight', 'trio-pipeline', 'goodhart-boundary',
  'sprint-contracts', 'files-on-disk', 'telemetry-layer',
  'karpathy-problem', 'anti-sycophancy', 'criteria-thresholds',
  'experiment-design', 'benchmark-matrix', 'headline-result',
  'full-scorecard', 'difficulty-classification', 'iteration-curve',
  'claims-confirmed', 'claims-partial', 'evaluator-leniency',
  'industry-timeline', 'ecosystem-network', 'showcase-rebuild',
  'demo-flow', 'decision-tree', 'model-tiering', 'round-robin',
  'closing',
];

test.describe('Scene screenshot audit', () => {
  for (const scene of SCENES) {
    test(`screenshot: ${scene}`, async ({ page }) => {
      await page.setViewportSize({ width: 1440, height: 900 });
      await page.goto(`/?rail=closed#${scene}`, { waitUntil: 'networkidle' });
      await page.waitForTimeout(300);
      // Scroll the scene into view
      const el = page.locator(`#${scene}`);
      if (await el.count() > 0) {
        await el.scrollIntoViewIfNeeded();
        await page.waitForTimeout(200);
      }
      await page.screenshot({
        path: `e2e/screenshots/${scene}.png`,
        fullPage: false,
      });
    });
  }
});

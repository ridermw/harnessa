import { test, expect } from '@playwright/test';

test.describe('Scene navigation', () => {
  test('deep-link to #headline-result loads the correct scene', async ({ page }) => {
    await page.goto('/#headline-result');
    const section = page.locator('#headline-result');
    await expect(section).toBeVisible();
  });

  test('alias deep-link #evidence resolves to headline-result', async ({ page }) => {
    await page.goto('/#evidence');
    // The alias "evidence" maps to "headline-result"
    const section = page.locator('#headline-result');
    await expect(section).toBeVisible();
  });

  test('ArrowDown moves to the next scene', async ({ page }) => {
    await page.goto('/#hero');
    await page.locator('#hero').waitFor({ state: 'visible' });

    // Press ArrowDown to advance
    await page.keyboard.press('ArrowDown');

    // The second scene should become the active scene (data-active attribute)
    await expect(page.locator('#anthropic-spark[data-active="true"]')).toBeVisible({ timeout: 10000 });
  });

  test('scene counter updates as you navigate', async ({ page }) => {
    await page.goto('/#hero');
    await page.locator('#hero').waitFor({ state: 'visible' });

    // The rail should show the first scene as active
    const activeItem = page.locator('.scene-nav__item.is-active');
    await expect(activeItem).toBeVisible();
    await expect(activeItem).toContainText('01');

    // Navigate forward
    await page.keyboard.press('ArrowDown');

    // Active item should now correspond to scene 02
    await expect(page.locator('.scene-nav__item.is-active')).toContainText('02', { timeout: 10000 });
  });
});

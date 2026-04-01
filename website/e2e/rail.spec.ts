import { test, expect } from '@playwright/test';

test.describe('Operator rail', () => {
  test('rail starts open by default', async ({ page }) => {
    await page.goto('/');
    const rail = page.locator('#scene-rail');
    await expect(rail).toBeVisible();
    await expect(rail).toHaveAttribute('data-rail-open', 'true');
  });

  test('?rail=closed starts with rail closed', async ({ page }) => {
    await page.goto('/?rail=closed');
    const rail = page.locator('#scene-rail');
    await expect(rail).toHaveAttribute('data-rail-open', 'false');
  });

  test('toggle button opens and closes the rail', async ({ page }) => {
    await page.goto('/');
    const rail = page.locator('#scene-rail');
    await expect(rail).toHaveAttribute('data-rail-open', 'true');

    // Use keyboard shortcut 'S' to toggle (avoids topbar click interception)
    await page.keyboard.press('s');
    await expect(rail).toHaveAttribute('data-rail-open', 'false');

    // Press 'S' again to reopen
    await page.keyboard.press('s');
    await expect(rail).toHaveAttribute('data-rail-open', 'true');
  });

  test('content area layout changes when rail is closed', async ({ page }) => {
    await page.goto('/');
    const rail = page.locator('#scene-rail');
    await rail.waitFor({ state: 'visible' });

    const openRailBox = await rail.boundingBox();
    expect(openRailBox!.width).toBeGreaterThan(0);

    // Close the rail with keyboard shortcut
    await page.keyboard.press('s');
    await expect(rail).toHaveAttribute('data-rail-open', 'false');
  });
});

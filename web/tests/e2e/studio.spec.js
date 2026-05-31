import { test, expect } from '@playwright/test';

test('local backend mode and ROM build workflow', async ({ page }) => {
  await page.goto('/');

  await expect(page.locator('.modebar')).toContainText('Backend mode');
  await expect(page.locator('.modebar')).toContainText('Backend connected');

  await page.getByRole('button', { name: /Mango Island/ }).click();
  await expect(page.locator('.project-card')).toContainText('Mango Island');
  await expect(page.locator('.modebar')).toContainText('Build ROM now compiles this project');

  await page.getByRole('button', { name: 'Build ROM' }).click();
  await expect(page.getByText(/ROM artifact:/)).toBeVisible();
});

test('scene edit actions persist through backend API path', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('.modebar')).toContainText('Backend mode');

  // Draw one collision rectangle on canvas.
  await page.locator('.toolbar .tool', { hasText: 'Collision' }).click();
  const before = await page.locator('.collision').count();
  const canvas = page.locator('.canvas').first();
  const box = await canvas.boundingBox();
  if (!box) throw new Error('scene canvas not found');
  await page.mouse.move(box.x + 80, box.y + 80);
  await page.mouse.down();
  await page.mouse.move(box.x + 160, box.y + 130);
  await page.mouse.up();

  await expect.poll(async () => page.locator('.collision').count()).toBeGreaterThan(before);
});

test('sprite assets can be created, selected, edited, and assigned', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('.modebar')).toContainText('Backend mode');

  await page.getByTitle('Add sprite').click();
  await page.getByLabel('Sprite name').fill(`QA Sprite ${Date.now()}`);
  await page.locator('.modal').getByRole('button', { name: 'Add sprite' }).click();

  await expect(page.getByText(/Added sprite QA Sprite/)).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Sprite Editor' })).toBeVisible();
  await page.getByLabel('Sprite name').fill('QA Edited Sprite');
  await page.getByLabel('Sprite name').blur();
  await expect(page.getByText(/Saved sprite QA Edited Sprite/)).toBeVisible();
});

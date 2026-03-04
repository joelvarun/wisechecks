import { test, expect } from '@playwright/test';

test('home shell', async ({ page }) => {
  await page.goto('http://localhost:3000');
  await expect(page.getByText('WiseChecks')).toBeVisible();
});

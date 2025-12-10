import { test, expect } from '@playwright/test';

test.describe('Stripe Elements scaffold', () => {
  test('checkout page loads and has content', async ({ page }) => {
    // Point this to a running local dev server when actually running the test.
    await page.goto('http://localhost:8000/');

    // Smoke: page loads and body contains some text (avoid brittle selector assumptions)
    const bodyText = await page.locator('body').innerText();
    expect(bodyText.length).toBeGreaterThan(0);
  });
});

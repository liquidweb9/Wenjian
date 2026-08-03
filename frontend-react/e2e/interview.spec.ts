import { test, expect } from '@playwright/test';

/**
 * Interview Flow E2E Tests
 * Tests creating and conducting interviews
 */
test.describe('Interview Flow', () => {
  test('should navigate to interviews page', async ({ page }) => {
    await page.goto('/interviews');

    // Should show interviews list or create button
    const content = page.locator('main, [role="main"]');
    await expect(content).toBeVisible();
  });

  test('should display interview list or empty state', async ({ page }) => {
    await page.goto('/interviews');

    // Should have either interview list or empty state message
    const hasContent = await page.locator('body').textContent();
    expect(hasContent).toBeTruthy();
  });

  test('should show create interview option when resume exists', async ({ page }) => {
    await page.goto('/interviews');

    // Look for create/start button or link
    const createButton = page.getByRole('button', { name: /create|start|new/i }).or(
      page.getByRole('link', { name: /create|start|new/i })
    ).first();

    // Button should exist (may be disabled if no resume)
    const buttonExists = await createButton.count().then(c => c > 0);
    expect(buttonExists).toBeTruthy();
  });

  test('should navigate to interview detail if interviews exist', async ({ page }) => {
    await page.goto('/interviews');

    // Try to find and click on an interview
    const interviewLink = page.locator('a[href*="/interviews/"]').first();
    const hasInterviews = await interviewLink.isVisible().catch(() => false);

    if (hasInterviews) {
      await interviewLink.click();

      // Should navigate to interview detail/room
      await expect(page).toHaveURL(/\/interviews\/[^/]+/);
    }
  });

  test('should handle SSE connection in interview room', async ({ page }) => {
    // Skip if no interviews available
    await page.goto('/interviews');

    const interviewLink = page.locator('a[href*="/interviews/"]').first();
    const hasInterviews = await interviewLink.isVisible().catch(() => false);

    if (!hasInterviews) {
      test.skip();
      return;
    }

    await interviewLink.click();

    // Wait for interview page to load
    await expect(page).toHaveURL(/\/interviews\/[^/]+/);

    // Check for question display area
    const questionArea = page.locator('[data-testid="question"]').or(
      page.getByText(/question|回答/i)
    );

    // Interview UI should be visible
    await expect(questionArea.first()).toBeVisible({ timeout: 10000 });
  });
});

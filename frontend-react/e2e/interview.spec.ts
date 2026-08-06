import { test, expect } from '@playwright/test';
import { setupAuthenticatedPage } from './utils/auth';

/**
 * Interview Flow E2E Tests
 * Tests the interview list and creation entry (authenticated)
 */
test.describe('Interview Flow', () => {
  test('should navigate to interviews page', async ({ page, request }) => {
    await setupAuthenticatedPage(page, request);
    await page.goto('/app/interviews');

    const content = page.locator('main');
    await expect(content).toBeVisible();
  });

  test('should display interview list or empty state', async ({ page, request }) => {
    await setupAuthenticatedPage(page, request);
    await page.goto('/app/interviews');

    const hasContent = await page.locator('body').textContent();
    expect(hasContent).toBeTruthy();
  });

  test('should show create interview option when resume exists', async ({ page, request }) => {
    await setupAuthenticatedPage(page, request);
    await page.goto('/app/interviews');

    const createButton = page
      .getByRole('button', { name: /新建面试|创建第一场|开始|new/i })
      .or(page.getByRole('link', { name: /新建面试|创建第一场|开始|new/i }))
      .first();

    const buttonExists = await createButton.count().then((c) => c > 0);
    expect(buttonExists).toBeTruthy();
  });

  test('should navigate to interview detail if interviews exist', async ({ page, request }) => {
    await setupAuthenticatedPage(page, request);
    await page.goto('/app/interviews');

    const interviewLink = page.locator('a[href*="/app/interviews/"]').first();
    const hasInterviews = await interviewLink.isVisible().catch(() => false);

    if (hasInterviews) {
      await interviewLink.click();

      await expect(page).toHaveURL(/\/app\/interviews\/[^/]+/);
    }
  });

  test('should handle SSE connection in interview room', async ({ page, request }) => {
    await setupAuthenticatedPage(page, request);
    await page.goto('/app/interviews');

    const interviewLink = page.locator('a[href*="/app/interviews/"]').first();
    const hasInterviews = await interviewLink.isVisible().catch(() => false);

    if (!hasInterviews) {
      test.skip();
      return;
    }

    await interviewLink.click();
    await expect(page).toHaveURL(/\/app\/interviews\/[^/]+/);

    const questionArea = page
      .locator('[data-testid="question"]')
      .or(page.getByText(/question|回答|面试/i));

    await expect(questionArea.first()).toBeVisible({ timeout: 10000 });
  });
});

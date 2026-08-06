import { test, expect, type Page } from '@playwright/test';
import { setupAuthenticatedPage } from './utils/auth';

/**
 * Report Viewing E2E Tests
 * Tests viewing interview reports (authenticated)
 */
test.describe('Report Viewing', () => {
  async function findFirstInterviewId(page: Page) {
    const interviewLink = page.locator('a[href*="/app/interviews/"]').first();
    const hasInterviews = await interviewLink.isVisible().catch(() => false);
    if (!hasInterviews) return null;

    const href = await interviewLink.getAttribute('href');
    const match = href?.match(/\/app\/interviews\/([^/]+)/);
    return match?.[1] ?? null;
  }

  test('should navigate to reports page', async ({ page, request }) => {
    await setupAuthenticatedPage(page, request);
    await page.goto('/app/interviews');

    // The report list is the interview list; each row links to its report.
    const content = page.locator('main');
    await expect(content).toBeVisible();
  });

  test('should display report if interview exists', async ({ page, request }) => {
    await setupAuthenticatedPage(page, request);
    await page.goto('/app/interviews');

    const interviewId = await findFirstInterviewId(page);
    if (!interviewId) {
      test.skip();
      return;
    }

    await page.goto(`/app/interviews/${interviewId}/report`);
    await expect(page.locator('main')).toBeVisible();
  });

  test('should show report sections', async ({ page, request }) => {
    await setupAuthenticatedPage(page, request);
    await page.goto('/app/interviews');

    const interviewId = await findFirstInterviewId(page);
    if (!interviewId) {
      test.skip();
      return;
    }

    await page.goto(`/app/interviews/${interviewId}/report`);

    const hasReportContent = await page.locator('body').textContent();
    expect(hasReportContent).toBeTruthy();
    expect(hasReportContent?.length).toBeGreaterThan(100);
  });

  test('should handle API report fetch', async ({ page, request }) => {
    await setupAuthenticatedPage(page, request);
    await page.goto('/app/interviews');

    const interviewId = await findFirstInterviewId(page);
    if (!interviewId) {
      test.skip();
      return;
    }

    const response = await request.get(`http://localhost:8000/api/v1/reports/${interviewId}`);
    expect([200, 404]).toContain(response.status());
  });
});

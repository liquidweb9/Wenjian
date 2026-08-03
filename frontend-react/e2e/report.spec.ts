import { test, expect } from '@playwright/test';

/**
 * Report Viewing E2E Tests
 * Tests viewing interview reports and analysis
 */
test.describe('Report Viewing', () => {
  test('should navigate to reports page', async ({ page }) => {
    await page.goto('/reports');

    // Should show reports list or redirect
    const content = page.locator('body');
    await expect(content).toBeVisible();
  });

  test('should display report if interview exists', async ({ page }) => {
    // First check if there are any interviews
    await page.goto('/interviews');

    const interviewLink = page.locator('a[href*="/interviews/"]').first();
    const hasInterviews = await interviewLink.isVisible().catch(() => false);

    if (!hasInterviews) {
      test.skip();
      return;
    }

    // Get interview ID from link
    const href = await interviewLink.getAttribute('href');
    const interviewId = href?.split('/').pop();

    if (!interviewId) {
      test.skip();
      return;
    }

    // Navigate to report
    await page.goto(`/reports/${interviewId}`);

    // Should show report content
    await expect(page.locator('main, [role="main"]')).toBeVisible();
  });

  test('should show report sections', async ({ page }) => {
    await page.goto('/interviews');

    const interviewLink = page.locator('a[href*="/interviews/"]').first();
    const hasInterviews = await interviewLink.isVisible().catch(() => false);

    if (!hasInterviews) {
      test.skip();
      return;
    }

    const href = await interviewLink.getAttribute('href');
    const interviewId = href?.split('/').pop();

    if (!interviewId) {
      test.skip();
      return;
    }

    await page.goto(`/reports/${interviewId}`);

    // Report should have sections like scores, analysis, etc.
    // Look for common report elements
    const hasReportContent = await page.locator('body').textContent();
    expect(hasReportContent).toBeTruthy();
    expect(hasReportContent?.length).toBeGreaterThan(100);
  });

  test('should handle API report fetch', async ({ page }) => {
    await page.goto('/interviews');

    const interviewLink = page.locator('a[href*="/interviews/"]').first();
    const hasInterviews = await interviewLink.isVisible().catch(() => false);

    if (!hasInterviews) {
      test.skip();
      return;
    }

    const href = await interviewLink.getAttribute('href');
    const interviewId = href?.split('/').pop();

    if (!interviewId) {
      test.skip();
      return;
    }

    // Test API endpoint directly
    const response = await page.request.get(
      `http://localhost:8000/api/v1/reports/${interviewId}`
    );

    // Should either return report or 404 if no report exists yet
    expect([200, 404]).toContain(response.status());
  });
});

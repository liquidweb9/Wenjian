import { test, expect } from '@playwright/test';
import { setupAuthenticatedPage } from './utils/auth';

/**
 * Dashboard E2E Tests
 * Tests the authenticated workspace landing page and navigation
 */
test.describe('Dashboard', () => {
  test('should load dashboard page', async ({ page, request }) => {
    await setupAuthenticatedPage(page, request);
    await page.goto('/app/dashboard');

    // Check page title (Chinese brand or latin name)
    await expect(page).toHaveTitle(/问鉴|Wenjian/i);

    // Check a heading renders inside the app layout
    const heading = page.locator('main h1, main h2').first();
    await expect(heading).toBeVisible();
  });

  test('should display navigation menu', async ({ page, request }) => {
    await setupAuthenticatedPage(page, request);
    await page.goto('/app/dashboard');

    const nav = page.locator('nav').first();
    await expect(nav).toBeVisible();

    await expect(page.getByRole('link', { name: /简历管理/ })).toBeVisible();
    await expect(page.getByRole('link', { name: /模拟面试/ })).toBeVisible();
  });

  test('should navigate to resume upload', async ({ page, request }) => {
    await setupAuthenticatedPage(page, request);
    await page.goto('/app/dashboard');

    const resumeLink = page.getByRole('link', { name: /简历管理/ }).first();
    await resumeLink.click();

    await expect(page).toHaveURL(/\/app\/resumes/);
  });

  test('should display health status', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/health');
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.status).toBe('ok');
  });
});

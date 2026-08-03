import { test, expect } from '@playwright/test';

/**
 * Dashboard E2E Tests
 * Tests the landing page and navigation
 */
test.describe('Dashboard', () => {
  test('should load dashboard page', async ({ page }) => {
    await page.goto('/');

    // Check page title
    await expect(page).toHaveTitle(/Wenjian/);

    // Check main heading exists
    const heading = page.locator('h1, h2').first();
    await expect(heading).toBeVisible();
  });

  test('should display navigation menu', async ({ page }) => {
    await page.goto('/');

    // Check for navigation links
    const nav = page.locator('nav').first();
    await expect(nav).toBeVisible();

    // Should have links to key sections
    await expect(page.getByRole('link', { name: /resumes?/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /interviews?/i })).toBeVisible();
  });

  test('should navigate to resume upload', async ({ page }) => {
    await page.goto('/');

    // Click resume link or upload button
    const resumeLink = page.getByRole('link', { name: /resumes?/i }).first();
    await resumeLink.click();

    // Should navigate to resume page
    await expect(page).toHaveURL(/\/resumes/);
  });

  test('should display health status', async ({ page }) => {
    await page.goto('/');

    // Check if health endpoint is accessible
    const response = await page.request.get('http://localhost:8000/api/v1/health');
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.status).toBe('ok');
  });
});

import { test, expect } from '@playwright/test';
import path from 'path';
import { setupAuthenticatedPage } from './utils/auth';

/**
 * Resume Upload E2E Tests
 * Tests the resume list and upload flow (authenticated)
 */
test.describe('Resume Upload', () => {
  test('should navigate to resume upload page', async ({ page, request }) => {
    await setupAuthenticatedPage(page, request);
    await page.goto('/app/resumes');

    // Upload entry lives on the list page via the "上传简历" button.
    const uploadButton = page.getByRole('link', { name: /上传简历|导入/ }).first();
    const fileInput = page.locator('input[type="file"]');
    await expect(uploadButton.or(fileInput).first()).toBeVisible();
  });

  test('should display resume list', async ({ page, request }) => {
    await setupAuthenticatedPage(page, request);
    await page.goto('/app/resumes');

    const content = page.locator('main');
    await expect(content).toBeVisible();
  });

  // Note: File upload test requires a sample resume file
  test.skip('should upload a resume file', async ({ page }) => {
    await page.goto('/app/resumes');

    // Locate file input
    const fileInput = page.locator('input[type="file"]');

    // Create a test file path (would need actual test file)
    const testFile = path.join(__dirname, '../test-fixtures/sample-resume.pdf');

    // Upload file
    await fileInput.setInputFiles(testFile);

    // Wait for upload to complete
    await page.waitForResponse(response =>
      response.url().includes('/api/v1/resumes') &&
      response.status() === 201
    );

    // Should show success message or redirect
    await expect(page.getByText(/success|uploaded|processing/i)).toBeVisible({ timeout: 10000 });
  });

  test('should handle navigation to resume detail', async ({ page, request }) => {
    await setupAuthenticatedPage(page, request);
    await page.goto('/app/resumes');

    const resumeLink = page.locator('a[href*="/app/resumes/"]').first();
    const hasResumes = await resumeLink.isVisible().catch(() => false);

    if (hasResumes) {
      await resumeLink.click();

      await expect(page).toHaveURL(/\/app\/resumes\/[^/]+/);
    }
  });
});

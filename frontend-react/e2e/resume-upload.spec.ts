import { test, expect } from '@playwright/test';
import path from 'path';

/**
 * Resume Upload E2E Tests
 * Tests the complete resume upload and parsing flow
 */
test.describe('Resume Upload', () => {
  test('should navigate to resume upload page', async ({ page }) => {
    await page.goto('/resumes');

    // Check for upload area or button
    const uploadArea = page.locator('input[type="file"]').or(page.getByText(/upload/i));
    await expect(uploadArea.first()).toBeVisible();
  });

  test('should display resume list', async ({ page }) => {
    await page.goto('/resumes');

    // Should show resume list or empty state
    const content = page.locator('main, [role="main"]');
    await expect(content).toBeVisible();
  });

  // Note: File upload test requires a sample resume file
  test.skip('should upload a resume file', async ({ page }) => {
    await page.goto('/resumes');

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

  test('should handle navigation to resume detail', async ({ page }) => {
    await page.goto('/resumes');

    // If there are any resumes, test clicking on one
    const resumeCard = page.locator('[data-testid="resume-card"]').or(
      page.locator('a[href*="/resumes/"]')
    ).first();

    const hasResumes = await resumeCard.isVisible().catch(() => false);

    if (hasResumes) {
      await resumeCard.click();

      // Should navigate to detail page
      await expect(page).toHaveURL(/\/resumes\/[^/]+/);
    }
  });
});

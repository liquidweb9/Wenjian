import { test, expect } from '@playwright/test';

/**
 * Authentication E2E Tests
 * Tests user registration, login, and profile access
 */
test.describe('Authentication', () => {
  const testPassword = 'SecurePass123!';
  const testName = 'E2E Test User';

  test('should show login page', async ({ page }) => {
    await page.goto('/login');

    // The login page is localized in Chinese.
    await expect(page.getByRole('heading', { name: /登录问鉴/ })).toBeVisible();
    await expect(page.getByPlaceholder('your@email.com')).toBeVisible();
  });

  test('should register new user via API', async ({ request }) => {
    const email = `e2e_${Date.now()}@example.com`;
    const response = await request.post('http://localhost:8000/api/v1/register', {
      data: { email, password: testPassword, full_name: testName },
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data).toHaveProperty('access_token');
  });

  test('should login existing user via API', async ({ request }) => {
    const email = `login_test_${Date.now()}@example.com`;

    // First register
    const registerResponse = await request.post('http://localhost:8000/api/v1/register', {
      data: { email, password: testPassword, full_name: testName },
    });
    expect(registerResponse.ok()).toBeTruthy();

    // Then login with the same credentials
    const loginResponse = await request.post('http://localhost:8000/api/v1/login', {
      data: { email, password: testPassword },
    });

    expect(loginResponse.ok()).toBeTruthy();
    const data = await loginResponse.json();
    expect(data).toHaveProperty('access_token');
  });

  test('should access profile with valid token', async ({ request }) => {
    const email = `profile_test_${Date.now()}@example.com`;
    const registerResponse = await request.post('http://localhost:8000/api/v1/register', {
      data: { email, password: testPassword, full_name: testName },
    });

    expect(registerResponse.ok()).toBeTruthy();
    const { access_token } = await registerResponse.json();

    const profileResponse = await request.get('http://localhost:8000/api/v1/me', {
      headers: { Authorization: `Bearer ${access_token}` },
    });

    expect(profileResponse.ok()).toBeTruthy();
    const profile = await profileResponse.json();
    expect(profile).toHaveProperty('email');
    expect(profile.full_name).toBe(testName);
  });

  test('should reject invalid token', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/me', {
      headers: { Authorization: 'Bearer invalid_token_12345' },
    });

    expect(response.status()).toBe(401);
  });
});

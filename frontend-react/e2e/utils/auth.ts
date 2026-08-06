import { expect, type APIRequestContext, type Page } from '@playwright/test';

export interface AuthUser {
  email: string;
  password: string;
  token: string;
}

/**
 * Register a fresh user through the API so tests stay isolated.
 */
export async function registerUser(request: APIRequestContext): Promise<AuthUser> {
  const email = `e2e_${Date.now()}_${Math.floor(Math.random() * 100000)}@example.com`;
  const password = 'SecurePass123!';
  const response = await request.post('http://localhost:8000/api/v1/register', {
    data: { email, password, full_name: 'E2E Test User' },
  });
  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  expect(data).toHaveProperty('access_token');
  return { email, password, token: data.access_token as string };
}

/**
 * Authenticate a page before navigation by seeding the Zustand auth store.
 * The app reads `auth-storage` from localStorage and injects the bearer token.
 */
export async function setupAuthenticatedPage(page: Page, request: APIRequestContext): Promise<AuthUser> {
  const user = await registerUser(request);

  const profileResponse = await request.get('http://localhost:8000/api/v1/me', {
    headers: { Authorization: `Bearer ${user.token}` },
  });
  const profile = profileResponse.ok() ? await profileResponse.json() : { email: user.email };

  await page.addInitScript(
    ({ token, profile }) => {
      localStorage.setItem(
        'auth-storage',
        JSON.stringify({ state: { token, user: profile }, version: 0 }),
      );
    },
    { token: user.token, profile },
  );

  return user;
}

# Playwright E2E Tests

This directory contains end-to-end tests for the Wenjian frontend using Playwright.

## Test Structure

```
e2e/
├── dashboard.spec.ts       # Dashboard and navigation tests
├── resume-upload.spec.ts   # Resume upload flow tests
├── auth.spec.ts           # Authentication tests (API level)
├── interview.spec.ts      # Interview creation and conduct tests
└── report.spec.ts         # Report viewing tests
```

## Prerequisites

1. **Backend server must be running** on `http://localhost:8000`
   ```bash
   # In project root
   uvicorn app.main:app --reload --port 8000
   ```

2. **Frontend dev server** will be started automatically by Playwright
   - Configured in `playwright.config.ts`
   - Runs on `http://localhost:5174`

## Running Tests

```bash
cd frontend-react

# Run all E2E tests (headless)
pnpm test:e2e

# Run tests with UI mode (recommended for development)
pnpm test:e2e:ui

# Run tests in headed mode (see browser)
pnpm test:e2e:headed

# Debug specific test
pnpm test:e2e:debug

# View test report
pnpm test:e2e:report
```

## Test Features

- **Dashboard Tests**: Verify landing page loads, navigation works, health endpoint accessible
- **Resume Upload Tests**: Check resume list, upload UI (file upload tests currently skipped)
- **Authentication Tests**: Test registration, login, profile access via API
- **Interview Tests**: Verify interview list, creation flow, SSE connection
- **Report Tests**: Check report viewing and API endpoints

## Notes

- Most tests are resilient to empty state (no resumes/interviews)
- File upload tests are skipped (require test fixtures)
- Tests use conditional logic to skip when data not available
- Authentication tests use unique emails with timestamps to avoid conflicts
- All tests run against real backend (not mocked)

## CI Integration

Tests are configured to:
- Run in headless mode on CI
- Retry failed tests 2x on CI
- Run sequentially on CI (workers: 1)
- Fail build if `test.only` is present

## Debugging

Use UI mode for the best debugging experience:
```bash
pnpm test:e2e:ui
```

This provides:
- Time travel through test steps
- Visual timeline
- Network inspector
- Console logs
- Screenshot on failure

## Adding New Tests

1. Create a new `.spec.ts` file in `e2e/`
2. Import test utilities: `import { test, expect } from '@playwright/test';`
3. Use `test.describe()` to group related tests
4. Use `test()` for individual test cases
5. Use `test.skip()` for tests that require specific conditions
6. Follow existing patterns for resilience to empty state

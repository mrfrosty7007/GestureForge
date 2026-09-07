import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E configuration for GestureForge.
 *
 * Automatically launches:
 * 1. FastAPI backend on http://127.0.0.1:8000
 * 2. Vite React frontend on http://127.0.0.1:5173
 *
 * Configured with fake media stream flags so tests never depend on
 * physical webcam hardware.
 */
export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30 * 1000,
  expect: {
    timeout: 7000,
  },
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
  ],
  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    launchOptions: {
      args: [
        '--use-fake-ui-for-media-stream',
        '--use-fake-device-for-media-stream',
        '--no-sandbox',
      ],
    },
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command: 'uv run --directory .. uvicorn backend.main:app --host 127.0.0.1 --port 8000',
      url: 'http://127.0.0.1:8000/health',
      timeout: 30 * 1000,
      reuseExistingServer: !process.env.CI,
    },
    {
      command: 'pnpm run dev --host 127.0.0.1 --port 5173',
      url: 'http://127.0.0.1:5173',
      timeout: 30 * 1000,
      reuseExistingServer: !process.env.CI,
    },
  ],
});

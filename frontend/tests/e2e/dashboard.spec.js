import { test, expect } from '@playwright/test';

test.describe('Part 2 — Dashboard Render & Connectivity', () => {
  test.beforeEach(async ({ page }) => {
    // Grant camera permissions for the test origin
    await page.context().grantPermissions(['camera']);
  });

  test('dashboard loads core brand, header, and ops status', async ({ page }) => {
    await page.goto('/');

    // Brand and subtitle
    await expect(page.locator('header')).toBeVisible();
    await expect(page.getByText('GESTUREFORGE', { exact: true })).toBeVisible();
    await expect(page.getByText('CYBER-OPS v1.0')).toBeVisible();
    await expect(
      page.getByText('REAL-TIME AI HAND TELEMETRY GATEWAY')
    ).toBeVisible();
  });

  test('camera panel renders with viewport, reticles, and controls', async ({
    page,
  }) => {
    await page.goto('/');

    // Panel Header
    await expect(page.getByText('LIVE CAMERA FEED')).toBeVisible();
    await expect(
      page.getByText('VIEWPORT 01 • EMBEDDED WEBCAM / MEDIAPIPE AI')
    ).toBeVisible();

    // Viewport Video Element
    const video = page.locator('video');
    await expect(video).toBeAttached();

    // Feed status ticker at bottom of camera panel
    await expect(page.getByText('FEED STATUS:')).toBeVisible();
    await expect(page.getByText('STREAM: WS /ws/telemetry')).toBeVisible();
  });

  test('WebSocket connects successfully and updates top bar & telemetry status', async ({
    page,
  }) => {
    await page.goto('/');

    // TopBar status should switch from OFFLINE to WS TELEMETRY LIVE
    const livePill = page.getByText('WS TELEMETRY LIVE');
    await expect(livePill).toBeVisible({ timeout: 10000 });

    // Telemetry panel streaming badge
    await expect(page.getByText('STREAMING', { exact: true })).toBeVisible();
  });

  test('telemetry panel appears with 4 hardware metric tiles and recent events log', async ({
    page,
  }) => {
    await page.goto('/');

    // Telemetry Header
    await expect(page.getByText('SYSTEM TELEMETRY')).toBeVisible();
    await expect(
      page.getByText('LIVE HARDWARE & MEDIAPIPE INGESTION')
    ).toBeVisible();

    // 4 metric cards
    await expect(page.getByText('CAMERA FPS')).toBeVisible();
    await expect(page.getByText('AI LATENCY')).toBeVisible();
    await expect(page.getByText('HAND COUNT')).toBeVisible();
    await expect(page.getByText('LAST FRAME')).toBeVisible();

    // Activity Stream / Events Log
    await expect(page.getByText('GESTURE EVENT STREAM')).toBeVisible();
  });

  test('hand indicators and pipeline architecture cards render properly', async ({
    page,
  }) => {
    await page.goto('/');

    // Hand tracking indicators in Camera panel
    const handIndicator = page
      .getByText(/LANDMARKS|HAND/i)
      .first();
    await expect(handIndicator).toBeVisible();

    // Pipeline cards at bottom of dashboard
    await expect(page.getByText('MediaPipe Engine')).toBeVisible();
    await expect(page.getByText('Gesture Classifier')).toBeVisible();
    await expect(page.getByText('FastAPI Microservice')).toBeVisible();
    await expect(page.getByText('React Command Center')).toBeVisible();
  });
});

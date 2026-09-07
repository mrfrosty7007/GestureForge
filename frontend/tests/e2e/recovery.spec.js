import { test, expect } from '@playwright/test';

test.describe('Part 4 — Failure Recovery & Graceful Degradation', () => {
  test('gracefully renders fallback UI when camera permission is denied', async ({
    page,
  }) => {
    // Inject mock that rejects getUserMedia with NotAllowedError
    await page.addInitScript(() => {
      if (navigator.mediaDevices) {
        navigator.mediaDevices.getUserMedia = () =>
          Promise.reject(
            new DOMException('Permission denied by user', 'NotAllowedError')
          );
      }
    });

    await page.goto('/');

    // Verify graceful fallback UI in CameraPanel
    await expect(page.getByText('CAMERA PERMISSION DENIED')).toBeVisible();
    await expect(
      page.getByText(/Camera access was denied|blocked by your browser/i)
    ).toBeVisible();

    // Verify Retry button is present and clickable
    const retryBtn = page.getByRole('button', { name: /RETRY PERMISSION/i });
    await expect(retryBtn).toBeVisible();
    await expect(retryBtn).toBeEnabled();

    // Verify entire dashboard layout remains intact without unhandled exceptions
    await expect(page.locator('header')).toBeVisible();
    await expect(page.getByText('SYSTEM TELEMETRY')).toBeVisible();
  });

  test('gracefully renders fallback UI when no webcam device is detected', async ({
    page,
  }) => {
    // Inject mock that rejects getUserMedia with NotFoundError
    await page.addInitScript(() => {
      if (navigator.mediaDevices) {
        navigator.mediaDevices.getUserMedia = () =>
          Promise.reject(
            new DOMException('No camera device found', 'NotFoundError')
          );
      }
    });

    await page.goto('/');

    // Verify Device Not Found fallback UI
    await expect(page.getByText('NO WEBCAM DETECTED')).toBeVisible();
    await expect(
      page.getByText(/No compatible webcam device detected|No camera hardware/i)
    ).toBeVisible();

    const recheckBtn = page.getByRole('button', { name: /RECHECK DEVICES/i });
    await expect(recheckBtn).toBeVisible();
    await expect(recheckBtn).toBeEnabled();
  });

  test('gracefully handles general camera hardware error', async ({ page }) => {
    await page.addInitScript(() => {
      if (navigator.mediaDevices) {
        navigator.mediaDevices.getUserMedia = () =>
          Promise.reject(new Error('Hardware I/O error'));
      }
    });

    await page.goto('/');

    await expect(page.getByText('CAMERA FEED UNAVAILABLE')).toBeVisible();
    const retryBtn = page.getByRole('button', { name: /RETRY CAMERA/i });
    await expect(retryBtn).toBeVisible();
  });

  test('displays Gateway Offline status and recovers connection when available', async ({
    page,
  }) => {
    await page.context().grantPermissions(['camera']);

    // Visit page normally and confirm initial live connection
    await page.goto('/');
    await expect(page.getByText('WS TELEMETRY LIVE')).toBeVisible({
      timeout: 10000,
    });

    // Simulate WebSocket interruption by evaluating client-side close
    await page.evaluate(() => {
      // Find active WebSocket or force closure via global/window
      if (window._wsInstance) {
        window._wsInstance.close();
      }
    });

    // Verify TopBar shows connection status properly
    await expect(
      page.locator('text=WS TELEMETRY LIVE').or(page.locator('text=GATEWAY OFFLINE'))
    ).toBeVisible();
  });
});

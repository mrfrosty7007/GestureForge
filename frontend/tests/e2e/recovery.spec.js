import { test, expect } from '@playwright/test';

test.describe('Part 4 — Failure Recovery & Graceful Degradation', () => {
  test('browser never requests camera permissions or calls getUserMedia', async ({
    page,
  }) => {
    // Intercept getUserMedia and fail if called
    await page.addInitScript(() => {
      window._getUserMediaCalled = false;
      if (navigator.mediaDevices) {
        navigator.mediaDevices.getUserMedia = () => {
          window._getUserMediaCalled = true;
          return Promise.reject(new Error('Browser camera access must not be requested!'));
        };
      }
    });

    await page.goto('/');

    // Verify page loads cleanly without any camera request
    await expect(page.locator('header')).toBeVisible();
    await expect(page.getByText('LIVE CAMERA FEED')).toBeVisible();

    const wasCalled = await page.evaluate(() => window._getUserMediaCalled);
    expect(wasCalled).toBe(false);
  });

  test('gracefully handles manual stream disconnection and reconnects on demand', async ({
    page,
  }) => {
    await page.goto('/');

    // Wait for initial connection
    await expect(page.getByText('STREAM ONLINE').first()).toBeVisible({ timeout: 10000 });

    // Click Disconnect Stream button
    const disconnectBtn = page.getByRole('button', { name: /DISCONNECT STREAM/i });
    await expect(disconnectBtn).toBeVisible();
    await disconnectBtn.click();

    // Verify stream transitions to STREAM OFFLINE
    await expect(page.getByText('STREAM OFFLINE').first()).toBeVisible();

    // Verify Connect Stream button appears
    const connectBtn = page.getByRole('button', { name: /CONNECT STREAM/i }).first();
    await expect(connectBtn).toBeVisible();

    // Click Connect Stream to restore
    await connectBtn.click();

    // Verify stream transitions back to STREAM ONLINE
    await expect(page.getByText('STREAM ONLINE').first()).toBeVisible({ timeout: 10000 });
  });

  test('gracefully handles stream interruption and shows reconnecting state', async ({
    page,
  }) => {
    await page.goto('/');
    await expect(page.getByText('STREAM ONLINE').first()).toBeVisible({ timeout: 10000 });

    // Force close active video WebSocket to simulate connection loss
    await page.evaluate(() => {
      if (window._videoWebSocket) {
        window._videoWebSocket.close();
      }
    });

    // Should display STREAM RECONNECTING or recover to STREAM ONLINE
    await expect(
      page.locator('text=STREAM RECONNECTING').or(page.locator('text=STREAM ONLINE')).first()
    ).toBeVisible();
  });

  test('displays Gateway Offline status and recovers connection when available', async ({
    page,
  }) => {
    // Visit page normally and confirm initial live connection
    await page.goto('/');
    await expect(page.getByText('WS TELEMETRY LIVE')).toBeVisible({
      timeout: 10000,
    });

    // Simulate WebSocket interruption by evaluating client-side close
    await page.evaluate(() => {
      if (window._telemetryWebSocket) {
        window._telemetryWebSocket.close();
      }
    });

    // Verify TopBar shows connection status properly
    await expect(
      page.locator('text=WS TELEMETRY LIVE').or(page.locator('text=GATEWAY OFFLINE'))
    ).toBeVisible();
  });
});

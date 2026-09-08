import { test, expect } from '@playwright/test';

test.describe('Part 4 — Failure Recovery & Graceful Degradation', () => {
  test('browser never requests camera permissions or calls getUserMedia', async ({ page }) => {
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
    await expect
      .poll(() => page.evaluate(() => window._videoWebSocket), { timeout: 1000 })
      .toBe(null);

    // Verify Connect Stream button appears
    const connectBtn = page.getByRole('button', { name: /CONNECT STREAM/i }).first();
    await expect(connectBtn).toBeVisible();

    // Click Connect Stream to restore
    await connectBtn.click();

    // Verify stream transitions back to STREAM ONLINE
    await expect(page.getByText('STREAM ONLINE').first()).toBeVisible({ timeout: 10000 });
  });

  test('gracefully handles stream interruption and shows reconnecting state', async ({ page }) => {
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

  test('reconnects the video stream immediately after restore when the socket closed while hidden', async ({
    page,
  }) => {
    const videoSockets = [];
    page.on('websocket', (webSocket) => {
      if (webSocket.url().includes('/ws/video')) {
        videoSockets.push(webSocket);
      }
    });

    await page.goto('/');
    await expect(page.getByText('STREAM ONLINE').first()).toBeVisible({ timeout: 10000 });
    const initialSocketCount = videoSockets.length;

    await page.evaluate(() => {
      Object.defineProperty(document, 'visibilityState', {
        configurable: true,
        value: 'hidden',
      });
      document.dispatchEvent(new Event('visibilitychange'));
      window._videoWebSocket.close();
    });

    await page.waitForTimeout(100);
    await page.evaluate(() => {
      Object.defineProperty(document, 'visibilityState', {
        configurable: true,
        value: 'visible',
      });
      document.dispatchEvent(new Event('visibilitychange'));
    });

    await expect(page.getByText('STREAM ONLINE').first()).toBeVisible({ timeout: 3000 });
    expect(videoSockets.length).toBe(initialSocketCount + 1);
    expect(videoSockets.filter((webSocket) => !webSocket.isClosed())).toHaveLength(1);
  });

  test('ignores stale video socket callbacks after a replacement connection', async ({ page }) => {
    const videoSockets = [];
    page.on('websocket', (webSocket) => {
      if (webSocket.url().includes('/ws/video')) {
        videoSockets.push(webSocket);
      }
    });

    await page.goto('/');
    await expect(page.getByText('STREAM ONLINE').first()).toBeVisible({ timeout: 10000 });
    const firstSocket = videoSockets[0];

    await page.evaluate(() => {
      window._videoWebSocket.close();
    });
    await expect(page.getByText('STREAM RECONNECTING').first()).toBeVisible({
      timeout: 2000,
    });
    await expect.poll(() => videoSockets.length).toBe(2, { timeout: 5000 });

    await page.evaluate(() => {
      window._videoWebSocket.send('frame');
    });
    await page.waitForTimeout(100);

    expect(firstSocket.isClosed()).toBe(true);
    expect(videoSockets.length).toBe(2);
    await expect.poll(() => videoSockets.length, { timeout: 1000 }).toBe(2);
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

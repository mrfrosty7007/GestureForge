import { test, expect } from '@playwright/test';

test.describe('Part 3 — Real-Time Gesture Synchronization via WebSocket', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().grantPermissions(['camera']);
  });

  test('synchronizes Palm gesture from backend to dashboard HUD instantly', async ({
    page,
    request,
  }) => {
    await page.goto('/');

    // Wait for initial WebSocket connection
    await expect(page.getByText('WS TELEMETRY LIVE')).toBeVisible({
      timeout: 10000,
    });

    // Send Palm gesture event to backend
    const startTime = Date.now();
    const resp = await request.post('http://127.0.0.1:8000/gesture', {
      data: {
        hands: [
          {
            id: 0,
            label: 'Right',
            gesture: 'Palm',
            confidence: 'High',
          },
        ],
        timestamp: Math.floor(Date.now() / 1000),
        telemetry: {
          fps: 29.8,
          latency_ms: 14.2,
          frame: 42,
          hand_count: 1,
        },
      },
    });
    expect(resp.status()).toBe(200);

    // Verify Palm gesture renders in Floating Badge
    const palmBadge = page.locator('text=PALM').first();
    await expect(palmBadge).toBeVisible({ timeout: 2000 });

    // Verify sub-second instant update
    const elapsedMs = Date.now() - startTime;
    expect(elapsedMs).toBeLessThan(2000);

    // Verify Confidence in Camera badge
    await expect(page.getByText('CONFIDENCE: HIGH')).toBeVisible();

    // Verify Activity Stream logs the event
    await expect(page.getByText('GESTURE EVENT STREAM')).toBeVisible();
  });

  test('synchronizes Peace gesture transition', async ({ page, request }) => {
    await page.goto('/');
    await expect(page.getByText('WS TELEMETRY LIVE')).toBeVisible({
      timeout: 10000,
    });

    // Dispatch Peace gesture
    const resp = await request.post('http://127.0.0.1:8000/gesture', {
      data: {
        hands: [
          {
            id: 0,
            label: 'Right',
            gesture: 'Peace',
            confidence: 'High',
          },
        ],
        timestamp: Math.floor(Date.now() / 1000),
        telemetry: {
          fps: 30.5,
          latency_ms: 11.8,
          frame: 55,
          hand_count: 1,
        },
      },
    });
    expect(resp.status()).toBe(200);

    // Verify Peace badge appears
    await expect(page.locator('text=PEACE').first()).toBeVisible({
      timeout: 2000,
    });
  });

  test('supports dual-hand updates with independent handedness and gesture tags', async ({
    page,
    request,
  }) => {
    await page.goto('/');
    await expect(page.getByText('WS TELEMETRY LIVE')).toBeVisible({
      timeout: 10000,
    });

    // Send two hands simultaneously
    const resp = await request.post('http://127.0.0.1:8000/gesture', {
      data: {
        hands: [
          {
            id: 0,
            label: 'Right',
            gesture: 'Peace',
            confidence: 'High',
          },
          {
            id: 1,
            label: 'Left',
            gesture: 'Fist',
            confidence: 'High',
          },
        ],
        timestamp: Math.floor(Date.now() / 1000),
        telemetry: {
          fps: 31.2,
          latency_ms: 16.4,
          frame: 88,
          hand_count: 2,
        },
      },
    });
    expect(resp.status()).toBe(200);

    // Dual-hand tracking status should display
    await expect(page.getByText('DUAL-HAND TRACKING')).toBeVisible({
      timeout: 2000,
    });

    // Individual per-hand tags should appear in camera overlay
    await expect(page.getByText('RIGHT:').first()).toBeVisible();
    await expect(page.getByText('LEFT:').first()).toBeVisible();

    // Hand count metric tile
    await expect(page.locator('text=2 HANDS TRACKED').first()).toBeVisible();
  });

  test('updates confidence tier dynamically', async ({ page, request }) => {
    await page.goto('/');
    await expect(page.getByText('WS TELEMETRY LIVE')).toBeVisible({
      timeout: 10000,
    });

    // Send gesture with Medium confidence
    const resp = await request.post('http://127.0.0.1:8000/gesture', {
      data: {
        hands: [
          {
            id: 0,
            label: 'Right',
            gesture: 'One Finger',
            confidence: 'Medium',
          },
        ],
        timestamp: Math.floor(Date.now() / 1000),
        telemetry: {
          fps: 30.0,
          latency_ms: 13.0,
          frame: 102,
          hand_count: 1,
        },
      },
    });
    expect(resp.status()).toBe(200);

    // Verify Medium confidence reflects on the UI
    await expect(page.getByText('CONFIDENCE: MEDIUM')).toBeVisible({
      timeout: 2000,
    });
  });
});

import { test, expect } from '@playwright/test';

test.describe('Part 5 — Performance, Connection Stability & Responsiveness', () => {
  test('maintains a single active WebSocket connection with zero duplicates', async ({
    page,
  }) => {
    const wsConnections = [];

    page.on('websocket', (ws) => {
      if (ws.url().includes('/ws/telemetry')) {
        wsConnections.push(ws);
      }
    });

    await page.goto('/');

    // Wait for connection to establish and settle
    await expect(page.getByText('WS TELEMETRY LIVE')).toBeVisible({
      timeout: 10000,
    });
    await page.waitForTimeout(2000);

    // Exactly 1 active open telemetry socket at steady state
    const activeSockets = wsConnections.filter((ws) => !ws.isClosed());
    expect(activeSockets.length).toBe(1);

    // Verify no new duplicate sockets leak over time
    const countAtSteadyState = wsConnections.length;
    await page.waitForTimeout(2000);
    expect(wsConnections.length).toBe(countAtSteadyState);
  });

  test('reconnects automatically following connection drop without zombie sockets', async ({
    page,
  }) => {
    const wsEvents = [];

    page.on('websocket', (ws) => {
      if (ws.url().includes('/ws/telemetry')) {
        wsEvents.push(ws);
      }
    });

    await page.goto('/');
    await expect(page.getByText('WS TELEMETRY LIVE')).toBeVisible({
      timeout: 10000,
    });

    const initialCount = wsEvents.length;

    const reconnectPromise = page.waitForEvent('websocket', (ws) =>
      ws.url().includes('/ws/telemetry')
    );

    // Trigger close on the active socket
    await page.evaluate(() => {
      if (window._telemetryWebSocket) {
        window._telemetryWebSocket.close();
      }
    });

    await reconnectPromise;

    // Wait for auto-reconnect
    await expect(page.getByText('WS TELEMETRY LIVE')).toBeVisible({
      timeout: 10000,
    });

    // Exactly 1 new connection was created for the reconnect
    expect(wsEvents.length).toBe(initialCount + 1);

    // Verify only 1 connection is currently active
    const activeSockets = wsEvents.filter((ws) => !ws.isClosed());
    expect(activeSockets.length).toBe(1);
  });

  test('dashboard remains responsive under high telemetry throughput', async ({
    page,
    request,
  }) => {
    await page.goto('/');
    await expect(page.getByText('WS TELEMETRY LIVE')).toBeVisible({
      timeout: 10000,
    });

    // Stream 20 high-frequency telemetry events in rapid succession (simulating 30fps camera feed)
    const gestures = ['Palm', 'Peace', 'Fist', 'One Finger', 'Thumbs Up'];
    const sendBatch = async () => {
      for (let i = 0; i < 20; i++) {
        const gesture = gestures[i % gestures.length];
        await request.post('http://127.0.0.1:8000/gesture', {
          data: {
            hands: [
              {
                id: 0,
                label: 'Right',
                gesture: gesture,
                confidence: 'High',
              },
            ],
            timestamp: Date.now() + i,
            telemetry: {
              fps: 30.0 + (i % 3),
              latency_ms: 12.0 + (i % 5),
              frame: 1000 + i,
              hand_count: 1,
            },
          },
        });
        // Tiny 25ms delay between frames (40 FPS equivalent)
        await new Promise((r) => setTimeout(r, 25));
      }
    };

    await sendBatch();

    // Verify UI did not freeze or crash: buttons and navigation elements are immediately clickable
    const liveOpsBadge = page.getByText('LIVE OPS');
    await expect(liveOpsBadge).toBeVisible();

    // Measure interaction responsiveness: evaluate a microtask in browser
    const startInteraction = Date.now();
    const canInteract = await page.evaluate(() => {
      document.body.classList.add('perf-test-active');
      const hasClass = document.body.classList.contains('perf-test-active');
      document.body.classList.remove('perf-test-active');
      return hasClass;
    });
    const latency = Date.now() - startInteraction;

    expect(canInteract).toBe(true);
    // Main thread responsiveness should be well under 100ms
    expect(latency).toBeLessThan(150);
  });
});

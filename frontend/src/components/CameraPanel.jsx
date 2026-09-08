import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Camera,
  CameraOff,
  Crosshair,
  Zap,
  Shield,
  RefreshCw,
  Radio,
  Layers,
  Power,
  Play,
} from 'lucide-react';

export default function CameraPanel({
  gestureData = null,
  isConnected = false,
  handsDetected = 0,
  telemetry = null,
}) {
  // 'active' (STREAM ONLINE) | 'reconnecting' (STREAM RECONNECTING) | 'offline' (STREAM OFFLINE)
  const [streamState, setStreamState] = useState('reconnecting');
  const [errorMessage, setErrorMessage] = useState('');
  const canvasRef = useRef(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const manualDisconnectRef = useRef(false);
  const pendingFrameRef = useRef(null);
  const renderingFrameRef = useRef(false);
  const animationFrameRef = useRef(null);
  const scheduleRenderRef = useRef(null);
  const mountedRef = useRef(true);
  const streamStateRef = useRef('reconnecting');
  const connectionGenerationRef = useRef(0);
  const renderGenerationRef = useRef(0);

  const hasGesture = gestureData && gestureData.gesture && gestureData.gesture !== 'None';
  const primaryGesture = hasGesture ? gestureData.gesture : null;
  const hands = gestureData && Array.isArray(gestureData.hands) ? gestureData.hands : [];

  const updateStreamState = useCallback((nextState) => {
    streamStateRef.current = nextState;
    setStreamState((currentState) => (currentState === nextState ? currentState : nextState));
  }, []);

  const cancelRender = useCallback(() => {
    if (animationFrameRef.current !== null) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    pendingFrameRef.current = null;
    renderGenerationRef.current += 1;
  }, []);

  // Safely close active video WebSocket
  const closeWebSocket = useCallback(() => {
    connectionGenerationRef.current += 1;
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (wsRef.current) {
      try {
        wsRef.current.onclose = null;
        wsRef.current.onerror = null;
        wsRef.current.onmessage = null;
        wsRef.current.close();
      } catch {
        // ignore
      }
      wsRef.current = null;
      if (typeof window !== 'undefined') {
        window._videoWebSocket = null;
      }
    }
    cancelRender();
  }, [cancelRender]);

  const scheduleRender = useCallback(() => {
    if (
      !mountedRef.current ||
      animationFrameRef.current !== null ||
      renderingFrameRef.current ||
      !pendingFrameRef.current
    ) {
      return;
    }

    animationFrameRef.current = requestAnimationFrame(() => {
      animationFrameRef.current = null;
      if (!mountedRef.current || renderingFrameRef.current || !pendingFrameRef.current) {
        return;
      }

      const frame = pendingFrameRef.current;
      const renderGeneration = renderGenerationRef.current;
      pendingFrameRef.current = null;
      renderingFrameRef.current = true;

      createImageBitmap(frame)
        .then((bitmap) => {
          if (
            !mountedRef.current ||
            renderGeneration !== renderGenerationRef.current ||
            !canvasRef.current
          ) {
            bitmap.close();
            return;
          }
          const canvas = canvasRef.current;
          if (canvas.width !== bitmap.width || canvas.height !== bitmap.height) {
            canvas.width = bitmap.width;
            canvas.height = bitmap.height;
          }
          const ctx = canvas.getContext('2d');
          if (ctx) ctx.drawImage(bitmap, 0, 0);
          bitmap.close();
          if (streamStateRef.current !== 'active') {
            updateStreamState('active');
          }
        })
        .catch((err) => {
          if (mountedRef.current && renderGeneration === renderGenerationRef.current) {
            console.warn('Frame render error:', err);
          }
        })
        .finally(() => {
          renderingFrameRef.current = false;
          if (mountedRef.current && pendingFrameRef.current) {
            scheduleRenderRef.current?.();
          }
        });
    });
  }, [updateStreamState]);
  scheduleRenderRef.current = scheduleRender;

  // Connect to backend WebSocket /ws/video
  const connectStream = useCallback(() => {
    closeWebSocket();
    if (!mountedRef.current) return;
    manualDisconnectRef.current = false;
    updateStreamState('reconnecting');
    setErrorMessage('');

    const host = window.location.hostname || '127.0.0.1';
    const wsUrl = `ws://${host}:8000/ws/video`;
    const connectionGeneration = connectionGenerationRef.current;

    try {
      const ws = new WebSocket(wsUrl);
      ws.binaryType = 'blob';
      wsRef.current = ws;
      if (typeof window !== 'undefined') {
        window._videoWebSocket = ws;
      }

      ws.onopen = () => {
        if (!mountedRef.current || connectionGeneration !== connectionGenerationRef.current) return;
        updateStreamState('active');
        setErrorMessage('');
      };

      ws.onmessage = (event) => {
        if (
          mountedRef.current &&
          connectionGeneration === connectionGenerationRef.current &&
          event.data instanceof Blob
        ) {
          pendingFrameRef.current = event.data;
          scheduleRender();
        }
      };

      ws.onerror = () => {
        if (
          mountedRef.current &&
          connectionGeneration === connectionGenerationRef.current &&
          !manualDisconnectRef.current
        ) {
          updateStreamState('reconnecting');
        }
      };

      ws.onclose = () => {
        if (!mountedRef.current || connectionGeneration !== connectionGenerationRef.current) {
          return;
        }
        if (!manualDisconnectRef.current) {
          updateStreamState('reconnecting');
          // Automatically attempt reconnection every 2.5 seconds
          reconnectTimeoutRef.current = setTimeout(() => {
            connectStream();
          }, 2500);
        } else {
          updateStreamState('offline');
        }
      };
    } catch (err) {
      updateStreamState('offline');
      setErrorMessage(err.message || 'Failed to connect to video stream');
    }
  }, [closeWebSocket, scheduleRender, updateStreamState]);

  // User manual control actions
  const handleDisconnect = useCallback(() => {
    manualDisconnectRef.current = true;
    closeWebSocket();
    updateStreamState('offline');
  }, [closeWebSocket, updateStreamState]);

  const handleConnect = useCallback(() => {
    connectStream();
  }, [connectStream]);

  const handleRetry = useCallback(() => {
    connectStream();
  }, [connectStream]);

  // Mount / Unmount lifecycle
  useEffect(() => {
    mountedRef.current = true;
    connectStream();
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        renderGenerationRef.current += 1;
        pendingFrameRef.current = null;
        return;
      }
      if (document.visibilityState === 'visible') {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send('frame');
        } else if (!manualDisconnectRef.current) {
          connectStream();
        }
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      mountedRef.current = false;
      manualDisconnectRef.current = true;
      closeWebSocket();
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [connectStream, closeWebSocket]);

  return (
    <div className="cyber-panel cyber-panel-glow cyber-corner-reticle rounded-2xl p-4 md:p-6 relative flex flex-col justify-between overflow-hidden min-h-[460px] lg:min-h-[520px]">
      {/* 1. Top Panel Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-cyber-border/80">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-md bg-cyber-teal/15 text-cyber-teal border border-cyber-teal/30">
            <Camera size={18} />
          </div>
          <div>
            <h3 className="font-heading font-bold text-sm md:text-base tracking-wider text-white flex items-center gap-2">
              LIVE CAMERA FEED
              {streamState === 'active' && (
                <span className="inline-flex items-center gap-1 font-mono text-[10px] px-2 py-0.5 rounded bg-cyber-teal/10 text-cyber-teal border border-cyber-teal/30">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyber-teal status-dot" />
                  STREAM ONLINE
                </span>
              )}
              {streamState === 'reconnecting' && (
                <span className="inline-flex items-center gap-1 font-mono text-[10px] px-2 py-0.5 rounded bg-cyber-warning/10 text-cyber-warning border border-cyber-warning/30">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyber-warning animate-pulse" />
                  STREAM RECONNECTING
                </span>
              )}
              {streamState === 'offline' && (
                <span className="inline-flex items-center gap-1 font-mono text-[10px] px-2 py-0.5 rounded bg-cyber-danger/10 text-cyber-danger border border-cyber-danger/30">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyber-danger" />
                  STREAM OFFLINE
                </span>
              )}
            </h3>
            <span className="font-mono text-[11px] text-cyber-muted tracking-wide">
              VIEWPORT 01 • UNIFIED WEBCAM PIPELINE / MEDIAPIPE AI
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          {/* Stream Control Action Buttons */}
          {streamState === 'active' ? (
            <button
              onClick={handleDisconnect}
              className="px-2.5 py-1 rounded bg-cyber-danger/10 hover:bg-cyber-danger/20 text-cyber-danger border border-cyber-danger/30 flex items-center gap-1.5 transition-colors cursor-pointer"
              title="Disconnect Stream"
            >
              <Power size={12} />
              <span>Disconnect Stream</span>
            </button>
          ) : streamState === 'offline' ? (
            <button
              onClick={handleConnect}
              className="px-2.5 py-1 rounded bg-cyber-teal/15 hover:bg-cyber-teal/25 text-cyber-teal border border-cyber-teal/40 flex items-center gap-1.5 transition-colors cursor-pointer"
              title="Connect Stream"
            >
              <Play size={12} />
              <span>Connect Stream</span>
            </button>
          ) : (
            <button
              onClick={handleRetry}
              className="px-2.5 py-1 rounded bg-cyber-warning/15 hover:bg-cyber-warning/25 text-cyber-warning border border-cyber-warning/40 flex items-center gap-1.5 transition-colors cursor-pointer"
              title="Retry Stream"
            >
              <RefreshCw size={12} className="animate-spin" />
              <span>Retry Stream</span>
            </button>
          )}

          <span className="px-2.5 py-1 rounded bg-cyber-panel-dark text-cyber-teal border border-cyber-border flex items-center gap-1.5">
            <Crosshair
              size={13}
              className={`text-cyber-teal ${streamState === 'active' ? 'animate-spin' : ''}`}
              style={{ animationDuration: '12s' }}
            />
            {handsDetected > 0
              ? `${handsDetected} HAND${handsDetected > 1 ? 'S' : ''} TRACKED`
              : '21 LANDMARKS'}
          </span>
          <span className="px-2.5 py-1 rounded bg-cyber-teal/10 text-cyber-teal border border-cyber-teal/30 font-semibold">
            {telemetry && typeof telemetry.fps === 'number' && telemetry.fps > 0
              ? `1280×720 • ${telemetry.fps.toFixed(1)} FPS`
              : '1280×720 • 30 FPS'}
          </span>
        </div>
      </div>

      {/* 2. Main Viewport Display Area */}
      <div className="relative my-4 flex-1 rounded-xl bg-cyber-panel-dark/95 border border-cyber-teal/30 overflow-hidden flex items-center justify-center shadow-inner min-h-[340px] md:min-h-[400px]">
        {/* Background Grid */}
        <div
          className="absolute inset-0 opacity-15 pointer-events-none z-0"
          style={{
            backgroundImage:
              'radial-gradient(circle at 50% 50%, rgba(46,242,197,0.15) 0%, transparent 70%), linear-gradient(to right, rgba(46,242,197,0.2) 1px, transparent 1px), linear-gradient(to bottom, rgba(46,242,197,0.2) 1px, transparent 1px)',
            backgroundSize: '100% 100%, 32px 32px, 32px 32px',
          }}
        />

        {/* Live Canvas Element rendering WebSocket JPEG frames */}
        <canvas
          ref={canvasRef}
          className={`w-full h-full object-cover transition-opacity duration-300 ${
            streamState === 'active' ? 'opacity-100' : 'opacity-0 absolute pointer-events-none'
          }`}
        />

        {/* Radar Sweep Scanline Overlay */}
        <div className="absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-cyber-teal/40 to-transparent radar-sweep pointer-events-none z-20" />

        {/* Corner Reticle Brackets on Viewport */}
        <div className="absolute top-3 left-3 w-4 h-4 border-t-2 border-l-2 border-cyber-teal pointer-events-none z-20" />
        <div className="absolute top-3 right-3 w-4 h-4 border-t-2 border-r-2 border-cyber-teal pointer-events-none z-20" />
        <div className="absolute bottom-3 left-3 w-4 h-4 border-b-2 border-l-2 border-cyber-teal pointer-events-none z-20" />
        <div className="absolute bottom-3 right-3 w-4 h-4 border-b-2 border-r-2 border-cyber-teal pointer-events-none z-20" />

        {/* Center Target Reticle */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-20 z-10">
          <div className="w-48 h-48 rounded-full border border-cyber-teal/40 flex items-center justify-center">
            <div className="w-32 h-32 rounded-full border border-dashed border-cyber-teal/60" />
          </div>
        </div>

        {/* Fallback 1: Stream Reconnecting / Awaiting frames */}
        {streamState === 'reconnecting' && (
          <div className="relative z-30 flex flex-col items-center text-center p-6 max-w-sm animate-fadeIn">
            <div className="w-16 h-16 rounded-2xl bg-cyber-warning/15 border-2 border-cyber-warning flex items-center justify-center text-cyber-warning mb-4 shadow-lg shadow-cyber-warning/20">
              <RefreshCw size={28} className="animate-spin text-cyber-warning" />
            </div>
            <h4 className="font-heading font-semibold text-white text-base tracking-wide mb-1">
              STREAM RECONNECTING
            </h4>
            <p className="font-mono text-xs text-cyber-muted leading-relaxed mb-4">
              Awaiting video frames from backend AI worker via{' '}
              <code className="text-cyber-teal">/ws/video</code>.
            </p>
            <button
              onClick={handleRetry}
              className="px-4 py-2 rounded-lg bg-cyber-warning/20 hover:bg-cyber-warning/30 text-cyber-warning border border-cyber-warning font-mono text-xs font-semibold flex items-center gap-2 transition-colors cursor-pointer"
            >
              <RefreshCw size={12} />
              Retry Stream
            </button>
          </div>
        )}

        {/* Fallback 2: Stream Offline */}
        {streamState === 'offline' && (
          <div className="relative z-30 flex flex-col items-center text-center p-6 max-w-sm animate-fadeIn">
            <div className="w-16 h-16 rounded-2xl bg-cyber-danger/15 border-2 border-cyber-danger flex items-center justify-center text-cyber-danger mb-4 shadow-lg shadow-cyber-danger/20">
              <CameraOff size={28} />
            </div>
            <h4 className="font-heading font-semibold text-white text-base tracking-wide mb-1">
              STREAM OFFLINE
            </h4>
            <p className="font-mono text-xs text-cyber-muted leading-relaxed mb-4">
              {errorMessage ||
                'Unified video stream is disconnected. Connect stream to receive live perception.'}
            </p>
            <button
              onClick={handleConnect}
              className="px-4 py-2 rounded-lg bg-cyber-teal/20 hover:bg-cyber-teal/30 text-cyber-teal border border-cyber-teal font-mono text-xs font-semibold flex items-center gap-2 transition-colors cursor-pointer"
            >
              <Play size={12} />
              Connect Stream
            </button>
          </div>
        )}

        {/* Top HUD Stats Overlay */}
        {streamState === 'active' && (
          <>
            <div className="absolute top-3 inset-x-3 flex flex-wrap items-center justify-between gap-2 z-20 pointer-events-none">
              {/* Top Left: Live Recording Pill & Dual-Track Status */}
              <div className="flex items-center gap-2">
                <div className="px-2.5 py-1 rounded bg-black/60 backdrop-blur-md border border-cyber-teal/40 font-mono text-[11px] text-cyber-teal flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-cyber-teal status-dot" />
                  <span className="font-semibold tracking-wider">LIVE FEED</span>
                </div>
                <div className="hidden sm:flex items-center gap-1 px-2.5 py-1 rounded bg-black/60 backdrop-blur-md border border-cyber-border font-mono text-[11px] text-white">
                  <Layers size={11} className="text-cyber-teal" />
                  <span>
                    {handsDetected === 2
                      ? 'DUAL-HAND TRACKING'
                      : handsDetected === 1
                        ? 'SINGLE-HAND TRACKING'
                        : 'AWAITING HANDS'}
                  </span>
                </div>
              </div>

              {/* Top Right: Multi-Hand Real-Time Pills */}
              <div className="flex items-center gap-1.5">
                {hands.length > 0 ? (
                  hands.map((hand) => (
                    <div
                      key={hand.id}
                      className="px-2 py-0.5 rounded bg-black/70 backdrop-blur-md border border-cyber-teal/50 font-mono text-[10px] text-white flex items-center gap-1.5 shadow-glow-teal"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-cyber-teal status-dot" />
                      <span className="text-cyber-teal font-bold">{hand.label.toUpperCase()}:</span>
                      <span className="font-semibold">{hand.gesture}</span>
                      <span className="text-cyber-muted text-[9px]">({hand.confidence})</span>
                    </div>
                  ))
                ) : (
                  <div className="px-2 py-0.5 rounded bg-black/60 backdrop-blur-md border border-cyber-border font-mono text-[10px] text-cyber-muted flex items-center gap-1">
                    <Radio size={10} className="text-cyber-teal" />
                    <span>WS TELEMETRY SYNCED</span>
                  </div>
                )}
              </div>
            </div>

            {/* Center / Bottom Floating Gesture Badge */}
            {hasGesture ? (
              <div className="absolute bottom-10 inset-x-4 mx-auto max-w-sm z-20 pointer-events-none animate-fadeIn">
                <div className="p-3 rounded-xl bg-cyber-panel/90 backdrop-blur-md border border-cyber-teal shadow-glow-teal-lg flex items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-cyber-teal/20 border border-cyber-teal flex items-center justify-center text-cyber-teal shadow-inner">
                      <Zap size={18} className="animate-pulse" />
                    </div>
                    <div>
                      <div className="font-heading font-bold text-base md:text-lg text-white tracking-wider flex items-center gap-2">
                        {primaryGesture.toUpperCase()}
                        <span className="font-mono font-normal text-[10px] px-1.5 py-0.5 rounded bg-cyber-teal/15 text-cyber-teal border border-cyber-teal/30">
                          {handsDetected > 1 ? 'MULTI-HAND' : 'DETECTED'}
                        </span>
                      </div>
                      <div className="font-mono text-[10px] text-cyber-muted">
                        CONFIDENCE:{' '}
                        <span className="text-cyber-teal font-semibold">
                          {gestureData.confidence || 'HIGH'}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="font-mono text-[10px] px-2.5 py-1 rounded bg-cyber-teal text-cyber-bg font-bold tracking-wider">
                    RECOGNIZED
                  </div>
                </div>
              </div>
            ) : (
              <div className="absolute bottom-10 inset-x-4 mx-auto max-w-xs z-20 pointer-events-none">
                <div className="px-3 py-1.5 rounded-lg bg-black/65 backdrop-blur-sm border border-cyber-border/70 text-center font-mono text-[11px] text-cyber-muted shadow-sm">
                  SHOW HAND GESTURE TO CAMERA
                </div>
              </div>
            )}
          </>
        )}

        {/* Viewport Meta Tags Bottom Left */}
        <div className="absolute bottom-3 left-4 font-mono text-[11px] text-cyber-muted flex items-center gap-3 z-20 pointer-events-none">
          <span className="flex items-center gap-1 text-cyber-teal">
            <Zap size={11} /> AI STREAM: {hasGesture ? 'SYNCED' : 'STANDBY'}
          </span>
          <span className="hidden sm:inline text-white/20">|</span>
          <span className="hidden sm:inline">MIRROR: ENABLED</span>
          {telemetry && typeof telemetry.latency_ms === 'number' && telemetry.latency_ms > 0 && (
            <>
              <span className="hidden sm:inline text-white/20">|</span>
              <span className="hidden sm:inline text-cyber-teal">
                INFERENCE: {telemetry.latency_ms.toFixed(1)}ms
              </span>
            </>
          )}
        </div>

        {/* Viewport Meta Tags Bottom Right */}
        <div className="absolute bottom-3 right-4 font-mono text-[11px] text-cyber-muted flex items-center gap-1.5 z-20 pointer-events-none">
          <Shield size={11} className="text-cyber-teal" />
          <span>
            {telemetry && telemetry.frame ? `FRAME #${telemetry.frame}` : 'SECURED LOCAL'}
          </span>
        </div>
      </div>

      {/* 3. Bottom Status Ticker */}
      <div className="pt-2 flex flex-wrap items-center justify-between gap-2 font-mono text-xs text-cyber-muted">
        <span>
          FEED STATUS:{' '}
          <span
            className={
              streamState === 'active'
                ? 'text-cyber-teal font-semibold'
                : streamState === 'reconnecting'
                  ? 'text-cyber-warning'
                  : 'text-cyber-danger'
            }
          >
            {streamState === 'active'
              ? 'STREAM ONLINE'
              : streamState === 'reconnecting'
                ? 'STREAM RECONNECTING'
                : 'STREAM OFFLINE'}
          </span>
          {' • TELEMETRY: '}
          <span className={isConnected ? 'text-cyber-teal font-semibold' : 'text-cyber-muted'}>
            {isConnected ? 'SYNCED' : 'STANDBY'}
          </span>
        </span>
        <span className="text-cyber-teal">STREAM: WS /ws/video</span>
      </div>
    </div>
  );
}

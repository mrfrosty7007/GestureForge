import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Camera,
  CameraOff,
  Crosshair,
  Zap,
  Shield,
  AlertTriangle,
  RefreshCw,
  Radio,
  Layers,
} from 'lucide-react';

export default function CameraPanel({
  gestureData = null,
  isConnected = false,
  handsDetected = 0,
  telemetry = null,
}) {
  const [cameraState, setCameraState] = useState('loading'); // 'loading' | 'active' | 'denied' | 'notfound' | 'error'
  const [errorMessage, setErrorMessage] = useState('');
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  const hasGesture = gestureData && gestureData.gesture && gestureData.gesture !== 'None';
  const primaryGesture = hasGesture ? gestureData.gesture : null;
  const hands = gestureData && Array.isArray(gestureData.hands) ? gestureData.hands : [];

  // Stop any existing camera tracks cleanly
  const stopCurrentStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        try {
          track.stop();
        } catch {
          // ignore
        }
      });
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  }, []);

  // Request browser webcam access using navigator.mediaDevices.getUserMedia
  const startCamera = useCallback(async () => {
    stopCurrentStream();
    setCameraState('loading');
    setErrorMessage('');

    if (
      typeof navigator === 'undefined' ||
      !navigator.mediaDevices ||
      !navigator.mediaDevices.getUserMedia
    ) {
      setCameraState('error');
      setErrorMessage('Browser does not support navigator.mediaDevices.getUserMedia API.');
      return;
    }

    try {
      const constraints = {
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'user',
        },
        audio: false,
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        try {
          await videoRef.current.play();
        } catch {
          // Some browsers require user interaction; muted video usually autoplays
        }
      }
      setCameraState('active');
    } catch (err) {
      const errorName = err.name || '';
      if (errorName === 'NotAllowedError' || errorName === 'PermissionDeniedError') {
        setCameraState('denied');
        setErrorMessage(
          'Camera access was denied. Please allow camera permissions in your browser.'
        );
      } else if (
        errorName === 'NotFoundError' ||
        errorName === 'DevicesNotFoundError' ||
        errorName === 'OverconstrainedError'
      ) {
        setCameraState('notfound');
        setErrorMessage('No compatible webcam device detected on this system.');
      } else {
        setCameraState('error');
        setErrorMessage(err.message || 'Unable to start camera feed.');
      }
    }
  }, [stopCurrentStream]);

  // Lifecycle: initialize camera on mount, stop tracks on unmount
  useEffect(() => {
    let isMounted = true;

    async function init() {
      if (isMounted) {
        await startCamera();
      }
    }
    init();

    return () => {
      isMounted = false;
      stopCurrentStream();
    };
  }, [startCamera, stopCurrentStream]);

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
              {cameraState === 'active' && (
                <span className="inline-flex items-center gap-1 font-mono text-[10px] px-2 py-0.5 rounded bg-cyber-teal/10 text-cyber-teal border border-cyber-teal/30">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyber-teal status-dot" />
                  ONLINE
                </span>
              )}
            </h3>
            <span className="font-mono text-[11px] text-cyber-muted tracking-wide">
              VIEWPORT 01 • EMBEDDED WEBCAM / MEDIAPIPE AI
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="px-2.5 py-1 rounded bg-cyber-panel-dark text-cyber-teal border border-cyber-border flex items-center gap-1.5">
            <Crosshair
              size={13}
              className={`text-cyber-teal ${cameraState === 'active' ? 'animate-spin' : ''}`}
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

        {/* Live Video Element */}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className={`w-full h-full object-cover transform -scale-x-100 transition-opacity duration-500 ${
            cameraState === 'active' ? 'opacity-100' : 'opacity-0 absolute'
          }`}
        />

        {/* Optional Overlay Canvas for future landmark rendering */}
        <canvas
          ref={canvasRef}
          className="absolute inset-0 w-full h-full pointer-events-none z-10"
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

        {/* Fallback 1: Loading State */}
        {cameraState === 'loading' && (
          <div className="relative z-30 flex flex-col items-center text-center p-6 max-w-sm animate-fadeIn">
            <div className="w-16 h-16 rounded-2xl bg-cyber-teal/15 border-2 border-cyber-teal flex items-center justify-center text-cyber-teal mb-4 shadow-glow-teal">
              <RefreshCw size={28} className="animate-spin text-cyber-teal" />
            </div>
            <h4 className="font-heading font-semibold text-white text-base tracking-wide mb-1">
              INITIALIZING WEBCAM...
            </h4>
            <p className="font-mono text-xs text-cyber-muted leading-relaxed">
              Requesting camera stream via <code className="text-cyber-teal">getUserMedia()</code>.
              Please allow camera permissions if prompted.
            </p>
          </div>
        )}

        {/* Fallback 2: Permission Denied */}
        {cameraState === 'denied' && (
          <div className="relative z-30 flex flex-col items-center text-center p-6 max-w-sm animate-fadeIn">
            <div className="w-16 h-16 rounded-2xl bg-cyber-danger/15 border-2 border-cyber-danger flex items-center justify-center text-cyber-danger mb-4 shadow-lg shadow-cyber-danger/20">
              <CameraOff size={28} />
            </div>
            <h4 className="font-heading font-semibold text-white text-base tracking-wide mb-1">
              CAMERA PERMISSION DENIED
            </h4>
            <p className="font-mono text-xs text-cyber-muted leading-relaxed mb-4">
              {errorMessage ||
                'Camera access was blocked by your browser. Please allow camera permissions to enable live perception.'}
            </p>
            <button
              onClick={startCamera}
              className="px-4 py-2 rounded-lg bg-cyber-teal/20 hover:bg-cyber-teal/30 text-cyber-teal border border-cyber-teal font-mono text-xs font-semibold flex items-center gap-2 transition-colors cursor-pointer"
            >
              <RefreshCw size={12} />
              RETRY PERMISSION
            </button>
          </div>
        )}

        {/* Fallback 3: Device Not Found */}
        {cameraState === 'notfound' && (
          <div className="relative z-30 flex flex-col items-center text-center p-6 max-w-sm animate-fadeIn">
            <div className="w-16 h-16 rounded-2xl bg-cyber-warning/15 border-2 border-cyber-warning flex items-center justify-center text-cyber-warning mb-4 shadow-lg shadow-cyber-warning/20">
              <AlertTriangle size={28} />
            </div>
            <h4 className="font-heading font-semibold text-white text-base tracking-wide mb-1">
              NO WEBCAM DETECTED
            </h4>
            <p className="font-mono text-xs text-cyber-muted leading-relaxed mb-4">
              {errorMessage || 'No camera hardware found. Please connect a USB webcam and retry.'}
            </p>
            <button
              onClick={startCamera}
              className="px-4 py-2 rounded-lg bg-cyber-teal/20 hover:bg-cyber-teal/30 text-cyber-teal border border-cyber-teal font-mono text-xs font-semibold flex items-center gap-2 transition-colors cursor-pointer"
            >
              <RefreshCw size={12} />
              RECHECK DEVICES
            </button>
          </div>
        )}

        {/* Fallback 4: General Error */}
        {cameraState === 'error' && (
          <div className="relative z-30 flex flex-col items-center text-center p-6 max-w-sm animate-fadeIn">
            <div className="w-16 h-16 rounded-2xl bg-cyber-danger/15 border-2 border-cyber-danger flex items-center justify-center text-cyber-danger mb-4 shadow-lg shadow-cyber-danger/20">
              <AlertTriangle size={28} />
            </div>
            <h4 className="font-heading font-semibold text-white text-base tracking-wide mb-1">
              CAMERA FEED UNAVAILABLE
            </h4>
            <p className="font-mono text-xs text-cyber-muted leading-relaxed mb-4">
              {errorMessage}
            </p>
            <button
              onClick={startCamera}
              className="px-4 py-2 rounded-lg bg-cyber-teal/20 hover:bg-cyber-teal/30 text-cyber-teal border border-cyber-teal font-mono text-xs font-semibold flex items-center gap-2 transition-colors cursor-pointer"
            >
              <RefreshCw size={12} />
              RETRY CAMERA
            </button>
          </div>
        )}

        {/* Live Camera Overlays (Active State) */}
        {cameraState === 'active' && (
          <>
            {/* Top HUD Stats Overlay */}
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

              {/* Top Right: Multi-Hand Real-Time Pills from Task 2.1 */}
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
          <span className={isConnected ? 'text-cyber-teal font-semibold' : 'text-cyber-danger'}>
            {isConnected ? 'TELEMETRY STREAM OPEN' : 'STANDBY MODE'}
          </span>{' '}
          • CAMERA:{' '}
          <span
            className={
              cameraState === 'active'
                ? 'text-cyber-teal font-semibold'
                : cameraState === 'loading'
                  ? 'text-cyber-warning'
                  : 'text-cyber-danger'
            }
          >
            {cameraState.toUpperCase()}
          </span>
        </span>
        <span className="text-cyber-teal">STREAM: WS /ws/telemetry</span>
      </div>
    </div>
  );
}

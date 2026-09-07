import { Camera, Eye, Crosshair, Terminal, Zap, Shield } from 'lucide-react';

export default function CameraPanel({ gestureData, isConnected }) {
  const hasGesture = gestureData && gestureData.gesture && gestureData.gesture !== 'None';
  const gesture = hasGesture ? gestureData.gesture : null;

  return (
    <div className="cyber-panel cyber-panel-glow cyber-corner-reticle rounded-2xl p-4 md:p-6 relative flex flex-col justify-between overflow-hidden min-h-[420px] lg:min-h-[480px]">
      {/* Top Panel Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-cyber-border/80">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-md bg-cyber-teal/15 text-cyber-teal border border-cyber-teal/30">
            <Camera size={18} />
          </div>
          <div>
            <h3 className="font-heading font-bold text-sm md:text-base tracking-wider text-white">
              LIVE CAMERA FEED
            </h3>
            <span className="font-mono text-[11px] text-cyber-muted tracking-wide">
              VIEWPORT 01 • OPENCV / MEDIAPIPE INGESTION
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="px-2.5 py-1 rounded bg-cyber-panel-dark text-cyber-teal border border-cyber-border flex items-center gap-1.5">
            <Crosshair
              size={13}
              className="text-cyber-teal animate-spin"
              style={{ animationDuration: '12s' }}
            />
            21 LANDMARKS TRACKING
          </span>
          <span className="px-2.5 py-1 rounded bg-cyber-teal/10 text-cyber-teal border border-cyber-teal/30 font-semibold">
            1280×720 • 30 FPS
          </span>
        </div>
      </div>

      {/* Main Viewport Display Area */}
      <div className="relative my-4 flex-1 rounded-xl bg-cyber-panel-dark/95 border border-cyber-teal/30 overflow-hidden flex items-center justify-center p-6 shadow-inner">
        {/* Background Grid & Radar Sweep */}
        <div
          className="absolute inset-0 opacity-15 pointer-events-none"
          style={{
            backgroundImage:
              'radial-gradient(circle at 50% 50%, rgba(46,242,197,0.15) 0%, transparent 70%), linear-gradient(to right, rgba(46,242,197,0.2) 1px, transparent 1px), linear-gradient(to bottom, rgba(46,242,197,0.2) 1px, transparent 1px)',
            backgroundSize: '100% 100%, 32px 32px, 32px 32px',
          }}
        />

        {/* Scanline line overlay */}
        <div className="absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-cyber-teal/40 to-transparent radar-sweep pointer-events-none" />

        {/* Corner Reticle Brackets on inner viewport */}
        <div className="absolute top-3 left-3 w-4 h-4 border-t-2 border-l-2 border-cyber-teal pointer-events-none" />
        <div className="absolute top-3 right-3 w-4 h-4 border-t-2 border-r-2 border-cyber-teal pointer-events-none" />
        <div className="absolute bottom-3 left-3 w-4 h-4 border-b-2 border-l-2 border-cyber-teal pointer-events-none" />
        <div className="absolute bottom-3 right-3 w-4 h-4 border-b-2 border-r-2 border-cyber-teal pointer-events-none" />

        {/* Center Target Reticle */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-20">
          <div className="w-48 h-48 rounded-full border border-cyber-teal/40 flex items-center justify-center">
            <div className="w-32 h-32 rounded-full border border-dashed border-cyber-teal/60" />
          </div>
        </div>

        {/* Dynamic Hand Detection Hologram Overlay */}
        <div className="relative z-10 flex flex-col items-center text-center max-w-md">
          {hasGesture ? (
            <div className="flex flex-col items-center animate-fadeIn">
              <div className="relative flex items-center justify-center w-24 h-24 rounded-2xl bg-cyber-teal/15 border-2 border-cyber-teal shadow-glow-teal-lg mb-4">
                <svg
                  className="w-14 h-14 text-cyber-teal animate-pulse"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                >
                  <path d="M18 11V6a2 2 0 0 0-4 0v5h-1V3a2 2 0 0 0-4 0v8H8V5a2 2 0 0 0-4 0v9a8 8 0 0 0 16 0v-3z" />
                </svg>
                <div className="absolute -top-2 -right-2 px-2 py-0.5 rounded bg-cyber-teal text-cyber-bg font-mono font-bold text-[10px]">
                  ACTIVE
                </div>
              </div>

              <div className="px-4 py-1.5 rounded-full bg-cyber-teal/20 border border-cyber-teal text-cyber-teal font-heading font-bold text-lg md:text-xl tracking-wider shadow-glow-teal mb-2">
                {gesture.toUpperCase()}
              </div>

              <p className="font-mono text-xs text-cyber-teal/90">
                Confidence: <span className="font-bold text-white">{gestureData.confidence}</span> •
                Ingested via Backend API
              </p>
            </div>
          ) : (
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 rounded-xl bg-cyber-panel border border-cyber-border flex items-center justify-center text-cyber-teal/60 mb-3 shadow-inner">
                <Eye size={28} className="animate-pulse" />
              </div>

              <h4 className="font-heading font-semibold text-white text-base tracking-wide mb-1">
                AWAITING CAMERA INGESTION
              </h4>
              <p className="font-mono text-xs text-cyber-muted max-w-xs leading-relaxed mb-4">
                Webcam stream is processed locally in{' '}
                <code className="text-cyber-teal">ai-model/hand_detection.py</code> and synchronized
                to this HUD.
              </p>

              <div className="p-3 rounded-lg bg-cyber-panel border border-cyber-border/60 text-left font-mono text-xs text-cyber-muted w-full">
                <div className="text-[11px] text-cyber-teal uppercase tracking-wider mb-1 flex items-center gap-1">
                  <Terminal size={12} /> Launch AI Perception:
                </div>
                <code className="text-white select-all block bg-black/40 px-2 py-1 rounded">
                  cd ai-model && python hand_detection.py
                </code>
              </div>
            </div>
          )}
        </div>

        {/* Viewport Meta Tags Bottom Left */}
        <div className="absolute bottom-3 left-4 font-mono text-[11px] text-cyber-muted flex items-center gap-3">
          <span className="flex items-center gap-1 text-cyber-teal">
            <Zap size={11} /> AI STREAM: {hasGesture ? 'SYNCED' : 'STANDBY'}
          </span>
          <span className="hidden sm:inline text-white/20">|</span>
          <span className="hidden sm:inline">MIRROR VIEW: ENABLED</span>
        </div>

        {/* Viewport Meta Tags Bottom Right */}
        <div className="absolute bottom-3 right-4 font-mono text-[11px] text-cyber-muted flex items-center gap-1.5">
          <Shield size={11} className="text-cyber-teal" />
          <span>SECURITY: SECURED LOCAL</span>
        </div>
      </div>

      {/* Bottom Status Ticker */}
      <div className="pt-2 flex flex-wrap items-center justify-between gap-2 font-mono text-xs text-cyber-muted">
        <span>FEED STATUS: {isConnected ? 'TELEMETRY STREAM OPEN' : 'STANDBY MODE'}</span>
        <span className="text-cyber-teal">TARGET: /gesture/latest</span>
      </div>
    </div>
  );
}

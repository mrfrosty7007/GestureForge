import { Hand, Gauge, Server, CheckCircle2, AlertTriangle, Sparkles } from 'lucide-react';

export default function KpiCards({ gestureData, backendStatus, pingMs }) {
  const isOnline = backendStatus === 'connected';
  const hasGesture = gestureData && gestureData.gesture && gestureData.gesture !== 'None';
  const gestureName = hasGesture ? gestureData.gesture.toUpperCase() : (isOnline ? 'WAITING FOR GESTURE' : 'DISCONNECTED');
  const confidence = hasGesture ? (gestureData.confidence || 'HIGH') : (isOnline ? 'STANDBY' : 'N/A');

  // Confidence progress gauge percentage
  const getConfidencePercent = () => {
    if (!hasGesture) return 0;
    if (confidence.toLowerCase() === 'high') return 95;
    if (confidence.toLowerCase() === 'medium') return 72;
    return 45;
  };

  const confidencePercent = getConfidencePercent();

  return (
    <section className="grid grid-cols-1 md:grid-cols-3 gap-4 lg:gap-6">
      {/* 1. Current Gesture Card */}
      <div className="cyber-panel cyber-corner-reticle rounded-xl p-5 relative overflow-hidden transition-all duration-300 hover:shadow-glow-teal hover:border-cyber-teal/60">
        <div className="flex items-center justify-between mb-3">
          <span className="font-mono text-xs font-semibold tracking-wider text-cyber-muted uppercase flex items-center gap-2">
            <Hand size={15} className="text-cyber-teal" />
            CURRENT GESTURE
          </span>
          <span
            className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded border ${
              hasGesture
                ? 'bg-cyber-teal/15 text-cyber-teal border-cyber-teal/40'
                : 'bg-white/5 text-cyber-muted border-white/10'
            }`}
          >
            {hasGesture ? 'DETECTED' : 'AWAITING INPUT'}
          </span>
        </div>

        <div className="my-2">
          <h2
            className={`font-heading text-2xl lg:text-3xl font-extrabold tracking-wide transition-all duration-300 ${
              hasGesture
                ? 'text-white drop-shadow-[0_0_12px_rgba(46,242,197,0.7)]'
                : 'text-cyber-muted/60 text-xl'
            }`}
          >
            {gestureName}
          </h2>
          <p className="font-mono text-xs text-cyber-muted mt-1 flex items-center gap-1.5">
            <Sparkles size={12} className={hasGesture ? 'text-cyber-teal animate-pulse' : 'text-cyber-muted'} />
            {hasGesture ? `Timestamp: ${gestureData.timestamp || 'Live Stream'}` : 'Position hand in webcam view'}
          </p>
        </div>

        {/* Ambient background glow */}
        <div className="absolute -bottom-6 -right-6 w-28 h-28 rounded-full bg-cyber-teal/10 blur-2xl pointer-events-none" />
      </div>

      {/* 2. Confidence Card */}
      <div className="cyber-panel cyber-corner-reticle rounded-xl p-5 relative overflow-hidden transition-all duration-300 hover:shadow-glow-teal hover:border-cyber-teal/60">
        <div className="flex items-center justify-between mb-3">
          <span className="font-mono text-xs font-semibold tracking-wider text-cyber-muted uppercase flex items-center gap-2">
            <Gauge size={15} className="text-cyber-teal" />
            DETECTION CONFIDENCE
          </span>
          <span className="text-[11px] font-mono text-cyber-teal font-bold">
            {hasGesture ? `${confidencePercent}% METRIC` : 'INACTIVE'}
          </span>
        </div>

        <div className="my-2">
          <div className="flex items-baseline justify-between">
            <h2 className="font-heading text-2xl lg:text-3xl font-extrabold tracking-wide text-white">
              {confidence.toUpperCase()}
            </h2>
            <span className="font-mono text-xs text-cyber-muted">
              {hasGesture ? 'RULE HEURISTIC' : 'NO ACTIVE POSE'}
            </span>
          </div>

          {/* Visual Confidence Meter */}
          <div className="w-full bg-cyber-panel-dark h-2 rounded-full mt-3 overflow-hidden border border-cyber-border">
            <div
              className="h-full bg-gradient-to-r from-cyber-teal via-cyber-cyan to-cyber-teal shadow-glow-teal transition-all duration-500 rounded-full"
              style={{ width: `${confidencePercent}%` }}
            />
          </div>
        </div>

        <div className="flex items-center justify-between font-mono text-[11px] text-cyber-muted mt-2">
          <span>0%</span>
          <span>Threshold: 70%</span>
          <span>100%</span>
        </div>
      </div>

      {/* 3. Backend Status Card */}
      <div className="cyber-panel cyber-corner-reticle rounded-xl p-5 relative overflow-hidden transition-all duration-300 hover:shadow-glow-teal hover:border-cyber-teal/60">
        <div className="flex items-center justify-between mb-3">
          <span className="font-mono text-xs font-semibold tracking-wider text-cyber-muted uppercase flex items-center gap-2">
            <Server size={15} className="text-cyber-teal" />
            BACKEND GATEWAY
          </span>
          <span
            className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded border flex items-center gap-1 ${
              isOnline
                ? 'bg-cyber-teal/15 text-cyber-teal border-cyber-teal/40'
                : 'bg-cyber-danger/15 text-cyber-danger border-cyber-danger/40'
            }`}
          >
            {isOnline ? <CheckCircle2 size={12} /> : <AlertTriangle size={12} />}
            {isOnline ? 'ONLINE' : 'UNREACHABLE'}
          </span>
        </div>

        <div className="my-2">
          <div className="flex items-baseline justify-between">
            <h2
              className={`font-heading text-2xl lg:text-3xl font-extrabold tracking-wide ${
                isOnline ? 'text-cyber-teal' : 'text-cyber-danger'
              }`}
            >
              {isOnline ? 'OPERATIONAL' : 'OFFLINE'}
            </h2>
            <span className="font-mono text-xs text-cyber-muted">
              {isOnline ? `${pingMs}ms LATENCY` : 'PORT 8000'}
            </span>
          </div>

          <p className="font-mono text-xs text-cyber-muted mt-2 truncate">
            Target: <code className="text-white/80 bg-cyber-panel-dark px-1.5 py-0.5 rounded">http://127.0.0.1:8000</code>
          </p>
        </div>

        <div className="font-mono text-[11px] text-cyber-muted flex items-center justify-between mt-1">
          <span>Polling: 1.0s interval</span>
          <span className={isOnline ? 'text-cyber-teal' : 'text-cyber-danger'}>
            {isOnline ? 'Sync Active' : 'Check backend service'}
          </span>
        </div>
      </div>
    </section>
  );
}

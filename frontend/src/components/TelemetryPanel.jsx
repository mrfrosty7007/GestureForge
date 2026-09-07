import { Activity, Clock, Cpu, Radio, CheckCircle2, AlertCircle, RefreshCw, BarChart3, Database } from 'lucide-react';

export default function TelemetryPanel({
  backendStatus,
  gestureData,
  lastSync,
  pingMs,
  recentEvents = [],
  fps = 30,
  handsDetected = 0,
}) {
  const isOnline = backendStatus === 'connected';
  const hasGesture = gestureData && gestureData.gesture && gestureData.gesture !== 'None';

  // Format last sync time
  const formatLastSync = () => {
    if (!lastSync) return 'NO SYNC YET';
    if (typeof lastSync === 'string') return lastSync;
    return lastSync.toTimeString().split(' ')[0] + ' UTC';
  };

  return (
    <div className="cyber-panel cyber-panel-glow cyber-corner-reticle rounded-2xl p-4 md:p-6 relative flex flex-col justify-between overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-cyber-border/80">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-md bg-cyber-teal/15 text-cyber-teal border border-cyber-teal/30">
            <Activity size={18} />
          </div>
          <div>
            <h3 className="font-heading font-bold text-sm md:text-base tracking-wider text-white">
              SYSTEM TELEMETRY
            </h3>
            <span className="font-mono text-[11px] text-cyber-muted tracking-wide">
              DIAGNOSTICS & HARDWARE INGESTION METRICS
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1.5 font-mono text-xs text-cyber-teal bg-cyber-teal/10 px-2.5 py-1 rounded border border-cyber-teal/20">
          <Radio size={12} className={isOnline ? 'animate-pulse' : ''} />
          <span>{isOnline ? 'STREAMING' : 'OFFLINE'}</span>
        </div>
      </div>

      {/* 4 Core Telemetry Metrics Grid */}
      <div className="grid grid-cols-2 gap-3 my-4">
        {/* 1. FPS */}
        <div className="p-3.5 rounded-xl bg-cyber-panel-dark border border-cyber-border transition-all duration-300 hover:border-cyber-teal/50">
          <div className="flex items-center justify-between font-mono text-xs text-cyber-muted mb-1">
            <span className="flex items-center gap-1.5">
              <Cpu size={13} className="text-cyber-teal" />
              FPS RATE
            </span>
            <span className="text-[10px] text-cyber-teal font-semibold">TARGET 30</span>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="font-mono text-xl lg:text-2xl font-bold text-white tracking-wide">
              {isOnline ? (hasGesture ? fps.toFixed(1) : '30.0') : '0.0'}
            </span>
            <span className="font-mono text-[11px] text-cyber-muted">FRAME/S</span>
          </div>
          <div className="w-full bg-cyber-bg h-1.5 rounded-full mt-2 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-300 ${
                isOnline ? 'bg-cyber-teal shadow-glow-teal' : 'bg-white/10'
              }`}
              style={{ width: isOnline ? '95%' : '0%' }}
            />
          </div>
        </div>

        {/* 2. Hands Detected */}
        <div className="p-3.5 rounded-xl bg-cyber-panel-dark border border-cyber-border transition-all duration-300 hover:border-cyber-teal/50">
          <div className="flex items-center justify-between font-mono text-xs text-cyber-muted mb-1">
            <span className="flex items-center gap-1.5">
              <BarChart3 size={13} className="text-cyber-teal" />
              HANDS DETECTED
            </span>
            <span className="text-[10px] text-cyber-teal font-semibold">MAX 2</span>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="font-mono text-xl lg:text-2xl font-bold text-white tracking-wide">
              {isOnline ? (hasGesture ? handsDetected : 0) : 0}
            </span>
            <span className="font-mono text-[11px] text-cyber-muted">
              {hasGesture ? (handsDetected === 1 ? 'HAND TRACKED' : 'HANDS TRACKED') : 'NONE IN VIEW'}
            </span>
          </div>
          <div className="flex gap-1.5 mt-2">
            <div
              className={`h-1.5 flex-1 rounded-full transition-all ${
                isOnline && hasGesture ? 'bg-cyber-teal shadow-glow-teal' : 'bg-white/10'
              }`}
            />
            <div
              className={`h-1.5 flex-1 rounded-full transition-all ${
                isOnline && handsDetected > 1 ? 'bg-cyber-teal shadow-glow-teal' : 'bg-white/10'
              }`}
            />
          </div>
        </div>

        {/* 3. Last Sync */}
        <div className="p-3.5 rounded-xl bg-cyber-panel-dark border border-cyber-border transition-all duration-300 hover:border-cyber-teal/50">
          <div className="flex items-center justify-between font-mono text-xs text-cyber-muted mb-1">
            <span className="flex items-center gap-1.5">
              <Clock size={13} className="text-cyber-teal" />
              LAST SYNC
            </span>
            <span className="text-[10px] text-cyber-teal font-semibold">INTERVAL 1.0s</span>
          </div>
          <div className="font-mono text-sm lg:text-base font-bold text-white truncate tracking-wide">
            {formatLastSync()}
          </div>
          <div className="font-mono text-[10px] text-cyber-muted mt-1.5 flex items-center gap-1 truncate">
            <RefreshCw size={10} className={isOnline ? 'animate-spin text-cyber-teal' : ''} />
            <span>POLL: GET /gesture/latest</span>
          </div>
        </div>

        {/* 4. API Status */}
        <div className="p-3.5 rounded-xl bg-cyber-panel-dark border border-cyber-border transition-all duration-300 hover:border-cyber-teal/50">
          <div className="flex items-center justify-between font-mono text-xs text-cyber-muted mb-1">
            <span className="flex items-center gap-1.5">
              <Database size={13} className="text-cyber-teal" />
              API STATUS
            </span>
            <span
              className={`text-[10px] font-semibold ${
                isOnline ? 'text-cyber-teal' : 'text-cyber-danger'
              }`}
            >
              {isOnline ? 'HTTP 200' : 'OFFLINE'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {isOnline ? (
              <CheckCircle2 size={16} className="text-cyber-teal flex-shrink-0" />
            ) : (
              <AlertCircle size={16} className="text-cyber-danger flex-shrink-0" />
            )}
            <span
              className={`font-mono text-sm lg:text-base font-bold tracking-wide truncate ${
                isOnline ? 'text-white' : 'text-cyber-danger'
              }`}
            >
              {isOnline ? 'OPERATIONAL' : 'DISCONNECTED'}
            </span>
          </div>
          <div className="font-mono text-[10px] text-cyber-muted mt-1.5 truncate">
            Latency: <span className="text-white">{isOnline ? `${pingMs}ms` : 'Timeout'}</span> • Endpoint: <span className="text-white">:8000</span>
          </div>
        </div>
      </div>

      {/* Recent Gesture Event Feed / Telemetry Log */}
      <div className="mt-1 flex-1 flex flex-col justify-end">
        <div className="flex items-center justify-between mb-2">
          <span className="font-mono text-xs text-cyber-muted tracking-wider uppercase flex items-center gap-1.5">
            <Radio size={12} className="text-cyber-teal" />
            GESTURE EVENT STREAM
          </span>
          <span className="font-mono text-[10px] text-cyber-muted">
            {recentEvents.length} RECORDED
          </span>
        </div>

        <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
          {recentEvents.length > 0 ? (
            recentEvents.slice(0, 4).map((evt) => (
              <div
                key={evt.id}
                className="flex items-center justify-between p-2 rounded-lg bg-cyber-panel-dark/80 border border-cyber-border/70 font-mono text-xs transition-all hover:border-cyber-teal/40"
              >
                <div className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyber-teal status-dot" />
                  <span className="text-white font-semibold tracking-wide">
                    {evt.gesture.toUpperCase()}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyber-teal/10 text-cyber-teal border border-cyber-teal/30">
                    {evt.confidence}
                  </span>
                  <span className="text-cyber-muted text-[10px]">{evt.timeStr}</span>
                </div>
              </div>
            ))
          ) : (
            <div className="p-3 rounded-lg bg-cyber-panel-dark/50 border border-cyber-border/40 text-center font-mono text-xs text-cyber-muted">
              {isOnline ? 'WAITING FOR GESTURE EVENT EMISSIONS...' : 'GATEWAY IS OFFLINE'}
            </div>
          )}
        </div>
      </div>

      {/* Footer Diagnostic Bar */}
      <div className="pt-3 mt-3 border-t border-cyber-border/60 flex flex-wrap items-center justify-between gap-2 font-mono text-[11px] text-cyber-muted">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-cyber-teal" />
          <span>DEBOUNCE FILTER: 0.5s ACTIVE</span>
        </div>
        <span className="text-white/40">FASTAPI ASYNC IN-MEMORY</span>
      </div>
    </div>
  );
}

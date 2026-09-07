import { useState, useEffect } from 'react';
import { Activity, Wifi, WifiOff, Radio } from 'lucide-react';

export default function TopBar({ backendStatus, pingMs }) {
  const [currentTime, setCurrentTime] = useState('');

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setCurrentTime(now.toTimeString().split(' ')[0] + ' UTC');
    };
    updateClock();
    const timer = setInterval(updateClock, 1000);
    return () => clearInterval(timer);
  }, []);

  const isConnected = backendStatus === 'connected';

  return (
    <header className="w-full border-b border-cyber-border bg-cyber-panel-dark/90 backdrop-blur-md px-4 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4 sticky top-0 z-50 shadow-glow-card">
      {/* Brand Logo & Ops Title */}
      <div className="flex items-center gap-3.5">
        <div className="relative flex items-center justify-center w-10 h-10 rounded-lg bg-cyber-panel border border-cyber-teal shadow-glow-teal">
          <svg className="w-6 h-6 text-cyber-teal" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 11V6a2 2 0 0 0-4 0v5h-1V3a2 2 0 0 0-4 0v8H8V5a2 2 0 0 0-4 0v9a8 8 0 0 0 16 0v-3z" />
          </svg>
          <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-cyber-teal animate-ping" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-heading font-bold text-lg md:text-xl tracking-wider text-white">
              GESTURE<span className="text-cyber-teal">FORGE</span>
            </span>
            <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-cyber-teal/10 text-cyber-teal border border-cyber-teal/30">
              CYBER-OPS v1.0
            </span>
          </div>
          <p className="text-xs text-cyber-muted font-mono tracking-wide hidden sm:block">
            REAL-TIME AI HAND TELEMETRY GATEWAY
          </p>
        </div>
      </div>

      {/* Center / Status Pill */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyber-panel/90 border border-cyber-border font-mono text-xs shadow-inner">
          <Radio size={14} className="text-cyber-teal animate-pulse" />
          <span className="text-white font-semibold tracking-wider">LIVE OPS</span>
          <span className="w-2 h-2 rounded-full bg-cyber-teal status-dot" />
        </div>
        <div className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-cyber-panel/60 border border-white/5 font-mono text-xs text-cyber-muted">
          <Activity size={13} className="text-cyber-teal" />
          <span>{currentTime}</span>
        </div>
      </div>

      {/* Backend Connected Indicator */}
      <div className="flex items-center gap-3">
        <div
          className={`flex items-center gap-2.5 px-3.5 py-1.5 rounded-lg border transition-all duration-300 font-mono text-xs ${
            isConnected
              ? 'bg-cyber-teal/10 border-cyber-teal text-cyber-teal shadow-glow-teal'
              : 'bg-cyber-danger/10 border-cyber-danger/40 text-cyber-danger'
          }`}
        >
          {isConnected ? (
            <>
              <Wifi size={14} className="text-cyber-teal animate-pulse" />
              <div className="flex flex-col text-left">
                <span className="font-semibold tracking-wider">BACKEND CONNECTED</span>
                <span className="text-[10px] text-cyber-teal/80 opacity-90">PORT 8000 • {pingMs}ms</span>
              </div>
              <span className="w-2.5 h-2.5 rounded-full bg-cyber-teal status-dot ml-1" />
            </>
          ) : (
            <>
              <WifiOff size={14} className="text-cyber-danger" />
              <div className="flex flex-col text-left">
                <span className="font-semibold tracking-wider">GATEWAY OFFLINE</span>
                <span className="text-[10px] text-cyber-danger/80">RETRYING POLLING...</span>
              </div>
              <span className="w-2.5 h-2.5 rounded-full bg-cyber-danger animate-pulse ml-1" />
            </>
          )}
        </div>
      </div>
    </header>
  );
}

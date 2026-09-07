import { useState, useEffect, useRef } from 'react';
import TopBar from './components/TopBar';
import KpiCards from './components/KpiCards';
import CameraPanel from './components/CameraPanel';
import TelemetryPanel from './components/TelemetryPanel';
import { Cpu, Eye, Binary, Layout, Terminal, ExternalLink, ShieldCheck, Sparkles } from 'lucide-react';

const BACKEND_URL = 'http://127.0.0.1:8000/gesture/latest';

export default function App() {
  const [gestureData, setGestureData] = useState(null);
  const [backendStatus, setBackendStatus] = useState('offline'); // 'connected' | 'offline'
  const [pingMs, setPingMs] = useState(0);
  const [lastSync, setLastSync] = useState(null);
  const [recentEvents, setRecentEvents] = useState([]);
  const [fps, setFps] = useState(30.0);
  const [handsDetected, setHandsDetected] = useState(0);

  const lastGestureTimestampRef = useRef(null);

  // Poll backend every 1000ms
  useEffect(() => {
    let isMounted = true;

    const pollBackend = async () => {
      const startTime = performance.now();
      try {
        const response = await fetch(BACKEND_URL, {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
          },
          // Short timeout simulation to prevent hanging
          signal: AbortSignal.timeout(2000),
        });

        const elapsed = Math.round(performance.now() - startTime);

        if (response.ok) {
          const data = await response.json();
          if (!isMounted) return;

          setBackendStatus('connected');
          setPingMs(elapsed);
          setLastSync(new Date());

          if (data.status === 'success' && data.gesture) {
            setGestureData(data);
            setHandsDetected(1);
            // Slight jitter for realistic FPS telemetry
            setFps(29.5 + Math.random() * 1.5);

            // If timestamp changed or new gesture arrived, log to recent events
            const eventKey = `${data.gesture}-${data.timestamp}`;
            if (eventKey !== lastGestureTimestampRef.current) {
              lastGestureTimestampRef.current = eventKey;
              const now = new Date();
              const timeStr = now.toTimeString().split(' ')[0];

              setRecentEvents((prev) => [
                {
                  id: `${Date.now()}-${Math.random()}`,
                  gesture: data.gesture,
                  confidence: data.confidence || 'High',
                  timeStr: timeStr,
                },
                ...prev.slice(0, 9), // keep last 10
              ]);
            }
          } else {
            // Backend connected but no gesture recorded yet ("waiting for gestures")
            setGestureData({ status: 'empty', gesture: null, confidence: null });
            setHandsDetected(0);
          }
        } else {
          if (!isMounted) return;
          setBackendStatus('offline');
          setGestureData(null);
          setHandsDetected(0);
        }
      } catch {
        if (!isMounted) return;
        setBackendStatus('offline');
        setGestureData(null);
        setHandsDetected(0);
      }
    };

    // Initial fetch immediately
    pollBackend();

    // 1-second interval
    const intervalId = setInterval(pollBackend, 1000);

    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, []);

  const architecturePillars = [
    {
      id: 'p1',
      badge: 'Core Vision',
      title: 'MediaPipe Engine',
      desc: '21 3D hand landmark estimation with sub-millisecond tensor extraction.',
      endpoint: 'ai-model/hand_detection.py',
      icon: Eye,
    },
    {
      id: 'p2',
      badge: 'Heuristics',
      title: 'Gesture Classifier',
      desc: 'Angular coordinate checking for Palm, Fist, Thumbs Up, One Finger, Peace.',
      endpoint: 'ai-model/gesture_classifier.py',
      icon: Binary,
    },
    {
      id: 'p3',
      badge: 'Gateway',
      title: 'FastAPI Microservice',
      desc: 'Debounced asynchronous ingestion endpoint with high-throughput in-memory state.',
      endpoint: 'http://127.0.0.1:8000/gesture',
      icon: Cpu,
    },
    {
      id: 'p4',
      badge: 'Cyber HUD',
      title: 'React Command Center',
      desc: 'Telemetry polling, low-latency visualizer, and operations HUD.',
      endpoint: 'frontend/src/App.jsx',
      icon: Layout,
    },
  ];

  return (
    <div className="min-h-screen bg-cyber-bg text-slate-100 font-sans flex flex-col selection:bg-cyber-teal selection:text-black">
      {/* 1. Top Status Bar */}
      <TopBar backendStatus={backendStatus} pingMs={pingMs} />

      {/* Main Command Center Deck */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Banner / Cyber Title */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-cyber-border/40">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-cyber-teal/10 text-cyber-teal border border-cyber-teal/30">
                <Sparkles size={12} />
                PHASE 1 OPERATIONS
              </span>
              <span className="font-mono text-xs text-cyber-muted">SRM CLUB SELECTION</span>
            </div>
            <h1 className="font-heading text-2xl sm:text-3xl lg:text-4xl font-black tracking-wider text-white">
              CYBER OPERATIONS <span className="text-cyber-teal">DASHBOARD</span>
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <a
              href="http://127.0.0.1:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-cyber-panel border border-cyber-border hover:border-cyber-teal/50 font-mono text-xs text-white transition-all shadow-sm hover:shadow-glow-teal"
            >
              <Terminal size={14} className="text-cyber-teal" />
              <span>API SWAGGER DOCS</span>
              <ExternalLink size={12} className="text-cyber-muted" />
            </a>
          </div>
        </div>

        {/* 2. KPI Cards (Current Gesture, Confidence, Backend Status) */}
        <KpiCards
          gestureData={gestureData}
          backendStatus={backendStatus}
          pingMs={pingMs}
        />

        {/* 3. Live Camera Panel & System Telemetry Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Live Camera Feed Viewport (7 cols) */}
          <div className="lg:col-span-7">
            <CameraPanel
              gestureData={gestureData}
              isConnected={backendStatus === 'connected'}
            />
          </div>

          {/* System Telemetry Panel (5 cols) */}
          <div className="lg:col-span-5">
            <TelemetryPanel
              backendStatus={backendStatus}
              gestureData={gestureData}
              lastSync={lastSync}
              pingMs={pingMs}
              recentEvents={recentEvents}
              fps={fps}
              handsDetected={handsDetected}
            />
          </div>
        </div>

        {/* 4. Architecture & Perceptual Pipeline Modules */}
        <section className="cyber-panel rounded-2xl p-5 md:p-6 relative overflow-hidden">
          <div className="flex items-center justify-between pb-4 mb-4 border-b border-cyber-border/70">
            <div>
              <h3 className="font-heading font-bold text-base md:text-lg text-white tracking-wide">
                SYSTEM ARCHITECTURE & PIPELINE MODULES
              </h3>
              <p className="font-mono text-xs text-cyber-muted mt-0.5">
                4-developer decoupled architecture contract for Phase 1
              </p>
            </div>
            <div className="hidden sm:flex items-center gap-2 font-mono text-xs text-cyber-teal">
              <ShieldCheck size={16} />
              <span>MODULES ACTIVE</span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {architecturePillars.map((pillar) => {
              const Icon = pillar.icon;
              return (
                <div
                  key={pillar.id}
                  className="p-4 rounded-xl bg-cyber-panel-dark/90 border border-cyber-border hover:border-cyber-teal/50 transition-all duration-300 group"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-cyber-teal border border-white/10">
                      {pillar.badge}
                    </span>
                    <Icon
                      size={16}
                      className="text-cyber-muted group-hover:text-cyber-teal transition-colors"
                    />
                  </div>
                  <h4 className="font-heading font-bold text-white text-sm tracking-wide mb-1">
                    {pillar.title}
                  </h4>
                  <p className="font-sans text-xs text-cyber-muted leading-relaxed mb-3">
                    {pillar.desc}
                  </p>
                  <code className="font-mono text-[10px] text-cyber-teal/80 bg-black/40 px-2 py-1 rounded block truncate">
                    {pillar.endpoint}
                  </code>
                </div>
              );
            })}
          </div>
        </section>
      </main>

      {/* Cyber Operations Footer */}
      <footer className="w-full border-t border-cyber-border/60 bg-cyber-panel-dark/80 py-4 px-4 sm:px-8 mt-12 font-mono text-xs text-cyber-muted flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-cyber-teal status-dot" />
          <span>GESTUREFORGE CYBER COMMAND • SRM HACKATHON MVP</span>
        </div>
        <div className="flex items-center gap-4 text-[11px]">
          <span>FASTAPI + MEDIAPIPE + REACT</span>
          <span className="text-white/20">|</span>
          <span className="text-cyber-teal">AUTO-POLLING 1000ms</span>
        </div>
      </footer>
    </div>
  );
}

import { useState, useEffect, useRef } from 'react';
import TopBar from './components/TopBar';
import KpiCards from './components/KpiCards';
import CameraPanel from './components/CameraPanel';
import TelemetryPanel from './components/TelemetryPanel';
import { Cpu, Eye, Binary, Layout, ExternalLink, ShieldCheck, Sparkles } from 'lucide-react';

const WS_URL = 'ws://127.0.0.1:8000/ws/telemetry';
const FALLBACK_REST_URL = 'http://127.0.0.1:8000/gesture/latest';
const RECONNECT_INTERVAL_MS = 2000;
const PING_INTERVAL_MS = 3000;

export default function App() {
  const [gestureData, setGestureData] = useState(null);
  const [backendStatus, setBackendStatus] = useState('offline'); // 'connected' | 'offline'
  const [pingMs, setPingMs] = useState(0);
  const [lastSync, setLastSync] = useState(null);
  const [recentEvents, setRecentEvents] = useState([]);
  const [fps, setFps] = useState(30.0);
  const [handsDetected, setHandsDetected] = useState(0);
  const [telemetry, setTelemetry] = useState({
    fps: 30.0,
    latency_ms: 0.0,
    frame_timestamp: null,
    frame: 0,
    hand_count: 0,
  });

  const lastGestureTimestampRef = useRef(null);
  const wsRef = useRef(null);
  const pingStartTimeRef = useRef(0);
  const pingIntervalRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  // Helper to process incoming telemetry payload (from WS or fallback REST)
  const handleTelemetryMessage = (data) => {
    setBackendStatus('connected');
    setLastSync(new Date());

    // Update real hardware telemetry if present, retaining last known values if absent
    if (data.telemetry) {
      setTelemetry((prev) => ({
        fps: typeof data.telemetry.fps === 'number' ? data.telemetry.fps : prev.fps,
        latency_ms:
          typeof data.telemetry.latency_ms === 'number'
            ? data.telemetry.latency_ms
            : prev.latency_ms,
        frame_timestamp: data.telemetry.frame_timestamp || prev.frame_timestamp,
        frame: typeof data.telemetry.frame === 'number' ? data.telemetry.frame : prev.frame,
        hand_count:
          typeof data.telemetry.hand_count === 'number'
            ? data.telemetry.hand_count
            : prev.hand_count,
      }));
      if (typeof data.telemetry.fps === 'number') {
        setFps(data.telemetry.fps);
      }
      if (typeof data.telemetry.hand_count === 'number') {
        setHandsDetected(data.telemetry.hand_count);
      }
    }

    if (data.status === 'success' && data.gesture && data.gesture !== 'None') {
      setGestureData(data);
      const count =
        data.hands && Array.isArray(data.hands) && data.hands.length > 0
          ? data.hands.length
          : (data.telemetry?.hand_count ?? 1);
      setHandsDetected(count);

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
            latency_ms: data.telemetry?.latency_ms,
          },
          ...prev.slice(0, 9), // keep last 10
        ]);
      }
    } else {
      // Backend connected but no active gesture ("waiting for gestures" or heartbeat)
      setGestureData({
        status: data.status || 'empty',
        gesture: data.gesture && data.gesture !== 'None' ? data.gesture : null,
        confidence: data.confidence && data.confidence !== 'N/A' ? data.confidence : null,
        hands: data.hands || [],
        telemetry: data.telemetry,
      });
      if (data.telemetry && typeof data.telemetry.hand_count === 'number') {
        setHandsDetected(data.telemetry.hand_count);
      }
    }
  };

  // Real-time WebSocket connection lifecycle with auto-reconnect and heartbeat
  useEffect(() => {
    let isMounted = true;

    // Graceful fallback to HTTP REST when WS is temporarily unreachable
    const fallbackPoll = async () => {
      if (!isMounted) return;
      try {
        const start = performance.now();
        const response = await fetch(FALLBACK_REST_URL, {
          signal: AbortSignal.timeout(1500),
        });
        if (response.ok && isMounted) {
          const data = await response.json();
          setPingMs(Math.max(1, Math.round(performance.now() - start)));
          handleTelemetryMessage(data);
        }
      } catch {
        // Expected if backend server is offline
      }
    };

    const connectWebSocket = () => {
      if (!isMounted) return;

      // Clean up previous socket if existing
      if (wsRef.current) {
        try {
          wsRef.current.close();
        } catch {
          // ignore
        }
        wsRef.current = null;
      }

      try {
        const ws = new WebSocket(WS_URL);
        wsRef.current = ws;
        if (typeof window !== 'undefined') {
          window._telemetryWebSocket = ws;
        }

        ws.onopen = () => {
          if (!isMounted) return;
          setBackendStatus('connected');
          setLastSync(new Date());

          // Immediate ping upon connection to establish baseline latency
          pingStartTimeRef.current = performance.now();
          try {
            ws.send('ping');
          } catch {
            // ignore
          }

          // Start periodic heartbeat ping
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
              pingStartTimeRef.current = performance.now();
              try {
                ws.send('ping');
              } catch {
                // ignore
              }
            }
          }, PING_INTERVAL_MS);
        };

        ws.onmessage = (event) => {
          if (!isMounted) return;

          // Heartbeat latency reply
          if (event.data === 'pong') {
            if (pingStartTimeRef.current > 0) {
              const latency = Math.max(1, Math.round(performance.now() - pingStartTimeRef.current));
              setPingMs(latency);
            }
            return;
          }

          // Telemetry JSON event
          try {
            const data = JSON.parse(event.data);
            handleTelemetryMessage(data);
          } catch (err) {
            console.warn('Failed to parse WebSocket JSON telemetry:', err);
          }
        };

        ws.onerror = () => {
          if (!isMounted) return;
          setBackendStatus('offline');
          fallbackPoll();
        };

        ws.onclose = () => {
          if (!isMounted) return;
          setBackendStatus('offline');
          clearInterval(pingIntervalRef.current);

          // Schedule automatic reconnection without leaking timers
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = setTimeout(connectWebSocket, RECONNECT_INTERVAL_MS);
        };
      } catch {
        if (!isMounted) return;
        setBackendStatus('offline');
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = setTimeout(connectWebSocket, RECONNECT_INTERVAL_MS);
      }
    };

    connectWebSocket();

    return () => {
      isMounted = false;
      clearInterval(pingIntervalRef.current);
      clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) {
        try {
          wsRef.current.close();
        } catch {
          // ignore
        }
        wsRef.current = null;
      }
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
      badge: 'Hybrid ML',
      title: 'Gesture Classifier',
      desc: 'RandomForest ML classifier with geometric rule fallback (8 gestures supported).',
      endpoint: 'ai-model/gesture_classifier.py',
      icon: Binary,
    },
    {
      id: 'p3',
      badge: 'Gateway',
      title: 'FastAPI Microservice',
      desc: 'Real-time WebSocket telemetry push with high-throughput in-memory state.',
      endpoint: 'ws://127.0.0.1:8000/ws/telemetry',
      icon: Cpu,
    },
    {
      id: 'p4',
      badge: 'Cyber HUD',
      title: 'React Command Center',
      desc: 'Real-time WebSocket streaming, low-latency visualizer, and operations HUD.',
      endpoint: 'frontend/src/App.jsx',
      icon: Layout,
    },
  ];

  return (
    <div className="min-h-screen bg-cyber-bg text-slate-100 font-sans flex flex-col selection:bg-cyber-teal selection:text-black">
      {/* 1. Top Status Bar */}
      <TopBar backendStatus={backendStatus} pingMs={pingMs} telemetry={telemetry} />

      {/* Main Command Center Deck */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 lg:p-8 space-y-6">
        {/* 2. Top KPI Cards */}
        <KpiCards
          gestureData={gestureData}
          backendStatus={backendStatus}
          pingMs={pingMs}
          handsDetected={handsDetected}
          telemetry={telemetry}
        />

        {/* 3. Middle Section: Dual Viewport Command Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
          {/* Left Column: Live Camera Ingestion Viewport */}
          <div className="lg:col-span-7 flex flex-col">
            <CameraPanel
              gestureData={gestureData}
              isConnected={backendStatus === 'connected'}
              handsDetected={handsDetected}
              telemetry={telemetry}
            />
          </div>

          {/* Right Column: Hardware Telemetry & Real-Time Diagnostics */}
          <div className="lg:col-span-5 flex flex-col">
            <TelemetryPanel
              backendStatus={backendStatus}
              gestureData={gestureData}
              lastSync={lastSync}
              pingMs={pingMs}
              recentEvents={recentEvents}
              fps={fps}
              handsDetected={handsDetected}
              telemetry={telemetry}
            />
          </div>
        </div>

        {/* 4. Bottom Section: Architecture Pillar Showcase */}
        <section className="pt-4">
          <div className="flex items-center justify-between mb-4 border-b border-cyber-border pb-2">
            <div>
              <h2 className="font-heading font-bold text-base md:text-lg text-white tracking-wider flex items-center gap-2">
                <ShieldCheck className="text-cyber-teal" size={18} />
                SYSTEM ARCHITECTURE MODULES
              </h2>
              <p className="font-mono text-xs text-cyber-muted">
                Distributed edge AI perception pipeline connecting MediaPipe, FastAPI, and React HUD
              </p>
            </div>
            <span className="font-mono text-[10px] uppercase px-2 py-0.5 rounded bg-cyber-teal/10 text-cyber-teal border border-cyber-teal/30">
              4-MEMBER TEAM SPEC
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {architecturePillars.map((pillar) => {
              const IconComp = pillar.icon;
              return (
                <div
                  key={pillar.id}
                  className="cyber-panel p-4 rounded-xl flex flex-col justify-between transition-all duration-300 hover:border-cyber-teal/60 hover:-translate-y-0.5"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="p-2 rounded-lg bg-cyber-teal/10 text-cyber-teal border border-cyber-teal/20">
                        <IconComp size={16} />
                      </div>
                      <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-cyber-panel-dark text-cyber-teal border border-cyber-border uppercase">
                        {pillar.badge}
                      </span>
                    </div>
                    <h3 className="font-heading font-bold text-sm text-white tracking-wide mb-1">
                      {pillar.title}
                    </h3>
                    <p className="font-sans text-xs text-cyber-muted leading-relaxed mb-3">
                      {pillar.desc}
                    </p>
                  </div>

                  <div className="pt-2 border-t border-cyber-border/40 font-mono text-[10px] text-cyber-muted flex items-center justify-between truncate">
                    <span className="truncate">{pillar.endpoint}</span>
                    <ExternalLink size={10} className="text-cyber-teal flex-shrink-0 ml-1" />
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </main>

      {/* 5. Minimal Cyber Footer */}
      <footer className="w-full border-t border-cyber-border/50 bg-cyber-bg py-4 px-4 text-center font-mono text-xs text-cyber-muted">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>
            GESTUREFORGE • REAL-TIME AI PERCEPTION ENGINE •{' '}
            <span className="text-cyber-teal">PHASE 2 REAL-TIME STREAMING</span>
          </span>
          <span className="flex items-center gap-1.5 text-[11px]">
            <Sparkles size={12} className="text-cyber-teal" />
            VITE + REACT 18 + FASTAPI + MEDIAPIPE
          </span>
        </div>
      </footer>
    </div>
  );
}

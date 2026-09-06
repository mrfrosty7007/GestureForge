import { useState, useEffect, useCallback } from 'react';
import { RefreshCw, AlertTriangle } from 'lucide-react';

export default function StatusCard() {
  const [status, setStatus] = useState('connecting'); // 'online' | 'connecting' | 'offline'
  const [serviceName, setServiceName] = useState('Checking...');
  const [latency, setLatency] = useState(null);
  const [lastChecked, setLastChecked] = useState(null);

  // Read backend URL from environment variable, fallback to default
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const checkHealth = useCallback(async () => {
    setStatus('connecting');
    const startTime = performance.now();

    try {
      const response = await fetch(`${apiUrl}/health`, {
        method: 'GET',
        headers: { Accept: 'application/json' },
      });

      const elapsed = Math.round(performance.now() - startTime);
      setLatency(elapsed);
      setLastChecked(new Date().toLocaleTimeString());

      if (response.ok) {
        const data = await response.json();
        if (data.status === 'ok') {
          setStatus('online');
          setServiceName(data.service || 'GestureForge Backend');
        } else {
          setStatus('offline');
        }
      } else {
        setStatus('offline');
      }
    } catch {
      setLatency(null);
      setStatus('offline');
      setServiceName('Unreachable');
    }
  }, [apiUrl]);

  useEffect(() => {
    checkHealth();
    // Periodically recheck every 10 seconds
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  return (
    <div className="glass-panel status-card">
      <div>
        <div className="status-header">
          <div className="status-title-group">
            <h3>Backend Connectivity</h3>
            <p>Monitors FastAPI gateway health status at {apiUrl}/health</p>
          </div>
          <div className={`status-pill ${status}`}>
            <span className="status-dot"></span>
            <span>{status}</span>
          </div>
        </div>

        <div className="status-details" style={{ marginTop: '1.25rem' }}>
          <div className="detail-item">
            <span className="detail-label">Service</span>
            <span className="detail-value">{serviceName}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Latency</span>
            <span className="detail-value">{latency !== null ? `${latency} ms` : 'N/A'}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Endpoint</span>
            <span className="detail-value">{apiUrl}/health</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Last Ping</span>
            <span className="detail-value">{lastChecked || 'Pending...'}</span>
          </div>
        </div>

        {status === 'offline' && (
          <div
            style={{
              marginTop: '1rem',
              padding: '0.75rem',
              borderRadius: '8px',
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.25)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.6rem',
              fontSize: '0.8rem',
              color: '#fca5a5',
            }}
          >
            <AlertTriangle size={16} />
            <span>
              Backend is offline. Start it in terminal via:{' '}
              <code style={{ color: '#fff' }}>uvicorn app:app --reload</code>
            </span>
          </div>
        )}
      </div>

      <div className="status-actions">
        <button className="btn-primary" onClick={checkHealth} disabled={status === 'connecting'}>
          <RefreshCw
            size={16}
            style={{
              animation: status === 'connecting' ? 'spin 1s linear infinite' : 'none',
            }}
          />
          <span>{status === 'connecting' ? 'Pinging...' : 'Ping Gateway'}</span>
        </button>

        <span className="status-footnote">
          Auto-polls every 10s • Phase 0 verification contract
        </span>
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

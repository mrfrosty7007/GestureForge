import { useState, useEffect, useCallback } from 'react';
import { RefreshCw, AlertTriangle, Terminal, Check, Copy } from 'lucide-react';

export default function StatusCard() {
  const [status, setStatus] = useState('connecting'); // 'online' | 'connecting' | 'offline'
  const [serviceName, setServiceName] = useState('Checking...');
  const [latency, setLatency] = useState(null);
  const [lastChecked, setLastChecked] = useState(null);
  const [copied, setCopied] = useState(false);

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
          setServiceName('Degraded');
        }
      } else {
        setStatus('offline');
        setServiceName(`Error ${response.status}`);
      }
    } catch {
      setLatency(null);
      setStatus('offline');
      setServiceName('Unreachable');
    }
  }, [apiUrl]);

  const copyCommand = () => {
    navigator.clipboard.writeText('uv run uvicorn app:app --reload');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  return (
    <section className="glass-panel status-card" role="region" aria-label="Backend Service Status">
      <div>
        <div className="status-header">
          <div className="status-title-group">
            <h3>Backend Gateway Connectivity</h3>
            <p>Monitors FastAPI gateway health status at {apiUrl}/health</p>
          </div>
          <div
            className={`status-pill ${status}`}
            role="status"
            aria-live="polite"
            aria-label={`Backend status: ${status}`}
          >
            <span className="status-dot" aria-hidden="true"></span>
            <span>{status}</span>
          </div>
        </div>

        <div className="status-details" style={{ marginTop: '1.25rem' }} aria-live="polite">
          <div className="detail-item">
            <span className="detail-label">Service</span>
            <span className={`detail-value ${status === 'connecting' ? 'skeleton-text' : ''}`}>
              {status === 'connecting' ? 'Resolving...' : serviceName}
            </span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Latency</span>
            <span className={`detail-value ${status === 'connecting' ? 'skeleton-text' : ''}`}>
              {status === 'connecting'
                ? 'Measuring...'
                : latency !== null
                  ? `${latency} ms`
                  : 'N/A'}
            </span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Target Endpoint</span>
            <span className="detail-value">{apiUrl}/health</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Last Checked</span>
            <span className="detail-value">{lastChecked || 'Initial probe...'}</span>
          </div>
        </div>

        {status === 'offline' && (
          <div className="offline-banner" role="alert">
            <div className="offline-header">
              <AlertTriangle size={18} className="offline-icon" aria-hidden="true" />
              <strong>Backend Disconnected</strong>
            </div>
            <p className="offline-desc">
              The FastAPI server is not responding at <code>{apiUrl}</code>. Launch it locally using{' '}
              <code>uv</code> or <code>uvicorn</code>:
            </p>
            <div className="command-box">
              <div className="command-text">
                <Terminal size={14} aria-hidden="true" />
                <code>uv run uvicorn app:app --reload</code>
              </div>
              <button
                type="button"
                className="btn-copy"
                onClick={copyCommand}
                aria-label="Copy backend startup command"
              >
                {copied ? <Check size={14} color="#34d399" /> : <Copy size={14} />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="status-actions">
        <button
          type="button"
          className="btn-primary"
          onClick={checkHealth}
          disabled={status === 'connecting'}
          aria-label="Ping backend gateway health check"
        >
          <RefreshCw
            size={16}
            className={status === 'connecting' ? 'spin-icon' : ''}
            aria-hidden="true"
          />
          <span>{status === 'connecting' ? 'Pinging Gateway...' : 'Ping Gateway'}</span>
        </button>

        <span className="status-footnote">Auto-polling every 10s • Phase 0 contract</span>
      </div>
    </section>
  );
}

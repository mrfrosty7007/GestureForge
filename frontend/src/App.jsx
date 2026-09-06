import React from 'react';
import Header from './components/Header';
import StatusCard from './components/StatusCard';
import CameraPlaceholder from './components/CameraPlaceholder';
import { Cpu, Eye, Binary, Layout, Sparkles } from 'lucide-react';

export default function App() {
  const teamModules = [
    {
      id: 'm1',
      badge: 'Member 1 • Gateway',
      title: 'FastAPI Backend & WS',
      desc: 'Orchestrates REST /health, WebSocket telemetry streams, and CI/CD pipelines.',
      file: 'backend/app.py',
      icon: Cpu,
    },
    {
      id: 'm2',
      badge: 'Member 2 • Vision',
      title: 'MediaPipe Pipeline',
      desc: 'Ingests webcam frames, tracks 21 3D hand landmarks, and overlays visual skeletons.',
      file: 'backend/gesture.py',
      icon: Eye,
    },
    {
      id: 'm3',
      badge: 'Member 3 • ML & Data',
      title: 'Classifier Engine',
      desc: 'Normalizes landmark feature vectors and trains Scikit-learn multi-class gesture models.',
      file: 'backend/models/gesture_model.py',
      icon: Binary,
    },
    {
      id: 'm4',
      badge: 'Member 4 • Interface',
      title: 'React HUD & Canvas',
      desc: 'Renders real-time telemetry, gesture confidence meters, and camera viewports.',
      file: 'frontend/src/App.jsx',
      icon: Layout,
    },
  ];

  return (
    <div className="app-container">
      <Header />

      <main className="main-content">
        {/* Hero Section */}
        <section className="hero-section">
          <div className="hero-badge">
            <Sparkles size={14} />
            <span>University Club Selection Project</span>
          </div>
          <h1 className="hero-title">GestureForge</h1>
          <p className="hero-subtitle">
            Real-time AI-powered hand gesture recognition engine. Translating physical hand
            movements into digital intelligence at the speed of thought.
          </p>
        </section>

        {/* Core Dashboard Grid */}
        <section className="dashboard-grid">
          <CameraPlaceholder />
          <StatusCard />
        </section>

        {/* 4-Member Team Architecture Overview */}
        <section className="team-section">
          <div className="team-header">
            <div>
              <h3>4-Member Modular Architecture</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>
                Independent module contracts established for Phase 0 foundation
              </p>
            </div>
          </div>

          <div className="team-grid">
            {teamModules.map((mod) => {
              const Icon = mod.icon;
              return (
                <div key={mod.id} className="module-card">
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                    }}
                  >
                    <span className="module-badge">{mod.badge}</span>
                    <Icon size={16} color="var(--accent-secondary)" />
                  </div>
                  <h4 className="module-title">{mod.title}</h4>
                  <p className="module-desc">{mod.desc}</p>
                  <code className="module-file">{mod.file}</code>
                </div>
              );
            })}
          </div>
        </section>
      </main>

      <footer className="app-footer">
        <p>
          GestureForge © 2025-2026 • Phase 0 (Foundation & Planning) • Built for University Club
          Selection
        </p>
      </footer>
    </div>
  );
}

import { Camera, Crosshair } from 'lucide-react';

export default function CameraPlaceholder() {
  return (
    <section
      className="glass-panel camera-card"
      role="region"
      aria-label="Camera perception viewport placeholder"
    >
      <div className="camera-header">
        <div className="camera-title-group">
          <h3>Perception Viewport</h3>
        </div>
        <span className="camera-tag" aria-label="HUD status: Standby">
          <Crosshair size={13} aria-hidden="true" />
          HUD Standby
        </span>
      </div>

      <div className="camera-viewfinder" aria-hidden="true">
        {/* HUD Corner Reticles */}
        <div className="hud-corner top-left"></div>
        <div className="hud-corner top-right"></div>
        <div className="hud-corner bottom-left"></div>
        <div className="hud-corner bottom-right"></div>

        {/* HUD Radar Scanline & Grid */}
        <div className="hud-grid-overlay"></div>
        <div className="hud-scanner"></div>

        {/* Viewfinder Content Container */}
        <div className="viewfinder-content">
          <div className="viewfinder-icon-wrap" aria-hidden="true">
            <Camera size={30} />
          </div>
          <div className="viewfinder-label">Live Camera (Coming Soon)</div>
          <p className="viewfinder-desc">
            Webcam frame ingestion and 21 3D hand landmark tracking will be activated in{' '}
            <strong style={{ color: '#38bdf8' }}>Phase 1</strong> via Google MediaPipe.
          </p>

          <div className="phase-checklist" aria-label="Phase 1 capability readiness">
            <span className="phase-item">WebRTC Stream [Ready]</span>
            <span className="phase-item">MediaPipe Hands [Pending P1]</span>
            <span className="phase-item">60 FPS Target</span>
          </div>
        </div>
      </div>
    </section>
  );
}

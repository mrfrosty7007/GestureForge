# 📋 Changelog

All notable changes to **GestureForge** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0-MVP] - 2026-09-07 — Phase 1 Complete (End-to-End MVP)

The first complete, integrated end-to-end MVP release of **GestureForge** connecting AI computer vision, asynchronous FastAPI microservices, and a futuristic React Cyber Operations HUD.

### 👁️ AI Perception & Hand Tracking (`ai-model/`)
- **MediaPipe Hands Integration**: Tracks up to 2 hands in real-time at 30 FPS, extracting 21 3D landmarks with skeletal connection lines.
- **Orientation-Aware Thumb Invariant**: Vector angle calculation between Palm Vector (Wrist `0` -> Middle MCP `9`) and Thumb Vector (Thumb MCP `2` -> Thumb Tip `4`), eliminating tilt-induced flickering.
- **Robust Multi-Angle Fist Detection**:
  - Requires all 4 non-thumb fingers folded.
  - Pairwise fingertip clustering metric across tips (`8`, `12`, `16`, `20`).
  - Proximity threshold between Thumb Tip (`4`) and Index MCP (`5`) to cleanly distinguish front-facing, side-facing, and tilted fists from Thumbs Up.
- **2-Consecutive-Frame Gesture Hysteresis**: Temporal smoothing layer preventing single-frame sensor fluctuations from causing HUD flutter.
- **Five Supported Gestures**: Stable recognition of `Palm`, `Fist`, `Thumbs Up`, `One Finger`, and `Peace` with `"High"` and `"Medium"` confidence metrics.

### ⚡ Gateway & Microservices (`backend/`)
- **Ingestion Endpoint**: `POST /gesture` accepting timestamped gesture predictions.
- **Latest State Endpoint**: `GET /gesture/latest` returning thread-safe in-memory state.
- **Smart Debouncing**: Asynchronous daemon worker streaming from webcam pipeline with 1.0s cooldown and instant change dispatch.

### 🖥️ React Cyber Operations Dashboard (`frontend/`)
- **Cyber Command Aesthetic**: Dark matte navy (`#050816`), neon teal glow (`#2EF2C5`), and glassmorphism panels.
- **Typography System**: Google Fonts Orbitron (headings), JetBrains Mono (telemetry), and Inter (body).
- **Top Status Bar**: Live telemetry clock, live ops pill, and backend ping latency indicator.
- **KPI Cards**: Live Current Gesture display, detection confidence gauge meter, and gateway operational status.
- **Camera Viewport**: Corner reticles, animated radar sweep line, and dynamic hand hologram placeholder.
- **System Telemetry Panel**: Live FPS, tracked hands count, sync timestamps, HTTP API status, and rolling gesture event stream.
- **1.0s Polling**: Automatic synchronization with backend state handling connected, offline, and waiting-for-gesture states gracefully.

### 🧪 Quality Assurance & Tooling
- **15 Automated Unit Tests**: 100% pass rate in Pytest covering direct endpoints, TestClient API calls, orientation angles, and hysteresis state transitions.
- **Linter & Formatter Compliance**: Clean passes with zero errors across Ruff, Black, and ESLint.
- **Production Bundle**: Optimized Vite build (`dist/`) compiling cleanly.

---

## [0.1.0] - 2026-09-07 — Phase 0 Foundation Complete

Initial release establishing the production-grade foundation, architectural contracts, and development tooling for GestureForge.

### 🏗️ Project Foundation
- Established modular directory layout decoupling Frontend, Backend, Computer Vision, and Machine Learning modules.
- Formulated clear contract interfaces enabling a 4-member hackathon / university club team to develop concurrently with zero merge conflicts.
- Initialized Git version control with GitFlow branching standards off `develop`.

### ⚡ Backend Scaffolding
- Built asynchronous **FastAPI** application with structured logging and request timing middleware.
- Implemented `GET /health` endpoint conforming to specification:
  ```json
  {
    "status": "ok",
    "service": "GestureForge Backend"
  }
  ```
- Configured dynamic Cross-Origin Resource Sharing (CORS) with startup origin verification.
- Integrated **Pydantic Settings** (`BaseSettings`) in `backend/config.py` for typed environment variable loading.
- Created typed scaffolding for Google MediaPipe hand tracking in `backend/gesture.py`.
- Created typed scaffolding for Scikit-learn multi-class gesture classification in `backend/models/gesture_model.py`.

### 🖥️ Frontend Dashboard
- Initialized **React 18 + Vite** client application with dark cyberpunk glassmorphism design.
- Implemented reusable components:
  - `Header.jsx`: Branding, phase badge, and version indicators.
  - `StatusCard.jsx`: Real-time backend health probe, latency calculation, offline diagnostic banner, and one-click copyable startup command.
  - `CameraPlaceholder.jsx`: Styled perception viewport with HUD reticles, radar scanline animations, and Phase 1 readiness tags.
- Built 4-member architecture overview showcase grid on landing page.
- Fully accessible with ARIA attributes (`role="status"`, `role="region"`, `aria-live="polite"`).

### 🚀 CI Pipeline & Tooling
- Implemented GitHub Actions CI workflow (`.github/workflows/ci.yml`) testing on Ubuntu:
  - Backend validation via `astral-sh/setup-uv` (Python 3.11).
  - Frontend validation via `pnpm/action-setup` (Node.js 20).
  - Automated Ruff linting, Black formatting check, Pytest suite, and live FastAPI server startup test.
  - Automated ESLint analysis, Prettier check, and Vite production bundle compilation.
- Integrated **uv** for ultra-fast dependency resolution and locked dependencies in `uv.lock`.
- Configured **Ruff** (primary linter) and **Black** (formatter) in `pyproject.toml`.

### 🔒 Security Improvements
- Sealed environment variables: strictly ignored `.env` and `.env.*` while committing `.env.example` templates.
- Verified zero tracked secrets in Git history.

### 🧪 Testing & Code Quality
- Created automated Pytest suite (`backend/tests/test_health.py`) validating direct route calls, TestClient `/health`, and root `/` endpoints.
- Validated 100% compliance across Ruff, Black, ESLint, and Prettier.

### 📚 Documentation
- Streamlined `README.md` with shields badges, problem statement, architecture diagram, 3-command Quick Start, and team ownership breakdown.
- Produced comprehensive deep-dive guides:
  - `docs/architecture.md`: Pipeline architecture & latency budget (<35ms).
  - `docs/setup_guide.md`: Cross-platform quickstart for Windows, macOS, Linux with `uv`.
  - `docs/team_roles.md`: 4-member role specialization matrix & GitFlow rules.
  - `docs/roadmap.md`: 4-phase milestone timeline.
  - `dataset/README.md`: 8-gesture taxonomy and landmark coordinate schemas.

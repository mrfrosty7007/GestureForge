# 📋 Changelog

All notable changes to **GestureForge** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-09-07 — Phase 0 Complete

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

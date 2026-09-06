# GestureForge ⚡
> **Real-Time AI-Powered Hand Gesture Recognition Engine**

![CI Status](https://img.shields.io/badge/CI-Passing-10b981?style=for-the-badge&logo=githubactions&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776ab?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18+-61dafb?style=for-the-badge&logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-6+-646cff?style=for-the-badge&logo=vite&logoColor=white)
![Ruff](https://img.shields.io/badge/Linter-Ruff-orange?style=for-the-badge&logo=ruff&logoColor=white)
![Black](https://img.shields.io/badge/Formatted%20with-Black-000000?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)

---

## 🛑 Problem Statement

Touchless human-computer interaction (HCI) is critical in modern digital environments—from sterile operating rooms and VR gaming to accessibility tools for motor-impaired individuals.

Traditional systems either rely on expensive, proprietary sensor hardware (e.g. depth cameras) or suffer from high latency and monolithic architectures. **GestureForge** solves this with an open, modular pipeline: capturing standard consumer webcam feeds, extracting 21 3D hand keypoints via Google MediaPipe, classifying gestures in sub-millisecond time via Scikit-learn, and streaming real-time telemetry into a cyberpunk React HUD.

---

## ✨ Planned Features

- 🖐️ **21 3D Hand Landmark Tracking**: Sub-millimeter keypoint extraction using Google MediaPipe.
- ⚡ **Sub-35ms Latency Budget**: High-throughput asynchronous streaming between browser and backend.
- 🧠 **ML Gesture Classification**: Multi-class model recognizing 8 core gestures with confidence telemetry.
- 🖥️ **Futuristic Cyberpunk HUD**: Glassmorphic dashboard with live health diagnostics and radar reticles.
- 👥 **Decoupled Team Architecture**: Clear API contracts tailored for 4 independent contributors.
- 🛡️ **Production-Grade Quality**: Enforced with Ruff, Black, ESLint, Prettier, and GitHub Actions CI.

---

## 🏛️ Architecture Preview

```mermaid
graph LR
    Cam["Webcam Video Feed"] -->|Frames| Gateway["FastAPI Gateway (backend/app.py)"]
    Gateway -->|BGR Frames| Vision["MediaPipe Perception (backend/gesture.py)"]
    Vision -->|21 3D Landmarks| ML["Classifier Engine (backend/models/)"]
    ML -->|Gesture & Confidence| Gateway
    Gateway -->|Telemetry Event| HUD["React + Vite HUD (frontend/)"]
```

> 📖 **Deep Dive**: See [`docs/architecture.md`](docs/architecture.md) for full pipeline specs and latency budgets.

---

## 🚀 Quick Start (3 Commands)

Get GestureForge up and running locally in seconds:

```bash
# 1. Clone repo & sync Python environment (using uv)
git clone https://github.com/your-org/GestureForge.git && cd GestureForge && uv sync

# 2. Start the FastAPI Backend Gateway
uv run uvicorn app:app --reload

# 3. Start the React Frontend Dashboard (in a second terminal)
cd frontend && pnpm install && pnpm run dev
```

- **Frontend Dashboard**: [`http://localhost:5173`](http://localhost:5173)
- **Backend API & Health**: [`http://127.0.0.1:8000/health`](http://127.0.0.1:8000/health)
- **Interactive Swagger Docs**: [`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs)

*(Note: Traditional `pip install -r backend/requirements.txt` and `npm run dev` are also fully supported).*

---

## 👥 4-Member Team Ownership

GestureForge separates responsibilities so 4 engineers can ship features simultaneously:

| Member | Specialization | Core Files | Delivered Interface |
|:---|:---|:---|:---|
| **Member 1** | Backend & API Gateway | `backend/app.py`, `backend/routes/` | `/health`, WebSocket streaming gateway |
| **Member 2** | Computer Vision & Perception | `backend/gesture.py` | `extract_landmarks(frame) -> list[HandDetectionResult]` |
| **Member 3** | ML Models & Datasets | `backend/models/`, `dataset/` | `predict(features) -> {"gesture": str, "confidence": float}` |
| **Member 4** | Frontend UI & HUD | `frontend/src/` | Interactive telemetry HUD & camera viewports |

> 👥 **Team Contract**: Review [`docs/team_roles.md`](docs/team_roles.md) for the complete collaboration and branching matrix.

---

## 📚 Detailed Documentation

Comprehensive specifications have been moved into dedicated documents:

- 🏛️ [**System Architecture & Data Flow**](docs/architecture.md) — Technical component breakdown & latency budgets.
- 🛠️ [**Setup & Installation Guide**](docs/setup_guide.md) — Detailed instructions for Windows, macOS, and Linux with `uv`.
- 👥 [**Team Roles & Branching Guide**](docs/team_roles.md) — 4-member responsibility matrix and Git workflow.
- 🗺️ [**Development Roadmap**](docs/roadmap.md) — 4-phase agile milestones and deliverable criteria.
- 📊 [**Dataset Taxonomy & Schema**](dataset/README.md) — 8-class gesture catalog and landmark normalization formulas.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

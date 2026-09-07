# GestureForge

Real-time AI-powered hand gesture recognition system built with MediaPipe, FastAPI, and React.

---

## 📁 Folder Structure

```text
GestureForge/
├── backend/          # FastAPI backend (API gateway, routes, models)
├── frontend/         # React + Vite frontend dashboard
├── ai-model/         # MediaPipe models & gesture classifiers
├── dataset/          # Raw frames & extracted landmark datasets
├── docs/             # Setup guides & architecture documentation
├── README.md         # Project overview & workflow
└── .gitignore        # Ignored files & directories
```

---

## 👥 Team Workflow

We are 4 developers building an MVP foundation for the SRM hackathon. We follow a simple Git branching model:

* **`main`** — Stable, tested releases ready for demonstration.
* **`develop`** — Active integration branch where features are combined and tested.
* **Feature Branches** (`feature/<name>-<task>`) — Dedicated branch for each developer. Never push directly to `main` or `develop`.

```text
feature/dev1-mediapipe ──┐
feature/dev2-backend   ──┼──> develop (Integration) ────> main (Stable MVP)
feature/dev3-frontend  ──┤
feature/dev4-dataset   ──┘
```

### Git Branching Rules

1. Create a feature branch off `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/<your-name>-<feature>
   ```
2. Make your commits and push your branch:
   ```bash
   git push origin feature/<your-name>-<feature>
   ```
3. Open a Pull Request targeting `develop`. Once reviewed and approved, merge into `develop`.

---

## 🚀 Quick Start (Full Stack MVP)

Run the 3 modules in separate terminals:

### 1. Backend Gateway (Terminal 1)

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

- API Base: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Health Check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- Swagger Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Frontend Cyber Dashboard (Terminal 2)

```bash
cd frontend
pnpm install
pnpm run dev
```

- Cyber Operations HUD: [http://localhost:5173](http://localhost:5173)

### 3. Real-Time AI Camera Pipeline (Terminal 3)

```bash
cd ai-model
pip install -r requirements.txt
python hand_detection.py
```

- Tracks 21 hand landmarks, classifies 5 gestures in real-time, and streams debounced telemetry to the FastAPI gateway.
- Press `Q` in the camera viewport to quit cleanly.

---

## 🖐️ Recognized Gestures

| Gesture | Description | Supported In |
|:---|:---|:---:|
| ✋ **Palm** | All 5 fingers extended outward | v1.0.0-MVP |
| ✊ **Fist** | All 4 fingers folded, compact cluster, thumb wrapped | v1.0.0-MVP |
| 👍 **Thumbs Up** | Thumb elevated & separated, 4 fingers folded | v1.0.0-MVP |
| ☝️ **One Finger** | Only index finger extended upward | v1.0.0-MVP |
| ✌️ **Peace** | Index and middle fingers extended | v1.0.0-MVP |

---

## 🎯 Roadmap & Milestones

| Milestone | Status | Details |
|:---|:---:|:---|
| **Phase 0 — Foundation** | ✅ Complete | Repository structure, CI workflows, tooling, documentation |
| **Phase 1 — Perception MVP** | ✅ Complete | MediaPipe tracking, 5 gestures, FastAPI gateway, React Cyber HUD |
| **Phase 2 — Machine Learning** | ⏳ Next | Custom gesture dataset capture, feature extraction, ML classifiers |
| **Phase 3 — System Polish** | ⏳ Planned | Expanded gestures, audio/visual triggers, hackathon showcase deck |


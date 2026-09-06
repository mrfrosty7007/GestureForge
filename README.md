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

## 🚀 Quick Start (Local Setup)

### 1. Backend Setup

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload
```

- API Base: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Health Endpoint: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- Swagger Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Frontend Setup (in a separate terminal)

```bash
cd frontend
pnpm install
pnpm run dev
```

- Web Dashboard: [http://localhost:5173](http://localhost:5173)

---

## 🎯 Next Steps

* **Phase 1 — Task 2**: MediaPipe 21 hand landmarks detection and webcam capture integration.
* **Phase 2**: Multi-class gesture dataset collection and classification model training.
* **Phase 3**: Telemetry HUD, audio/visual triggers, and final hackathon presentation.

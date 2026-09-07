# 🛠️ GestureForge Setup & Installation Guide

## 🎯 Purpose
Provides complete, reproducible development environment setup instructions for Windows, macOS, and Linux, featuring modern dependency management with `uv` and `pnpm`.

## 👤 Document Owner
- **Primary Owner**: Member 1 (Backend, DevOps & CI/CD)
- **Collaborators**: All Team Members

---

## 📋 System Prerequisites

- **Python**: 3.11 or 3.12 (`python --version`)
- **Node.js**: 20.x or 22.x (`node --version`)
- **Package Managers**: `uv` (recommended for Python) & `pnpm` / `npm` (for Node.js)
- **Git**: 2.30+ (`git --version`)
- **Hardware**: Working webcam / integrated camera for upcoming Phase 1 testing.

---

## ⚡ 1. Modern Fast Setup (Recommended via `uv`)

### Step 1.1: Clone and sync Python dependencies
```bash
# Clone the repository
git clone https://github.com/mrfrosty7007/GestureForge.git
cd GestureForge

# Modern one-step virtual environment and lockfile sync
uv sync
```

### Step 1.2: Configure environment variables
```bash
# Copy backend environment template (never commit real .env!)
# Windows PowerShell:
Copy-Item backend/.env.example backend/.env

# macOS / Linux:
cp backend/.env.example backend/.env
```

### Step 1.3: Start the backend server
```bash
uv run uvicorn backend.main:app --reload
```
- API Base URL: `http://127.0.0.1:8000`
- Health Endpoint: `http://127.0.0.1:8000/health`
- OpenAPI Swagger Docs: `http://127.0.0.1:8000/docs`

---

## 🐍 2. Legacy Setup (pip + venv fallback)

If `uv` is not installed on your machine:

```bash
cd backend
python -m venv .venv

# On Windows:
.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

---

## ⚛️ 3. Frontend Setup

In a new terminal window:

```bash
cd frontend

# Install dependencies (pnpm recommended; npm also supported)
pnpm install
# or: npm install

# Configure environment variables
# Windows PowerShell:
Copy-Item .env.example .env
# macOS / Linux:
cp .env.example .env

# Start the Vite development server
pnpm run dev
# or: npm run dev
```
Open your browser at **`http://localhost:5173`**.

---

## 🧪 4. Running Verification & Quality Checks

### Backend Quality Suite (Ruff, Black, Pytest)
```bash
# Run Ruff linter
uv run ruff check .

# Run Black code formatting check
uv run black --check backend

# Run automated tests
uv run pytest backend/tests
```

### Frontend Quality Suite (ESLint, Prettier, Vite Build)
```bash
cd frontend

# Check code formatting
pnpm run format

# Run ESLint static analysis
pnpm run lint

# Compile production distribution bundle
pnpm run build
```

---

## 🔄 Phase 1 Handoff
Before beginning Phase 1:
1. Ensure both `uv run pytest backend/tests` and `pnpm run build` execute with zero warnings or errors on your machine.
2. Confirm browser access to `http://localhost:5173` displays `Backend Gateway Connectivity: online` with active latency measurements.
3. Grant camera permissions in your web browser for `localhost:5173` in preparation for Phase 1 webcam stream integration.

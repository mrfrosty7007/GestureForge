# 🛠️ GestureForge Setup & Installation Guide

This guide walks through configuring the development environment on Windows, macOS, and Linux.

---

## 📋 System Prerequisites

- **Python**: 3.10, 3.11, or 3.12 (`python --version`)
- **Node.js**: 18.x, 20.x, or 22.x (`node --version`)
- **Git**: 2.30+ (`git --version`)
- **Hardware**: Working webcam / integrated camera for future Phase 1 testing.

---

## 🐍 1. Backend Setup

### Step 1.1: Navigate into backend directory
```bash
cd backend
```

### Step 1.2: Create and activate a virtual environment
- **Windows (PowerShell)**:
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  ```
- **macOS / Linux**:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### Step 1.3: Install backend dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 1.4: Configure environment variables
```bash
# Windows PowerShell:
Copy-Item .env.example .env

# macOS / Linux:
cp .env.example .env
```

### Step 1.5: Start the backend server
```bash
uvicorn app:app --reload
```
The API will be live at: **`http://127.0.0.1:8000`**
- Health Check: `http://127.0.0.1:8000/health`
- Swagger Docs: `http://127.0.0.1:8000/docs`

---

## ⚛️ 2. Frontend Setup

### Step 2.1: Open a second terminal and navigate to frontend directory
```bash
cd frontend
```

### Step 2.2: Install dependencies
```bash
npm install
```

### Step 2.3: Configure environment variables
```bash
# Windows PowerShell:
Copy-Item .env.example .env

# macOS / Linux:
cp .env.example .env
```

### Step 2.4: Start the Vite development server
```bash
npm run dev
```
Open your browser and navigate to **`http://localhost:5173`**.

---

## 🧪 3. Running Verification & Tests

### Backend Unit Tests
```bash
# From the project root or backend directory:
pytest backend/tests
```

### Frontend Production Build
```bash
# From frontend directory:
npm run build
```

# ⚡ GestureForge Backend API

Lightweight FastAPI backend gateway for GestureForge. Ingests real-time gesture telemetry from the AI perception module and exposes endpoints for frontend HUD integration.

---

## 🚀 Setup & Execution

### 1. Activate the Virtual Environment

**Windows:**
```bash
.venv\Scripts\activate
```

*(Or create one if needed: `python -m venv .venv && .venv\Scripts\activate`)*

**macOS / Linux:**
```bash
source .venv/bin/activate
```

*(Or create one if needed: `python3 -m venv .venv && source .venv/bin/activate`)*

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the FastAPI Server

```bash
uvicorn main:app --reload
```

- **Base URL**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **ReDoc Docs**: `http://127.0.0.1:8000/redoc`

---

## 📡 API Endpoints

### 1. Root Status
* **Endpoint**: `GET /`
* **Description**: Returns backend service identification and running status.
* **Sample Response** (`200 OK`):
  ```json
  {
    "project": "GestureForge Backend",
    "status": "running"
  }
  ```

---

### 2. Health Check
* **Endpoint**: `GET /health`
* **Description**: Diagnostic endpoint confirming operational readiness.
* **Sample Response** (`200 OK`):
  ```json
  {
    "status": "ok",
    "service": "GestureForge Backend"
  }
  ```

---

### 3. Ingest Gesture Prediction
* **Endpoint**: `POST /gesture`
* **Description**: Receives and stores the latest gesture prediction from the AI module in thread-safe memory.
* **Sample Request Payload**:
  ```json
  {
    "gesture": "Peace",
    "confidence": "High",
    "timestamp": "2026-09-07T17:50:00Z"
  }
  ```
* **Sample Response** (`200 OK`):
  ```json
  {
    "status": "received",
    "gesture": "Peace"
  }
  ```

---

### 4. Get Latest Gesture
* **Endpoint**: `GET /gesture/latest`
* **Description**: Returns the most recently received gesture prediction.
* **Sample Response — When Gesture Exists** (`200 OK`):
  ```json
  {
    "status": "success",
    "gesture": "Peace",
    "confidence": "High",
    "timestamp": "2026-09-07T17:50:00Z"
  }
  ```
* **Sample Response — When No Data Yet** (`200 OK`):
  ```json
  {
    "status": "empty",
    "message": "No gestures recorded yet",
    "gesture": null
  }
  ```

---

## 🔒 In-Memory Storage (`storage.py`)

- **Thread-safe**: Utilizes Python `threading.Lock` to ensure atomic read/write operations during high-frequency telemetry ingestion.
- **Zero External Dependencies**: Stores only the latest prediction in RAM (no database, SQLite, or Redis required for hackathon MVP).

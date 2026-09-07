# 🏛️ GestureForge System Architecture

## 🎯 Purpose
Defines the end-to-end technical architecture, component boundaries, data protocols, and target sub-35ms latency budget for the planned GestureForge real-time gesture recognition engine.

## 👤 Document Owner
- **Primary Owner**: System Architect & Member 1 (Backend & API Gateway)
- **Collaborators**: Member 2 (Computer Vision), Member 3 (ML Engineering), Member 4 (Frontend UI)

---

## 🔄 High-Level Data Flow

```mermaid
graph LR
    subgraph Client ["Client Browser (React + Vite)"]
        Cam["Streamed Video Frames"]
        HUD["Live HUD & Telemetry UI"]
        Status["Status & Health Monitor"]
    end

    subgraph Backend ["FastAPI Gateway & Pipelines"]
        WS["WebSocket / REST Handler<br/>(backend/main.py)"]
        HealthRoute["Health Endpoint<br/>(backend/routes.py)"]
        Vision["MediaPipe Pipeline<br/>(ai-model/hand_detection.py)"]
        Classifier["ML Model Classifier<br/>(ai-model/gesture_classifier.py)"]
    end

    Status -->|HTTP GET /health| HealthRoute
    Vision -->|JPEG latest-frame stream| Cam
    Vision -->|21 Normalized Landmarks (x,y,z)| Classifier
    Classifier -->|Predicted Class & Confidence| WS
    WS -->|JSON Telemetry Event| HUD
```

---

## 📦 Component Overview

### 1. Frontend Layer (`frontend/`)
- **Technology**: React 18 / 19, Vite, Modern CSS.
- **Role**:
  - Consumes binary JPEG frames from the backend's primary `WS /ws/video` stream.
  - Renders live HUD overlays with gesture and hardware telemetry.
  - Monitors backend gateway uptime and latency via `StatusCard.jsx`.
  - Does not access or reopen the webcam. `GET /video/feed` is an MJPEG fallback only.

### 2. API Gateway (`backend/main.py`, `backend/routes.py`)
- **Technology**: FastAPI, Uvicorn, Pydantic, WebSockets.
- **Role**:
  - Serves REST endpoints (`/`, `/health`, `/gesture`, `/gesture/latest`).
  - Implements CORS middleware allowing cross-origin requests from the React dev server (`http://localhost:5173`).
  - Provides separate real-time WebSocket telemetry (`/ws/telemetry`) and binary video (`/ws/video`) gateways.
  - Owns the headless AI worker lifecycle and is the sole webcam owner in normal operation.
  - Retains `GET /video/feed` as an MJPEG fallback without replacing latest-frame buffering.

### 3. Perception & Computer Vision (`ai-model/hand_detection.py`)
- **Technology**: Google MediaPipe, OpenCV (cv2).
- **Role**:
  - Ingests raw video frames from webcam.
  - Detects 21 3D hand keypoints (Wrist, Thumb CMC-IP-TIP, Index MCP-PIP-DIP-TIP, etc.).
  - Extracts normalized coordinates invariant to hand distance and position in frame.

### 4. ML Classification Engine (`ai-model/gesture_classifier.py`)
- **Technology**: Scikit-Learn, NumPy, Joblib.
- **Role**:
  - Converts 21 3D landmarks into a 63-dimensional feature vector.
  - Normalizes coordinates relative to wrist anchor point.
  - Evaluates vector against pre-trained classification models (Random Forest) with geometric fallback.
  - Outputs predicted gesture label and probability distribution.

---

## ⏱️ Target Latency Budget

| Pipeline Stage | Target Latency | Notes |
|:---|:---|:---|
| Frame Capture & Encoding | ~5 ms | Browser Canvas / OffscreenCanvas |
| Network Transport (Local WS) | < 2 ms | Localhost WebSocket socket |
| MediaPipe Landmark Inference | 10 - 15 ms | MediaPipe GPU/CPU Lite model |
| Scikit-learn Feature Inference | < 1 ms | Vectorized matrix multiplication |
| Frontend Render & HUD Update | ~16 ms | 60 FPS animation frame |
| **Total Round-Trip Latency** | **< 35 ms** | **Smooth real-time experience** |

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
        Cam["Webcam Video Stream"]
        HUD["Live HUD & Telemetry UI"]
        Status["Status & Health Monitor"]
    end

    subgraph Backend ["FastAPI Gateway & Pipelines"]
        WS["WebSocket / REST Handler<br/>(backend/app.py)"]
        HealthRoute["Health Endpoint<br/>(backend/routes/health.py)"]
        Vision["MediaPipe Pipeline<br/>(backend/gesture.py)"]
        Classifier["ML Model Classifier<br/>(backend/models/gesture_model.py)"]
    end

    Status -->|HTTP GET /health| HealthRoute
    Cam -->|Base64 / WebRTC Frame| WS
    WS -->|OpenCV BGR Matrix| Vision
    Vision -->|21 Normalized Landmarks (x,y,z)| Classifier
    Classifier -->|Predicted Class & Confidence| WS
    WS -->|JSON Telemetry Event| HUD
```

---

## 📦 Component Overview

### 1. Frontend Layer (`frontend/`)
- **Technology**: React 18 / 19, Vite, Modern CSS.
- **Role**:
  - Captures webcam video feed via browser's `navigator.mediaDevices.getUserMedia()`.
  - Renders live HUD overlay with landmark points and confidence gauges.
  - Monitors backend gateway uptime and latency via `StatusCard.jsx`.
  - Provides a camera placeholder during Phase 0 and real-time canvas rendering in Phase 1.

### 2. API Gateway (`backend/app.py`, `backend/routes/health.py`)
- **Technology**: FastAPI, Uvicorn, Pydantic Settings.
- **Role**:
  - Serves REST endpoints (`/health`, `/docs`).
  - Implements CORS middleware allowing cross-origin requests from the React dev server (`http://localhost:5173`).
  - Provides structured logging and planned WebSocket gateway for streaming bidirectional frame/telemetry packets with target sub-30ms latency.

### 3. Perception & Computer Vision (`backend/gesture.py`)
- **Technology**: Google MediaPipe, OpenCV (cv2).
- **Role**:
  - Ingests raw video frames.
  - Detects 21 3D hand keypoints (Wrist, Thumb CMC-IP-TIP, Index MCP-PIP-DIP-TIP, etc.).
  - Extracts normalized coordinates invariant to hand distance and position in frame.

### 4. ML Classification Engine (`backend/models/gesture_model.py`)
- **Technology**: Scikit-Learn, NumPy, Joblib.
- **Role**:
  - Converts 21 3D landmarks into a 63-dimensional feature vector.
  - Normalizes coordinates relative to wrist anchor point.
  - Evaluates vector against pre-trained classification models (Random Forest, SVM, or MLP).
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

---

## 🔄 Phase 1 Handoff
When transitioning from Phase 0 to Phase 1:
1. **Member 1 (Gateway)** will open `@app.websocket("/ws/gesture")` in `backend/app.py` to stream binary/base64 frame payloads.
2. **Member 2 (Perception)** will instantiate `mp.solutions.hands.Hands` within `backend/gesture.py` and implement `extract_landmarks(frame)`.
3. **Member 4 (Frontend)** will activate webcam capture in `frontend/src/components/CameraPlaceholder.jsx` using `navigator.mediaDevices.getUserMedia` and transmit frames to Member 1's WebSocket.
4. **Member 3 (ML)** will collect the first baseline landmark coordinate sequences to populate `dataset/raw/`.

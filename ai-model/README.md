# 🖐️ GestureForge — Hand Detection & Gesture Recognition Module

Real-time computer vision module tracking up to 2 hands, extracting 21 3D landmarks, and recognizing 5 distinct hand gestures in real time using **MediaPipe Hands** and rule-based geometric heuristics. Connected automatically to the **FastAPI Backend** with non-blocking smart debouncing.

---

## 🎯 Supported Gestures

GestureForge uses landmark position heuristics (comparing fingertip coordinates against knuckle and PIP joints) without requiring heavy ML inference:

| Gesture | Finger State Rule | Description |
|:---|:---|:---|
| **Palm** | All 5 fingers extended | All fingertips (Index, Middle, Ring, Pinky, Thumb) extended outward. |
| **Fist** | All fingers folded | All 5 fingers curled tightly toward palm; thumb folded across fingers. |
| **Thumbs Up** | Thumb extended up, 4 folded | Thumb tip elevated vertically above index knuckle; other 4 fingers curled. |
| **One Finger** | Index extended, other 4 folded | Index fingertip pointing upward; Middle, Ring, Pinky, and Thumb folded. |
| **Peace** | Index + Middle extended | Index and Middle extended in a 'V' shape; Ring, Pinky, and Thumb folded. |

---

## 🔄 End-to-End System Architecture

```text
Webcam Frame Ingestion
        ↓
MediaPipe Hands Perception (21 3D Keypoints)
        ↓
GestureClassifier (Geometric Heuristic Engine)
        ↓
HUD Overlay (FPS, Landmarks, Telemetry Card)
        ↓ (Smart Debouncing: On-Change or 1s Cooldown)
FastAPI Backend (POST http://127.0.0.1:8000/gesture)
```

---

## 🚀 Startup Order & Execution

> [!IMPORTANT]
> **Startup Order**: For end-to-end integration, the **FastAPI Backend** must be started first so that incoming gesture telemetry is received and stored.

### Step 1: Start the Backend Gateway (Terminal 1)

```bash
cd backend
.venv\Scripts\activate          # Windows (source .venv/bin/activate on macOS/Linux)
uvicorn main:app --reload
```
* Backend will be live at `http://127.0.0.1:8000`.

---

### Step 2: Start the AI Gesture Recognition Demo (Terminal 2)

```bash
cd ai-model
.venv\Scripts\activate          # Windows (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
python hand_detection.py
```

---

## 📡 API Communication & Smart Debouncing

The module sends HTTP POST requests to `http://127.0.0.1:8000/gesture`.

### Payload Format
```json
{
  "gesture": "Peace",
  "confidence": "High",
  "timestamp": "2026-09-07T18:00:00Z"
}
```

### Smart Debouncing Logic
To prevent overwhelming the backend with 30–60 identical frames per second:
1. **On Gesture Transition**: Sent immediately whenever a new gesture is recognized (e.g. switching from `Peace` to `Palm`).
2. **Cooldown Renewal**: Sent every **1.0 second** while holding the same continuous gesture.
3. **Non-Blocking Background Thread**: Network requests run in a background daemon thread with a 0.5s timeout. If the backend is temporarily unavailable, the camera feed and HUD continue running at full speed without lagging or crashing.

---

## 🖥️ Expected Output

### Console Output
```text
=================================================================
GestureForge — Real-Time Hand Detection & Gesture Recognition
Supported Gestures: Palm | Fist | Thumbs Up | One Finger | Peace
Streaming to Backend: http://127.0.0.1:8000/gesture
Press 'Q' in the video window to quit.
=================================================================
Sent: Peace (High)
Sent: Palm (High)
Sent: Fist (High)
```

If the backend is not running:
```text
[API Error] Could not reach backend at http://127.0.0.1:8000/gesture: ConnectionError
```
*(The webcam application continues running smoothly).*

### Video Window Output
An OpenCV GUI window titled **`GestureForge Hand Detection`** displays:
1. **Live Camera Feed**: Mirrored real-time webcam video.
2. **21 Landmarks & Bones**: Color-coded points and skeletal connection lines.
3. **Floating Wrist Tag**: Shows `Gesture (Confidence)` near the hand.
4. **Telemetry HUD Card**:
   - `FPS: <value>` (real-time framerate)
   - `Hands: <count>` (0, 1, or 2)
   - `Gesture: <name>`
   - `Confidence: <High | Medium>`
   - `Press 'Q' to Exit`

---

## ⌨️ Controls

- **`Q`**: Exit the video window, release the camera hardware, and destroy all OpenCV windows cleanly.

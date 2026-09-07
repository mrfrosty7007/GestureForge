# 🖐️ GestureForge — Hand Detection & Gesture Recognition Module

Real-time computer vision module tracking up to 2 hands, extracting 21 3D landmarks, and recognizing 5 distinct hand gestures in real time using **MediaPipe Hands** and rule-based geometric heuristics.

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

## 📁 Architecture & File Structure

```text
ai-model/
├── hand_detection.py       # Main webcam ingestion, MediaPipe pipeline, drawing & HUD overlay
├── gesture_classifier.py   # Modular rule-based gesture classifier for 21 MediaPipe landmarks
├── requirements.txt        # Pinned Python dependencies (mediapipe, opencv-python, etc.)
└── README.md               # Setup and usage documentation
```

---

## 🚀 Setup & Execution

### 1. Navigate to the Module Directory

```bash
cd ai-model
```

### 2. Activate the Virtual Environment

**Windows:**
```bash
.venv\Scripts\activate
```

*(Or create one if not yet initialized: `python -m venv .venv && .venv\Scripts\activate`)*

**macOS / Linux:**
```bash
source .venv/bin/activate
```

*(Or create one if not yet initialized: `python3 -m venv .venv && source .venv/bin/activate`)*

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Gesture Recognition Demo

```bash
python hand_detection.py
```

---

## 🖥️ Expected Output

### Console Output
```text
============================================================
GestureForge — Real-Time Hand Detection & Gesture Recognition
Supported Gestures: Palm | Fist | Thumbs Up | One Finger | Peace
Tracking up to 2 hands with 21 landmarks each.
Press 'Q' in the video window to quit.
============================================================
```

Upon pressing `Q`:
```text
Exit key pressed. Closing...
Webcam released and OpenCV windows destroyed cleanly.
```

### Video Window Output
An OpenCV GUI window titled **`GestureForge Hand Detection`** will launch showing:
1. **Live Camera Feed**: Mirrored real-time webcam video.
2. **21 Landmarks**: Color-coded points on wrist and finger joints.
3. **Hand Connections**: Skeletal lines connecting joints.
4. **Per-Hand Gesture Tag**: Floating label near wrist indicating recognized gesture.
5. **HUD Telemetry Card**:
   - `FPS: <value>` (real-time framerate)
   - `Hands: <count>` (0, 1, or 2)
   - `Gesture: <Palm | Fist | Thumbs Up | One Finger | Peace>`
   - `Confidence: <High | Medium>`
   - `Press 'Q' to Exit`

---

## ⌨️ Controls

- **`Q`**: Exit the video window, release the camera hardware, and destroy all OpenCV windows cleanly.

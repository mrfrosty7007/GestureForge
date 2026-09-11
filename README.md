# GestureForge

**Real-Time Hand Gesture Recognition**

GestureForge is a native real-time hand gesture recognition application built with **Python**, **OpenCV**, **MediaPipe**, and **scikit-learn**.

It performs live hand tracking, gesture classification, and performance monitoring through a lightweight native OpenCV interface.

---

## Features

* Native OpenCV interface
* Real-time gesture recognition (28–30 FPS)
* MediaPipe 21-hand-landmark tracking
* Independent two-hand recognition
* Live FPS counter
* Live latency display
* Live hand count
* Left & Right hand gesture indicators with emojis
* Fullscreen mode (`F`)
* Instant camera cleanup (`Q`)

---

## Supported Gestures

| Emoji | Gesture |
| :---: | :--- |
| ✋ | Open Palm |
| ✊ | Closed Fist |
| 👍 | Thumbs Up |
| ✌️ | Peace |
| 👌 | OK |
| ☝️ | Pointing |
| 🤘 | Rock |
| 🤙 | Call Me |

> **Note:** Both hands can be tracked and recognized simultaneously with independent gesture classification.

---

## Project Structure

```text
GestureForge/
├── ai-model/        # MediaPipe pipeline, threaded camera runtime, gesture classifier
├── backend/         # Archived backend components for future expansion
├── frontend/        # Archived experimental web interface
├── dataset/         # Landmark datasets
├── docs/            # Documentation
├── main.py          # Native application entrypoint
├── pyproject.toml
└── README.md
```

---

## Quick Start

Run the application directly using [`uv`](https://docs.astral.sh/uv/):

```bash
uv sync
uv run python main.py
```

Alternative using standard Python (virtual environment):

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r ai-model/requirements.txt
python main.py
```

**macOS/Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r ai-model/requirements.txt
python main.py
```

> [!NOTE]
> **Troubleshooting / Dependency Isolation:** MediaPipe pins `protobuf<5`, so installation should always be done inside the project's virtual environment to avoid conflicts with globally installed packages like Streamlit.

---

## Controls

| Key | Action |
| :---: | :--- |
| `F` | Toggle Fullscreen |
| `Q` | Quit |

---

## Live Metrics

The real-time native HUD displays:

* **FPS**: Current pipeline throughput measured over recent frames
* **Latency**: End-to-end processing latency in milliseconds
* **Hands detected**: Number of active hands visible in the frame (0, 1, or 2)
* **Left-hand gesture**: Real-time gesture classification and emoji indicator for the left hand
* **Right-hand gesture**: Real-time gesture classification and emoji indicator for the right hand

---

## Performance

| Metric | Value |
| :--- | :--- |
| FPS | 28–30 |
| Latency | 34–40 ms |
| Startup | ~1 s |
| Hands | Up to 2 |

---

## Architecture

```text
Camera
   │
ThreadedCamera
   │
Latest Frame Buffer
   │
MediaPipe Hands
   │
Gesture Classifier
   │
Native OpenCV HUD
```

* **Threaded Camera Acquisition**: A dedicated worker thread captures webcam frames continuously via DirectShow (`cv2.CAP_DSHOW`) without blocking pipeline execution.
* **Latest-Frame Buffering**: The buffer always retains only the most recent frame, preventing queue latency and ensuring minimum processing delay.
* **MediaPipe Inference**: Uses MediaPipe Hands (`model_complexity=0`) to extract 21 3D landmarks per detected hand with sub-15ms inference latency.
* **Gesture Classifier**: Identifies gestures for each hand independently using geometric finger-state analysis and landmark heuristic models.
* **Native OpenCV HUD**: Overlays real-time performance metrics, dual-hand indicators, and controls via hardware-blended OpenCV rendering.

---

## Legacy Components

The repository contains experimental components preserved for future architecture exploration:

* **FastAPI Backend (`backend/`)**: Web API gateway and streaming services.
* **React Frontend (`frontend/`)**: Browser-based telemetry interface.
* **Tauri Shell (`frontend/src-tauri/`)**: Desktop application wrapper for the web frontend.

These components are preserved for future expansion but are **not required** to run the native application.

---

## Future Improvements

* Additional static and dynamic gesture classifications
* Gesture-controlled system automation (media playback, slide navigation)
* Hardware acceleration via ONNX Runtime and TensorRT
* Optional telemetry dashboard restoration

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.

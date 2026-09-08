"""GestureForge — Native Real-Time Hand Gesture Recognition Application.

Primary entry point for high-performance live camera hand tracking and gesture recognition.
Launches a native OpenCV desktop window with zero web/streaming overhead.

Usage:
    python main.py
    python main.py --camera 0
"""

import argparse
import sys
from pathlib import Path

# Ensure ai-model directory is in python search path
_ai_model_path = str(Path(__file__).resolve().parent / "ai-model")
if _ai_model_path not in sys.path:
    sys.path.insert(0, _ai_model_path)

from hand_detection import run_native_camera_app  # noqa: E402


def main() -> None:
    """Primary CLI entrypoint for running the native OpenCV camera application."""
    parser = argparse.ArgumentParser(
        description="GestureForge — Native Real-Time Hand Gesture Recognition"
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Webcam device index (default: 0)",
    )
    args = parser.parse_args()

    run_native_camera_app(camera_index=args.camera)


if __name__ == "__main__":
    main()

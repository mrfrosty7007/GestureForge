"""AI Worker integration module for GestureForge backend.

Provides a singleton AIWorker instance running OpenCV and MediaPipe in a background
thread, decoupled from GUI rendering.
"""

import sys
from pathlib import Path

# Ensure ai-model is discoverable on sys.path without breaking package imports
_ai_model_dir = str(Path(__file__).resolve().parent.parent / "ai-model")
if _ai_model_dir not in sys.path:
    sys.path.insert(0, _ai_model_dir)

from hand_detection import AIWorker  # noqa: E402

# Global singleton AIWorker instance for FastAPI backend lifecycle
ai_worker = AIWorker(headless=True)

__all__ = ["AIWorker", "ai_worker"]

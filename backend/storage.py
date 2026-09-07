"""In-memory thread-safe storage for the latest gesture prediction.

Designed specifically for the GestureForge hackathon MVP without
external database dependencies (no Redis, no SQLite).
"""

import threading

from models import GesturePrediction, HandGesture


class GestureStorage:
    """Thread-safe in-memory store holding the latest multi-hand gesture prediction."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._latest_gesture: GesturePrediction | None = None

    def set_latest_gesture(self, prediction: GesturePrediction) -> None:
        """Stores the latest gesture prediction in a thread-safe manner."""
        with self._lock:
            self._latest_gesture = prediction

    def get_latest_gesture(self) -> GesturePrediction | None:
        """Retrieves the latest gesture prediction, or None if none has been recorded."""
        with self._lock:
            return self._latest_gesture

    def get_latest_hands(self) -> list[HandGesture]:
        """Retrieves the list of detected hands from the latest prediction."""
        with self._lock:
            if self._latest_gesture is not None:
                return list(self._latest_gesture.hands)
            return []

    def clear(self) -> None:
        """Resets the storage (useful during automated testing)."""
        with self._lock:
            self._latest_gesture = None


# Singleton instance shared across the application lifetime
storage = GestureStorage()

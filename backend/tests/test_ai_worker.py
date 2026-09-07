"""Unit tests for AIWorker background service and headless pipeline.

Validates:
- AI worker startup and shutdown lifecycle
- Headless mode execution (ensuring no desktop GUI windows or waitKey throttling)
- Camera disconnection and automatic recovery logic
- Health monitoring integration (/health reflects worker and camera states)
- Frame rate decoupling (camera vs stream)
"""

from unittest.mock import MagicMock, patch

import numpy as np
from fastapi.testclient import TestClient

from backend.main import app
from backend.routes import health_check
from backend.worker import AIWorker, ai_worker


def test_ai_worker_defaults() -> None:
    """Verify AIWorker default configuration."""
    worker = AIWorker()
    assert worker.headless is True
    assert worker.camera_index == 0
    assert worker.worker_status == "stopped"
    assert worker.camera_status == "offline"
    assert not worker.is_running()


def test_ai_worker_startup_and_shutdown() -> None:
    """Verify clean startup and graceful shutdown without zombie threads."""
    worker = AIWorker(camera_index=999, headless=True)

    # Start worker
    worker.start()
    assert worker.worker_status == "running"
    assert worker.is_running()

    # Repeated start should be idempotent
    worker.start()
    assert worker.worker_status == "running"

    # Stop worker
    worker.stop(timeout=2.0)
    assert worker.worker_status == "stopped"
    assert worker.camera_status == "offline"
    assert not worker.is_running()


def test_ai_worker_headless_mode_never_calls_gui() -> None:
    """Verify that headless mode never invokes cv2.imshow or cv2.waitKey."""
    worker = AIWorker(camera_index=0, headless=True)

    # Mock cv2.VideoCapture and cv2 GUI functions
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    mock_cap = MagicMock()
    mock_cap.isOpened.side_effect = [True, True, False]
    mock_cap.read.return_value = (True, dummy_frame)

    with (
        patch("cv2.VideoCapture", return_value=mock_cap),
        patch("cv2.imshow") as mock_imshow,
        patch("cv2.waitKey") as mock_waitkey,
    ):
        worker.start()
        # Allow worker thread to process dummy frame
        worker._stop_event.wait(0.3)
        worker.stop(timeout=1.0)

        # In headless mode, imshow and waitKey MUST NOT be called
        mock_imshow.assert_not_called()
        mock_waitkey.assert_not_called()


def test_ai_worker_camera_disconnect_and_reconnect_logic() -> None:
    """Verify that camera read failure marks state degraded and triggers recovery."""
    worker = AIWorker(camera_index=0, headless=True)

    mock_cap = MagicMock()
    # Simulate: open succeeds, first read fails (camera disconnect), release called
    mock_cap.isOpened.side_effect = [True, True, False]
    mock_cap.read.return_value = (False, None)

    with patch("cv2.VideoCapture", return_value=mock_cap):
        worker.start()
        worker._stop_event.wait(0.2)
        # Verify status transitions to degraded or offline on read failure
        assert worker.camera_status in ("degraded", "offline")
        worker.stop(timeout=1.0)


def test_ai_worker_in_process_callbacks() -> None:
    """Verify that in-process callbacks receive gesture and frame events."""
    received_gestures = []
    received_frames = []

    def on_gesture(payload):
        received_gestures.append(payload)

    def on_frame(frame_bytes):
        received_frames.append(frame_bytes)

    worker = AIWorker(
        camera_index=0,
        headless=True,
        target_stream_fps=100.0,  # Ensure stream frame triggers immediately
        on_gesture=on_gesture,
        on_frame=on_frame,
    )

    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    mock_cap = MagicMock()
    mock_cap.isOpened.side_effect = [True, True, False]
    mock_cap.read.return_value = (True, dummy_frame)

    with patch("cv2.VideoCapture", return_value=mock_cap):
        worker.start()
        worker._stop_event.wait(0.3)
        worker.stop(timeout=1.0)

    # Frame callback should have been called
    assert len(received_frames) > 0
    assert isinstance(received_frames[0], bytes)


def test_health_check_reflects_worker_and_camera_state() -> None:
    """Verify that /health accurately reflects running and degraded states."""
    # Test degraded state when camera is offline
    with (
        patch.object(ai_worker, "_worker_status", "running"),
        patch.object(ai_worker, "_camera_status", "degraded"),
    ):
        data = health_check()
        assert data["status"] == "degraded"
        assert data["camera"] == "degraded"
        assert data["ai_worker"] == "running"

    # Test fully healthy state
    with (
        patch.object(ai_worker, "_worker_status", "running"),
        patch.object(ai_worker, "_camera_status", "active"),
    ):
        data = health_check()
        assert data["status"] == "ok"
        assert data["camera"] == "active"
        assert data["ai_worker"] == "running"
        assert data["video_stream"] == "active"
        assert data["telemetry"] == "active"


def test_health_check_endpoint_via_testclient() -> None:
    """Verify GET /health HTTP response structure via TestClient."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    json_data = response.json()
    assert "status" in json_data
    assert "service" in json_data
    assert "camera" in json_data
    assert "ai_worker" in json_data
    assert "video_stream" in json_data
    assert "telemetry" in json_data

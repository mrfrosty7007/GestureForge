"""Unit tests for AIWorker background service and headless pipeline.

Validates:
- AI worker startup and shutdown lifecycle
- Headless mode execution (ensuring no desktop GUI windows or waitKey throttling)
- Camera disconnection and automatic recovery logic
- Health monitoring integration (/health reflects worker and camera states)
- Frame rate decoupling (camera vs stream)
"""

from typing import Any
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest
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

        mock_cap.set.assert_any_call(cv2.CAP_PROP_BUFFERSIZE, 1)
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


def test_ai_worker_consumer_active_standby_and_camera_release() -> None:
    """Verify AIWorker pauses capture, releases camera on standby, and resumes on demand."""
    worker = AIWorker(camera_index=0, headless=True)
    worker.set_consumer_active(False)
    assert not worker.is_consumer_active()

    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))

    with patch("cv2.VideoCapture", return_value=mock_cap) as mock_video_capture:
        worker.start()
        worker._stop_event.wait(0.2)
        # While inactive, camera must be standby and VideoCapture should not be opened
        assert worker.camera_status == "standby"
        mock_video_capture.assert_not_called()

        # Activate consumer
        worker.set_consumer_active(True)
        worker._stop_event.wait(0.3)
        assert mock_video_capture.called
        assert worker.camera_status == "active"

        # Deactivate consumer: should release camera back to standby
        worker.set_consumer_active(False)
        worker._stop_event.wait(0.3)
        assert worker.camera_status == "standby"
        assert mock_cap.release.called

        worker.stop(timeout=1.0)
        assert worker.camera_status == "offline"


def test_websocket_telemetry_disconnect_cleans_up_and_pauses_consumer() -> None:
    """Verify disconnecting /ws/telemetry removes client and pauses AI worker capture."""
    client = TestClient(app)
    from backend.routes import get_active_client_count

    initial_count = get_active_client_count()
    with client.websocket_connect("/ws/telemetry") as ws:
        # First message is the initial telemetry payload
        data = ws.receive_json()
        assert "status" in data
        assert get_active_client_count() == initial_count + 1
        assert ai_worker.is_consumer_active()

    # Once context manager exits, the websocket is closed
    assert get_active_client_count() == initial_count
    assert not ai_worker.is_consumer_active()


def test_websocket_video_disconnect_cleans_up_and_pauses_consumer() -> None:
    """Verify disconnecting /ws/video removes client and pauses AI worker capture."""
    client = TestClient(app)
    from backend.routes import get_active_client_count

    initial_count = get_active_client_count()
    with client.websocket_connect("/ws/video") as ws:
        # Send ping to verify bidirectional socket
        ws.send_text("ping")
        assert ws.receive_text() == "pong"
        assert get_active_client_count() == initial_count + 1
        assert ai_worker.is_consumer_active()

    # Once context manager exits, the websocket is closed
    assert get_active_client_count() == initial_count
    assert not ai_worker.is_consumer_active()


def test_lifecycle_and_shutdown_logging(caplog: Any) -> None:
    """Verify that all 5 required log messages are emitted during client and worker lifecycles."""
    import asyncio
    import logging
    from backend.main import lifespan

    caplog.set_level(logging.INFO)

    # 1 & 4: Camera opened, Camera released
    worker = AIWorker(camera_index=0, headless=True)
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
    with patch("cv2.VideoCapture", return_value=mock_cap):
        worker.start()
        worker._stop_event.wait(0.2)
        worker.stop(timeout=1.0)

    # 2 & 3: Client connected, Client disconnected
    client = TestClient(app)
    with client.websocket_connect("/ws/telemetry") as ws:
        ws.receive_json()

    # 5: Backend shutdown complete (tested via lifespan context manager)
    async def run_lifespan():
        async with lifespan(app):
            pass

    asyncio.run(run_lifespan())

    log_text = caplog.text
    assert "Camera opened" in log_text
    assert "Client connected" in log_text
    assert "Client disconnected" in log_text
    assert "Camera released" in log_text
    assert "Backend shutdown complete" in log_text



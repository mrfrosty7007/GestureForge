"""Tests for GestureForge Backend Endpoints.

Validates:
- GET /
- GET /health
- POST /gesture (single-hand, multi-hand, and legacy payloads)
- GET /gesture/latest (empty, single-hand, and two-hand states)
- GestureStorage thread-safe multi-hand retrieval
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models import GesturePrediction, HandGesture
from backend.routes import health_check, manager, video_manager
from backend.storage import storage


@pytest.fixture(autouse=True)
def reset_storage():
    """Ensure in-memory storage is cleared before each test."""
    storage.clear()
    video_manager._latest_frame = None
    yield
    storage.clear()
    video_manager._latest_frame = None


def test_health_check_function_direct() -> None:
    """Unit test for the health_check route function directly."""
    response = health_check()
    assert isinstance(response, dict)
    assert response["service"] == "GestureForge Backend"
    assert response["status"] in ("ok", "degraded")
    assert "camera" in response
    assert "ai_worker" in response
    assert "video_stream" in response
    assert "telemetry" in response


def test_health_check_via_testclient() -> None:
    """Integration test invoking GET /health through FastAPI TestClient."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "GestureForge Backend"
    assert data["status"] in ("ok", "degraded")
    assert "camera" in data
    assert "ai_worker" in data
    assert "video_stream" in data
    assert "telemetry" in data


def test_root_endpoint_via_testclient() -> None:
    """Integration test invoking GET / through FastAPI TestClient."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data == {
        "project": "GestureForge Backend",
        "status": "running",
    }


def test_get_latest_gesture_empty() -> None:
    """Test GET /gesture/latest returns a clean JSON message when empty."""
    client = TestClient(app)
    response = client.get("/gesture/latest")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "empty"
    assert data["gesture"] is None
    assert data["hands"] == []
    assert "No gestures recorded yet" in data["message"]


def test_post_gesture_and_retrieve_latest() -> None:
    """Test POST /gesture stores legacy single-hand prediction and GET /gesture/latest retrieves it."""
    client = TestClient(app)
    payload = {
        "gesture": "Peace",
        "confidence": "High",
        "timestamp": "2026-09-07T17:50:00Z",
    }

    # Ingest prediction
    post_res = client.post("/gesture", json=payload)
    assert post_res.status_code == 200
    post_data = post_res.json()
    assert post_data["status"] == "received"
    assert post_data["gesture"] == "Peace"
    assert len(post_data["hands"]) == 1
    assert post_data["hands"][0]["gesture"] == "Peace"
    assert post_data["hands"][0]["confidence"] == "High"

    # Retrieve latest
    get_res = client.get("/gesture/latest")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["status"] == "success"
    assert get_data["gesture"] == "Peace"
    assert get_data["confidence"] == "High"
    assert get_data["timestamp"] == "2026-09-07T17:50:00Z"
    assert get_data["message"] is None
    assert len(get_data["hands"]) == 1
    assert get_data["hands"][0]["id"] == 0
    assert get_data["hands"][0]["gesture"] == "Peace"


def test_post_multi_hand_two_hands() -> None:
    """Test POST /gesture accepts a two-hand payload and GET /gesture/latest returns both hands."""
    client = TestClient(app)
    payload = {
        "hands": [
            {
                "id": 0,
                "label": "Right",
                "gesture": "Peace",
                "confidence": "High",
            },
            {
                "id": 1,
                "label": "Left",
                "gesture": "Palm",
                "confidence": "Medium",
            },
        ],
        "timestamp": 1725700000,
    }

    post_res = client.post("/gesture", json=payload)
    assert post_res.status_code == 200
    post_data = post_res.json()
    assert post_data["status"] == "received"
    assert post_data["gesture"] == "Peace"
    assert len(post_data["hands"]) == 2
    assert post_data["hands"][0]["label"] == "Right"
    assert post_data["hands"][0]["gesture"] == "Peace"
    assert post_data["hands"][1]["label"] == "Left"
    assert post_data["hands"][1]["gesture"] == "Palm"

    get_res = client.get("/gesture/latest")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["status"] == "success"
    assert get_data["gesture"] == "Peace"
    assert get_data["confidence"] == "High"
    assert get_data["timestamp"] == 1725700000
    assert len(get_data["hands"]) == 2
    assert get_data["hands"][0]["id"] == 0
    assert get_data["hands"][0]["label"] == "Right"
    assert get_data["hands"][0]["gesture"] == "Peace"
    assert get_data["hands"][0]["confidence"] == "High"
    assert get_data["hands"][1]["id"] == 1
    assert get_data["hands"][1]["label"] == "Left"
    assert get_data["hands"][1]["gesture"] == "Palm"
    assert get_data["hands"][1]["confidence"] == "Medium"


def test_post_multi_hand_single_hand() -> None:
    """Test POST /gesture with a single hand in the 'hands' list."""
    client = TestClient(app)
    payload = {
        "hands": [
            {
                "id": 0,
                "label": "Left",
                "gesture": "Thumbs Up",
                "confidence": "High",
            }
        ],
        "timestamp": "2026-09-07T18:00:00Z",
    }

    post_res = client.post("/gesture", json=payload)
    assert post_res.status_code == 200
    post_data = post_res.json()
    assert len(post_data["hands"]) == 1
    assert post_data["gesture"] == "Thumbs Up"

    get_res = client.get("/gesture/latest")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["gesture"] == "Thumbs Up"
    assert len(get_data["hands"]) == 1
    assert get_data["hands"][0]["label"] == "Left"


def test_storage_stores_and_returns_both_hands() -> None:
    """Directly verifies GestureStorage stores multi-hand predictions and returns both hands."""
    hands = [
        HandGesture(id=0, label="Right", gesture="Fist", confidence="High"),
        HandGesture(id=1, label="Left", gesture="One Finger", confidence="Medium"),
    ]
    prediction = GesturePrediction(
        hands=hands,
        timestamp=1725701234,
    )
    storage.set_latest_gesture(prediction)

    retrieved = storage.get_latest_gesture()
    assert retrieved is not None
    assert len(retrieved.hands) == 2
    assert retrieved.hands[0].gesture == "Fist"
    assert retrieved.hands[1].gesture == "One Finger"

    hands_list = storage.get_latest_hands()
    assert len(hands_list) == 2
    assert hands_list[0].id == 0
    assert hands_list[0].label == "Right"
    assert hands_list[1].id == 1
    assert hands_list[1].label == "Left"


def test_post_gesture_invalid_payload() -> None:
    """Test POST /gesture rejects invalid payloads missing required fields."""
    client = TestClient(app)
    # Missing confidence and timestamp
    invalid_payload = {"gesture": "Fist"}
    response = client.post("/gesture", json=invalid_payload)
    assert response.status_code == 422

    # Empty hands list and no gesture/confidence
    empty_hands_payload = {"hands": [], "timestamp": 1725700000}
    response2 = client.post("/gesture", json=empty_hands_payload)
    assert response2.status_code == 422


def test_websocket_telemetry_initial_empty() -> None:
    """Test WebSocket /ws/telemetry connects and immediately receives empty initial state."""
    client = TestClient(app)
    with client.websocket_connect("/ws/telemetry") as ws:
        data = ws.receive_json()
        assert data["status"] == "empty"
        assert data["gesture"] is None
        assert data["hands"] == []
        assert "No gestures recorded yet" in data["message"]


def test_websocket_telemetry_initial_populated() -> None:
    """Test WebSocket /ws/telemetry receives current gesture if already stored."""
    # Pre-populate storage
    hands = [HandGesture(id=0, label="Right", gesture="Rock", confidence="High")]
    storage.set_latest_gesture(GesturePrediction(hands=hands, timestamp=1725705000))

    client = TestClient(app)
    with client.websocket_connect("/ws/telemetry") as ws:
        data = ws.receive_json()
        assert data["status"] == "success"
        assert data["gesture"] == "Rock"
        assert len(data["hands"]) == 1
        assert data["hands"][0]["gesture"] == "Rock"


def test_websocket_broadcast_after_post_gesture() -> None:
    """Test POST /gesture broadcasts new multi-hand telemetry to active WebSocket clients."""
    client = TestClient(app)
    with client.websocket_connect("/ws/telemetry") as ws:
        # Initial message on connect
        init_data = ws.receive_json()
        assert init_data["status"] == "empty"

        # Now send a POST request with two hands
        payload = {
            "hands": [
                {
                    "id": 0,
                    "label": "Right",
                    "gesture": "Peace",
                    "confidence": "High",
                },
                {
                    "id": 1,
                    "label": "Left",
                    "gesture": "Open_Palm",
                    "confidence": "Medium",
                },
            ],
            "timestamp": 1725709999,
        }
        res = client.post("/gesture", json=payload)
        assert res.status_code == 200

        # WebSocket should receive the broadcast immediately
        broadcast_data = ws.receive_json()
        assert broadcast_data["status"] == "success"
        assert broadcast_data["gesture"] == "Peace"
        assert len(broadcast_data["hands"]) == 2
        assert broadcast_data["hands"][0]["gesture"] == "Peace"
        assert broadcast_data["hands"][1]["gesture"] == "Open_Palm"
        assert broadcast_data["timestamp"] == 1725709999


def test_websocket_ping_pong() -> None:
    """Test sending ping over WebSocket receives pong heartbeat response."""
    client = TestClient(app)
    with client.websocket_connect("/ws/telemetry") as ws:
        # Consume initial state
        ws.receive_json()

        # Send heartbeat ping
        ws.send_text("ping")
        reply = ws.receive_text()
        assert reply == "pong"


def test_websocket_disconnect_cleanup() -> None:
    """Test client disconnection cleanly removes the connection from ConnectionManager."""
    client = TestClient(app)
    initial_count = len(manager.active_connections)

    with client.websocket_connect("/ws/telemetry") as ws:
        assert len(manager.active_connections) == initial_count + 1
        # Read initial message
        ws.receive_json()

    # Once context manager exits, client has disconnected
    assert len(manager.active_connections) == initial_count


def test_post_gesture_with_hardware_telemetry() -> None:
    """Test POST /gesture accepts hardware telemetry and GET /gesture/latest returns it."""
    client = TestClient(app)
    payload = {
        "hands": [
            {
                "id": 0,
                "label": "Right",
                "gesture": "Peace",
                "confidence": "High",
            },
            {
                "id": 1,
                "label": "Left",
                "gesture": "Palm",
                "confidence": "Medium",
            },
        ],
        "timestamp": 1725700000,
        "telemetry": {
            "fps": 31.4,
            "latency_ms": 18.2,
            "frame_timestamp": 1725700000.24,
            "frame": 5234,
            "hand_count": 2,
        },
    }

    post_res = client.post("/gesture", json=payload)
    assert post_res.status_code == 200

    get_res = client.get("/gesture/latest")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["status"] == "success"
    assert data["telemetry"] is not None
    assert data["telemetry"]["fps"] == 31.4
    assert data["telemetry"]["latency_ms"] == 18.2
    assert data["telemetry"]["frame"] == 5234
    assert data["telemetry"]["hand_count"] == 2


def test_websocket_broadcast_hardware_telemetry() -> None:
    """Test WebSocket receives real-time broadcast of hardware telemetry."""
    client = TestClient(app)
    with client.websocket_connect("/ws/telemetry") as ws:
        # Initial message
        ws.receive_json()

        payload = {
            "hands": [
                {
                    "id": 0,
                    "label": "Right",
                    "gesture": "Thumbs Up",
                    "confidence": "High",
                }
            ],
            "timestamp": 1725705555,
            "telemetry": {
                "fps": 59.8,
                "latency_ms": 14.1,
                "frame_timestamp": 1725705555.12,
                "frame": 8901,
                "hand_count": 1,
            },
        }
        res = client.post("/gesture", json=payload)
        assert res.status_code == 200

        data = ws.receive_json()
        assert data["status"] == "success"
        assert data["telemetry"] is not None
        assert data["telemetry"]["fps"] == 59.8
        assert data["telemetry"]["latency_ms"] == 14.1
        assert data["telemetry"]["frame"] == 8901
        assert data["telemetry"]["hand_count"] == 1


def test_post_gesture_telemetry_heartbeat_zero_hands() -> None:
    """Test POST /gesture with telemetry and zero hands is accepted as telemetry heartbeat."""
    client = TestClient(app)
    payload = {
        "hands": [],
        "timestamp": 1725709999,
        "telemetry": {
            "fps": 29.5,
            "latency_ms": 11.2,
            "frame_timestamp": 1725709999.5,
            "frame": 120,
            "hand_count": 0,
        },
    }

    res = client.post("/gesture", json=payload)
    assert res.status_code == 200

    get_res = client.get("/gesture/latest")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["status"] == "success"
    assert data["gesture"] == "None"
    assert data["hands"] == []
    assert data["telemetry"]["fps"] == 29.5
    assert data["telemetry"]["hand_count"] == 0


def test_websocket_video_connect_and_ping() -> None:
    """Test WebSocket /ws/video connects, tracks connection, and responds to ping."""
    client = TestClient(app)
    initial_count = len(video_manager.active_connections)

    with client.websocket_connect("/ws/video") as ws:
        assert len(video_manager.active_connections) == initial_count + 1
        ws.send_text("ping")
        reply = ws.receive_text()
        assert reply == "pong"

    assert len(video_manager.active_connections) == initial_count


def test_websocket_video_frame_broadcast() -> None:
    """Test publisher sends binary JPEG frame and subscriber receives it."""
    client = TestClient(app)
    fake_jpeg = (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00\x60\x00\x60\x00\x00\xff\xdb"
    )

    with (
        client.websocket_connect("/ws/video") as sub,
        client.websocket_connect("/ws/video") as pub,
    ):
        # Publisher sends binary bytes
        pub.send_bytes(fake_jpeg)

        # Subscriber receives binary bytes
        received = sub.receive_bytes()
        assert received == fake_jpeg


def test_websocket_video_cached_frame_on_connect() -> None:
    """Test newly connected viewer receives cached latest frame immediately."""
    client = TestClient(app)
    cached_frame = b"\xff\xd8\xff\xe0\xaa\xbb\xcc"
    video_manager._latest_frame = cached_frame

    with client.websocket_connect("/ws/video") as ws:
        received = ws.receive_bytes()
        assert received == cached_frame


def test_video_manager_replaces_cached_frame() -> None:
    """Test that publishing a new frame replaces the cached frame immediately."""
    first_frame = b"first-jpeg"
    latest_frame = b"latest-jpeg"

    async def publish_frames() -> None:
        await video_manager.broadcast_frame(first_frame)
        await video_manager.broadcast_frame(latest_frame)

    import asyncio

    asyncio.run(publish_frames())
    assert video_manager._latest_frame == latest_frame


def test_websocket_video_refresh_returns_latest_frame() -> None:
    """Test that a viewer can request a fresh frame after visibility restoration."""
    latest_frame = b"latest-after-refresh"
    video_manager._latest_frame = latest_frame
    client = TestClient(app)

    with client.websocket_connect("/ws/video") as ws:
        ws.send_text("refresh")
        assert ws.receive_bytes() == latest_frame

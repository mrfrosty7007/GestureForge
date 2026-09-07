"""Tests for GestureForge Backend Endpoints.

Validates:
- GET /
- GET /health
- POST /gesture (single-hand, multi-hand, and legacy payloads)
- GET /gesture/latest (empty, single-hand, and two-hand states)
- GestureStorage thread-safe multi-hand retrieval
"""

import sys
from pathlib import Path

# Ensure backend directory is in sys.path when running pytest or direct execution
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402
from models import GesturePrediction, HandGesture  # noqa: E402
from routes import health_check  # noqa: E402
from storage import storage  # noqa: E402


@pytest.fixture(autouse=True)
def reset_storage():
    """Ensure in-memory storage is cleared before each test."""
    storage.clear()
    yield
    storage.clear()


def test_health_check_function_direct() -> None:
    """Unit test for the health_check route function directly."""
    response = health_check()
    assert isinstance(response, dict)
    assert response["status"] == "ok"
    assert response["service"] == "GestureForge Backend"


def test_health_check_via_testclient() -> None:
    """Integration test invoking GET /health through FastAPI TestClient."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {
        "status": "ok",
        "service": "GestureForge Backend",
    }


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

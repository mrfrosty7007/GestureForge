"""Tests for GestureForge Backend Endpoints.

Validates:
- GET /
- GET /health
- POST /gesture
- GET /gesture/latest (empty and populated states)
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
    assert "No gestures recorded yet" in data["message"]


def test_post_gesture_and_retrieve_latest() -> None:
    """Test POST /gesture stores the prediction and GET /gesture/latest retrieves it."""
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
    assert post_data == {
        "status": "received",
        "gesture": "Peace",
    }

    # Retrieve latest
    get_res = client.get("/gesture/latest")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data == {
        "status": "success",
        "gesture": "Peace",
        "confidence": "High",
        "timestamp": "2026-09-07T17:50:00Z",
        "message": None,
    }


def test_post_gesture_invalid_payload() -> None:
    """Test POST /gesture rejects invalid payloads missing required fields."""
    client = TestClient(app)
    invalid_payload = {"gesture": "Fist"}  # missing confidence and timestamp
    response = client.post("/gesture", json=invalid_payload)
    assert response.status_code == 422

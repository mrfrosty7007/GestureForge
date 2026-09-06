"""Tests for GestureForge Health and Gateway Endpoints.

Validates that the FastAPI application initializes properly and returns
the expected status response conforming to the project specification.
"""

import sys
from pathlib import Path

# Ensure backend directory is in sys.path when running script directly
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402
from routes import health_check  # noqa: E402


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
    assert "message" in data
    assert data["service"] == "GestureForge Backend"


if __name__ == "__main__":
    test_health_check_function_direct()
    test_health_check_via_testclient()
    print("Health check tests passed directly!")

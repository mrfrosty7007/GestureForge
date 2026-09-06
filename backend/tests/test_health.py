"""Tests for GestureForge Health and Gateway Endpoints.

Validates that the FastAPI application initializes properly and returns
the expected status response conforming to the Phase 0 specification.
"""

import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    import pytest
except ImportError:
    pytest = None

from app import app
from routes.health import health_check


def test_health_check_function_direct():
    """Unit test for the health_check route function directly."""
    response = health_check()
    assert isinstance(response, dict)
    assert response["status"] == "ok"
    assert response["service"] == "GestureForge Backend"


def test_health_check_via_testclient():
    """Integration test invoking GET /health through FastAPI TestClient."""
    try:
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data == {
            "status": "ok",
            "service": "GestureForge Backend",
        }
    except ImportError:
        if pytest:
            pytest.skip("httpx or testclient not installed in current environment")
        return


def test_root_endpoint_via_testclient():
    """Integration test invoking GET / through FastAPI TestClient."""
    try:
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["service"] == "GestureForge Backend"
    except ImportError:
        if pytest:
            pytest.skip("httpx or testclient not installed in current environment")
        return


if __name__ == "__main__":
    test_health_check_function_direct()
    print("Health check tests passed directly!")

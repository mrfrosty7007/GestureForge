"""Health Check Endpoint.

Exposes a lightweight route to verify that the FastAPI backend is operational
and responsive to incoming client requests.
"""

from fastapi import APIRouter
from config import SERVICE_NAME

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check() -> dict:
    """Return backend operational status.

    Response format satisfies Phase 0 project specification:
    {
        "status": "ok",
        "service": "GestureForge Backend"
    }
    """
    return {
        "status": "ok",
        "service": SERVICE_NAME,
    }

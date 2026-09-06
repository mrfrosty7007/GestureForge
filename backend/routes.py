"""API routes for GestureForge backend."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check():
    """Health check endpoint confirming backend service status."""
    return {
        "status": "ok",
        "service": "GestureForge Backend",
    }

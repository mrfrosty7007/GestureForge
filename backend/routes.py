"""API routes for GestureForge backend.

Provides endpoints for service health, root status, gesture ingestion,
and polling the latest detected gesture.
"""

from fastapi import APIRouter

from models import (
    GesturePrediction,
    GestureReceiptResponse,
    HealthResponse,
    LatestGestureResponse,
)
from storage import storage

router = APIRouter()


@router.get("/", tags=["Status"])
def root_status() -> dict:
    """Root status endpoint returning service identity and operational state."""
    return {
        "project": "GestureForge Backend",
        "status": "running",
    }


@router.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check() -> dict:
    """Health check endpoint confirming backend service readiness."""
    return {
        "status": "ok",
        "service": "GestureForge Backend",
    }


@router.post("/gesture", response_model=GestureReceiptResponse, tags=["Gestures"])
def ingest_gesture(prediction: GesturePrediction) -> dict:
    """Receives and stores the latest gesture prediction from the AI module."""
    storage.set_latest_gesture(prediction)
    return {
        "status": "received",
        "gesture": prediction.gesture,
        "hands": prediction.hands,
    }


@router.get("/gesture/latest", response_model=LatestGestureResponse, tags=["Gestures"])
def get_latest_gesture() -> dict:
    """Retrieves the most recently received gesture prediction.

    If no gesture has been ingested yet, returns a clean JSON message instead of crashing.
    """
    latest = storage.get_latest_gesture()
    if latest is None:
        return {
            "status": "empty",
            "message": "No gestures recorded yet",
            "hands": [],
            "gesture": None,
            "confidence": None,
            "timestamp": None,
        }

    return {
        "status": "success",
        "hands": latest.hands,
        "gesture": latest.gesture,
        "confidence": latest.confidence,
        "timestamp": latest.timestamp,
        "message": None,
    }

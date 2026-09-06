"""Data models and schemas for GestureForge."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    service: str


class GesturePrediction(BaseModel):
    """Gesture prediction result schema."""

    gesture: str
    confidence: float

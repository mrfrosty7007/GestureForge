"""Data models and schemas for GestureForge backend."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = "ok"
    service: str = "GestureForge Backend"


class GesturePrediction(BaseModel):
    """Payload schema for an incoming gesture prediction."""

    gesture: str = Field(
        ..., description="Name of the recognized gesture (e.g. Peace, Fist, Palm)"
    )
    confidence: str = Field(
        ..., description="Confidence level (e.g. High, Medium, Low)"
    )
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp of detection")


class GestureReceiptResponse(BaseModel):
    """Response schema returned after ingesting a gesture."""

    status: str = "received"
    gesture: str


class LatestGestureResponse(BaseModel):
    """Response schema for the most recently detected gesture."""

    status: str
    gesture: str | None = None
    confidence: str | None = None
    timestamp: str | None = None
    message: str | None = None

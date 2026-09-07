"""Data models and schemas for GestureForge backend."""

from typing import Any

from pydantic import BaseModel, Field, model_validator


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = "ok"
    service: str = "GestureForge Backend"
    camera: str = "active"
    ai_worker: str = "running"
    video_stream: str = "active"
    telemetry: str = "active"


class HandGesture(BaseModel):
    """Schema for a single detected hand gesture."""

    id: int = Field(
        ...,
        description="Hand identifier index (0 for primary, 1 for secondary)",
    )
    label: str = Field(
        default="Unknown",
        description="Handedness label ('Left', 'Right', 'Unknown')",
    )
    gesture: str = Field(
        ...,
        description="Recognized gesture name (e.g. Peace, Fist, Palm)",
    )
    confidence: str = Field(
        ...,
        description="Confidence tier (High, Medium, Low)",
    )


class HardwareTelemetry(BaseModel):
    """Real-time hardware performance & inference metrics."""

    fps: float = Field(
        default=0.0,
        description="Actual camera FPS measured from frame capture loop",
    )
    latency_ms: float = Field(
        default=0.0,
        description="MediaPipe inference latency in milliseconds",
    )
    frame_timestamp: float | None = Field(
        default=None,
        description="Precise frame capture timestamp in epoch seconds",
    )
    frame: int | None = Field(
        default=None,
        description="Monotonically increasing frame sequence number",
    )
    hand_count: int = Field(
        default=0,
        description="Number of hands detected in the frame",
    )


class GesturePrediction(BaseModel):
    """Payload schema for an incoming gesture prediction.

    Supports both multi-hand payloads (hands: list[HandGesture]) and legacy
    single-hand payloads (gesture + confidence) for backward compatibility,
    along with hardware telemetry streaming.
    """

    hands: list[HandGesture] = Field(
        default_factory=list,
        description="List of detected hand gestures",
    )
    timestamp: str | int | float = Field(
        ...,
        description="Timestamp of detection (ISO 8601 string or numeric epoch)",
    )
    gesture: str | None = Field(
        default=None,
        description="Primary recognized gesture name (backward compatibility)",
    )
    confidence: str | None = Field(
        default=None,
        description="Primary confidence level (backward compatibility)",
    )
    telemetry: HardwareTelemetry | None = Field(
        default=None,
        description="Real-time hardware performance and MediaPipe inference telemetry",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_and_normalize(cls, data: Any) -> Any:
        """Validates payload structure and normalizes single/multi-hand representations."""
        if not isinstance(data, dict):
            return data

        raw_hands = data.get("hands")
        raw_gesture = data.get("gesture")
        raw_confidence = data.get("confidence")
        raw_telemetry = data.get("telemetry")

        # Multi-hand payload provided with hands
        if raw_hands is not None and isinstance(raw_hands, list) and len(raw_hands) > 0:
            primary = raw_hands[0]
            if isinstance(primary, dict):
                if not raw_gesture:
                    data["gesture"] = primary.get("gesture")
                if not raw_confidence:
                    data["confidence"] = primary.get("confidence")
            elif isinstance(primary, HandGesture):
                if not raw_gesture:
                    data["gesture"] = primary.gesture
                if not raw_confidence:
                    data["confidence"] = primary.confidence
            return data

        # Legacy single-hand payload provided
        if raw_gesture and raw_confidence:
            data["hands"] = [
                {
                    "id": 0,
                    "label": data.get("label", "Unknown"),
                    "gesture": raw_gesture,
                    "confidence": raw_confidence,
                }
            ]
            return data

        # Telemetry heartbeat payload (e.g. camera active with 0 hands in frame)
        if raw_telemetry is not None:
            data["hands"] = []
            data["gesture"] = data.get("gesture") or "None"
            data["confidence"] = data.get("confidence") or "N/A"
            return data

        # Neither valid hands, gesture+confidence, nor telemetry was provided
        raise ValueError(
            "Payload must contain either a non-empty 'hands' list, 'gesture' and 'confidence', or 'telemetry'."
        )


class GestureReceiptResponse(BaseModel):
    """Response schema returned after ingesting a gesture."""

    status: str = "received"
    gesture: str | None = None
    hands: list[HandGesture] = Field(default_factory=list)


class LatestGestureResponse(BaseModel):
    """Response schema for the most recently detected gesture."""

    status: str
    hands: list[HandGesture] = Field(default_factory=list)
    gesture: str | None = None
    confidence: str | None = None
    timestamp: str | int | float | None = None
    telemetry: HardwareTelemetry | None = None
    message: str | None = None

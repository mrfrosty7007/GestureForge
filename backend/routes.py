"""API routes for GestureForge backend.

Provides endpoints for service health, root status, gesture ingestion,
polling the latest detected gesture, and real-time WebSocket telemetry streaming.
"""

import contextlib
import logging
import threading
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .models import (
    GesturePrediction,
    GestureReceiptResponse,
    HealthResponse,
    LatestGestureResponse,
)
from .storage import storage
from .worker import ai_worker

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts telemetry updates."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accepts a new WebSocket connection and registers it."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            "WebSocket client connected. Active connections: %d",
            len(self.active_connections),
        )

    def disconnect(self, websocket: WebSocket) -> None:
        """Safely removes a disconnected WebSocket client."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(
                "WebSocket client disconnected. Active connections: %d",
                len(self.active_connections),
            )

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcasts a JSON message to all active WebSocket clients.

        Safely purges any stale or abruptly disconnected clients.
        """
        dead_connections: list[WebSocket] = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as exc:
                logger.warning("Failed to send to WebSocket client: %s", exc)
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)


# Global singleton connection manager for telemetry broadcast
manager = ConnectionManager()


class VideoStreamManager:
    """Manages active WebSocket connections for binary video streaming."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []
        self._frame_lock = threading.Lock()
        self._latest_frame: bytes | None = None
        self._broadcasting = False

    async def connect(self, websocket: WebSocket) -> None:
        """Accepts a new WebSocket connection and registers it."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            "Video WebSocket client connected. Active connections: %d",
            len(self.active_connections),
        )
        with self._frame_lock:
            latest_frame = self._latest_frame
        if latest_frame is not None:
            with contextlib.suppress(Exception):
                await websocket.send_bytes(latest_frame)

    def disconnect(self, websocket: WebSocket) -> None:
        """Safely removes a disconnected WebSocket client."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(
                "Video WebSocket client disconnected. Active connections: %d",
                len(self.active_connections),
            )

    async def broadcast_frame(
        self, frame_bytes: bytes, sender: WebSocket | None = None
    ) -> None:
        """Broadcasts only the newest JPEG, coalescing concurrent frame updates."""
        with self._frame_lock:
            self._latest_frame = frame_bytes

        if self._broadcasting:
            return

        self._broadcasting = True
        try:
            while True:
                with self._frame_lock:
                    frame_to_send = self._latest_frame
                dead_connections: list[WebSocket] = []
                for connection in list(self.active_connections):
                    if connection is sender:
                        continue
                    try:
                        await connection.send_bytes(frame_to_send)
                    except Exception as exc:
                        logger.warning(
                            "Failed to send frame to WebSocket client: %s", exc
                        )
                        dead_connections.append(connection)

                for dead in dead_connections:
                    self.disconnect(dead)

                with self._frame_lock:
                    if self._latest_frame is frame_to_send:
                        break
        finally:
            self._broadcasting = False


# Global singleton video stream manager
video_manager = VideoStreamManager()


@router.get("/", tags=["Status"])
def root_status() -> dict:
    """Root status endpoint returning service identity and operational state."""
    return {
        "project": "GestureForge Backend",
        "status": "running",
    }


@router.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check() -> dict:
    """Health check endpoint confirming backend service readiness and AI worker state."""
    worker_status = ai_worker.worker_status
    camera_status = ai_worker.camera_status
    is_healthy = worker_status == "running" and camera_status == "active"

    return {
        "status": "ok" if is_healthy else "degraded",
        "service": "GestureForge Backend",
        "camera": camera_status,
        "ai_worker": worker_status,
        "video_stream": "active",
        "telemetry": "active",
    }


@router.post("/gesture", response_model=GestureReceiptResponse, tags=["Gestures"])
async def ingest_gesture(prediction: GesturePrediction) -> dict:
    """Receives, stores, and immediately broadcasts the latest gesture prediction."""
    storage.set_latest_gesture(prediction)

    broadcast_payload = {
        "status": "success",
        "hands": [h.model_dump() for h in prediction.hands],
        "gesture": prediction.gesture,
        "confidence": prediction.confidence,
        "timestamp": prediction.timestamp,
        "telemetry": (
            prediction.telemetry.model_dump() if prediction.telemetry else None
        ),
        "message": None,
    }
    await manager.broadcast(broadcast_payload)

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
            "telemetry": None,
        }

    return {
        "status": "success",
        "hands": latest.hands,
        "gesture": latest.gesture,
        "confidence": latest.confidence,
        "timestamp": latest.timestamp,
        "telemetry": latest.telemetry,
        "message": None,
    }


@router.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket) -> None:
    """Real-time WebSocket telemetry endpoint.

    Streams immediate gesture prediction events to connected HUD dashboards.
    Sends current state immediately upon connection, then listens for heartbeat pings.
    """
    await manager.connect(websocket)

    # Immediately emit current latest state upon connection
    latest = storage.get_latest_gesture()
    if latest is not None:
        initial_payload = {
            "status": "success",
            "hands": [h.model_dump() for h in latest.hands],
            "gesture": latest.gesture,
            "confidence": latest.confidence,
            "timestamp": latest.timestamp,
            "telemetry": (latest.telemetry.model_dump() if latest.telemetry else None),
            "message": None,
        }
    else:
        initial_payload = {
            "status": "empty",
            "message": "No gestures recorded yet",
            "hands": [],
            "gesture": None,
            "confidence": None,
            "timestamp": None,
            "telemetry": None,
        }

    try:
        await websocket.send_json(initial_payload)
        while True:
            # Keep connection open; receive client heartbeats / ping
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        logger.warning("WebSocket error encountered: %s", exc)
        manager.disconnect(websocket)


@router.websocket("/ws/video")
async def websocket_video(websocket: WebSocket) -> None:
    """Real-time binary video streaming endpoint.

    Accepts binary JPEG frames from publisher clients (AI vision pipeline)
    and broadcasts them to all connected subscriber clients (React HUD).
    """
    await video_manager.connect(websocket)
    try:
        while True:
            message = await websocket.receive()
            if "bytes" in message and message["bytes"]:
                await video_manager.broadcast_frame(message["bytes"], sender=websocket)
            elif "text" in message:
                if message["text"] == "ping":
                    await websocket.send_text("pong")
                elif message["text"] in ("frame", "refresh"):
                    with video_manager._frame_lock:
                        latest_frame = video_manager._latest_frame
                    if latest_frame is not None:
                        await websocket.send_bytes(latest_frame)
    except WebSocketDisconnect:
        video_manager.disconnect(websocket)
    except Exception as exc:
        logger.warning("Video WebSocket error encountered: %s", exc)
        video_manager.disconnect(websocket)

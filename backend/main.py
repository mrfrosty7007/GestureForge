"""Main entry point for GestureForge FastAPI backend.

Configures CORS, registers API routers, manages the background AI worker lifespan,
and provides Swagger documentation.
"""

import asyncio
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .models import GesturePrediction
from .routes import manager, router, video_manager
from .storage import storage
from .worker import ai_worker

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """FastAPI lifespan context manager starting and stopping the AI perception worker."""
    loop = asyncio.get_running_loop()

    def on_gesture_dispatch(payload_dict: dict[str, Any]) -> None:
        """In-process thread-safe gesture telemetry dispatch to FastAPI storage and WebSockets."""
        try:
            prediction = GesturePrediction.model_validate(payload_dict)
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
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    manager.broadcast(broadcast_payload), loop
                )
        except Exception as exc:
            logger.debug("Error during in-process gesture dispatch: %s", exc)

    def on_frame_dispatch(frame_bytes: bytes) -> None:
        """In-process thread-safe video frame dispatch to FastAPI video WebSocket subscribers."""
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(
                video_manager.broadcast_frame(frame_bytes), loop
            )

    # Allow disabling auto-start if explicitly requested via environment variable
    auto_start = os.getenv("GESTUREFORGE_DISABLE_AI_WORKER", "").lower() not in (
        "1",
        "true",
        "yes",
    )

    if auto_start:
        logger.info("Initializing and starting headless AI perception worker...")
        ai_worker.configure(
            on_gesture=on_gesture_dispatch,
            on_frame=on_frame_dispatch,
        )
        ai_worker.start()

    yield

    # Clean shutdown on application exit
    if ai_worker.is_running():
        logger.info("Stopping AI perception worker cleanly...")
        ai_worker.stop()


app = FastAPI(
    title="GestureForge Backend",
    description="Lightweight FastAPI gateway for GestureForge real-time gesture telemetry",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Enable CORS to allow the local frontend (Vite/React) to connect seamlessly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(router)

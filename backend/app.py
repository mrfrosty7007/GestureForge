"""GestureForge Backend Application Entry Point.

This module sets up the FastAPI application with structured logging,
CORS middleware for cross-origin communication with the React frontend,
and registers core API routers.

Development Execution:
    uvicorn app:app --reload --host 127.0.0.1 --port 8000
    or using uv:
    uv run uvicorn app:app --reload
"""

import logging
import sys
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

import config
from routes.health import router as health_router

# ----------------------------------------------------------------------
# Structured Logging Configuration
# ----------------------------------------------------------------------
log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format=log_format,
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("gestureforge.gateway")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for startup and shutdown logging."""
    logger.info("Initializing %s (%s)", config.SERVICE_NAME, config.API_VERSION)
    logger.info("Server bound to %s:%s", config.HOST, config.PORT)
    logger.info("Active CORS Origins: %s", config.CORS_ORIGINS)
    yield
    logger.info("Shutting down %s", config.SERVICE_NAME)


# Initialize FastAPI Application
app = FastAPI(
    title="GestureForge API",
    description="Real-time AI-Powered Hand Gesture Recognition Engine Backend",
    version=config.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Structured request logging middleware."""
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
    logger.info(
        "%s %s -> %s (%sms)",
        request.method,
        request.url.path,
        response.status_code,
        process_time_ms,
    )
    return response


# Register Core Routers
app.include_router(health_router)


@app.get("/")
def root_status() -> dict:
    """Root endpoint welcoming developers and confirming API gateway health."""
    return {
        "message": "Welcome to GestureForge API Gateway",
        "service": config.SERVICE_NAME,
        "version": config.API_VERSION,
        "phase": "Phase 0 (Foundation & Planning)",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
        },
    }


# ============================================================================
# Phase 1 & 2 Planned Routes Scaffolding
# ============================================================================
# TODO (Phase 1 - Member 1 & 2): Mount WebSocket route for real-time video frame streaming
# @app.websocket("/ws/gesture")
# async def websocket_gesture_stream(websocket: WebSocket): ...

# TODO (Phase 2 - Member 3): Mount REST inference endpoint for single-frame classification
# @app.post("/api/gesture/classify")
# async def classify_gesture_endpoint(payload: LandmarkPayload): ...


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower(),
    )

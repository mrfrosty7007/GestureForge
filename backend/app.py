"""GestureForge Backend Application Entry Point.

This module sets up the FastAPI application, mounts CORS middleware to allow
cross-origin communication from the React frontend, and registers API routers.

Development Execution:
    uvicorn app:app --reload --host 127.0.0.1 --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from routes.health import router as health_router

# Initialize FastAPI Application
app = FastAPI(
    title="GestureForge API",
    description="Real-time AI-Powered Hand Gesture Recognition Engine Backend",
    version=config.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure Cross-Origin Resource Sharing (CORS)
# Ensures the React + Vite frontend can communicate without browser blocking
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

    uvicorn.run("app:app", host=config.HOST, port=config.PORT, reload=config.DEBUG)

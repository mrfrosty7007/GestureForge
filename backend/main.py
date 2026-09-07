"""Main entry point for GestureForge FastAPI backend.

Configures CORS, registers API routers, and provides Swagger documentation.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router

app = FastAPI(
    title="GestureForge Backend",
    description="Lightweight FastAPI gateway for GestureForge real-time gesture telemetry",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
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

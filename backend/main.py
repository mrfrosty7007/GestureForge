"""Main entry point for GestureForge FastAPI backend."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import router

app = FastAPI(
    title="GestureForge",
    description="Real-time AI-powered hand gesture recognition backend",
    version="0.1.0",
)

# Enable CORS for frontend dashboard communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def read_root():
    """Root status endpoint."""
    return {
        "message": "GestureForge Backend is running",
        "service": "GestureForge Backend",
    }

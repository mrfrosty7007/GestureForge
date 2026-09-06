"""GestureForge Configuration Module.

Centralizes runtime environment variables, server parameters, and CORS policy
for the FastAPI application.
"""

import os
from pathlib import Path
from typing import List

# Base directories
BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent

# Load local environment variables if python-dotenv is available
try:
    from dotenv import load_dotenv

    env_path = BACKEND_DIR / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()
except ImportError:
    pass

# Server Configuration
HOST: str = os.getenv("HOST", "127.0.0.1")
PORT: int = int(os.getenv("PORT", "8000"))
DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")

# Service Metadata
SERVICE_NAME: str = "GestureForge Backend"
API_VERSION: str = "v0.1.0-phase0"

# CORS Configuration
# Allows React Vite development server (default port 5173) to communicate with FastAPI
DEFAULT_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

raw_origins = os.getenv("CORS_ORIGINS", "")
if raw_origins:
    CORS_ORIGINS: List[str] = [
        origin.strip() for origin in raw_origins.split(",") if origin.strip()
    ]
else:
    CORS_ORIGINS: List[str] = DEFAULT_ORIGINS

"""GestureForge Configuration Module.

Loads and validates runtime environment variables using Pydantic Settings,
centralizing server parameters, logging levels, and CORS origin policy.
"""

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory paths
BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables with strong typing."""

    model_config = SettingsConfigDict(
        env_file=(BACKEND_DIR / ".env", ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server Configuration
    HOST: str = Field(default="127.0.0.1", description="Server host interface")
    PORT: int = Field(default=8000, description="Server port")
    DEBUG: bool = Field(default=True, description="Debug mode")

    # Service Metadata
    SERVICE_NAME: str = Field(
        default="GestureForge Backend", description="Service identifier"
    )
    API_VERSION: str = Field(
        default="v0.1.0-phase0", description="API semantic version"
    )

    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", description="Standard logging level")

    # CORS Configuration
    # Defaults allow React Vite development servers (5173 / 3000)
    CORS_ORIGINS: list[str] | str = Field(
        default=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        description="Allowed origins for Cross-Origin Resource Sharing",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, tuple)):
            return [str(i).strip() for i in v if str(i).strip()]
        return ["http://localhost:5173", "http://127.0.0.1:5173"]


# Instantiate global settings singleton
settings = Settings()

# Backward compatibility exports for direct attribute imports
HOST = settings.HOST
PORT = settings.PORT
DEBUG = settings.DEBUG
SERVICE_NAME = settings.SERVICE_NAME
API_VERSION = settings.API_VERSION
CORS_ORIGINS = settings.CORS_ORIGINS
LOG_LEVEL = settings.LOG_LEVEL

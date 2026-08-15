"""
Application Configuration
Central configuration management using environment variables.
All settings can be overridden via .env file or environment variables.
"""
import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load .env file from project root (3 levels up from this file: core -> app -> backend -> project_root)
_env_path = Path(__file__).resolve().parents[3] / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path)
else:
    # Fallback: try backend/.env
    _backend_env = Path(__file__).resolve().parents[2] / ".env"
    if _backend_env.exists():
        load_dotenv(dotenv_path=_backend_env)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ============================================
    # Application
    # ============================================
    APP_NAME: str = Field(default="AI Workforce OS", description="Application name")
    APP_VERSION: str = Field(default="0.2.0", description="Application version")
    APP_HOST: str = Field(default="0.0.0.0", description="Host to bind")
    APP_PORT: int = Field(default=8000, description="Port to bind")
    APP_DEBUG: bool = Field(default=False, description="Debug mode")

    # ============================================
    # LLM Provider API Keys
    # ============================================
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    OPENAI_MODEL: str = Field(default="gpt-5-mini", description="OpenAI model name")
    GOOGLE_API_KEY: str = Field(default="AQ." + "Ab8RN6I6om9lmHQpmQpNhQfVXbARhztTE_INRfUhh4-Tb3W0mA", description="Google API key")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash", description="Gemini model name")
    DEEPSEEK_API_KEY: str = Field(default="", description="DeepSeek API key")
    DEEPSEEK_MODEL: str = Field(default="deepseek-v4-flash", description="DeepSeek model name (deepseek-v4-flash or deepseek-v4-pro)")
    DEEPSEEK_BASE_URL: str = Field(default="https://api.deepseek.com", description="DeepSeek API base URL")

    # ============================================
    # JWT Authentication
    # ============================================
    JWT_SECRET: str = Field(
        default="",
        description="JWT secret key for token signing",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    JWT_EXPIRATION_HOURS: int = Field(default=24, description="JWT token expiration hours")

    # ============================================
    # Database
    # ============================================
    DATABASE_URL: str = Field(
        default="sqlite:///./ai_workforce.db",
        description="Database connection URL",
    )
    DATABASE_POOL_SIZE: int = Field(default=5, description="Database connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(
        default=10, description="Database max overflow connections"
    )

    # ============================================
    # Voice & Media (TTS)
    # ============================================
    TTS_PROVIDER: str = Field(default="openai", description="TTS provider")
    TTS_VOICE: str = Field(default="alloy", description="TTS voice")
    TTS_MODEL: str = Field(default="tts-1", description="TTS model")
    TTS_SPEED: float = Field(default=1.0, description="TTS playback speed")
    TTS_LANGUAGE: str = Field(default="en-US", description="TTS language")

    # Deepgram TTS
    DEEPGRAM_API_KEY: str = Field(default="", description="Deepgram API key")
    DEEPGRAM_MODEL: str = Field(
        default="aura-asteria-en", description="Deepgram TTS model"
    )

    # ============================================
    # Lip-Sync Settings
    # ============================================
    LIP_SYNC_PROVIDER: str = Field(
        default="did", description="Lip-sync provider (hedra, did, simulated)"
    )
    LIP_SYNC_RESOLUTION: str = Field(
        default="720p", description="Lip-sync resolution (480p, 720p, 1080p)"
    )
    D_ID_API_KEY: str = Field(default="", description="D-ID API key")
    D_ID_BASE_URL: str = Field(
        default="https://api.d-id.com", description="D-ID API base URL"
    )
    HEDRA_API_KEY: str = Field(default="", description="Hedra API key")
    HEDRA_BASE_URL: str = Field(
        default="https://api.hedra.com", description="Hedra API base URL"
    )

    # ============================================
    # Movie Pipeline Settings
    # ============================================
    MOVIES_DIR: str = Field(default="./movies", description="Directory for movie output")
    SCENES_PER_EPISODE: int = Field(
        default=5, description="Number of scenes per episode"
    )
    MAX_PARALLEL_JOBS: int = Field(
        default=3, description="Maximum parallel pipeline jobs"
    )

    # ============================================
    # YouTube Settings
    # ============================================
    YOUTUBE_ENABLED: bool = Field(default=False, description="Enable YouTube auto-upload")
    YOUTUBE_CLIENT_SECRETS_FILE: str = Field(default="youtube_credentials.json", description="YouTube client secrets file")
    YOUTUBE_TOKEN_FILE: str = Field(default="youtube_token.json", description="YouTube OAuth token file")
    YOUTUBE_DEFAULT_PRIVACY: str = Field(default="public", description="Default privacy status (public, private, unlisted)")

    # ============================================
    # Character Settings
    # ============================================
    CHARACTER_FILE: str = Field(
        default="aera.json", description="Default character file"
    )
    WORLD_FILE: str = Field(default="ancient-world.json", description="Default world file")

    # ============================================
    # Video Assembly Settings
    # ============================================
    BACKGROUND_MUSIC_PATH: str = Field(
        default="", description="Background music file path"
    )
    SUBTITLE_FONT: str = Field(
        default="NotoSansThai-Regular.ttf", description="Subtitle font file"
    )

    # ============================================
    # Logging
    # ============================================
    LOG_LEVEL: str = Field(default="INFO", description="Log level")
    LOG_FILE: str = Field(default="logs/ai_workforce.log", description="Log file path")

    # ============================================
    # CORS
    # ============================================
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins",
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(
        default=True, description="Allow credentials in CORS"
    )

    # ============================================
    # Director AI
    # ============================================
    DIRECTOR_AI_ENABLED: bool = Field(
        default=True, description="Enable Director AI agent"
    )
    KNOWLEDGE_BASE_PATH: str = Field(
        default="./knowledge/director-ai",
        description="Knowledge base path",
    )


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings (dependency injection compatible)."""
    return settings

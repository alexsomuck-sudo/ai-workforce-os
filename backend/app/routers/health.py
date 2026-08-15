"""
Health Router - System health check endpoints
Provides detailed health status for all system components.
"""
import logging
import time
from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.schemas import HealthResponse
from app.core.config import settings

logger = logging.getLogger("ai_workforce.routers.health")

router = APIRouter(prefix="/api/v1/health", tags=["Health"])

_start_time = time.time()


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Check system health status."""
    services = {}

    # Check API
    services["api"] = "healthy"

    # Check database
    try:
        from database.session import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        services["database"] = "healthy"
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        services["database"] = f"unhealthy: {str(e)[:50]}"

    # Check LLM factory
    try:
        from app.services.llm.factory import LLMFactory
        services["llm_factory"] = "healthy"
    except Exception as e:
        services["llm_factory"] = f"unhealthy: {str(e)[:50]}"

    # Check Director AI
    if settings.DIRECTOR_AI_ENABLED:
        try:
            from app.agents.director_ai.memory_loader import DirectorMemoryLoader
            loader = DirectorMemoryLoader()
            services["director_ai"] = "healthy"
        except Exception as e:
            services["director_ai"] = f"unhealthy: {str(e)[:50]}"

    # Check YouTube
    if settings.YOUTUBE_ENABLED:
        try:
            from app.services.youtube_service import YouTubeService
            yt = YouTubeService()
            if yt.authenticate():
                services["youtube"] = "healthy"
            else:
                services["youtube"] = "unauthenticated"
        except Exception as e:
            services["youtube"] = f"error: {str(e)[:50]}"

    # Determine overall status
    overall = "healthy" if all(v == "healthy" for v in services.values()) else "degraded"

    return HealthResponse(
        status=overall,
        version=settings.APP_VERSION,
        services=services,
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/ready")
async def readiness_check():
    """Check if the system is ready to accept requests."""
    return {
        "ready": True,
        "uptime_seconds": round(time.time() - _start_time, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

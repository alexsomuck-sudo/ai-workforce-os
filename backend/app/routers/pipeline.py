"""
Pipeline Router - API endpoints for movie pipeline operations
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("ai_workforce.routers.pipeline")

router = APIRouter(prefix="/api/v1/pipeline", tags=["Movie Pipeline"])


class PipelineRunRequest(BaseModel):
    """Request to run the movie pipeline."""
    character: str = Field(default="linhfeng", description="Character name")
    world: str = Field(default="ancient-world", description="World name")
    episode: str = Field(default="ep001", description="Episode name")
    scene_index: int = Field(default=0, description="Starting scene index")


@router.post("/run")
async def run_pipeline(request: PipelineRunRequest):
    """Run the movie generation pipeline for an episode."""
    try:
        from app.services.pipeline.movie_pipeline import MoviePipeline
        pipeline = MoviePipeline()
        result = pipeline.generate_episode(
            character=request.character,
            episode=request.episode,
            scene_index=request.scene_index,
        )
        return result
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")


@router.get("/status")
async def pipeline_status():
    """Get the current status of the movie pipeline."""
    return {
        "status": "idle",
        "movies_dir": "./movies",
        "scenes_per_episode": 5,
        "max_parallel_jobs": 3,
    }


class LipSyncRequest(BaseModel):
    """Request for lip-sync generation."""
    character: str = Field(default="linhfeng", description="Character name")
    text: str = Field(..., min_length=1, description="Dialogue text")
    image_path: Optional[str] = Field(default=None, description="Path to character image")
    audio_path: Optional[str] = Field(default=None, description="Path to audio file")


@router.post("/lip-sync")
async def lip_sync(request: LipSyncRequest):
    """Generate lip-sync video from character image and audio."""
    try:
        from app.services.lip_sync.lip_sync_service import LipSyncService
        service = LipSyncService()
        result = service.generate_lip_sync(
            image_path=request.image_path,
            audio_path=request.audio_path,
        )
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lip-sync error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Lip-sync failed: {str(e)}")

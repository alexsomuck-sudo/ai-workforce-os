import os
import sys
import logging
from pathlib import Path
import random

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.services.pipeline.movie_pipeline import MoviePipeline
from app.agents.director_ai.memory_loader import DirectorMemoryLoader
from app.core.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auto_post")

def main():
    logger.info("Starting automated drama post...")
    
    # Ensure YouTube is enabled for this run
    # (In production, this should be in .env, but we can override here for the script)
    os.environ["YOUTUBE_ENABLED"] = "True"
    
    # Initialize pipeline
    pipeline = MoviePipeline(
        llm_provider="gemini",
        lip_sync_provider="gemini",
        image_provider="openai" # DALL-E 3 for better visuals
    )
    
    # Pick a random character and episode for the post
    loader = DirectorMemoryLoader()
    available = {
        "characters": ["linhfeng"],
        "episodes": ["ep001"]
    }
    
    char = random.choice(available["characters"])
    ep = random.choice(available["episodes"])
    
    logger.info(f"Generating post for character: {char}, episode: {ep}")
    
    try:
        # Generate full episode and auto-upload
        result = pipeline.generate_episode(
            character=char,
            episode=ep,
            max_scenes=3 # Keep it short for frequent posts
        )
        
        if result.get("status") == "success":
            logger.info("✓ Automated post completed successfully!")
            if "youtube" in result:
                logger.info(f"  YouTube URL: {result['youtube'].get('url')}")
        else:
            logger.error(f"✗ Automated post failed: {result.get('message')}")
            
    except Exception as e:
        logger.error(f"✗ Unexpected error in auto-post: {e}")

if __name__ == "__main__":
    main()

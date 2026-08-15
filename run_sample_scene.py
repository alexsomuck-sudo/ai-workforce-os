import os
import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.services.pipeline.movie_pipeline import MoviePipeline

# Setup logging to see what's happening
logging.basicConfig(level=logging.INFO)

def main():
    print("============================================================")
    print("Running Sample Scene Generation with Gemini")
    print("============================================================")
    
    # Initialize pipeline with Gemini
    pipeline = MoviePipeline(
        llm_provider="gemini",
        lip_sync_provider="gemini",
        image_provider="gemini"
    )
    
    # Generate one scene
    # Character: linhfeng, Episode: ep001, Scene: 0
    try:
        result = pipeline.generate_scene(
            character="linhfeng",
            episode="ep001",
            scene_index=0,
            output_dir="./movies/test_run"
        )
        
        if result.get("status") == "success":
            print("\n✓ Scene Generation Successful!")
            print(f"  Video Path: {result.get('video_path')}")
            print(f"  Dialogue: {result.get('dialogue')}")
            print(f"  Pipeline Log: {result.get('pipeline')}")
        else:
            print(f"\n✗ Scene Generation Failed: {result.get('message')}")
            
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

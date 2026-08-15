"""
DirectorAI - AI Director agent for cinematic scene generation
Loads knowledge from the knowledge base and generates scene prompts.
"""
import logging
from typing import Any, Dict, Optional
from .memory_loader import DirectorMemoryLoader
from .prompt_engine import PromptEngine
from .character_memory import CharacterMemory

logger = logging.getLogger("ai_workforce.agents.director_ai")


class DirectorAI:
    """AI Director agent that creates cinematic scenes from knowledge base data."""

    def __init__(self):
        self.memory = DirectorMemoryLoader()
        self.prompt_engine = PromptEngine()
        self.character_memory = CharacterMemory()

    def create_scene(
        self,
        character: str = "linhfeng",
        world: str = "ancient-world",
        episode: str = "ep001",
        scene_index: int = 0,
    ) -> Dict[str, Any]:
        """
        Create a cinematic scene.

        Args:
            character: Character name from knowledge base
            world: World name from knowledge base
            episode: Episode name from knowledge base
            scene_index: Index of the scene in the episode

        Returns:
            Dict with episode, scene, and prompt data
        """
        char_data = self.memory.load_character(character)
        world_data = self.memory.load_world(world)
        episode_data = self.memory.load_episode(episode)

        scenes = episode_data.get("scenes", [])
        if scene_index >= len(scenes):
            scene_index = 0
        scene = scenes[scene_index]

        prompt = self.prompt_engine.create_scene_prompt(
            char_data, world_data, scene
        )

        # Update character memory with conversation
        dialogue = scene.get("dialogue", {}).get("text", "")
        if dialogue:
            self.character_memory.add_conversation(character, dialogue, "character")

        result = {
            "episode": episode_data.get("title", ""),
            "scene": scene.get("title", ""),
            "prompt": prompt,
            "character": character,
            "world": world,
            "scene_index": scene_index,
            "dialogue": dialogue,
            "emotion": scene.get("emotion", "neutral"),
            "action": scene.get("action", ""),
        }
        logger.info(f"Scene created: {result['episode']} - {result['scene']}")
        return result

    def get_character_context(self, character_name: str) -> str:
        """Get the full context for a character."""
        return self.character_memory.get_context(character_name)

    def list_available_content(self) -> Dict[str, Any]:
        """List available characters, worlds, and episodes."""
        return {
            "characters": ["linhfeng", "aera"],
            "worlds": ["ancient-world"],
            "episodes": ["ep001", "fp_ep001"],
        }

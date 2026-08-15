"""
Voice Service - Unified interface for text-to-speech generation
Supports OpenAI TTS and Deepgram TTS.
"""
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger("ai_workforce.voice")


class VoiceService:
    """Text-to-Speech service with multiple provider support."""

    def __init__(self):
        self.provider = settings.TTS_PROVIDER
        self.voice = settings.TTS_VOICE
        self.model = settings.TTS_MODEL
        self.speed = settings.TTS_SPEED
        self.language = settings.TTS_LANGUAGE

    def generate_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        model: Optional[str] = None,
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate speech audio from text.

        Args:
            text: Text to convert to speech
            voice: Voice name override
            model: TTS model override
            output_dir: Directory for output file

        Returns:
            Dict with status and audio file path/URL
        """
        voice = voice or self.voice
        model = model or self.model
        output_dir = output_dir or settings.MOVIES_DIR

        if self.provider == "openai":
            return self._generate_openai(text, voice, model, output_dir)
        elif self.provider == "deepgram":
            return self._generate_deepgram(text, voice, model, output_dir)
        else:
            return {"status": "error", "message": f"Unknown TTS provider: {self.provider}"}

    def _generate_openai(self, text: str, voice: str, model: str, output_dir: str) -> Dict[str, Any]:
        """Generate speech using OpenAI TTS."""
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", ""),
                timeout=30.0,
            )
            output_path = os.path.join(output_dir, f"speech_{hash(text) % 10000}.mp3")
            os.makedirs(output_dir, exist_ok=True)

            response = client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                speed=self.speed,
            )
            response.stream_to_file(output_path)

            logger.info(f"OpenAI TTS: Generated {output_path}")
            return {
                "status": "success",
                "provider": "openai",
                "voice": voice,
                "model": model,
                "output_path": output_path,
            }
        except Exception as e:
            logger.error(f"OpenAI TTS error: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    def _generate_deepgram(self, text: str, voice: str, model: str, output_dir: str) -> Dict[str, Any]:
        """Generate speech using Deepgram TTS."""
        try:
            import requests
            api_key = settings.DEEPGRAM_API_KEY or os.getenv("DEEPGRAM_API_KEY", "")
            output_path = os.path.join(output_dir, f"speech_{hash(text) % 10000}.mp3")
            os.makedirs(output_dir, exist_ok=True)

            headers = {
                "Authorization": f"Token {api_key}",
                "Content-Type": "application/json",
            }
            data = {
                "text": text,
                "model": model,
                "options": {
                    "language": self.language,
                    "speed": self.speed,
                },
            }

            response = requests.post(
                "https://api.deepgram.com/v1/speak",
                headers=headers,
                json=data,
                timeout=30,
            )
            response.raise_for_status()

            with open(output_path, "wb") as f:
                f.write(response.content)

            logger.info(f"Deepgram TTS: Generated {output_path}")
            return {
                "status": "success",
                "provider": "deepgram",
                "voice": voice,
                "model": model,
                "output_path": output_path,
            }
        except Exception as e:
            logger.error(f"Deepgram TTS error: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    @staticmethod
    def select_voice(character_voice_data: dict, provider: str = "openai") -> str:
        """
        Select a voice ID based on character voice data.
        """
        gender = character_voice_data.get("gender", "female").lower()
        age = character_voice_data.get("age", "young").lower()
        archetype = character_voice_data.get("archetype", "").lower()
        
        if provider == "openai":
            if archetype == "wise guide":
                return "shimmer" # Calm and melodic
            if gender == "male":
                return "onyx" if age == "old" else "echo"
            else:
                return "nova" if age == "young" else "shimmer"
        
        return "alloy"

    def get_available_voices(self) -> list:
        """Get available voices based on current provider."""
        if self.provider == "openai":
            return [
                {"name": "alloy", "description": "Balanced, neutral voice"},
                {"name": "echo", "description": "Deep, resonant voice"},
                {"name": "fable", "description": "Warm, storytelling voice"},
                {"name": "onyx", "description": "Strong, authoritative voice"},
                {"name": "nova", "description": "Bright, energetic voice"},
                {"name": "shimmer", "description": "Light, youthful voice"},
            ]
        elif self.provider == "deepgram":
            return [
                {"name": "aura-asteria-en", "description": "English female"},
                {"name": "aura-luna-en", "description": "English female"},
                {"name": "aura-stella-en", "description": "English female"},
            ]
        return []

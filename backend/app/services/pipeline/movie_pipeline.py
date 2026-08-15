"""
MoviePipeline — ระบบสร้างหนังอัตโนมัติแบบ End-to-End

Flow:
  1. DirectorAI → สร้าง Scene Prompt + Dialogue
  2. ImageService → สร้างภาพตัวละคร (DALL-E 3 / Gemini)
  3. OpenAIVoiceClient → สร้างเสียงพูด (TTS)
  4. LipSyncService → รวมภาพ + เสียง → วิดีโอปากขยับ
  5. VideoAssemblyService → รวมหลายฉาก → หนังเต็มตอน

Usage:
    pipeline = MoviePipeline()
    result = pipeline.generate_episode(
        character="linhfeng",
        episode="ep001",
        output_dir="./movies/ep001"
    )
"""

import os
import json
import uuid
import logging
import shutil
from pathlib import Path
from typing import Optional
from app.core.config import settings

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


class MoviePipeline:
    """Pipeline สำหรับสร้างหนังอัตโนมัติแบบ End-to-End"""

    def __init__(
        self,
        llm_provider: str = "openai",
        lip_sync_provider: str = "simulated",
        image_provider: str = "openai",
    ):
        """
        Args:
            llm_provider: LLM ที่ใช้สร้าง dialogue — "openai", "gemini", "deepseek"
            lip_sync_provider: Lip-Sync engine — "hedra", "did", "simulated"
            image_provider: Image generator — "openai", "gemini"
        """
        self.llm_provider = llm_provider
        self.lip_sync_provider = lip_sync_provider
        self.image_provider = image_provider

        # Lazy imports — โหลดเฉพาะเมื่อจำเป็น
        self._director = None
        self._image_service = None
        self._tts_client = None
        self._lip_sync = None
        self._youtube = None

    # ────────────────────────────────────────────────────────────
    # Lazy loading
    # ────────────────────────────────────────────────────────────
    @property
    def director(self):
        if self._director is None:
            from app.agents.director_ai.director import DirectorAI
            self._director = DirectorAI()
        return self._director

    @property
    def image_service(self):
        if self._image_service is None:
            if self.image_provider == "openai":
                from app.services.llm.image_service import ImageService
                self._image_service = ImageService()
            else:
                from app.services.llm.gemini_media import GeminiMediaService
                self._image_service = GeminiMediaService()
        return self._image_service

    @property
    def tts_client(self):
        if self._tts_client is None:
            from app.services.llm.openai_voice import OpenAIVoiceClient
            self._tts_client = OpenAIVoiceClient()
        return self._tts_client

    @property
    def lip_sync(self):
        if self._lip_sync is None:
            from app.services.lip_sync.lip_sync_service import LipSyncService
            self._lip_sync = LipSyncService(provider=self.lip_sync_provider)
        return self._lip_sync

    @property
    def youtube(self):
        if self._youtube is None:
            from app.services.youtube_service import YouTubeService
            self._youtube = YouTubeService()
        return self._youtube

    # ────────────────────────────────────────────────────────────
    # Scene Generation (ขั้นตอนเดียว)
    # ────────────────────────────────────────────────────────────
    def generate_scene(
        self,
        character: str = "linhfeng",
        episode: str = "ep001",
        scene_index: int = 0,
        output_dir: Optional[str] = None,
    ) -> dict:
        """
        สร้างวิดีโอตัวละครพูดได้ 1 ฉาก

        Flow:
          DirectorAI → Scene Prompt → Image → TTS → Lip-Sync → MP4

        Args:
            character: ชื่อตัวละคร (ตรงกับไฟล์ใน knowledge/)
            episode: ชื่อตอน
            scene_index: index ของ scene ใน episode (default: 0)
            output_dir: โฟลเดอร์เก็บผลลัพธ์ (default: ./movies/{episode}/scenes/)

        Returns:
            dict {
                "status": "success"|"error",
                "scene_id": str,
                "image_path": str,
                "audio_path": str,
                "video_path": str,
                "dialogue": str,
                "character": str,
                "episode": str,
                "scene_title": str,
                "pipeline": {...}
            }
        """
        run_id = uuid.uuid4().hex[:8]
        output_path = Path(output_dir) if output_dir else Path(f"./movies/{episode}/scenes")
        output_path.mkdir(parents=True, exist_ok=True)

        scene_dir = output_path / f"scene_{scene_index:03d}_{run_id}"
        scene_dir.mkdir(parents=True, exist_ok=True)

        pipeline_log = {}

        # ── Step 1: DirectorAI สร้าง Scene ──
        logger.info("[Pipeline] Step 1: DirectorAI creating scene...")
        try:
            scene_data = self.director.create_scene(character=character, episode=episode)
            pipeline_log["director"] = "success"
        except Exception as e:
            logger.error(f"[Pipeline] DirectorAI failed: {e}")
            # Fallback: โหลด scene โดยตรงจาก knowledge base
            scene_data = self._fallback_load_scene(character, episode, scene_index)
            pipeline_log["director"] = "fallback"

        dialogue = scene_data.get("dialogue", "")
        scene_title = scene_data.get("scene_title", f"Scene {scene_index}")
        image_prompt = scene_data.get("image_prompt", "")
        emotion = scene_data.get("emotion", "neutral")

        if not dialogue:
            return {
                "status": "error",
                "message": "No dialogue found for this scene",
                "scene_data": scene_data,
            }

        # ── Step 2: สร้างภาพตัวละคร ──
        logger.info("[Pipeline] Step 2: Generating character image...")
        image_path = str(scene_dir / "character.png")
        try:
            image_prompt_full = self._build_image_prompt(
                character=character, image_prompt=image_prompt, emotion=emotion
            )
            if self.image_provider == "openai":
                result = self.image_service.generate_character_image(
                    visual_prompt=image_prompt_full, size="1024x1024"
                )
                if result["status"] == "success":
                    self._download_image(result["url"], image_path)
                else:
                    raise Exception(result.get("message", "Image gen failed"))
            else:
                result = self.image_service.generate_image(image_prompt_full)
                # Gemini returns text prompt — จำลองภาพ
                self._create_placeholder_image(image_path, image_prompt_full)
            pipeline_log["image"] = "success"
        except Exception as e:
            logger.warning(f"[Pipeline] Image generation failed: {e}")
            self._create_placeholder_image(image_path, image_prompt_full)
            pipeline_log["image"] = "placeholder"

        # ── Step 3: สร้างเสียงพูด (TTS) ──
        logger.info("[Pipeline] Step 3: Generating TTS audio...")
        audio_path = str(scene_dir / "dialogue.mp3")
        try:
            character_voice = self._load_character_voice(character)
            result = self.tts_client.generate_speech(
                text=dialogue,
                character_voice_data=character_voice,
                output_path=audio_path,
            )
            pipeline_log["tts"] = result.get("status", "error")
        except Exception as e:
            logger.warning(f"[Pipeline] TTS failed: {e}")
            pipeline_log["tts"] = "failed"
            # สร้างไฟล์เสียงว่างสำหรับทดสอบ
            self._create_silent_audio(audio_path, 5)

        # ── Step 4: Lip-Sync (ภาพ + เสียง → วิดีโอ) ──
        logger.info("[Pipeline] Step 4: Generating lip-sync video...")
        video_path = str(scene_dir / "scene_video.mp4")
        try:
            result = self.lip_sync.generate_lip_sync(
                image_path=image_path,
                audio_path=audio_path,
                output_path=video_path,
                duration_hint=10,
            )
            pipeline_log["lip_sync"] = result.get("status", "error")
            pipeline_log["lip_sync_provider"] = result.get("provider", self.lip_sync_provider)
        except Exception as e:
            logger.error(f"[Pipeline] Lip-sync failed: {e}")
            pipeline_log["lip_sync"] = "failed"

        # ── Step 5: รวมผลลัพธ์ ──
        metadata = {
            "status": "success",
            "scene_id": f"{episode}_scene_{scene_index:03d}",
            "run_id": run_id,
            "image_path": image_path,
            "audio_path": audio_path,
            "video_path": video_path,
            "dialogue": dialogue,
            "character": character,
            "episode": episode,
            "scene_title": scene_title,
            "emotion": emotion,
            "pipeline": pipeline_log,
        }

        # บันทึก metadata
        with open(scene_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        logger.info(f"[Pipeline] Scene complete: {video_path}")
        return metadata

    # ────────────────────────────────────────────────────────────
    # Episode Generation (หลายฉาก → หนัง)
    # ────────────────────────────────────────────────────────────
    def generate_episode(
        self,
        character: str = "linhfeng",
        episode: str = "ep001",
        output_dir: Optional[str] = None,
        max_scenes: int = 10,
    ) -> dict:
        """
        สร้างหนังเต็มตอน — สร้างทุกฉากแล้วรวมเป็นวิดีโอเดียว

        Returns:
            dict {
                "status": str,
                "episode": str,
                "total_scenes": int,
                "scenes": [...],
                "final_video": str,
            }
        """
        output_path = Path(output_dir) if output_dir else Path(f"./movies/{episode}")
        output_path.mkdir(parents=True, exist_ok=True)

        # โหลด episode
        from app.agents.director_ai.memory_loader import DirectorMemoryLoader
        loader = DirectorMemoryLoader()
        ep_data = loader.load_episode(episode)

        scenes = ep_data.get("scenes", [])
        if not scenes:
            return {"status": "error", "message": "No scenes found in episode"}

        total_scenes = min(len(scenes), max_scenes)
        scene_results = []

        for i in range(total_scenes):
            logger.info(f"[Pipeline] Generating scene {i+1}/{total_scenes}...")
            result = self.generate_scene(
                character=character,
                episode=episode,
                scene_index=i,
                output_dir=str(output_path / "scenes"),
            )
            scene_results.append(result)

        # รวมวิดีโอทั้งหมด
        from app.services.pipeline.video_assembly import VideoAssemblyService
        assembler = VideoAssemblyService()

        video_files = [
            r["video_path"]
            for r in scene_results
            if r.get("status") == "success" and Path(r["video_path"]).exists()
        ]

        final_video = str(output_path / "full_episode.mp4")
        assembly_result = assembler.combine_videos(video_files, final_video)

        result = {
            "status": "success",
            "episode": episode,
            "total_scenes": total_scenes,
            "successful_scenes": len(video_files),
            "scenes": scene_results,
            "final_video": final_video if assembly_result.get("status") == "success" else None,
            "assembly": assembly_result,
        }

        # Auto-upload to YouTube if enabled
        if settings.YOUTUBE_ENABLED and result["final_video"]:
            logger.info(f"[Pipeline] Auto-uploading episode {episode} to YouTube...")
            title = ep_data.get("title", f"AI Workforce OS - {episode}")
            description = ep_data.get("description", "Automated video generated by AI Workforce OS.")
            
            upload_result = self.youtube.upload_video(
                file_path=result["final_video"],
                title=title,
                description=description
            )
            result["youtube"] = upload_result
            if upload_result["status"] == "success":
                logger.info(f"[Pipeline] YouTube upload successful: {upload_result['url']}")
            else:
                logger.warning(f"[Pipeline] YouTube upload failed: {upload_result['message']}")

        return result

    # ────────────────────────────────────────────────────────────
    # Generate Single Character Video (พูดจากข้อความ)
    # ────────────────────────────────────────────────────────────
    def generate_character_video(
        self,
        character: str = "linhfeng",
        text: str = "",
        output_dir: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> dict:
        """
        สร้างวิดีโอตัวละครพูดข้อความโดยตรง (ไม่ต้องผ่าน DirectorAI)

        Flow: Image → TTS → Lip-Sync → MP4

        Args:
            character: ชื่อตัวละคร
            text: ข้อความที่ต้องการให้พูด
            output_dir: โฟลเดอร์เก็บผลลัพธ์
            run_id: identifier สำหรับ run นี้ (optional)

        Returns:
            dict with status, video_path, audio_path, etc.
        """
        run = run_id or uuid.uuid4().hex[:8]
        output_path = Path(output_dir) if output_dir else Path(f"./movies/{character}/{run}")
        output_path.mkdir(parents=True, exist_ok=True)

        pipeline_log = {}

        # Step 1: สร้างภาพตัวละคร
        image_path = str(output_path / "character.png")
        try:
            char_data = self._load_character_full(character)
            image_prompt = self._build_image_prompt(
                character=character,
                image_prompt="",
                emotion="neutral",
            )
            if self.image_provider == "openai":
                result = self.image_service.generate_character_image(
                    visual_prompt=image_prompt, size="1024x1024"
                )
                if result["status"] == "success":
                    self._download_image(result["url"], image_path)
                else:
                    raise Exception(result.get("message"))
            else:
                result = self.image_service.generate_image(image_prompt)
                self._create_placeholder_image(image_path, image_prompt)
            pipeline_log["image"] = "success"
        except Exception as e:
            logger.warning(f"Image gen failed: {e}")
            self._create_placeholder_image(image_path, f"Character: {character}")
            pipeline_log["image"] = "placeholder"

        # Step 2: สร้างเสียง
        audio_path = str(output_path / "dialogue.mp3")
        try:
            char_voice = self._load_character_voice(character)
            result = self.tts_client.generate_speech(
                text=text,
                character_voice_data=char_voice,
                output_path=audio_path,
            )
            pipeline_log["tts"] = result.get("status", "error")
        except Exception as e:
            logger.warning(f"TTS failed: {e}")
            pipeline_log["tts"] = "failed"
            self._create_silent_audio(audio_path, 5)

        # Step 3: Lip-Sync
        video_path = str(output_path / "character_video.mp4")
        try:
            result = self.lip_sync.generate_lip_sync(
                image_path=image_path,
                audio_path=audio_path,
                output_path=video_path,
                duration_hint=15,
            )
            pipeline_log["lip_sync"] = result.get("status", "error")
        except Exception as e:
            logger.error(f"Lip-sync failed: {e}")
            pipeline_log["lip_sync"] = "failed"

        return {
            "status": "success",
            "run_id": run,
            "character": character,
            "text": text,
            "image_path": image_path,
            "audio_path": audio_path,
            "video_path": video_path,
            "pipeline": pipeline_log,
        }

    # ────────────────────────────────────────────────────────────
    # Helpers
    # ────────────────────────────────────────────────────────────
    def _build_image_prompt(self, character: str, image_prompt: str, emotion: str) -> str:
        """สร้าง image prompt ที่ละเอียดจากข้อมูลตัวละคร"""
        try:
            char_data = self._load_character_full(character)
            face = char_data.get("appearance", {}).get("face", {}).get("description", "")
            hair = char_data.get("appearance", {}).get("hair", {})
            hair_desc = f"{hair.get('color', '')} {hair.get('style', '')}".strip()
            outfit = char_data.get("costume", {}).get("main_outfit", "traditional outfit")
            body = char_data.get("appearance", {}).get("body", {})
            build = body.get("build", "")

            base = (
                f"Cinematic portrait of a {char_data.get('basic_information', {}).get('gender', 'male')}, "
                f"face: {face}, hair: {hair_desc}, body build: {build}. "
                f"Wearing: {outfit}. "
            )
            if image_prompt:
                base += f"Scene: {image_prompt}. "
            base += f"Emotion: {emotion}. "
            base += "Realistic skin texture, cinematic lighting, 4K quality, photorealistic."
            return base
        except Exception:
            return image_prompt or f"Cinematic portrait of {character}"

    def _load_character_full(self, character: str) -> dict:
        """โหลดข้อมูลตัวละครทั้งหมด"""
        from app.agents.director_ai.memory_loader import DirectorMemoryLoader
        return DirectorMemoryLoader().load_character(character)

    def _load_character_voice(self, character: str) -> dict:
        """โหลดเฉพาะส่วน voice ของตัวละคร"""
        char_data = self._load_character_full(character)
        return char_data.get("voice", {})

    def _fallback_load_scene(self, character: str, episode: str, scene_index: int) -> dict:
        """Fallback: โหลด scene โดยตรงจาก knowledge base"""
        try:
            from app.agents.director_ai.memory_loader import DirectorMemoryLoader
            loader = DirectorMemoryLoader()
            ep = loader.load_episode(episode)
            scenes = ep.get("scenes", [])
            if scene_index < len(scenes):
                scene = scenes[scene_index]
                return {
                    "dialogue": scene.get("dialogue", {}).get("text", ""),
                    "scene_title": scene.get("title", ""),
                    "image_prompt": scene.get("action", ""),
                    "emotion": scene.get("emotion", "neutral"),
                }
        except Exception:
            pass
        return {"dialogue": "", "scene_title": "", "image_prompt": "", "emotion": "neutral"}

    def _download_image(self, url: str, path: str) -> bool:
        """ดาวน์โหลดภาพจาก URL"""
        import requests
        try:
            resp = requests.get(url, timeout=30)
            with open(path, "wb") as f:
                f.write(resp.content)
            return True
        except Exception:
            return False

    def _create_placeholder_image(self, path: str, prompt: str):
        """สร้างภาพ placeholder ถ้า image gen ล้มเหลว"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new("RGB", (1024, 1024), color=(30, 30, 50))
            draw = ImageDraw.Draw(img)
            # ใส่ข้อความ
            text = prompt[:200]
            draw.text((50, 50), text[:100], fill=(200, 200, 255))
            img.save(path)
        except Exception:
            # ถ้า PIL ไม่มี ก็สร้างไฟล์ว่าง
            Path(path).touch()

    def _create_silent_audio(self, path: str, duration: int):
        """สร้างไฟล์เสียงว่าง"""
        import subprocess
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi", "-i",
            f"anullsrc=r=24000:cl=mono", "-t", str(duration),
            "-q:a", "9", "-acodec", "libmp3lame", path,
        ]
        try:
            subprocess.run(cmd, capture_output=True, timeout=30)
        except Exception:
            Path(path).touch()

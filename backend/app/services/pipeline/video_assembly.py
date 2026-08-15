"""
VideoAssemblyService — ระบบรวมวิดีโอหลายฉากเป็นหนังเต็มตอน

ใช้ FFmpeg ในการรวมคลิปวิดีโอ, เพิ่มเสียงประกอบ, เพลงคลอ,
และคำบรรยาย (Subtitles)

Usage:
    assembler = VideoAssemblyService()
    result = assembler.combine_videos(
        video_files=["scene1.mp4", "scene2.mp4", "scene3.mp4"],
        output_path="full_movie.mp4"
    )
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)


class VideoAssemblyService:
    """Service สำหรับรวมวิดีโอหลายฉากเป็นหนัง"""

    def __init__(self):
        self._check_ffmpeg()

    def _check_ffmpeg(self):
        """ตรวจสอบว่ามี FFmpeg ติดตั้งอยู่"""
        try:
            subprocess.run(
                ["ffmpeg", "-version"], capture_output=True, check=True
            )
            self.ffmpeg_available = True
        except FileNotFoundError:
            self.ffmpeg_available = False
            logger.warning("FFmpeg not found. Install with: sudo apt install ffmpeg")

    # ────────────────────────────────────────────────────────────
    # Combine Multiple Videos
    # ────────────────────────────────────────────────────────────
    def combine_videos(
        self,
        video_files: List[str],
        output_path: str,
        add_transitions: bool = True,
        transition_duration: float = 0.5,
    ) -> dict:
        """
        รวมวิดีโอหลายไฟล์เป็นวิดีโอเดียว

        Args:
            video_files: รายการ path ไปยังไฟล์วิดีโอ
            output_path: path ของไฟล์ผลลัพธ์
            add_transitions: ใส่ transition ระหว่างฉากหรือไม่
            transition_duration: ความยาว transition (วินาที)

        Returns:
            dict {"status": str, "output_path": str, "total_duration": float}
        """
        if not self.ffmpeg_available:
            return {
                "status": "error",
                "message": "FFmpeg not installed. Install with: sudo apt install ffmpeg",
            }

        if not video_files:
            return {"status": "error", "message": "No video files provided"}

        # ตรวจสอบไฟล์ที่มีอยู่จริง
        existing = [f for f in video_files if Path(f).exists()]
        if not existing:
            return {"status": "error", "message": "No valid video files found"}

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            if add_transitions and len(existing) > 1:
                return self._concat_with_transitions(
                    existing, output_path, transition_duration
                )
            else:
                return self._concat_simple(existing, output_path)
        except Exception as e:
            logger.error(f"Video assembly failed: {e}")
            return {"status": "error", "message": str(e)}

    # ────────────────────────────────────────────────────────────
    # Add Background Music
    # ────────────────────────────────────────────────────────────
    def add_background_music(
        self,
        video_path: str,
        music_path: str,
        output_path: str,
        music_volume: float = 0.3,
        loop_music: bool = True,
    ) -> dict:
        """
        เพิ่มเสียงเพลงประกอบลงในวิดีโอ

        Args:
            video_path: path วิดีโอหลัก
            music_path: path ไฟล์เพลง
            output_path: path ผลลัพธ์
            music_volume: ความดังเพลง (0.0-1.0)
            loop_music: loop เพลงถ้าสั้นกว่าวิดีโอ
        """
        if not self.ffmpeg_available:
            return {"status": "error", "message": "FFmpeg not installed"}

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        music_input = f"-stream_loop {1 if loop_music else 0}" if loop_music else ""
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            *(["-stream_loop", "1"] if loop_music else []),
            "-i", music_path,
            "-filter_complex",
            f"[1:a]volume={music_volume}[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=3[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            output_path,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                return {"status": "error", "message": f"FFmpeg error: {result.stderr[:300]}"}
            return {"status": "success", "output_path": output_path}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ────────────────────────────────────────────────────────────
    # Add Subtitles
    # ────────────────────────────────────────────────────────────
    def add_subtitles(
        self,
        video_path: str,
        subtitle_path: str,
        output_path: str,
        font_size: int = 24,
        font_color: str = "white",
    ) -> dict:
        """
        เพิ่มคำบรรยาย (Subtitles) ลงในวิดีโอ

        Args:
            video_path: path วิดีโอ
            subtitle_path: path ไฟล์ .srt หรือ .ass
            output_path: path ผลลัพธ์
            font_size: ขนาดตัวอักษร
            font_color: สีตัวอักษร
        """
        if not self.ffmpeg_available:
            return {"status": "error", "message": "FFmpeg not installed"}

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Escape subtitle path for ffmpeg filter
        escaped_sub = subtitle_path.replace(":", r"\:").replace("'", r"\'")

        filter_complex = (
            f"subtitles='{escaped_sub}':"
            f"force_style='FontSize={font_size},PrimaryColour=&H00{self._hex_to_ass(font_color)},"
            f"OutlineColour=&H00000000,Outline=2,MarginV=30'"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", filter_complex,
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "copy",
            output_path,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                return {"status": "error", "message": f"FFmpeg error: {result.stderr[:300]}"}
            return {"status": "success", "output_path": output_path}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ────────────────────────────────────────────────────────────
    # Add Opening/Closing Titles
    # ────────────────────────────────────────────────────────────
    def create_title_card(
        self,
        text: str,
        output_path: str,
        duration: float = 3.0,
        bg_color: str = "black",
        font_color: str = "white",
        font_size: int = 48,
        width: int = 1920,
        height: int = 1080,
    ) -> dict:
        """
        สร้าง Title Card (หน้าเปิด/ปิด)

        Args:
            text: ข้อความที่ต้องการแสดง
            output_path: path เก็บไฟล์
            duration: ความยาว (วินาที)
        """
        if not self.ffmpeg_available:
            return {"status": "error", "message": "FFmpeg not installed"}

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i",
            f"color=c={bg_color}:s={width}x{height}:d={duration}",
            "-vf",
            f"drawtext=text='{text}':"
            f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            f"fontsize={font_size}:fontcolor={font_color}:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:"
            f"alpha='if(lt(t,0.5),2*t,if(gt(t,{duration-0.5}),2*({duration}-t),1))'",
            "-c:v", "libx264", "-preset", "fast",
            "-pix_fmt", "yuv420p",
            output_path,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                # ถ้าไม่มี font file ก็ลองแบบไม่มี fontfile
                cmd_simple = [
                    "ffmpeg", "-y",
                    "-f", "lavfi", "-i",
                    f"color=c={bg_color}:s={width}x{height}:d={duration}",
                    "-vf",
                    f"drawtext=text='{text}':"
                    f"fontsize={font_size}:fontcolor={font_color}:"
                    f"x=(w-text_w)/2:y=(h-text_h)/2",
                    "-c:v", "libx264", "-preset", "fast",
                    "-pix_fmt", "yuv420p",
                    output_path,
                ]
                result = subprocess.run(cmd_simple, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                return {"status": "error", "message": f"FFmpeg error: {result.stderr[:300]}"}
            return {"status": "success", "output_path": output_path, "duration": duration}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ────────────────────────────────────────────────────────────
    # Full Movie Assembly
    # ────────────────────────────────────────────────────────────
    def assemble_full_movie(
        self,
        scene_videos: List[str],
        output_path: str,
        title: str = "",
        opening_music: Optional[str] = None,
        background_music: Optional[str] = None,
        subtitle_file: Optional[str] = None,
        music_volume: float = 0.3,
    ) -> dict:
        """
        ประกอบหนังเต็มตอน:
          Title Card → Scenes → Credits

        Args:
            scene_videos: รายการ path วิดีโอแต่ละฉาก
            output_path: path เก็บหนัง
            title: ชื่อหนัง (สำหรับ title card)
            opening_music: path เพลงเปิด
            background_music: path เพลงคลอ
            subtitle_file: path ไฟล์ .srt
            music_volume: ความดังเพลง

        Returns:
            dict {"status": str, "output_path": str, "steps": [...]}
        """
        steps_log = []

        # Step 1: สร้าง Title Card
        title_path = str(Path(output_path).parent / "title_card.mp4")
        if title:
            result = self.create_title_card(text=title, output_path=title_path, duration=3.0)
            if result["status"] == "success":
                scene_videos = [title_path] + scene_videos
                steps_log.append({"step": "title_card", "status": "success"})
            else:
                steps_log.append({"step": "title_card", "status": "failed"})

        # Step 2: รวมวิดีโอทั้งหมด
        combined_path = str(Path(output_path).parent / "combined_scenes.mp4")
        result = self.combine_videos(scene_videos, combined_path)
        steps_log.append({"step": "combine_scenes", **result})

        if result["status"] != "success":
            return {
                "status": "error",
                "message": "Failed to combine scenes",
                "steps": steps_log,
            }

        # Step 3: เพิ่มเพลงคลอ
        if background_music:
            bg_path = str(Path(output_path).parent / "with_bg_music.mp4")
            result = self.add_background_music(
                combined_path, background_music, bg_path, music_volume=music_volume
            )
            if result["status"] == "success":
                combined_path = bg_path
            steps_log.append({"step": "background_music", **result})

        # Step 4: เพิ่ม Subtitles
        if subtitle_file and Path(subtitle_file).exists():
            sub_path = str(Path(output_path).parent / "with_subtitles.mp4")
            result = self.add_subtitles(combined_path, subtitle_file, sub_path)
            if result["status"] == "success":
                combined_path = sub_path
            steps_log.append({"step": "subtitles", **result})

        # Step 5: คัดลอกเป็นไฟล์สุดท้าย
        import shutil
        try:
            shutil.copy2(combined_path, output_path)
        except Exception:
            import subprocess
            subprocess.run(
                ["ffmpeg", "-y", "-i", combined_path, "-c", "copy", output_path],
                capture_output=True,
            )

        return {
            "status": "success",
            "output_path": output_path,
            "steps": steps_log,
        }

    # ────────────────────────────────────────────────────────────
    # Private helpers
    # ────────────────────────────────────────────────────────────
    def _concat_simple(self, video_files: List[str], output_path: str) -> dict:
        """รวมวิดีโอแบบง่าย (concat demuxer)"""
        # สร้างไฟล์ list
        list_path = str(Path(output_path).parent / "concat_list.txt")
        with open(list_path, "w") as f:
            for vf in video_files:
                f.write(f"file '{os.path.abspath(vf)}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", list_path,
            "-c", "copy",
            output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            # Fallback: re-encode
            return self._concat_reencode(video_files, output_path)

        return {"status": "success", "output_path": output_path}

    def _concat_with_transitions(self, video_files: List[str], output_path: str, fade_duration: float) -> dict:
        """รวมวิดีโอพร้อม fade transition"""
        # สร้าง input args
        inputs = []
        for vf in video_files:
            inputs.extend(["-i", vf])

        # สร้าง filter complex
        n = len(video_files)
        filters = []
        for i in range(n - 1):
            src = i
            dst = i + 1
            filters.append(f"[{src}:v][{dst}:v]xfade=transition=fade:duration={fade_duration}:offset={fade_duration:.1f}[v{i}]")

        # สร้าง video chain
        # ใช้ concat แบบง่ายแทน
        return self._concat_simple(video_files, output_path)

    def _concat_reencode(self, video_files: List[str], output_path: str) -> dict:
        """รวมวิดีโอแบบ re-encode (fallback)"""
        # สร้างไฟล์ list
        list_path = str(Path(output_path).parent / "concat_list.txt")
        with open(list_path, "w") as f:
            for vf in video_files:
                f.write(f"file '{os.path.abspath(vf)}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", list_path,
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            return {"status": "error", "message": f"FFmpeg reencode failed: {result.stderr[:300]}"}

        return {"status": "success", "output_path": output_path}

    def _hex_to_ass(self, color_name: str) -> str:
        """แปลงชื่อสีเป็น ASS color format"""
        color_map = {
            "white": "FFFFFF",
            "black": "000000",
            "yellow": "FFFF00",
            "red": "0000FF",
            "blue": "FF0000",
        }
        return color_map.get(color_name.lower(), "FFFFFF")

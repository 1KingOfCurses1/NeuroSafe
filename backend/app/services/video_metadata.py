import subprocess
import json
import os
import logging
from typing import Optional
from app.schemas.analysis import VideoMetadata

logger = logging.getLogger(__name__)

class VideoMetadataService:
    """
    Extracts video duration, FPS, and resolution using ffprobe.
    Safely falls back to defaults if ffprobe is unavailable or extraction fails.
    """

    def extract_metadata(self, video_path: str, fallback_filename: Optional[str] = None) -> VideoMetadata:
        """
        Attempts to extract metadata from the given video file.
        Returns a VideoMetadata object with fallback values on error.
        """
        filename = fallback_filename or os.path.basename(video_path) or "demo-video.mp4"
        
        # Default fallback values
        default_metadata = VideoMetadata(
            filename=filename,
            duration_seconds=30.0,
            fps=30.0,
            resolution="1920x1080"
        )

        if not os.path.exists(video_path):
            logger.warning(f"Video file not found at {video_path}. Using fallback metadata.")
            return default_metadata

        try:
            # ffprobe command to get width, height, r_frame_rate, and duration
            cmd = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height,r_frame_rate",
                "-show_entries", "format=duration",
                "-of", "json",
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            
            # Extract duration
            duration = float(data.get("format", {}).get("duration", 30.0))
            
            # Extract stream info
            streams = data.get("streams", [])
            if not streams:
                return default_metadata
            
            video_stream = streams[0]
            width = video_stream.get("width", 1920)
            height = video_stream.get("height", 1080)
            fps_str = video_stream.get("r_frame_rate", "30/1")
            
            # Parse FPS (e.g., "30/1" or "30000/1001")
            fps = self._parse_fps(fps_str)
            
            return VideoMetadata(
                filename=filename,
                duration_seconds=round(duration, 2),
                fps=round(fps, 2),
                resolution=f"{width}x{height}"
            )

        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            logger.warning(f"ffprobe extraction failed for {video_path}: {e}. Trying imageio fallback...")
            return self._extract_with_imageio(video_path, filename, default_metadata)

    def _parse_fps(self, fps_str: str) -> float:
        """
        Parses an FPS string which might be a fraction (e.g., "30/1" or "30000/1001").
        """
        try:
            if "/" in fps_str:
                num, den = map(int, fps_str.split("/"))
                if den == 0:
                    return 30.0
                return num / den
            return float(fps_str)
        except (ValueError, ZeroDivisionError):
            return 30.0

    def _extract_with_imageio(self, video_path: str, filename: str, default: VideoMetadata) -> VideoMetadata:
        """
        Fallback metadata extraction using imageio + imageio-ffmpeg.
        """
        try:
            import imageio.v2 as iio
            reader = iio.get_reader(video_path, "ffmpeg")
            meta = reader.get_meta_data()
            reader.close()

            fps = float(meta.get("fps", 30.0))
            duration = float(meta.get("duration", 30.0))
            size = meta.get("size", (1920, 1080))

            logger.info(f"imageio fallback succeeded: {duration:.1f}s, {fps:.1f}fps, {size[0]}x{size[1]}")
            return VideoMetadata(
                filename=filename,
                duration_seconds=round(duration, 2),
                fps=round(fps, 2),
                resolution=f"{size[0]}x{size[1]}",
            )
        except Exception as e2:
            logger.warning(f"imageio fallback also failed: {e2}. Using hardcoded defaults.")
            return default

video_metadata_service = VideoMetadataService()

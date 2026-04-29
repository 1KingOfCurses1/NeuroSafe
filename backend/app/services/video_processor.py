import subprocess
import json
import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

TRIBE_FRAME_SIZE = 224  # TRIBE v2 expected input resolution
TRIBE_FPS = 1.0         # TRIBE v2 processes at 1 frame per second


class VideoProcessor:
    """
    Extracts frames from a video file using FFmpeg for TRIBE v2 input.

    Outputs JPEG frames at 224x224, 1fps (letter-boxed to preserve aspect ratio).
    Returns a list of BIDS-style event dicts: onset, duration, file_path, trial_type.
    """

    def extract_frames(
        self,
        video_path: str,
        output_dir: str,
        fps: float = TRIBE_FPS,
        max_frames: int = 600,
        frame_size: int = TRIBE_FRAME_SIZE,
    ) -> List[Dict]:
        """
        Extract frames and return a list of event dicts compatible with
        TRIBE v2's get_events_dataframe() input format.
        """
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        frame_pattern = str(out / "frame_%04d.jpg")

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf",
            (
                f"fps={fps},"
                f"scale={frame_size}:{frame_size}:force_original_aspect_ratio=decrease,"
                f"pad={frame_size}:{frame_size}:(ow-iw)/2:(oh-ih)/2:black"
            ),
            "-q:v", "2",
            "-frames:v", str(max_frames),
            frame_pattern,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"FFmpeg frame extraction failed: {result.stderr[:500]}"
            )

        frames = sorted(out.glob("frame_*.jpg"))
        if not frames:
            raise RuntimeError("FFmpeg produced no output frames.")

        events = [
            {
                "onset": float(i) / fps,
                "duration": float(1.0 / fps),
                "file_path": str(f),
                "trial_type": "video_frame",
            }
            for i, f in enumerate(frames)
        ]

        logger.info(
            f"Extracted {len(events)} frames from {video_path} at {fps}fps "
            f"({frame_size}x{frame_size})"
        )
        return events

    def get_video_duration(self, video_path: str) -> float:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json",
            video_path,
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            return float(data["format"]["duration"])
        except Exception as e:
            logger.warning(f"ffprobe failed ({e}). Defaulting to 30s duration.")
            return 30.0


video_processor = VideoProcessor()

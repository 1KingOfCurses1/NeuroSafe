import math
import logging
import os
from typing import Optional, List, Dict

import numpy as np

from app.adapters.base import BaseModelAdapter, RawModelOutput

logger = logging.getLogger(__name__)


class DemoModelAdapter(BaseModelAdapter):
    """
    Smart demo adapter that performs lightweight frame-level flash detection
    on the actual video file.  This means a video with rapid flashing (like
    an epilepsy-warning clip) will score HIGH, while a calm talking-head or
    nature video will score LOW — just like the real TRIBE v2 pipeline would.
    """

    @property
    def provider_name(self) -> str:
        return "demo"

    @property
    def model_name(self) -> str:
        return "neurosafe-demo-flash-detector"

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def analyze_video(
        self, video_path: str, job_id: Optional[str] = None
    ) -> RawModelOutput:
        logger.info(f"Job {job_id}: Smart demo adapter starting on {video_path}")

        analysis = self._analyze_video_frames(video_path)
        duration = analysis["duration"]

        # Build timestamps at 1-second intervals
        n_steps = max(int(duration), 1)
        timestamps = [float(t) for t in range(n_steps + 1)]

        if analysis["flash_timestamps"]:
            logger.info(
                f"Job {job_id}: Detected {len(analysis['flash_timestamps'])} flash events — generating DANGER profile"
            )
            roi_activations = self._generate_danger_activations(timestamps, analysis)
        else:
            logger.info(f"Job {job_id}: No significant flashes — generating SAFE profile")
            roi_activations = self._generate_safe_activations(timestamps)

        vertex_activations = self._build_vertex_data(timestamps, roi_activations)

        output = RawModelOutput(
            duration_seconds=duration,
            timestamps=timestamps,
            roi_activations=roi_activations,
            vertex_activations=vertex_activations,
            model_name=self.model_name,
            model_provider=self.provider_name,
            metadata={
                "video_path": video_path,
                "flash_events_detected": len(analysis["flash_timestamps"]),
                "max_luminance_delta": analysis["max_lum_delta"],
                "video_duration": duration,
                "analysis_type": "flash_detection",
            },
        )
        return self.validate_output(output)

    # ------------------------------------------------------------------
    # Actual video flash detection (lightweight, uses imageio)
    # ------------------------------------------------------------------

    def _analyze_video_frames(self, video_path: str) -> Dict:
        result: Dict = {
            "duration": 30.0,
            "fps": 30.0,
            "resolution": "1920x1080",
            "flash_timestamps": [],
            "max_lum_delta": 0.0,
        }

        if not os.path.exists(video_path):
            logger.warning(f"Video not found at {video_path}, using safe defaults.")
            return result

        try:
            import imageio.v2 as iio

            reader = iio.get_reader(video_path, "ffmpeg")
            meta = reader.get_meta_data()

            fps = float(meta.get("fps", 30.0))
            duration = float(meta.get("duration", 30.0))
            size = meta.get("size", (1920, 1080))

            result["duration"] = round(duration, 2)
            result["fps"] = round(fps, 2)
            result["resolution"] = f"{size[0]}x{size[1]}"

            # Sample ~4 frames per second for flash analysis
            sample_every = max(1, int(fps / 4))
            max_sample_frames = int(fps * min(duration, 120))  # cap at 2 min

            prev_lum = None
            max_delta = 0.0

            for i, frame in enumerate(reader):
                if i >= max_sample_frames:
                    break
                if i % sample_every != 0:
                    continue

                # Luminance via Rec. 601 formula
                lum = float(
                    np.mean(
                        frame[:, :, 0] * 0.299
                        + frame[:, :, 1] * 0.587
                        + frame[:, :, 2] * 0.114
                    )
                )

                if prev_lum is not None:
                    delta = abs(lum - prev_lum)
                    max_delta = max(max_delta, delta)
                    if delta > 20:  # significant luminance swing
                        result["flash_timestamps"].append(
                            {"time": round(i / fps, 2), "delta": round(delta, 2)}
                        )

                prev_lum = lum

            reader.close()
            result["max_lum_delta"] = round(max_delta, 2)
            logger.info(
                f"Flash analysis complete: {len(result['flash_timestamps'])} events, "
                f"max Δlum={max_delta:.1f}, duration={duration:.1f}s"
            )

        except Exception as e:
            logger.warning(f"Video frame analysis failed ({e}). Using safe defaults.")

        return result

    # ------------------------------------------------------------------
    # Activation generators
    # ------------------------------------------------------------------

    def _generate_danger_activations(
        self, timestamps: List[float], analysis: Dict
    ) -> Dict[str, List[float]]:
        flash_times = [f["time"] for f in analysis["flash_timestamps"]]
        flash_deltas = [f["delta"] for f in analysis["flash_timestamps"]]
        max_delta = max(flash_deltas) if flash_deltas else 50.0

        rois = [("V1", 1.0), ("V2", 0.7), ("V3", 0.55), ("V4", 0.35), ("MT+", 0.9)]
        roi_activations: Dict[str, List[float]] = {}

        for roi, sensitivity in rois:
            acts = []
            for t in timestamps:
                val = 0.15 + 0.08 * math.sin(t * 0.3)
                for ft, fd in zip(flash_times, flash_deltas):
                    intensity = (fd / max_delta) * 3.5 * sensitivity
                    spike = intensity * math.exp(-((t - ft) ** 2) / (2 * 0.64))
                    val = max(val, spike)
                acts.append(round(val, 3))
            roi_activations[roi] = acts

        return roi_activations

    def _generate_safe_activations(
        self, timestamps: List[float]
    ) -> Dict[str, List[float]]:
        rois = [("V1", 0.18), ("V2", 0.14), ("V3", 0.11), ("V4", 0.09), ("MT+", 0.15)]
        roi_activations: Dict[str, List[float]] = {}

        for roi, base in rois:
            seed = sum(ord(c) for c in roi)
            acts = [
                round(base + 0.04 * math.sin(t * 0.4 + seed * 0.1), 3)
                for t in timestamps
            ]
            roi_activations[roi] = acts

        return roi_activations

    # ------------------------------------------------------------------
    # Vertex data for 3D brain visualization
    # ------------------------------------------------------------------

    def _build_vertex_data(
        self,
        timestamps: List[float],
        roi_activations: Dict[str, List[float]],
    ) -> List[List[float]]:
        vertex_activations = []
        for i in range(len(timestamps)):
            verts = [0.0] * 20484
            v1 = roi_activations["V1"][i]
            mt = roi_activations["MT+"][i]
            for j in range(1000, 2000):
                verts[j] = v1
            for j in range(5000, 6000):
                verts[j] = mt
            for j in range(11242, 12242):
                verts[j] = v1
            for j in range(15242, 16242):
                verts[j] = mt
            vertex_activations.append(verts)
        return vertex_activations


demo_model_adapter = DemoModelAdapter()

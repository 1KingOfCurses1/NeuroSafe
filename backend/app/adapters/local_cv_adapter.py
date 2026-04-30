import logging
import os
import math
import asyncio
import numpy as np
from typing import Optional, List, Dict, Any
from app.adapters.base import BaseModelAdapter, RawModelOutput

logger = logging.getLogger(__name__)

class LocalCVRiskAdapter(BaseModelAdapter):
    """
    Real local computer vision adapter that analyzes video frames to detect
    photosensitive triggers. Unlike the demo mode, this returns data derived
    from the actual video content.
    """

    @property
    def provider_name(self) -> str:
        return "local_cv"

    @property
    def model_name(self) -> str:
        return "neurosafe-local-cv-risk-analyzer"

    async def analyze_video(self, video_path: str, job_id: Optional[str] = None) -> RawModelOutput:
        logger.info(f"Job {job_id}: LocalCVRiskAdapter starting on {video_path}")
        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Offload heavy CV analysis to a thread
        analysis = await asyncio.to_thread(self._run_cv_analysis, video_path, job_id)
        
        output = RawModelOutput(
            duration_seconds=analysis["duration"],
            timestamps=analysis["timestamps"],
            roi_activations=analysis["roi_activations"],
            vertex_activations=None, 
            model_name=self.model_name,
            model_provider=self.provider_name,
            metadata={
                "inference_source": "local_cv",
                "fallback_used": False,
                "method": "frame_level_photosensitivity_analysis",
                "sample_fps": analysis["sample_fps"],
                "frames_sampled": analysis["frames_sampled"],
                "analysis_note": "Risk features derived from luminance, red-bias, contrast, edge instability, and motion energy."
            }
        )
        return self.validate_output(output)

    def _run_cv_analysis(self, video_path: str, job_id: Optional[str]) -> Dict[str, Any]:
        try:
            import imageio.v2 as iio
        except ImportError:
            raise ImportError("LocalCVRiskAdapter requires 'imageio' and 'imageio-ffmpeg'.")

        logger.info(f"Job {job_id}: Reading video frames for CV analysis...")
        reader = iio.get_reader(video_path, "ffmpeg")
        meta = reader.get_meta_data()
        
        fps = float(meta.get("fps", 30.0))
        duration = float(meta.get("duration", 30.0))
        
        # Sampling configuration: 4 FPS, max 120 samples (~30 seconds of content)
        sample_fps = 4.0
        sample_every = max(1, int(fps / sample_fps))
        max_samples = 120
        
        timestamps = []
        features = {
            "luminance_delta": [],
            "red_delta": [],
            "contrast_delta": [],
            "edge_delta": [],
            "motion_energy": []
        }
        
        prev_frame = None
        prev_lum = None
        prev_red = None
        prev_contrast = None
        prev_edge = None
        
        count = 0
        samples_taken = 0
        
        for frame in reader:
            if count % sample_every == 0:
                t = round(count / fps, 2)
                
                # 1. Luminance (Rec. 601)
                red = frame[:, :, 0].astype(float)
                green = frame[:, :, 1].astype(float)
                blue = frame[:, :, 2].astype(float)
                lum = np.mean(red * 0.299 + green * 0.587 + blue * 0.114)
                
                # 2. Red Intensity / Bias (High saturation red detection)
                red_bias = np.mean(np.maximum(0, red - (green + blue) / 2))
                
                # 3. Contrast (Standard deviation of luminance)
                contrast = np.std(red * 0.299 + green * 0.587 + blue * 0.114)
                
                # 4. Edge Energy (Pattern instability via neighbor diffs)
                gray = 0.299 * red + 0.587 * green + 0.114 * blue
                edge_val = np.mean(np.abs(gray[1:, :] - gray[:-1, :])) + np.mean(np.abs(gray[:, 1:] - gray[:, :-1]))
                
                # Calculate Deltas (Instability/Flicker)
                l_delta = abs(lum - prev_lum) if prev_lum is not None else 0.0
                r_delta = abs(red_bias - prev_red) if prev_red is not None else 0.0
                c_delta = abs(contrast - prev_contrast) if prev_contrast is not None else 0.0
                e_delta = abs(edge_val - prev_edge) if prev_edge is not None else 0.0
                
                # 5. Motion Energy (Mean absolute frame difference)
                if prev_frame is not None:
                    motion = np.mean(np.abs(frame.astype(float) - prev_frame.astype(float)))
                else:
                    motion = 0.0
                
                timestamps.append(t)
                features["luminance_delta"].append(l_delta)
                features["red_delta"].append(r_delta)
                features["contrast_delta"].append(c_delta)
                features["edge_delta"].append(e_delta)
                features["motion_energy"].append(motion)
                
                prev_lum = lum
                prev_red = red_bias
                prev_contrast = contrast
                prev_edge = edge_val
                prev_frame = frame
                
                samples_taken += 1
                if samples_taken >= max_samples:
                    break
            
            count += 1
            
        reader.close()
        
        # Convert raw features to ROI activations (0.0 to 3.2 scale)
        # Thresholds ensure calm videos stay low while intense ones spike.
        roi_activations = {
            "V1": [round(min(3.2, max(0.0, (v - 5.0) * 0.06)), 3) for v in features["luminance_delta"]],
            "V2": [round(min(3.2, max(0.0, (v - 3.0) * 0.1)), 3) for v in features["contrast_delta"]],
            "V3": [round(min(3.2, max(0.0, (v - 2.0) * 0.2)), 3) for v in features["edge_delta"]],
            "V4": [round(min(3.2, max(0.0, (v - 8.0) * 0.08)), 3) for v in features["red_delta"]],
            "MT+": [round(min(3.2, max(0.0, (v - 10.0) * 0.04)), 3) for v in features["motion_energy"]]
        }
        
        logger.info(f"Job {job_id}: CV analysis complete. Samples: {samples_taken}, Duration: {duration}s")
        
        return {
            "duration": duration,
            "timestamps": timestamps,
            "roi_activations": roi_activations,
            "sample_fps": sample_fps,
            "frames_sampled": samples_taken
        }

local_cv_adapter = LocalCVRiskAdapter()

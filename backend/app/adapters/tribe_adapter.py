"""
TRIBE v2 model adapter.

Two execution paths (chosen at runtime based on availability):

  LOCAL    — imports the `tribe_v2` Python package installed in the environment.
              Install:   pip install tribe-v2
              Env var:   TRIBE_MODEL_ID (optional, defaults to "facebook/tribev2")

  ENDPOINT — calls a HuggingFace Inference Endpoint over HTTPS.
              Env vars:  HF_API_URL, HF_API_TOKEN

In both cases the adapter:
  - Extracts video frames at 1fps (VideoProcessor via FFmpeg)
  - Applies a 5-second hemodynamic-lag correction to align BOLD predictions
    with the video frames that caused them
  - Maps the full (n_timesteps, 20484) vertex tensor → per-ROI timeseries (RoiMapper)
  - Stores the full vertex tensor in RawModelOutput.vertex_activations for rendering
"""

import asyncio
import base64
import logging
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.adapters.base import BaseModelAdapter, RawModelOutput
from app.core.config import settings
from app.services.roi_mapper import ROI_NAMES, roi_mapper
from app.services.video_processor import video_processor

logger = logging.getLogger(__name__)

HRF_LAG_SECONDS = 5.0   # BOLD signal peaks ~5 s after neural activation
MODEL_FPS = 1.0          # TRIBE v2 processes at 1 frame per second

try:
    import tribe_v2 as _tribe_pkg
    HAS_TRIBE_PACKAGE = True
    logger.info("tribe_v2 Python package found — will use local inference.")
except ImportError:
    _tribe_pkg = None
    HAS_TRIBE_PACKAGE = False


class TRIBEv2Adapter(BaseModelAdapter):
    """
    Adapter for TRIBE v2 — Meta AI's foundation model for cortical brain encoding.

    Full pipeline:
        video file
          → FFmpeg 1fps 224×224 JPEG frames
          → TRIBE v2 inference  →  (n_timesteps, 20484) activation tensor
          → hemodynamic lag correction (drop first 5 timesteps, realign)
          → Destrieux ROI extraction  →  {"V1": [...], "MT+": [...], ...}
          → RawModelOutput  (roi_activations + vertex_activations)
    """

    @property
    def provider_name(self) -> str:
        return "tribe_v2"

    @property
    def model_name(self) -> str:
        return settings.TRIBE_MODEL_ID or "facebook/tribev2"

    async def analyze_video(
        self, video_path: str, job_id: Optional[str] = None
    ) -> RawModelOutput:
        logger.info(f"Job {job_id}: TRIBE v2 pipeline starting on {video_path}")

        with tempfile.TemporaryDirectory() as tmpdir:
            # Step 1: Extract 1fps frames
            logger.info(f"Job {job_id}: Extracting 1fps frames via FFmpeg...")
            events = video_processor.extract_frames(
                video_path=video_path,
                output_dir=str(Path(tmpdir) / "frames"),
                fps=MODEL_FPS,
            )
            if not events:
                raise RuntimeError("No frames extracted from video.")
            logger.info(f"Job {job_id}: {len(events)} frames ready.")

            # Step 2: Inference
            if HAS_TRIBE_PACKAGE:
                preds, raw_ts = await self._infer_local(events, tmpdir)
            else:
                preds, raw_ts = await self._infer_hf_endpoint(events, job_id)
            # preds: (n_timesteps, n_vertices) float32

            logger.info(
                f"Job {job_id}: Inference complete — "
                f"shape {preds.shape}, range [{preds.min():.3f}, {preds.max():.3f}]"
            )

            # Step 3: Hemodynamic lag correction
            preds_corr, timestamps = self._apply_hrf_lag(preds, raw_ts)

            # Step 4: ROI extraction
            logger.info(f"Job {job_id}: Mapping vertices to V1/V2/V3/V4/MT+ ROIs...")
            roi_activations = roi_mapper.extract_roi_timeseries(preds_corr, ROI_NAMES)

            duration = timestamps[-1] if timestamps else float(len(events))

            return self.validate_output(
                RawModelOutput(
                    duration_seconds=duration,
                    timestamps=timestamps,
                    roi_activations=roi_activations,
                    vertex_activations=preds_corr.tolist(),
                    model_name=self.model_name,
                    model_provider=self.provider_name,
                    metadata={
                        "video_path": video_path,
                        "n_frames_extracted": len(events),
                        "n_vertices": preds.shape[1],
                        "hrf_lag_seconds": HRF_LAG_SECONDS,
                        "inference_path": "local" if HAS_TRIBE_PACKAGE else "hf_endpoint",
                    },
                )
            )

    # ------------------------------------------------------------------
    # Local inference (tribe_v2 Python package)
    # ------------------------------------------------------------------

    async def _infer_local(
        self, events: List[Dict], tmpdir: str
    ) -> Tuple[np.ndarray, List[float]]:
        import pandas as pd

        logger.info("Running TRIBE v2 local inference...")
        df = pd.DataFrame(events)

        model = await asyncio.to_thread(
            _tribe_pkg.TRIBEv2.from_pretrained, self.model_name
        )

        # Returns (preds, segments); preds.shape == (n_timesteps, 20480)
        preds_raw, _segments = await asyncio.to_thread(model.predict, events=df)
        preds = np.asarray(preds_raw, dtype=np.float32)

        timestamps = [float(e["onset"]) for e in events[: preds.shape[0]]]
        return preds, timestamps

    # ------------------------------------------------------------------
    # HuggingFace Inference Endpoint
    # ------------------------------------------------------------------

    async def _infer_hf_endpoint(
        self, events: List[Dict], job_id: Optional[str]
    ) -> Tuple[np.ndarray, List[float]]:
        if not settings.HF_API_URL or not settings.HF_API_TOKEN:
            raise RuntimeError(
                "TRIBE v2 requires the tribe_v2 Python package (pip install tribe-v2) "
                "or HF_API_URL + HF_API_TOKEN set in .env for the HF endpoint."
            )

        import httpx

        logger.info(f"Job {job_id}: Calling HF endpoint {settings.HF_API_URL}")

        frame_payloads: List[Dict] = []
        for ev in events:
            try:
                with open(ev["file_path"], "rb") as fh:
                    frame_payloads.append(
                        {
                            "onset": ev["onset"],
                            "duration": ev["duration"],
                            "image_b64": base64.b64encode(fh.read()).decode("utf-8"),
                        }
                    )
            except Exception as e:
                logger.warning(f"Skipping frame {ev['file_path']}: {e}")

        payload = {"inputs": {"events": frame_payloads}}

        async with httpx.AsyncClient(timeout=httpx.Timeout(360.0)) as client:
            resp = await client.post(
                settings.HF_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.HF_API_TOKEN}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if resp.status_code != 200:
            raise RuntimeError(
                f"HF endpoint returned {resp.status_code}: {resp.text[:300]}"
            )

        preds = self._parse_hf_response(resp.json())
        timestamps = [float(ev["onset"]) for ev in events[: preds.shape[0]]]
        return preds, timestamps

    def _parse_hf_response(self, data: Any) -> np.ndarray:
        """Accept several plausible shapes from a deployed HF endpoint."""
        if isinstance(data, dict):
            for key in ("predictions", "preds", "activations", "output"):
                if key in data:
                    val = data[key]
                    if isinstance(val, dict) and "activations" in val:
                        val = val["activations"]
                    return np.asarray(val, dtype=np.float32)
        if isinstance(data, list):
            return np.asarray(data, dtype=np.float32)
        raise RuntimeError(
            f"Cannot parse HF response. "
            f"Keys: {list(data.keys()) if isinstance(data, dict) else type(data)}"
        )

    # ------------------------------------------------------------------
    # Hemodynamic lag correction
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_hrf_lag(
        preds: np.ndarray, timestamps: List[float]
    ) -> Tuple[np.ndarray, List[float]]:
        """
        Drop the first HRF_LAG_SECONDS rows (unstable early BOLD predictions
        influenced by pre-stimulus cortical state) and realign remaining
        predictions with the video timestamps that caused them.
        """
        lag_samples = int(HRF_LAG_SECONDS * MODEL_FPS)
        if lag_samples >= len(timestamps):
            return preds, timestamps
        corrected = preds[lag_samples:]
        return corrected, timestamps[: len(corrected)]


tribe_v2_adapter = TRIBEv2Adapter()

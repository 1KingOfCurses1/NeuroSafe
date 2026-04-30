import logging
import os
import sys
import asyncio
from typing import Optional, Dict, Any, List, Tuple
import numpy as np

from app.adapters.base import BaseModelAdapter, RawModelOutput
from app.core.config import settings
from app.services.roi_mapper import roi_mapper, ROI_NAMES

logger = logging.getLogger(__name__)

# TRIBE v2 README states: "Predictions ... are offset by 5 seconds in the past, 
# in order to compensate for the hemodynamic lag."
# This implies the model output is already aligned with the stimuli.
HRF_LAG_SECONDS = 5.0 

class TribeV2Adapter(BaseModelAdapter):
    """
    Adapter for the real TRIBE v2 model.
    Interfaces with the local 'tribev2' package/repository.
    """
    _model = None

    @property
    def provider_name(self) -> str:
        return "tribev2"

    @property
    def model_name(self) -> str:
        return "tribe-v2"

    def _ensure_tribe_imported(self):
        """Ensure the tribev2 package is available in sys.path."""
        try:
            from tribev2 import TribeModel
            return TribeModel
        except ImportError:
            repo_path = settings.TRIBEV2_LOCAL_REPO_PATH
            if os.path.exists(repo_path):
                if repo_path not in sys.path:
                    logger.info(f"Adding local TRIBE v2 repo path to sys.path: {repo_path}")
                    sys.path.append(repo_path)
                from tribev2 import TribeModel
                return TribeModel
            else:
                logger.error(f"TRIBE v2 repo not found at {repo_path}")
                raise ImportError(f"Could not find 'tribev2' package or repo at {repo_path}")

    async def analyze_video(self, video_path: str, job_id: Optional[str] = None) -> RawModelOutput:
        logger.info(f"Job {job_id}: TribeV2Adapter starting on {video_path}")
        
        try:
            TribeModel = self._ensure_tribe_imported()
        except Exception as e:
            logger.error(f"Job {job_id}: Failed to import TRIBE v2: {e}")
            raise e
        
        if self._model is None:
            logger.info(f"Job {job_id}: Loading TRIBE v2 model weights (facebook/tribev2)...")
            try:
                # Model loading is blocking and heavy, run in thread
                self._model = await asyncio.to_thread(
                    TribeModel.from_pretrained,
                    "facebook/tribev2",
                    cache_folder=settings.TRIBEV2_CACHE_DIR
                )
                logger.info(f"Job {job_id}: Model loaded successfully.")
            except Exception as e:
                logger.error(f"Job {job_id}: Failed to load TRIBE v2 model: {e}")
                raise e

        model = self._model

        # Step 1: Extract events dataframe
        logger.info(f"Job {job_id}: Extracting video events...")
        try:
            df = await asyncio.to_thread(model.get_events_dataframe, video_path=video_path)
        except Exception as e:
            logger.error(f"Job {job_id}: Failed to extract events: {e}")
            raise e
        
        # Step 2: Predict brain activity
        logger.info(f"Job {job_id}: Running inference...")
        try:
            # preds: (n_timesteps, n_vertices), segments: list of segment objects
            preds, segments = await asyncio.to_thread(model.predict, events=df, verbose=False)
        except Exception as e:
            logger.error(f"Job {job_id}: Inference failed: {e}")
            raise e
        
        # Build timestamps from segments
        timestamps = [float(s.offset) for s in segments]
        
        if len(timestamps) != preds.shape[0]:
            logger.warning(f"Job {job_id}: Timestamps length ({len(timestamps)}) != Preds length ({preds.shape[0]}). Truncating.")
            min_len = min(len(timestamps), preds.shape[0])
            timestamps = timestamps[:min_len]
            preds = preds[:min_len]

        # Step 3: ROI Mapping (Backend-side aggregation)
        # Note: No official ROI mapper was found in the tribev2 repo, 
        # so we use the NeuroSafe backend's Destrieux-based RoiMapper.
        logger.info(f"Job {job_id}: Aggregating vertex predictions to ROIs...")
        roi_activations = roi_mapper.extract_roi_timeseries(preds, ROI_NAMES)
        
        # Construct output
        output = RawModelOutput(
            duration_seconds=float(timestamps[-1] - timestamps[0]) if timestamps else 0.0,
            timestamps=timestamps,
            roi_activations=roi_activations,
            vertex_activations=preds.tolist(),
            model_name=self.model_name,
            model_provider=self.provider_name,
            metadata={
                "video_path": video_path,
                "n_vertices": preds.shape[1],
                "n_timesteps": len(timestamps),
                "mapping_source": "NeuroSafe Backend (Destrieux Atlas on fsaverage5)",
                "note": "Temporary vertex aggregation used as no official ROI mapper was found in TRIBE v2 repo."
            }
        )
        
        return self.validate_output(output)

tribe_v2_adapter = TribeV2Adapter()

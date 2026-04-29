import logging
from typing import Optional, Dict, Any
from app.adapters.base import BaseModelAdapter, RawModelOutput
from app.core.config import settings

logger = logging.getLogger(__name__)

class HuggingFaceModelAdapter(BaseModelAdapter):
    """
    Adapter for Hugging Face Inference Endpoints.
    This is currently a stub for Developer 1 to plug into.
    
    Expected Future Response Shape:
    {
        "duration_seconds": 30.0,
        "timestamps": [0.0, 1.0, 2.0, ...],
        "roi_activations": {
            "V1": [0.1, 0.2, 2.8, ...],
            "V2": [0.1, 0.2, 2.1, ...],
            "V3": [0.1, 0.2, 1.7, ...],
            "V4": [0.1, 0.2, 1.2, ...],
            "MT+": [0.1, 0.3, 2.6, ...]
        },
        "model_name": "tribe-v2-hf"
    }
    """

    @property
    def provider_name(self) -> str:
        return "huggingface"

    @property
    def model_name(self) -> str:
        # Use the URL as a proxy for the model name if not explicitly set
        if settings.HF_API_URL:
            return settings.HF_API_URL.split("/")[-1] or "huggingface-model"
        return "huggingface-model"

    async def analyze_video(self, video_path: str, job_id: Optional[str] = None) -> RawModelOutput:
        """
        Stub for video analysis via Hugging Face.
        This will be implemented once Dev 1 provides the final model API contract.
        """
        # 1. Check Configuration
        if not settings.HF_API_URL or not settings.HF_API_TOKEN:
            logger.error("Hugging Face adapter called but HF_API_URL or HF_API_TOKEN is missing.")
            raise RuntimeError(
                "Hugging Face adapter is not configured. "
                "Please set HF_API_URL and HF_API_TOKEN in your .env file."
            )

        # 2. TODO: Implement HTTP call to Hugging Face Inference Endpoint
        # Example using httpx:
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(...)
        #     return self._parse_hf_response(response.json())

        logger.warning(f"analyze_video called for {video_path} but Hugging Face adapter is still a stub.")
        raise NotImplementedError(
            "Hugging Face model inference is not yet implemented. "
            "Developer 1 needs to provide the final API response contract."
        )

    def _parse_hf_response(self, response_json: Dict[str, Any]) -> RawModelOutput:
        """
        TODO: Implement parsing logic once the model output format is stable.
        
        Developer 1 Note:
        The model must return timestamp-aligned ROI activations for:
        V1, V2, V3, V4, and MT+.
        """
        # Example parsing:
        # return RawModelOutput(
        #     duration_seconds=response_json["duration_seconds"],
        #     timestamps=response_json["timestamps"],
        #     roi_activations=response_json["roi_activations"],
        #     model_name=self.model_name,
        #     model_provider=self.provider_name
        # )
        raise NotImplementedError("Hugging Face response parsing is not yet implemented.")

huggingface_model_adapter = HuggingFaceModelAdapter()

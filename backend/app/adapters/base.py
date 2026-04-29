from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator

class RawModelOutput(BaseModel):
    """
    Internal contract for model output.
    All adapters must return data in this format.
    """
    duration_seconds: float
    timestamps: List[float]
    roi_activations: Dict[str, List[float]] = Field(
        ..., 
        description="Dictionary mapping ROI names (V1, V2, V3, V4, MT+) to activation lists."
    )
    model_name: str
    model_provider: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamps")
    @classmethod
    def timestamps_not_empty(cls, v: List[float]) -> List[float]:
        if not v:
            raise ValueError("timestamps list cannot be empty")
        return v

    @field_validator("roi_activations")
    @classmethod
    def validate_roi_lengths(cls, v: Dict[str, List[float]], info) -> Dict[str, List[float]]:
        # Access timestamps from the data if available
        # Note: In Pydantic v2, we use 'info' or access 'v' after other fields.
        # However, it's easier to check after the model is initialized or use a model_validator.
        return v

    @field_validator("roi_activations")
    @classmethod
    def validate_required_rois(cls, v: Dict[str, List[float]]) -> Dict[str, List[float]]:
        required = {"V1", "V2", "V3", "V4", "MT+"}
        missing = required - set(v.keys())
        if missing:
            # We don't strictly enforce yet as per requirements, but let's warn or pass.
            pass
        return v

class BaseModelAdapter(ABC):
    """
    Abstract base class for all model adapters.
    This interface is the contract between Dev 1's model 
    and Dev 3's backend integration layer.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g., 'demo', 'huggingface', 'local')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the specific model being used."""
        pass

    @abstractmethod
    async def analyze_video(self, video_path: str, job_id: Optional[str] = None) -> RawModelOutput:
        """
        Runs the model analysis on a video file.
        The output must be timestamp-aligned for brain visualization.
        """
        pass

    def validate_output(self, output: RawModelOutput) -> RawModelOutput:
        """Optional helper to perform additional validation on the output."""
        if len(output.timestamps) == 0:
            raise ValueError("Model output has no timestamps.")
        
        for roi, activations in output.roi_activations.items():
            if len(activations) != len(output.timestamps):
                raise ValueError(f"ROI {roi} activation length does not match timestamp length.")
        
        return output

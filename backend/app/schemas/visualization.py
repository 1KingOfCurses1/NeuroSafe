from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.jobs import JobStatus

class BrainFrame(BaseModel):
    timestamp: float
    roi_activations: Dict[str, float]
    max_activation: float
    danger_level: str
    image_b64: Optional[str] = None  # base64 PNG from nilearn; None in demo mode

class BrainVisualizationPayload(BaseModel):
    job_id: str
    frames: List[BrainFrame]
    color_map: str = "deep-blue-yellow-red"
    timestamp_unit: str = "seconds"

class ProgressEvent(BaseModel):
    job_id: str
    status: JobStatus
    progress: int
    message: str
    timestamp: Optional[datetime] = None
    brain_frame: Optional[BrainFrame] = None

    model_config = ConfigDict(from_attributes=True)

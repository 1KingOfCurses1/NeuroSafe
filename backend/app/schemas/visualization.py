from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from app.schemas.jobs import JobStatus

class BrainFrame(BaseModel):
    timestamp: float
    roi_activations: Dict[str, float]
    max_activation: float
    danger_level: str

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
    timestamp: Optional[str] = None
    brain_frame: Optional[BrainFrame] = None

from enum import Enum
from typing import Optional, TYPE_CHECKING
from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from app.schemas.analysis import AnalysisResult

class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    EXTRACTING_METADATA = "extracting_metadata"
    RUNNING_MODEL = "running_model"
    SCORING_DANGER = "scoring_danger"
    GENERATING_VISUALIZATION = "generating_visualization"
    GENERATING_REPORT = "generating_report"
    COMPLETED = "completed"
    FAILED = "failed"

class SourceType(str, Enum):
    UPLOAD = "upload"
    YOUTUBE = "youtube"
    DEMO = "demo"

class JobCreateResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: int
    message: str
    result: Optional["AnalysisResult"] = None
    error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

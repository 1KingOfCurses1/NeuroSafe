from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.schemas.jobs import JobStatus
from app.schemas.reports import GeminiReport
from app.schemas.visualization import BrainVisualizationPayload

class YouTubeAnalyzeRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def url_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("URL cannot be empty")
        return v

class VideoMetadata(BaseModel):
    filename: str
    duration_seconds: float
    fps: float
    resolution: str

class DangerSegment(BaseModel):
    start_time: float
    end_time: float
    peak_time: float
    roi: str
    activation_level: float
    threshold: float
    severity: str
    reason: str

class AnalysisSummary(BaseModel):
    severity: str
    segments_detected: int
    total_danger_duration_seconds: float

class RoiTimeSeries(BaseModel):
    timestamps: List[float]
    V1: List[float]
    V2: List[float]
    V3: List[float]
    V4: List[float]
    MT_plus: List[float] = Field(..., serialization_alias="MT+")

    model_config = ConfigDict(populate_by_name=True)

class AnalysisResult(BaseModel):
    job_id: str
    status: JobStatus
    video: VideoMetadata
    danger_score: int
    summary: AnalysisSummary
    danger_segments: List[DangerSegment]
    roi_timeseries: RoiTimeSeries
    gemini_report: GeminiReport
    brain_visualization: Optional[BrainVisualizationPayload] = None

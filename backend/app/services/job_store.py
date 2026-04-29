import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.jobs import JobStatus, SourceType
from app.schemas.analysis import AnalysisResult

class JobNotFoundError(Exception):
    """Raised when a job is not found in the store."""
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.message = f"Job {job_id} not found."
        super().__init__(self.message)

class AnalysisJob(BaseModel):
    job_id: str
    status: JobStatus
    progress: int = 0
    source_type: SourceType
    source_name: str
    created_at: str
    updated_at: str
    message: str = ""
    result: Optional[AnalysisResult] = None
    error: Optional[str] = None

class JobStore:
    def __init__(self):
        self._jobs: Dict[str, AnalysisJob] = {}

    def _get_now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _clamp_progress(self, progress: int) -> int:
        return max(0, min(100, progress))

    def create_job(
        self, 
        source_type: SourceType, 
        source_name: str, 
        message: str = "Job created"
    ) -> AnalysisJob:
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        now = self._get_now_iso()
        
        job = AnalysisJob(
            job_id=job_id,
            status=JobStatus.QUEUED,
            progress=0,
            source_type=source_type,
            source_name=source_name,
            created_at=now,
            updated_at=now,
            message=message
        )
        self._jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> Optional[AnalysisJob]:
        return self._jobs.get(job_id)

    def update_job(
        self, 
        job_id: str, 
        status: Optional[JobStatus] = None, 
        progress: Optional[int] = None, 
        message: Optional[str] = None, 
        error: Optional[str] = None
    ) -> AnalysisJob:
        job = self.get_job(job_id)
        if not job:
            raise JobNotFoundError(job_id)

        if status:
            job.status = status
            if status == JobStatus.COMPLETED:
                job.progress = 100
            elif status == JobStatus.FAILED:
                # We can keep progress as is or set to 100. 
                # Let's keep it as is unless progress is also provided.
                pass

        if progress is not None:
            job.progress = self._clamp_progress(progress)

        if message is not None:
            job.message = message

        if error is not None:
            job.error = error

        job.updated_at = self._get_now_iso()
        return job

    def set_result(self, job_id: str, result: AnalysisResult) -> AnalysisJob:
        job = self.get_job(job_id)
        if not job:
            raise JobNotFoundError(job_id)

        job.result = result
        job.status = JobStatus.COMPLETED
        job.progress = 100
        job.updated_at = self._get_now_iso()
        return job

    def fail_job(self, job_id: str, error: str, message: str = "Job failed") -> AnalysisJob:
        job = self.get_job(job_id)
        if not job:
            raise JobNotFoundError(job_id)

        job.status = JobStatus.FAILED
        job.error = error
        job.message = message
        job.updated_at = self._get_now_iso()
        return job

    def delete_job(self, job_id: str) -> bool:
        if job_id in self._jobs:
            del self._jobs[job_id]
            return True
        return False

    def list_jobs(self) -> List[AnalysisJob]:
        return list(self._jobs.values())

job_store = JobStore()

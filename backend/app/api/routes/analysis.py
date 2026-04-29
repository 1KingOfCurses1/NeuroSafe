import shutil
import os
import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from app.schemas.jobs import JobCreateResponse, SourceType, JobStatusResponse, JobStatus
from app.schemas.analysis import YouTubeAnalyzeRequest
from app.services.job_store import job_store
from app.services.orchestrator import analysis_orchestrator
from app.services.youtube_downloader import youtube_downloader_service
from app.core.config import settings
from app.core.exceptions import (
    JobNotFoundAPIError, 
    ValidationAPIError, 
    UploadAPIError
)

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

async def _run_youtube_analysis_task(job_id: str, url: str):
    """
    Background task to download YouTube video and then run analysis.
    """
    try:
        # 1. Update status: Downloading
        job_store.update_job(
            job_id, 
            status=JobStatus.PROCESSING, 
            progress=5, 
            message="Downloading YouTube video..."
        )
        
        # 2. Attempt Download
        try:
            video_path = youtube_downloader_service.download(url, job_id)
            job_store.update_job(
                job_id, 
                message=f"Download complete: {os.path.basename(video_path)}. Starting analysis..."
            )
        except Exception as download_error:
            logger.warning(f"YouTube download failed for job {job_id}: {download_error}. Falling back to demo mode.")
            job_store.update_job(
                job_id, 
                message="YouTube download failed. Proceeding with demo analysis fallback..."
            )
            # We continue anyway to keep the hackathon demo resilient

        # 3. Run Analysis Orchestrator
        await analysis_orchestrator.run_demo_analysis(job_id)

    except Exception as e:
        logger.error(f"Background task failed for job {job_id}: {e}")
        job_store.fail_job(job_id, error=str(e), message="Background analysis failed")

@router.post("/upload", response_model=JobCreateResponse)
async def analyze_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    # 1. Basic Validation
    if not file.filename:
        raise ValidationAPIError(message="Filename is empty")
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise ValidationAPIError(
            message=f"Unsupported file extension. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
            details={"allowed": list(ALLOWED_EXTENSIONS), "provided": file_ext}
        )

    # 2. Create Job
    job = job_store.create_job(
        source_type=SourceType.UPLOAD,
        source_name=file.filename,
        message="Video accepted. Analysis starting..."
    )

    # 3. Save File
    try:
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / f"{job.job_id}_{file.filename}"
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
    except Exception as e:
        job_store.fail_job(job.job_id, error=str(e), message="Failed to save uploaded file")
        raise UploadAPIError(message=f"Could not save file: {e}")

    # 4. Start Background Analysis
    background_tasks.add_task(analysis_orchestrator.run_demo_analysis, job.job_id)

    return JobCreateResponse(
        job_id=job.job_id,
        status=job.status,
        message="Video accepted. Analysis started."
    )

@router.post("/youtube", response_model=JobCreateResponse)
async def analyze_youtube(
    request: YouTubeAnalyzeRequest,
    background_tasks: BackgroundTasks
):
    # 1. Basic URL Validation
    url = request.url.lower()
    youtube_domains = ["youtube.com", "youtu.be"]
    
    is_valid = any(domain in url for domain in youtube_domains)
    if not is_valid:
        raise ValidationAPIError(
            message="Invalid YouTube URL. Please provide a link from youtube.com or youtu.be",
            details={"provided_url": request.url}
        )

    # 2. Create Job
    job = job_store.create_job(
        source_type=SourceType.YOUTUBE,
        source_name=request.url,
        message="YouTube URL accepted. Queuing download..."
    )

    # 3. Start Background Download & Analysis
    background_tasks.add_task(_run_youtube_analysis_task, job.job_id, request.url)

    return JobCreateResponse(
        job_id=job.job_id,
        status=job.status,
        message="YouTube URL accepted. Analysis started."
    )

@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_analysis_result(job_id: str):
    job = job_store.get_job(job_id)
    if not job:
        raise JobNotFoundAPIError(job_id=job_id)

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        message=job.message,
        result=job.result,
        error=job.error
    )

@router.get("/demo/config")
async def get_demo_config():
    """
    Returns the current demo mode configuration.
    Useful for judges and teammates to verify the environment.
    """
    return {
        "model_provider": settings.MODEL_PROVIDER,
        "is_demo_mode": settings.is_demo_mode,
        "external_services_required": False if settings.is_demo_mode else True,
        "features": {
            "file_upload": True,
            "youtube_url": True,
            "websocket_progress": True,
            "deterministic_results": settings.is_demo_mode,
            "gemini_reports": "active" if settings.GEMINI_API_KEY else "fallback_mode"
        }
    }

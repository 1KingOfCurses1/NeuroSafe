import shutil
import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from app.schemas.jobs import JobCreateResponse, SourceType, JobStatusResponse
from app.schemas.analysis import YouTubeAnalyzeRequest
from app.services.job_store import job_store
from app.services.orchestrator import analysis_orchestrator
from app.core.config import settings

router = APIRouter()

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

@router.post("/upload", response_model=JobCreateResponse)
async def analyze_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    # 1. Basic Validation
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is empty")
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file extension. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
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
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")

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
        raise HTTPException(
            status_code=400, 
            detail="Invalid YouTube URL. Please provide a link from youtube.com or youtu.be"
        )

    # 2. Create Job
    job = job_store.create_job(
        source_type=SourceType.YOUTUBE,
        source_name=request.url,
        message="YouTube URL accepted. Analysis starting..."
    )

    # 3. Start Background Analysis
    background_tasks.add_task(analysis_orchestrator.run_demo_analysis, job.job_id)

    return JobCreateResponse(
        job_id=job.job_id,
        status=job.status,
        message="YouTube URL accepted. Analysis started."
    )

@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_analysis_result(job_id: str):
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        message=job.message,
        result=job.result,
        error=job.error
    )

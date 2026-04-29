import shutil
import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from app.schemas.jobs import JobCreateResponse, SourceType
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

@router.post("/youtube")
async def analyze_youtube():
    return {
        "message": "Analysis endpoint scaffolded. Job orchestration will be implemented in a later branch."
    }

@router.get("/{job_id}")
async def get_analysis_result(job_id: str):
    return {
        "job_id": job_id,
        "message": "Analysis endpoint scaffolded. Job orchestration will be implemented in a later branch."
    }

# NeuroSafe Backend

## Project Summary
NeuroSafe is a web application that screens videos and YouTube URLs for photosensitive epilepsy seizure triggers.

## Backend Role/Scope
The backend is responsible for:
- Creating analysis jobs.
- Extracting/receiving video metadata.
- Orchestrating model inference via model adapters.
- Converting model data into danger segments.
- Generating clinical reports using Gemini.
- Providing a stable REST/WebSocket API for the React frontend.

## Setup Instructions

### 1. Create a Virtual Environment
```bash
cd backend
python -m venv .venv
```

### 2. Activate the Virtual Environment
- **Windows:**
  ```powershell
  .venv\Scripts\activate
  ```
- **macOS/Linux:**
  ```bash
  source .venv/bin/activate
  ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Copy `.env.example` to `.env` and fill in the required values.
```bash
cp .env.example .env
```
Default `MODEL_PROVIDER=demo` is used for development/testing without real model access.

## Running the Backend
```bash
uvicorn app.main:app --reload
```

## Testing
- **Health Check:** `curl http://localhost:8000/health`
- **Interactive Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Job Store Test:**
  ```bash
  python -c "from app.services.job_store import job_store; from app.schemas.jobs import SourceType, JobStatus; j=job_store.create_job(SourceType.DEMO, 'demo-video.mp4'); print(j.job_id, j.status, j.progress); job_store.update_job(j.job_id, status=JobStatus.PROCESSING, progress=50, message='Processing'); print(job_store.get_job(j.job_id).status, job_store.get_job(j.job_id).progress); print(len(job_store.list_jobs()))"
  ```
- **Orchestrator Test:**
  ```bash
  python -c "import asyncio; from app.services.job_store import job_store; from app.schemas.jobs import SourceType; from app.services.orchestrator import analysis_orchestrator; j=job_store.create_job(SourceType.DEMO, 'demo-video.mp4'); result=asyncio.run(analysis_orchestrator.run_demo_analysis(j.job_id)); print(result.job_id, result.status, result.danger_score); print(job_store.get_job(j.job_id).status, job_store.get_job(j.job_id).progress); print(result.brain_visualization.frames[0].timestamp, result.roi_timeseries.timestamps[0])"
  ```

## Note
This is an initial scaffold. Model integration, job orchestration, Gemini integration, yt-dlp, and danger scoring will be added in later branches.

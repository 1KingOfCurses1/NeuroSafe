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

## Demo Mode
By default, the backend runs in **Demo Mode** (`MODEL_PROVIDER=demo`). This mode is designed for hackathon presentations and local testing.

### Key Features
- **Zero Configuration**: Works out of the box without Hugging Face or Gemini API keys.
- **Deterministic Data**: Uses realistic activation patterns for V1, V2, V3, V4, and MT+ regions.
- **Full Pipeline Support**: Supports both direct MP4 uploads and YouTube URL submissions.
- **Robust Fallbacks**: 
    - If `ffprobe` is missing, defaults to 1080p/30fps metadata.
    - If `yt-dlp` fails, falls back to demo analysis data.
    - If `GEMINI_API_KEY` is missing, uses a local rule-based report generator.

### Verification Commands
Check configuration:
```bash
curl http://localhost:8000/api/analyze/demo/config
```

Run a YouTube test:
```bash
curl.exe -X POST http://localhost:8000/api/analyze/youtube -H "Content-Type: application/json" -d "{\"url\":\"https://www.youtube.com/watch?v=dQw4w9WgXcQ\"}"
```

Poll for results (replace `JOB_ID`):
```bash
curl http://localhost:8000/api/analyze/JOB_ID
```

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
- **Upload Test (Windows):**
  ```powershell
  echo "fake video content" > test.mp4
  curl.exe -X POST http://localhost:8000/api/analyze/upload -F "file=@test.mp4"
  ```
- **YouTube Test:**
  ```powershell
  curl.exe -X POST http://localhost:8000/api/analyze/youtube -H "Content-Type: application/json" -d "{\"url\":\"https://www.youtube.com/watch?v=dQw4w9WgXcQ\"}"
  ```
- **Invalid URL Test:**
  ```powershell
  curl.exe -X POST http://localhost:8000/api/analyze/youtube -H "Content-Type: application/json" -d "{\"url\":\"https://example.com/video\"}"
  ```
- **Polling Status & Results:**
  1. Submit a job (Upload or YouTube).
  2. Copy the `job_id` from the response.
  3. Poll the status:
     ```powershell
     curl.exe http://localhost:8000/api/analyze/{job_id}
     ```
  4. After ~1-2 seconds, the `status` will be `completed` and the `result` field will be populated.
- **Model Adapter Interface Test:**
  ```bash
  python -c "from app.adapters import BaseModelAdapter, RawModelOutput; output=RawModelOutput(duration_seconds=10.0, timestamps=[0.0, 5.0, 10.0], roi_activations={'V1':[0.1,0.5,0.2],'V2':[0.1,0.4,0.2],'V3':[0.1,0.3,0.2],'V4':[0.1,0.2,0.2],'MT+':[0.1,0.6,0.2]}, model_name='test-model', model_provider='demo'); print(output.model_name, output.roi_activations['MT+'][1])"
  ```
- **Demo Model Adapter Test:**
  ```bash
  python -c "import asyncio; from app.adapters import demo_model_adapter; output=asyncio.run(demo_model_adapter.analyze_video('demo.mp4')); print(output.model_name, output.model_provider, output.duration_seconds); print(len(output.timestamps), len(output.roi_activations['V1'])); print(max(output.roi_activations['V1']), max(output.roi_activations['MT+']))"
  ```
- **Hugging Face Adapter Stub Test:**
  ```bash
  python -c "from app.adapters import huggingface_model_adapter; print(huggingface_model_adapter.provider_name, huggingface_model_adapter.model_name)"
  ```
- **Danger Scoring Service Test:**
  ```bash
  python -c "import asyncio; from app.adapters import demo_model_adapter; from app.services.danger_scoring import danger_scoring_service; output=asyncio.run(demo_model_adapter.analyze_video('demo.mp4')); score, summary, segments=danger_scoring_service.score_model_output(output); print(f'Score: {score}', f'Severity: {summary.severity}', f'Segments: {summary.segments_detected}'); print(f'First Segment: {segments[0].roi} at {segments[0].start_time}s, Peak: {segments[0].activation_level}')"
  ```
- **Result Formatter Service Test:**
  ```bash
  python -c "import asyncio; from app.adapters import demo_model_adapter; from app.services.danger_scoring import danger_scoring_service; from app.services.result_formatter import result_formatter; output=asyncio.run(demo_model_adapter.analyze_video('demo.mp4')); score, summary, segments=danger_scoring_service.score_model_output(output); result=result_formatter.format_analysis_result('job_test', output, score, summary, segments); print(result.job_id, result.status, result.danger_score); print(result.roi_timeseries.timestamps[0], result.brain_visualization.frames[0].timestamp); print(result.roi_timeseries.MT_plus[0], result.brain_visualization.frames[0].roi_activations['MT+']); print(result.gemini_report.headline)"
  ```
- **Gemini Report Service Test (Fallback Mode):**
  ```bash
  python -c "import asyncio; from app.schemas.analysis import AnalysisSummary, DangerSegment, VideoMetadata; from app.services.gemini_service import gemini_report_service; summary=AnalysisSummary(severity='high', segments_detected=1, total_danger_duration_seconds=3.0); seg=[DangerSegment(start_time=14.0,end_time=17.0,peak_time=15.5,roi='V1',activation_level=3.1,threshold=2.0,severity='critical',reason='Activation exceeded threshold')]; video=VideoMetadata(filename='demo.mp4',duration_seconds=30.0,fps=30.0,resolution='1920x1080'); report=asyncio.run(gemini_report_service.generate_report(87, summary, seg, video)); print(report.headline); print(report.findings[0]); print(report.recommended_actions[0])"
  ```
- **Video Metadata Service Test (Fallback Mode):**
  ```bash
  python -c "from app.services.video_metadata import video_metadata_service; meta=video_metadata_service.extract_metadata('missing-file.mp4'); print(meta.filename, meta.duration_seconds, meta.fps, meta.resolution)"
  ```
- **YouTube Analysis Test:**
  ```bash
  # Submit job
  curl.exe -X POST http://localhost:8000/api/analyze/youtube -H "Content-Type: application/json" -d "{\"url\":\"https://www.youtube.com/watch?v=dQw4w9WgXcQ\"}"
  
  # Poll status (replace JOB_ID)
  curl.exe http://localhost:8000/api/analyze/job_abc123
  ```
- **WebSocket Real-time Progress Test:**
  1. Start the backend: `python -m uvicorn app.main:app --reload`
  2. In a new terminal, create a job and copy the `job_id`:
     ```bash
     curl.exe -X POST http://localhost:8000/api/analyze/youtube -H "Content-Type: application/json" -d "{\"url\":\"https://www.youtube.com/watch?v=dQw4w9WgXcQ\"}"
     ```
  3. Run the WebSocket test script:
     ```bash
     python scripts/test_ws.py <job_id>
     ```

## Note
This is an initial scaffold. Model integration, job orchestration, Gemini integration, yt-dlp, and danger scoring will be added in later branches.

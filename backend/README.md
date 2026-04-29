# NeuroSafe Backend

The NeuroSafe backend is a FastAPI integration layer designed to orchestrate video analysis, process machine learning model outputs, and provide real-time content-safety feedback.

## Project Scope (Dev 3)
- **Job Orchestration**: Chaining metadata extraction, model inference, and scoring.
- **Service Integration**: Wiring Gemini API, yt-dlp, and ffprobe with robust fallbacks.
- **API Design**: Standardized REST and WebSocket endpoints for frontend consumption.
- **Demo Reliability**: Ensuring a "zero-config" demo experience for hackathon judges.

## Quick Start (Windows Friendly)

1. **Setup Environment**:
   ```powershell
   cd backend
   py -m venv .venv
   .venv\Scripts\activate
   ```
   *(If `py` is not found, use `python`)*

2. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

3. **Configure**:
   ```powershell
   cp .env.example .env
   ```

4. **Run Server**:
   ```powershell
   python -m uvicorn app.main:app --reload
   ```
   Backend active at: [http://localhost:8000](http://localhost:8000)

## Final Demo Checklist
To verify the system is ready for the demo:
1. **Health Check**: Visit `http://localhost:8000/health`.
2. **Config Verification**: Visit `http://localhost:8000/api/analyze/demo/config` to check active features.
3. **Automated YouTube Test**: Run `python scripts/demo_flow.py youtube`.
4. **Automated Upload Test**: Run `python scripts/demo_flow.py upload`.
5. **Frontend Connection**: Ensure the React app points to `http://localhost:8000`.

## Environment Variables
Defined in `.env.example`:
- `APP_ENV`: `development` or `production`.
- `MODEL_PROVIDER`: `demo` (default) or `huggingface`.
- `HF_API_URL` / `HF_API_TOKEN`: Required only for Hugging Face mode.
- `GEMINI_API_KEY`: Optional. If missing, a deterministic local generator is used.
- `UPLOAD_DIR`: Local path for video storage (default: `./uploads`).
- `ALLOWED_ORIGINS`: CORS configuration for the React frontend.

## Demo Mode
NeuroSafe defaults to **Demo Mode** (`MODEL_PROVIDER=demo`).
- **No API Keys Required**: Works without Gemini or Hugging Face tokens.
- **Deterministic Results**: Returns realistic, synchronized activation data for MT+, V1, V2, V3, and V4 regions.
- **Fallback Support**: Gracefully handles missing `ffprobe` or failed YouTube downloads by using safe defaults.
- **Robust Fallbacks**: 
    - If `ffprobe` is missing, defaults to 1080p/30fps metadata.
    - If `yt-dlp` fails, falls back to demo analysis data.
    - If `GEMINI_API_KEY` is missing, uses a local rule-based report generator.

## Configuration Validation
The backend performs lightweight environment validation on startup to ensure a smooth demo experience:
- **`MODEL_PROVIDER` Fallback**: If an invalid provider is specified, the system automatically falls back to `demo` mode with a warning log.
- **Dependency Checks**: Checks for missing Hugging Face tokens or Gemini API keys and announces the active feature set in the console.
- **Storage Auto-Provisioning**: Automatically creates the `UPLOAD_DIR` if it doesn't exist.
- **Visibility**: Use the `/api/analyze/demo/config` endpoint to view a summary of the current configuration and any active warnings.

## API Endpoints

### Core Analysis
- **`POST /api/analyze/upload`**: Upload an MP4/MOV file for analysis.
- **`POST /api/analyze/youtube`**: Submit a YouTube URL.
- **`GET /api/analyze/{job_id}`**: Poll for job status and final `AnalysisResult`.
- **`GET /api/analyze/demo/config`**: Check active demo features and provider state.

### Utilities
- **`GET /health`**: Backend health check.
- **`GET /`**: Service info and docs link.

## WebSocket Progress
**`WS /ws/analyze/{job_id}`**
Streams real-time updates to the frontend:
```json
{
  "job_id": "...",
  "status": "processing",
  "progress": 45,
  "message": "Running TRIBE model inference...",
  "timestamp": "..."
}
```

## Error Format
All errors return a standardized JSON shape:
```json
{
  "error": "job_not_found",
  "message": "Analysis job was not found.",
  "status_code": 404,
  "details": { "job_id": "..." }
}
```

## Integration Guide for Dev 1 (ML)
To plug in a new model:
1. Update `app/adapters/huggingface_adapter.py`.
2. Implement the `analyze_video` method.
3. Ensure it returns a `RawModelOutput` with:
   - `roi_activations`: Dictionary with keys `V1`, `V2`, `V3`, `V4`, `MT+`.
   - `timestamps`: List of times matching the activation array lengths.

## Integration Guide for Dev 2 (Frontend)
1. **Submit**: Use `/api/analyze/upload` or `/api/analyze/youtube`.
2. **Track**: Connect to `/ws/analyze/{job_id}` for progress.
3. **Retrieve**: When status is `completed`, read the `result` from the status endpoint.
4. **Render**:
   - `roi_timeseries`: Use for line charts.
   - `brain_visualization.frames`: Use for the 3D brain map.
   - `gemini_report`: Use for the final clinical summary.

## Pipeline Logging
The backend uses structured logging to provide visibility into the analysis pipeline:
- **Job-ID Centered**: All logs related to a specific analysis include the `job_id`.
- **Stage Transitions**: Logs highlight transitions between metadata extraction, model inference, scoring, and reporting.
- **Safety**: Logs avoid sensitive information such as API keys or full authentication headers.
- **Diagnostics**: Fallback behaviors (e.g., Gemini fallback, ffprobe fallback) are logged as warnings for easy identification.

## Full Demo Flow
Verify the entire pipeline using the automated script:
```bash
# YouTube Demo
python scripts/demo_flow.py youtube

# File Upload Demo
python scripts/demo_flow.py upload
```

```bash
docker run --rm -p 8000:8000 --env-file .env neurosafe-backend
```

## DigitalOcean Deployment Notes
The backend is designed for simple deployment on DigitalOcean using Docker or a direct Python process.

### Path A: Docker Droplet (Recommended)
1. **Create Droplet**: Launch an Ubuntu Droplet with Docker pre-installed.
2. **Clone & Setup**:
   ```bash
   git clone <repo-url>
   cd backend
   cp .env.production.example .env
   # Edit .env to set your ALLOWED_ORIGINS (frontend URL)
   ```
3. **Build & Run**:
   ```bash
   docker build -t neurosafe-backend .
   docker run -d --name neurosafe-backend -p 8000:8000 --env-file .env neurosafe-backend
   ```
4. **Verify**: Check `http://<YOUR_IP>:8000/health`.

### Path B: Manual Python Setup
1. **Setup**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Run**:
   ```bash
   python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

### Important Deployment Considerations
- **WebSockets**: Ensure your firewall allows incoming traffic on port 8000. If using a reverse proxy (Nginx), ensure it is configured for WebSocket upgrades.
- **HTTPS**: For production use with a domain, use a reverse proxy like Nginx or Caddy to handle SSL (WSS for WebSockets).
- **Storage**: Uploads are stored locally in the `./uploads` directory. For a persistent production app, integrate DigitalOcean Spaces.
- **Persistence**: The job store is in-memory; restarting the process clears all active and past jobs.

## Troubleshooting
- **`py` or `python` not found**: Ensure Python 3.10+ is in your PATH.
- **Module not found**: Confirm the virtual environment is activated and `pip install` succeeded.
- **Connection Refused**: Ensure the uvicorn server is running on port 8000.
- **ffprobe errors**: If FFmpeg is not installed, the backend uses fallback metadata (30s, 30fps). This is normal for local dev.
- **yt-dlp errors**: Some YouTube videos may be age-restricted or regional. The backend will fall back to demo mode data automatically.

## Docker Support
The backend can be run in a containerized environment for consistency across systems.

### 1. Build Image
From the `backend/` directory:
```powershell
docker build -t neurosafe-backend .
```

### 2. Run Container
```powershell
docker run --rm -p 8000:8000 neurosafe-backend
```
The backend will default to **Demo Mode** and be accessible at `http://localhost:8000`.

### 3. Run with Environment Variables
To use a real model or Gemini API keys from your local `.env` file:
```powershell
docker run --rm -p 8000:8000 --env-file .env neurosafe-backend
```

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

## Note
This is an initial scaffold. Model integration, job orchestration, Gemini integration, yt-dlp, and danger scoring will be added in later branches.

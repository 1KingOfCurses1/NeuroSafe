# NeuroSafe

NeuroSafe is a health-tech web application designed to screen videos for possible photosensitive epilepsy seizure triggers. By analyzing brain region activation patterns (ROIs) from video content, NeuroSafe identifies potential risks and provides detailed content-safety reports to creators.

This repository contains the **Backend Integration Layer**, responsible for orchestrating the analysis pipeline, integrating machine learning model outputs, and serving real-time progress via WebSockets.

## Project Context
- **Hackathon**: ConHacks 2026
- **Developer Role**: Developer 3 - Brain Visualization & Integration Lead

## Tech Stack
- **FastAPI**: High-performance web framework for API endpoints.
- **Pydantic**: Data validation and settings management using Python type annotations.
- **WebSockets**: Real-time progress streaming for analysis jobs.
- **Gemini API**: Automated generation of clinical safety reports (with local fallback).
- **Hugging Face**: Integration point for specialized TRIBE model adapters.
- **FFmpeg/ffprobe**: Automated video metadata extraction.

## Getting Started
For detailed instructions on setting up the backend, running the development server, and testing the API endpoints, please refer to the [Backend Documentation](backend/README.md).

## Core Services
- **Job Orchestrator**: Manages the lifecycle of an analysis job.
- **Danger Scoring**: Analyzes ROI spikes to calculate risk scores and identify danger segments.
- **Result Formatter**: Synchronizes model output with 3D brain visualization frames.
- **Gemini Service**: Transforms technical metrics into plain-English creator reports.
- **WebSocket Stream**: Provides live feedback to the frontend during processing.

---
*NeuroSafe is an accessibility screening tool and is not intended for medical diagnosis.*

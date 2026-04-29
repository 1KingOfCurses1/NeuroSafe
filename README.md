# NeuroSafe

NeuroSafe is a photosensitive seizure screening tool developed for **ConHacks 2026**. It analyzes video content (files or YouTube URLs) to identify visual patterns that could trigger photosensitive epilepsy.

## High-Level Architecture
NeuroSafe is built on a modular integration layer that connects deep learning model outputs with interactive 3D visualizations and clinical reporting.

- **FastAPI Backend**: Orchestrates the analysis pipeline and serves as the central API.
- **Model Adapter Layer**: Provides a standard interface for local or cloud-based model inference.
- **Risk Scoring Engine**: Analyzes ROI (Region of Interest) activations to calculate danger levels.
- **Gemini AI Integration**: Generates clinical safety reports based on technical analysis data.
- **Real-time Progress**: Uses WebSockets to stream analysis status to the frontend.

## Repository Structure
- `backend/`: The FastAPI integration layer, services, and API endpoints.
- `backend/app/adapters/`: Model integration points (TRIBE model).
- `backend/scripts/`: Verification and demo scripts.

## Getting Started
To set up the backend development environment, please refer to the detailed instructions in the **[Backend README](backend/README.md)**.

---
*NeuroSafe is an accessibility tool designed for creators and is not intended for medical diagnosis.*

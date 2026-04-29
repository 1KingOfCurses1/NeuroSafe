import asyncio
import logging
import os
from typing import Optional
from app.services.job_store import job_store
from app.schemas.jobs import JobStatus
from app.schemas.analysis import AnalysisResult
from app.adapters import demo_model_adapter
from app.services.danger_scoring import danger_scoring_service
from app.services.result_formatter import result_formatter
from app.services.gemini_service import gemini_report_service
from app.services.video_metadata import video_metadata_service

logger = logging.getLogger(__name__)

class AnalysisOrchestrator:
    """
    Orchestrates the full analysis pipeline by chaining together 
    specialized services for metadata extraction, model inference, 
    risk scoring, and report generation.
    """

    async def run_demo_analysis(self, job_id: str, video_path: Optional[str] = None) -> AnalysisResult:
        """
        Runs the full analysis pipeline in demo mode.
        If video_path is provided, it attempts to extract real metadata, 
        otherwise falls back to demo defaults.
        """
        try:
            # 1. Stage: Extracting Metadata (15%)
            job_store.update_job(
                job_id, 
                status=JobStatus.EXTRACTING_METADATA, 
                progress=15, 
                message="Analyzing video container and metadata..."
            )
            # Use real file if it exists, otherwise extract_metadata handles fallback
            path_to_extract = video_path if video_path and os.path.exists(video_path) else "demo.mp4"
            metadata = video_metadata_service.extract_metadata(path_to_extract)
            await asyncio.sleep(0.5) # Simulate slight delay for UI

            # 2. Stage: Running Model Inference (40%)
            job_store.update_job(
                job_id, 
                status=JobStatus.RUNNING_MODEL, 
                progress=40, 
                message="Running TRIBE model inference on visual cortex (V1-V4, MT+)..."
            )
            # demo_model_adapter always returns deterministic data
            raw_output = await demo_model_adapter.analyze_video(path_to_extract)
            await asyncio.sleep(0.5)

            # 3. Stage: Scoring Danger (65%)
            job_store.update_job(
                job_id, 
                status=JobStatus.SCORING_DANGER, 
                progress=65, 
                message="Calculating seizure risk scores and detecting danger segments..."
            )
            score, summary, danger_segments = danger_scoring_service.score_model_output(raw_output)
            await asyncio.sleep(0.5)

            # 4. Stage: Generating Report (85%)
            job_store.update_job(
                job_id, 
                status=JobStatus.GENERATING_REPORT, 
                progress=85, 
                message="Generating Gemini clinical content-safety report..."
            )
            report = await gemini_report_service.generate_report(
                danger_score=score,
                summary=summary,
                danger_segments=danger_segments,
                video_metadata=metadata
            )
            await asyncio.sleep(0.5)

            # 5. Stage: Formatting Results (95%)
            job_store.update_job(
                job_id, 
                status=JobStatus.GENERATING_VISUALIZATION, 
                progress=95, 
                message="Finalizing 3D brain visualization and result payload..."
            )
            result = result_formatter.format_analysis_result(
                job_id=job_id,
                model_output=raw_output,
                danger_score=score,
                summary=summary,
                danger_segments=danger_segments,
                report=report,
                video_metadata=metadata
            )
            
            # 6. Finalize: Completed (100%)
            job_store.set_result(job_id, result)
            logger.info(f"Analysis job {job_id} completed successfully.")
            
            return result

        except Exception as e:
            logger.error(f"Analysis pipeline failed for job {job_id}: {str(e)}", exc_info=True)
            job_store.fail_job(job_id, error=str(e), message="Analysis failed during orchestration")
            raise e

analysis_orchestrator = AnalysisOrchestrator()

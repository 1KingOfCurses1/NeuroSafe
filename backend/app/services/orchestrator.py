import asyncio
import logging
import os
from typing import Optional
from app.core.config import settings
from app.services.job_store import job_store
from app.schemas.jobs import JobStatus
from app.schemas.analysis import AnalysisResult
from app.adapters import demo_model_adapter, tribe_v2_adapter
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
        logger.info(f"Starting analysis pipeline for job {job_id}")
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
            logger.info(f"Job {job_id}: Extracting metadata from {path_to_extract}")
            metadata = video_metadata_service.extract_metadata(path_to_extract)
            logger.info(f"Job {job_id}: Metadata extracted successfully ({metadata.duration_seconds}s, {metadata.resolution})")
            await asyncio.sleep(0.1) # Brief yield for UI

            # 2. Stage: Running Model Inference (40%)
            if settings.is_tribe_mode:
                inference_label = "TRIBE v2 cortical encoding model"
                adapter = tribe_v2_adapter
            else:
                inference_label = "demo deterministic adapter"
                adapter = demo_model_adapter

            job_store.update_job(
                job_id,
                status=JobStatus.RUNNING_MODEL,
                progress=40,
                message=f"Running {inference_label} on visual cortex (V1-V4, MT+)..."
            )
            logger.info(f"Job {job_id}: Running inference via {adapter.provider_name}...")
            raw_output = await adapter.analyze_video(path_to_extract, job_id=job_id)
            logger.info(f"Job {job_id}: Model inference complete.")
            await asyncio.sleep(0.1)

            # 3. Stage: Scoring Danger (65%)
            job_store.update_job(
                job_id, 
                status=JobStatus.SCORING_DANGER, 
                progress=65, 
                message="Calculating seizure risk scores and detecting danger segments..."
            )
            logger.info(f"Job {job_id}: Scoring model output...")
            score, summary, danger_segments = danger_scoring_service.score_model_output(raw_output, job_id=job_id)
            logger.info(f"Job {job_id}: Scoring complete (Score: {score}, Severity: {summary.severity})")
            await asyncio.sleep(0.1)

            # 4. Stage: Generating Report (85%)
            job_store.update_job(
                job_id, 
                status=JobStatus.GENERATING_REPORT, 
                progress=85, 
                message="Generating Gemini clinical content-safety report..."
            )
            logger.info(f"Job {job_id}: Generating clinical report...")
            report = await gemini_report_service.generate_report(
                danger_score=score,
                summary=summary,
                danger_segments=danger_segments,
                job_id=job_id,
                video_metadata=metadata
            )
            logger.info(f"Job {job_id}: Report generation complete.")
            await asyncio.sleep(0.1)

            # 5. Stage: Formatting Results (95%)
            job_store.update_job(
                job_id, 
                status=JobStatus.GENERATING_VISUALIZATION, 
                progress=95, 
                message="Finalizing 3D brain visualization and result payload..."
            )
            logger.info(f"Job {job_id}: Formatting final results...")
            result = result_formatter.format_analysis_result(
                job_id=job_id,
                model_output=raw_output,
                danger_score=score,
                summary=summary,
                danger_segments=danger_segments,
                report=report,
                video_metadata=metadata
            )
            logger.info(f"Job {job_id}: Formatting complete.")
            
            # 6. Finalize: Completed (100%)
            job_store.set_result(job_id, result)
            logger.info(f"Analysis job {job_id} completed successfully.")
            
            return result

        except Exception as e:
            logger.error(f"Analysis pipeline failed for job {job_id}: {str(e)}", exc_info=True)
            job_store.fail_job(job_id, error=str(e), message="Analysis failed during orchestration")
            raise e

analysis_orchestrator = AnalysisOrchestrator()

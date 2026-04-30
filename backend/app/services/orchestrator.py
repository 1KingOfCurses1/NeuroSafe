import asyncio
import logging
import os
from pathlib import Path
from typing import Optional, Tuple
from app.core.config import settings
from app.services.job_store import job_store
from app.schemas.jobs import JobStatus
from app.schemas.analysis import AnalysisResult
from app.adapters import BaseModelAdapter, demo_model_adapter, tribe_v2_adapter
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

    def _select_adapter(self) -> Tuple[BaseModelAdapter, Optional[str]]:
        """
        Select the best available adapter for the current runtime config.
        Falls back to the demo adapter when an advanced provider is unavailable.
        """
        if settings.is_demo_mode:
            return demo_model_adapter, None

        if settings.is_tribe_mode:
            if tribe_v2_adapter.is_available():
                return tribe_v2_adapter, None
            return (
                demo_model_adapter,
                "TRIBE v2 is not configured in this environment. Falling back to demo analysis.",
            )

        if settings.is_huggingface_mode:
            return (
                demo_model_adapter,
                "Hugging Face inference is not implemented in this build. Falling back to demo analysis.",
            )

        return demo_model_adapter, "Unknown model provider configured. Falling back to demo analysis."

    def _cleanup_artifacts(self, video_path: Optional[str], job_id: str) -> None:
        """
        Best-effort cleanup for per-job media artifacts generated during analysis.
        Keeps the workspace from accumulating uploaded videos, extracted audio,
        and transcription sidecar files across runs.
        """
        if not video_path:
            return

        path = Path(video_path)
        candidates = {path}
        candidates.update(path.parent.glob(f"{path.stem}.*"))

        for candidate in candidates:
            try:
                if candidate.exists() and candidate.is_file():
                    candidate.unlink()
                    logger.info(f"Job {job_id}: Removed artifact {candidate}")
            except Exception as exc:
                logger.warning(
                    f"Job {job_id}: Failed to remove artifact {candidate}: {exc}"
                )

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
            adapter, fallback_message = self._select_adapter()
            if fallback_message:
                logger.warning(f"Job {job_id}: {fallback_message}")
                job_store.update_job(job_id, message=fallback_message)

            if adapter is tribe_v2_adapter:
                inference_label = "TRIBE v2 cortical encoding model"
            else:
                inference_label = "demo flash-detection adapter"

            job_store.update_job(
                job_id,
                status=JobStatus.RUNNING_MODEL,
                progress=40,
                message=f"Running {inference_label} on visual cortex (V1-V4, MT+)..."
            )
            logger.info(f"Job {job_id}: Running inference via {adapter.provider_name}...")
            try:
                raw_output = await adapter.analyze_video(path_to_extract, job_id=job_id)
            except Exception as exc:
                if adapter is demo_model_adapter:
                    raise

                logger.warning(
                    f"Job {job_id}: {adapter.provider_name} inference failed ({exc}). "
                    "Falling back to demo adapter.",
                    exc_info=True,
                )
                job_store.update_job(
                    job_id,
                    status=JobStatus.RUNNING_MODEL,
                    progress=40,
                    message="Advanced inference failed. Falling back to demo analysis.",
                )
                raw_output = await demo_model_adapter.analyze_video(path_to_extract, job_id=job_id)
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
        finally:
            self._cleanup_artifacts(video_path, job_id)

analysis_orchestrator = AnalysisOrchestrator()

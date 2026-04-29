import asyncio
from typing import List
from app.services.job_store import job_store, JobNotFoundError
from app.schemas.jobs import JobStatus
from app.schemas.analysis import (
    AnalysisResult, 
    VideoMetadata, 
    AnalysisSummary, 
    DangerSegment, 
    RoiTimeSeries
)
from app.schemas.reports import GeminiReport
from app.schemas.visualization import BrainFrame, BrainVisualizationPayload

class AnalysisOrchestrator:
    async def run_demo_analysis(self, job_id: str) -> AnalysisResult:
        try:
            # Stage: Queued
            job_store.update_job(job_id, status=JobStatus.QUEUED, progress=0, message="Analysis queued")
            await asyncio.sleep(0.1)

            # Stage: Extracting Metadata
            job_store.update_job(job_id, status=JobStatus.EXTRACTING_METADATA, progress=15, message="Extracting video metadata")
            await asyncio.sleep(0.2)

            # Stage: Running Model
            job_store.update_job(job_id, status=JobStatus.RUNNING_MODEL, progress=40, message="Running TRIBE model inference")
            await asyncio.sleep(0.2)

            # Stage: Scoring Danger
            job_store.update_job(job_id, status=JobStatus.SCORING_DANGER, progress=65, message="Calculating seizure risk scores")
            await asyncio.sleep(0.2)

            # Stage: Generating Visualization
            job_store.update_job(job_id, status=JobStatus.GENERATING_VISUALIZATION, progress=80, message="Generating 3D brain visualization data")
            await asyncio.sleep(0.1)

            # Stage: Generating Report
            job_store.update_job(job_id, status=JobStatus.GENERATING_REPORT, progress=90, message="Generating Gemini clinical report")
            await asyncio.sleep(0.1)

            # Generate Placeholder Result
            timestamps = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0]
            
            roi_timeseries = RoiTimeSeries(
                timestamps=timestamps,
                V1=[0.1, 0.2, 0.4, 0.9, 0.3, 0.2, 0.1],
                V2=[0.1, 0.1, 0.3, 0.8, 0.2, 0.1, 0.1],
                V3=[0.0, 0.1, 0.2, 0.7, 0.1, 0.1, 0.0],
                V4=[0.0, 0.0, 0.1, 0.6, 0.1, 0.0, 0.0],
                MT_plus=[0.1, 0.3, 0.5, 0.95, 0.4, 0.2, 0.1]
            )

            brain_frames = [
                BrainFrame(
                    timestamp=t,
                    roi_activations={
                        "V1": roi_timeseries.V1[i],
                        "V2": roi_timeseries.V2[i],
                        "V3": roi_timeseries.V3[i],
                        "V4": roi_timeseries.V4[i],
                        "MT+": roi_timeseries.MT_plus[i]
                    },
                    max_activation=max(roi_timeseries.V1[i], roi_timeseries.MT_plus[i]),
                    danger_level="high" if i == 3 else "low"
                )
                for i, t in enumerate(timestamps)
            ]

            visualization = BrainVisualizationPayload(
                job_id=job_id,
                frames=brain_frames
            )

            report = GeminiReport(
                headline="High Risk of Photosensitive Seizure Detected",
                findings=[
                    "High activation detected in V1 and MT+ regions between 14-17 seconds.",
                    "Luminance flash frequency exceeds safe thresholds (15Hz+).",
                    "Second danger segment identified at 23 seconds due to high contrast patterns."
                ],
                recommended_actions=[
                    "Apply a 20% luminance reduction filter to the 14-18s segment.",
                    "Reduce saturation in red channels during the 23-26s segment.",
                    "Add a viewer warning at the beginning of the video."
                ]
            )

            summary = AnalysisSummary(
                severity="high",
                segments_detected=2,
                total_danger_duration_seconds=5.8
            )

            metadata = VideoMetadata(
                filename="demo-video.mp4",
                duration_seconds=30.0,
                fps=30.0,
                resolution="1920x1080"
            )

            danger_segments = [
                DangerSegment(
                    start_time=14.0,
                    end_time=17.2,
                    peak_time=15.5,
                    roi="MT+",
                    activation_level=0.95,
                    threshold=0.7,
                    severity="high",
                    reason="High frequency luminance oscillation"
                ),
                DangerSegment(
                    start_time=23.0,
                    end_time=25.6,
                    peak_time=24.1,
                    roi="V1",
                    activation_level=0.88,
                    threshold=0.7,
                    severity="medium",
                    reason="High contrast repetitive patterns"
                )
            ]

            result = AnalysisResult(
                job_id=job_id,
                status=JobStatus.COMPLETED,
                video=metadata,
                danger_score=87,
                summary=summary,
                danger_segments=danger_segments,
                roi_timeseries=roi_timeseries,
                gemini_report=report,
                brain_visualization=visualization
            )

            # Stage: Completed
            job_store.set_result(job_id, result)
            return result

        except Exception as e:
            job_store.fail_job(job_id, error=str(e), message="Analysis failed")
            raise e

analysis_orchestrator = AnalysisOrchestrator()

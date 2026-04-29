from typing import List, Optional, Dict
from app.adapters.base import RawModelOutput
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

class ResultFormatter:
    """
    Combines model output, scoring output, and metadata into a synchronized AnalysisResult.
    Handles timestamp alignment and schema mapping (e.g., MT+ to MT_plus).
    """

    def format_analysis_result(
        self,
        job_id: str,
        model_output: RawModelOutput,
        danger_score: int,
        summary: AnalysisSummary,
        danger_segments: List[DangerSegment],
        video_metadata: Optional[VideoMetadata] = None,
        report: Optional[GeminiReport] = None,
    ) -> AnalysisResult:
        
        if not model_output.timestamps:
            raise ValueError("Model output timestamps list is empty.")

        # 1. Video Metadata
        if not video_metadata:
            video_metadata = VideoMetadata(
                filename=model_output.metadata.get("video_path", "demo-video.mp4"),
                duration_seconds=model_output.duration_seconds,
                fps=30.0,
                resolution="1920x1080"
            )

        # 2. ROI Time Series
        # Map MT+ to MT_plus and fill missing required ROIs with zeros
        ts_len = len(model_output.timestamps)
        zeros = [0.0] * ts_len
        
        roi_ts = RoiTimeSeries(
            timestamps=model_output.timestamps,
            V1=model_output.roi_activations.get("V1", zeros),
            V2=model_output.roi_activations.get("V2", zeros),
            V3=model_output.roi_activations.get("V3", zeros),
            V4=model_output.roi_activations.get("V4", zeros),
            MT_plus=model_output.roi_activations.get("MT+", zeros)
        )

        # 3. Gemini Report Fallback
        if not report:
            report = self._generate_fallback_report(danger_score, danger_segments)

        # 4. Brain Visualization Payload
        brain_frames = []
        for i, t in enumerate(model_output.timestamps):
            frame_activations = {
                roi: vals[i] for roi, vals in model_output.roi_activations.items()
            }
            # Ensure required keys exist for visualization
            for k in ["V1", "V2", "V3", "V4", "MT+"]:
                if k not in frame_activations:
                    frame_activations[k] = 0.0
            
            max_act = max(frame_activations.values()) if frame_activations else 0.0
            
            if max_act < 1.5:
                danger_level = "low"
            elif max_act < 2.0:
                danger_level = "medium"
            elif max_act < 2.8:
                danger_level = "high"
            else:
                danger_level = "critical"

            brain_frames.append(BrainFrame(
                timestamp=t,
                roi_activations=frame_activations,
                max_activation=round(max_act, 3),
                danger_level=danger_level
            ))

        visualization = BrainVisualizationPayload(
            job_id=job_id,
            frames=brain_frames,
            color_map="deep-blue-yellow-red",
            timestamp_unit="seconds"
        )

        return AnalysisResult(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            video=video_metadata,
            danger_score=danger_score,
            summary=summary,
            danger_segments=danger_segments,
            roi_timeseries=roi_ts,
            gemini_report=report,
            brain_visualization=visualization
        )

    def _generate_fallback_report(self, score: int, segments: List[DangerSegment]) -> GeminiReport:
        if score >= 70:
            headline = "High seizure-trigger risk detected."
            severity_text = "high or critical"
        elif score >= 30:
            headline = "Moderate visual risk detected."
            severity_text = "moderate"
        else:
            headline = "Low seizure-trigger risk detected."
            severity_text = "low"

        findings = []
        if segments:
            peak_roi = max(segments, key=lambda s: s.activation_level).roi
            findings.append(f"Detected {len(segments)} danger segments with {severity_text} severity.")
            findings.append(f"Peak activation was identified in the {peak_roi} region.")
            findings.append(f"Significant triggers found between {segments[0].start_time}s and {segments[-1].end_time}s.")
        else:
            findings.append("No activation exceeded the configured danger thresholds during this analysis.")
            findings.append("Visual cortex activation patterns remained within safe baseline levels.")

        recommended_actions = []
        if score >= 70:
            recommended_actions = [
                "Review and edit the flagged timestamps before publishing.",
                "Reduce rapid flashing, high-contrast transitions, or intense motion patterns in danger segments.",
                "Re-run NeuroSafe after edits to verify risk reduction."
            ]
        elif score >= 30:
            recommended_actions = [
                "Consider adding a viewer warning for photosensitive viewers.",
                "Subtly reduce luminance or saturation in flagged segments.",
                "Double-check the identified timestamps for high-frequency flickers."
            ]
        else:
            recommended_actions = [
                "No urgent edits required based on current thresholds.",
                "Standard content safety protocols are recommended.",
                "Keep a log of this report for content accessibility records."
            ]

        return GeminiReport(
            headline=headline,
            findings=findings,
            recommended_actions=recommended_actions
        )

result_formatter = ResultFormatter()

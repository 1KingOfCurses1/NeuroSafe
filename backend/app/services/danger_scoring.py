from typing import List, Tuple, Dict
from app.adapters.base import RawModelOutput
from app.schemas.analysis import DangerSegment, AnalysisSummary

class DangerScoringService:
    """
    Converts raw ROI activation data into seizure-risk segments and an overall score.
    Based on threshold detection and segment grouping.
    """
    
    def __init__(self, danger_threshold: float = 2.0):
        self.danger_threshold = danger_threshold

    def score_model_output(self, output: RawModelOutput) -> Tuple[int, AnalysisSummary, List[DangerSegment]]:
        if not output.timestamps:
            return 0, AnalysisSummary(severity="low", segments_detected=0, total_danger_duration_seconds=0), []

        # Validate lengths
        for roi, activations in output.roi_activations.items():
            if len(activations) != len(output.timestamps):
                raise ValueError(f"ROI {roi} activation length ({len(activations)}) does not match timestamp length ({len(output.timestamps)})")

        segments = self._detect_segments(output)
        
        # Calculate overall metrics
        total_segments = len(segments)
        total_duration = sum(s.end_time - s.start_time for s in segments)
        
        max_activation = 0.0
        if output.roi_activations:
            max_activation = max(max(vals) for vals in output.roi_activations.values())

        # Formula: score = min(100, int((max_activation / 3.2) * 70 + min(total_segments, 5) * 5 + min(total_duration, 10) * 1.5))
        score = min(100, int((max_activation / 3.2) * 70 + min(total_segments, 5) * 5 + min(total_duration, 10) * 1.5))

        # Severity
        if score < 30:
            severity = "low"
        elif score < 70:
            severity = "medium"
        elif score < 90:
            severity = "high"
        else:
            severity = "critical"

        summary = AnalysisSummary(
            severity=severity,
            segments_detected=total_segments,
            total_danger_duration_seconds=round(total_duration, 2)
        )

        return score, summary, segments

    def _detect_segments(self, output: RawModelOutput) -> List[DangerSegment]:
        all_segments = []
        
        for roi_name, activations in output.roi_activations.items():
            in_segment = False
            segment_start_idx = -1
            
            for i, (t, val) in enumerate(zip(output.timestamps, activations)):
                if val >= self.danger_threshold:
                    if not in_segment:
                        in_segment = True
                        segment_start_idx = i
                else:
                    if in_segment:
                        # Close segment
                        all_segments.append(self._create_segment(output, roi_name, segment_start_idx, i - 1))
                        in_segment = False
            
            # Handle segment at the very end
            if in_segment:
                all_segments.append(self._create_segment(output, roi_name, segment_start_idx, len(output.timestamps) - 1))
                
        return all_segments

    def _create_segment(self, output: RawModelOutput, roi: str, start_idx: int, end_idx: int) -> DangerSegment:
        activations = output.roi_activations[roi][start_idx:end_idx + 1]
        timestamps = output.timestamps[start_idx:end_idx + 1]
        
        peak_val = max(activations)
        peak_idx = activations.index(peak_val)
        peak_time = timestamps[peak_idx]
        
        # Severity inside segment
        if peak_val >= 2.8:
            severity = "critical"
        elif peak_val >= 2.0:
            severity = "high"
        elif peak_val >= 1.5:
            severity = "medium"
        else:
            severity = "low"

        return DangerSegment(
            start_time=output.timestamps[start_idx],
            end_time=output.timestamps[end_idx],
            peak_time=peak_time,
            roi=roi,
            activation_level=round(peak_val, 3),
            threshold=self.danger_threshold,
            severity=severity,
            reason="Activation exceeded the visual cortex danger threshold."
        )

danger_scoring_service = DangerScoringService()

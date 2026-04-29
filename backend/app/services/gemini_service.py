import logging
import json
import asyncio
from typing import List, Optional, Dict, Any
from app.core.config import settings
from app.schemas.reports import GeminiReport
from app.schemas.analysis import DangerSegment, AnalysisSummary, VideoMetadata

logger = logging.getLogger(__name__)

# Optional: Try to import Gemini SDK
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

class GeminiReportService:
    """
    Generates plain-English content-safety reports from danger scoring results.
    Uses Gemini when available, but always falls back to deterministic local reports.
    """

    async def generate_report(
        self,
        danger_score: int,
        summary: AnalysisSummary,
        danger_segments: List[DangerSegment],
        job_id: str = "unknown",
        video_metadata: Optional[VideoMetadata] = None,
    ) -> GeminiReport:
        """
        Main entry point for report generation. 
        Always returns a valid GeminiReport even on failure.
        """
        # 1. Immediate Fallback if not configured or dependency missing
        if not HAS_GEMINI or not settings.GEMINI_API_KEY:
            logger.info(f"Job {job_id}: Gemini API not configured or SDK missing. Using local fallback report.")
            return self._generate_fallback_report(danger_score, summary, danger_segments)

        # 2. Try Gemini Call
        try:
            logger.info(f"Job {job_id}: Calling Gemini API for clinical analysis...")
            report = await self._call_gemini(danger_score, summary, danger_segments, video_metadata)
            logger.info(f"Job {job_id}: Gemini API response received and parsed.")
            return report
        except Exception as e:
            logger.error(f"Job {job_id}: Gemini API call failed: {e}. Falling back to local report.")
            return self._generate_fallback_report(danger_score, summary, danger_segments)

    async def _call_gemini(
        self,
        danger_score: int,
        summary: AnalysisSummary,
        danger_segments: List[DangerSegment],
        video_metadata: Optional[VideoMetadata] = None,
    ) -> GeminiReport:
        """
        Minimal integration with Gemini API.
        """
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = self._build_prompt(danger_score, summary, danger_segments, video_metadata)
        
        response = await asyncio.to_thread(model.generate_content, prompt)
        
        # Try to extract JSON from response (handling potential markdown markers)
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        data = json.loads(text)
        
        return GeminiReport(
            headline=data.get("headline", "Video Safety Analysis Report"),
            findings=data.get("findings", []),
            recommended_actions=data.get("recommended_actions", [])
        )

    def _build_prompt(
        self,
        danger_score: int,
        summary: AnalysisSummary,
        danger_segments: List[DangerSegment],
        video_metadata: Optional[VideoMetadata] = None,
    ) -> str:
        """
        Builds the prompt for Gemini.
        """
        top_segments = sorted(danger_segments, key=lambda s: s.activation_level, reverse=True)[:3]
        
        segments_info = "\n".join([
            f"- {s.roi} region: Peak {s.activation_level} at {s.peak_time}s (from {s.start_time}s to {s.end_time}s)"
            for s in top_segments
        ])
        
        prompt = f"""
        Generate a concise content-safety report for a video seizure-trigger screening tool called NeuroSafe.
        Avoid medical diagnosis claims. Use professional, content-safety risk language.
        
        Input Data:
        - Overall Danger Score: {danger_score}/100
        - Severity: {summary.severity}
        - Total Danger Segments: {summary.segments_detected}
        - Total Danger Duration: {summary.total_danger_duration_seconds} seconds
        - Key Danger Segments:
        {segments_info}
        
        Return the report strictly as a JSON object with the following fields:
        "headline": A punchy one-sentence summary of the risk.
        "findings": A list of 2-3 specific observations based on the data.
        "recommended_actions": A list of 2-3 actionable steps for the content creator to reduce risk.
        """
        return prompt

    def _generate_fallback_report(
        self,
        danger_score: int,
        summary: AnalysisSummary,
        danger_segments: List[DangerSegment],
    ) -> GeminiReport:
        """
        Deterministic local report generation based on analysis data.
        """
        if summary.severity in ["critical", "high"]:
            headline = "High seizure-trigger risk detected."
        elif summary.severity == "medium":
            headline = "Moderate visual risk detected."
        else:
            headline = "Low seizure-trigger risk detected."

        findings = []
        if danger_segments:
            top_seg = max(danger_segments, key=lambda s: s.activation_level)
            findings.append(f"Analysis yielded a danger score of {danger_score}/100.")
            findings.append(f"Detected {len(danger_segments)} segments exceeding safety thresholds.")
            findings.append(f"Strongest activation found in the {top_seg.roi} region ({top_seg.activation_level}) at {top_seg.peak_time}s.")
        else:
            findings.append("No activation exceeded the configured danger thresholds during this analysis.")
            findings.append("Visual cortex activation patterns remained within safe baseline levels.")

        recommended_actions = []
        if summary.severity in ["critical", "high"]:
            recommended_actions = [
                "Review and edit the flagged timestamps before publishing.",
                "Reduce rapid flashing, high-contrast transitions, or intense motion patterns.",
                "Re-run NeuroSafe after edits."
            ]
        elif summary.severity == "medium":
            recommended_actions = [
                "Review the flagged timestamps before publishing.",
                "Consider softening intense transitions or motion-heavy sequences.",
                "Add a content warning if the visual pattern is intentional."
            ]
        else:
            recommended_actions = [
                "No immediate edits are required based on the current screening.",
                "Re-run NeuroSafe if the video is significantly edited.",
                "Continue following accessibility-safe video design practices."
            ]

        return GeminiReport(
            headline=headline,
            findings=findings,
            recommended_actions=recommended_actions
        )

# Instantiate singleton
gemini_report_service = GeminiReportService()

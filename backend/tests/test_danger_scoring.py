import pytest
from app.services.danger_scoring import DangerScoringService
from app.adapters.base import RawModelOutput


def make_output(activations: dict, timestamps: list | None = None) -> RawModelOutput:
    ts = timestamps or [float(i) for i in range(10)]
    base = {roi: [0.0] * len(ts) for roi in ["V1", "V2", "V3", "V4", "MT+"]}
    base.update(activations)
    return RawModelOutput(
        duration_seconds=float(len(ts)),
        timestamps=ts,
        roi_activations=base,
        model_name="test",
        model_provider="test",
    )


class TestDangerScoringService:
    def setup_method(self):
        self.svc = DangerScoringService(danger_threshold=2.0)

    def test_no_activations_returns_zero_score(self):
        output = make_output({})
        score, summary, segments = self.svc.score_model_output(output)
        assert score == 0
        assert summary.severity == "low"
        assert segments == []

    def test_detects_segment_above_threshold(self):
        output = make_output({"V1": [0.0, 2.5, 2.8, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]})
        score, summary, segments = self.svc.score_model_output(output)
        assert len(segments) == 1
        assert segments[0].roi == "V1"
        assert segments[0].activation_level == pytest.approx(2.8)

    def test_no_segment_below_threshold(self):
        output = make_output({"V1": [1.9] * 10})
        _, _, segments = self.svc.score_model_output(output)
        assert segments == []

    def test_score_above_zero_when_activation_high(self):
        output = make_output({"MT+": [3.0] * 10})
        score, _, _ = self.svc.score_model_output(output)
        assert score > 0

    def test_critical_severity_for_very_high_score(self):
        output = make_output({"V1": [4.0] * 10, "MT+": [4.0] * 10})
        score, summary, _ = self.svc.score_model_output(output)
        assert score >= 90
        assert summary.severity == "critical"

    def test_low_severity_for_minimal_activation(self):
        output = make_output({"V1": [0.1, 0.2, 0.0, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]})
        _, summary, _ = self.svc.score_model_output(output)
        assert summary.severity == "low"

    def test_segment_peak_time_correct(self):
        ts = [0.0, 1.0, 2.0, 3.0, 4.0]
        activations = [0.0, 2.1, 3.5, 2.2, 0.0]
        output = make_output({"V2": activations}, timestamps=ts)
        _, _, segments = self.svc.score_model_output(output)
        assert len(segments) == 1
        assert segments[0].peak_time == pytest.approx(2.0)

    def test_multiple_rois_produce_multiple_segments(self):
        output = make_output({
            "V1": [2.5, 2.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "V3": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.5, 2.5, 0.0],
        })
        _, summary, segments = self.svc.score_model_output(output)
        assert summary.segments_detected == 2
        rois = {s.roi for s in segments}
        assert rois == {"V1", "V3"}

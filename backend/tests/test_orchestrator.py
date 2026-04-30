from pathlib import Path

import pytest

from app.services.orchestrator import analysis_orchestrator
from app.adapters import demo_model_adapter, tribe_v2_adapter
from app.core.config import settings


def test_select_adapter_falls_back_to_demo_when_tribe_unavailable(monkeypatch):
    monkeypatch.setattr(settings, "MODEL_PROVIDER", "tribe_v2")
    monkeypatch.setattr(tribe_v2_adapter, "is_available", lambda: False)

    adapter, message = analysis_orchestrator._select_adapter()

    assert adapter is demo_model_adapter
    assert message is not None
    assert "Falling back to demo analysis" in message


def test_select_adapter_uses_tribe_when_available(monkeypatch):
    monkeypatch.setattr(settings, "MODEL_PROVIDER", "tribe_v2")
    monkeypatch.setattr(tribe_v2_adapter, "is_available", lambda: True)

    adapter, message = analysis_orchestrator._select_adapter()

    assert adapter is tribe_v2_adapter
    assert message is None


@pytest.mark.asyncio
async def test_cleanup_artifacts_removes_video_and_sidecars(tmp_path):
    video_path = tmp_path / "job_123_youtube.mp4"
    wav_path = tmp_path / "job_123_youtube.wav"
    tsv_path = tmp_path / "job_123_youtube.tsv"
    unrelated_path = tmp_path / "keep.txt"

    for path in (video_path, wav_path, tsv_path, unrelated_path):
        path.write_text("x", encoding="utf-8")

    await analysis_orchestrator._cleanup_artifacts(str(video_path), "job_123")

    assert not video_path.exists()
    assert not wav_path.exists()
    assert not tsv_path.exists()
    assert unrelated_path.exists()

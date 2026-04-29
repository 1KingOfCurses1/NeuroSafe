import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_valid_video(client: AsyncClient):
    fake_video = b"\x00" * 16
    response = await client.post(
        "/api/analyze/upload",
        files={"file": ("test_video.mp4", fake_video, "video/mp4")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"


@pytest.mark.asyncio
async def test_upload_invalid_extension_rejected(client: AsyncClient):
    response = await client.post(
        "/api/analyze/upload",
        files={"file": ("document.pdf", b"fake", "application/pdf")},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_youtube_valid_url_accepted(client: AsyncClient):
    response = await client.post(
        "/api/analyze/youtube",
        json={"url": "https://youtube.com/watch?v=test123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["job_id"].startswith("job_")


@pytest.mark.asyncio
async def test_youtube_invalid_url_rejected(client: AsyncClient):
    response = await client.post(
        "/api/analyze/youtube",
        json={"url": "https://vimeo.com/123456"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_job_not_found(client: AsyncClient):
    response = await client.get("/api/analyze/job_doesnotexist")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_job_after_upload(client: AsyncClient):
    upload = await client.post(
        "/api/analyze/upload",
        files={"file": ("clip.mp4", b"\x00" * 16, "video/mp4")},
    )
    job_id = upload.json()["job_id"]

    response = await client.get(f"/api/analyze/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job_id
    assert "status" in data
    assert "progress" in data

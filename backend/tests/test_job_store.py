import pytest
from app.services.job_store import JobStore, JobNotFoundError
from app.schemas.jobs import SourceType, JobStatus


@pytest.fixture
def store():
    return JobStore()


def test_create_job_returns_job_with_id(store):
    job = store.create_job(source_type=SourceType.UPLOAD, source_name="test.mp4")
    assert job.job_id.startswith("job_")
    assert job.status == "queued"
    assert job.progress == 0


def test_get_job_returns_created_job(store):
    job = store.create_job(source_type=SourceType.UPLOAD, source_name="test.mp4")
    fetched = store.get_job(job.job_id)
    assert fetched is not None
    assert fetched.job_id == job.job_id


def test_get_job_returns_none_for_unknown(store):
    assert store.get_job("job_unknown") is None


def test_update_job_changes_status_and_progress(store):
    job = store.create_job(source_type=SourceType.UPLOAD, source_name="test.mp4")
    updated = store.update_job(job.job_id, status=JobStatus.PROCESSING, progress=25)
    assert updated.status == "processing"
    assert updated.progress == 25


def test_update_job_clamps_progress_above_100(store):
    job = store.create_job(source_type=SourceType.UPLOAD, source_name="test.mp4")
    updated = store.update_job(job.job_id, progress=150)
    assert updated.progress == 100


def test_update_job_clamps_progress_below_0(store):
    job = store.create_job(source_type=SourceType.UPLOAD, source_name="test.mp4")
    updated = store.update_job(job.job_id, progress=-10)
    assert updated.progress == 0


def test_fail_job_sets_failed_status(store):
    job = store.create_job(source_type=SourceType.UPLOAD, source_name="test.mp4")
    failed = store.fail_job(job.job_id, error="Something broke", message="Failed")
    assert failed.status == "failed"
    assert failed.error == "Something broke"


def test_update_nonexistent_job_raises(store):
    with pytest.raises(JobNotFoundError):
        store.update_job("job_ghost", progress=50)


def test_delete_job_removes_it(store):
    job = store.create_job(source_type=SourceType.UPLOAD, source_name="test.mp4")
    store.delete_job(job.job_id)
    assert store.get_job(job.job_id) is None


def test_list_jobs_returns_all(store):
    store.create_job(source_type=SourceType.UPLOAD, source_name="a.mp4")
    store.create_job(source_type=SourceType.YOUTUBE, source_name="https://youtube.com/watch?v=abc")
    assert len(store.list_jobs()) == 2


def test_completed_job_has_100_progress(store):
    job = store.create_job(source_type=SourceType.UPLOAD, source_name="test.mp4")
    updated = store.update_job(job.job_id, status=JobStatus.COMPLETED)
    assert updated.progress == 100

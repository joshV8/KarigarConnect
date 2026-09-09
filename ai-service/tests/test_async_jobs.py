"""
Gate 12 tests — Async AI Processing Service & Endpoints.

Per 12_GATE_ASYNC_JOBS.md acceptance criteria:
- Prevents client/mobile app from waiting on long-running AI requests.
- When catalog request starts: returns 202 with { "status": "processing", "job_id": "..." }.
- Runs pipeline as a background task.
- Exposes GET /ai/status/{job_id}:
    - processing: { "status": "processing", "job_id": "..." }
    - completed: { "status": "completed", "result": { ... } }
    - failed: { "status": "failed", "error": "..." }
- Unknown job returns 404.
"""

import io
import time
import pytest
from PIL import Image

from app.models.jobs import AsyncCatalogSubmissionResponse, JobStatusResponse
from app.services.job_service import create_job, get_job, start_catalog_job

try:
    from fastapi.testclient import TestClient
    from app.main import app

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


def _make_test_image(width: int = 350, height: int = 350) -> bytes:
    img = Image.new("RGB", (width, height), color=(180, 100, 60))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Unit and Model Tests
# ---------------------------------------------------------------------------


def test_job_models():
    """Job status models serialize correctly."""
    sub = AsyncCatalogSubmissionResponse(job_id="test123", status="processing")
    assert sub.job_id == "test123"
    assert sub.status == "processing"

    stat = JobStatusResponse(job_id="test123", status="completed", result=None)
    assert stat.job_id == "test123"
    assert stat.status == "completed"


def test_create_and_get_job():
    """Job creation and retrieval in in-memory store."""
    job_id = create_job()
    assert job_id is not None
    job = get_job(job_id)
    assert job is not None
    assert job.status == "processing"
    assert job.job_id == job_id


def test_get_unknown_job_returns_none():
    """Non-existent job returns None."""
    assert get_job("non_existent_id") is None


def test_start_catalog_job_execution(monkeypatch):
    """start_catalog_job spawns background thread and completes with result."""
    monkeypatch.setenv("AI_EMULATOR_MODE", "true")
    img_bytes = _make_test_image()

    job_id = start_catalog_job(
        image_bytes=img_bytes,
        raw_material_cost=200.0,
        labour_cost=150.0,
        skip_bg_removal=True,
    )
    assert job_id is not None

    # Poll until completion or timeout (max 5 seconds)
    max_wait = 5.0
    start = time.time()
    completed = False
    while time.time() - start < max_wait:
        job = get_job(job_id)
        if job and job.status == "completed":
            completed = True
            assert job.result is not None
            assert job.result.product.name != ""
            break
        time.sleep(0.1)

    assert completed, "Background job did not complete within timeout"


# ---------------------------------------------------------------------------
# FastAPI Endpoint Tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="fastapi not installed")
class TestAsyncJobsEndpoint:
    def setup_method(self):
        self.client = TestClient(app)

    def test_endpoint_async_flow(self, monkeypatch):
        """Full end-to-end async submit and poll cycle."""
        monkeypatch.setenv("AI_EMULATOR_MODE", "true")
        img_bytes = _make_test_image()

        files = {"image": ("test.jpg", img_bytes, "image/jpeg")}
        data = {
            "raw_material_cost": "300",
            "labour_cost": "200",
            "skip_bg_removal": "true",
        }

        # 1. Submit async job
        res = self.client.post("/ai/generate-catalog-async", files=files, data=data)
        assert res.status_code == 202
        body = res.json()
        assert "job_id" in body
        assert body["status"] == "processing"
        job_id = body["job_id"]

        # 2. Poll status
        max_wait = 5.0
        start = time.time()
        final_status = None
        while time.time() - start < max_wait:
            poll_res = self.client.get(f"/ai/status/{job_id}")
            assert poll_res.status_code == 200
            p_data = poll_res.json()
            if p_data["status"] == "completed":
                final_status = "completed"
                assert "result" in p_data and p_data["result"] is not None
                assert "product" in p_data["result"]
                assert "pricing" in p_data["result"]
                break
            time.sleep(0.1)

        assert final_status == "completed"

    def test_endpoint_status_unknown_job_returns_404(self):
        """Polling non-existent job returns HTTP 404."""
        res = self.client.get("/ai/status/unknown_12345")
        assert res.status_code == 404
        assert "not found" in res.json()["detail"]

    def test_endpoint_async_rejects_empty_file(self):
        """Submitting empty file is rejected with 400."""
        files = {"image": ("empty.jpg", b"", "image/jpeg")}
        res = self.client.post("/ai/generate-catalog-async", files=files)
        assert res.status_code in (400, 422)

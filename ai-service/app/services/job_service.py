"""
Job Service — Gate 12: Async AI Processing.

Manages background task execution for long-running catalog generation jobs.
Maintains in-memory job dictionary with status tracking ('processing', 'completed', 'failed').
"""

import asyncio
import logging
import threading
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from app.models.catalog import CatalogResult
from app.models.jobs import JobStatusResponse
from app.services.catalog_service import orchestrate_catalog

logger = logging.getLogger("artisan_ai_service.jobs")

# In-memory job repository for hackathon / demo MVP
# Thread-safe access via lock
_jobs_lock = threading.Lock()
_jobs: Dict[str, Dict[str, Any]] = {}


def create_job() -> str:
    """Initialize a new job record with status 'processing' and return its unique ID."""
    job_id = uuid.uuid4().hex[:12]
    with _jobs_lock:
        _jobs[job_id] = {
            "job_id": job_id,
            "status": "processing",
            "result": None,
            "error": None,
            "created_at": datetime.utcnow().isoformat(),
        }
    return job_id


def get_job(job_id: str) -> Optional[JobStatusResponse]:
    """Retrieve current job record if exists."""
    with _jobs_lock:
        data = _jobs.get(job_id)
        if not data:
            return None
        return JobStatusResponse(
            job_id=data["job_id"],
            status=data["status"],
            result=data.get("result"),
            error=data.get("error"),
        )


def _execute_catalog_worker(
    job_id: str,
    image_bytes: bytes,
    image_filename: str,
    image_mime_type: str,
    audio_bytes: Optional[bytes],
    audio_filename: str,
    raw_material_cost: float,
    labour_cost: float,
    packaging_cost: float,
    other_cost: float,
    quality: Optional[str],
    demand: Optional[str],
    artisan_notes: Optional[str],
    skip_bg_removal: bool,
):
    """Worker function that runs synchronous orchestrate_catalog inside background thread/task."""
    logger.info("Executing background catalog job: %s", job_id)
    try:
        catalog_result = orchestrate_catalog(
            image_bytes=image_bytes,
            image_filename=image_filename,
            image_mime_type=image_mime_type,
            audio_bytes=audio_bytes,
            audio_filename=audio_filename,
            raw_material_cost=raw_material_cost,
            labour_cost=labour_cost,
            packaging_cost=packaging_cost,
            other_cost=other_cost,
            quality=quality,
            demand=demand,
            artisan_notes=artisan_notes,
            skip_bg_removal=skip_bg_removal,
        )
        with _jobs_lock:
            if job_id in _jobs:
                _jobs[job_id]["status"] = "completed"
                _jobs[job_id]["result"] = catalog_result
        logger.info("Background catalog job completed successfully: %s", job_id)
    except Exception as exc:
        logger.exception("Background catalog job failed for %s: %s", job_id, exc)
        with _jobs_lock:
            if job_id in _jobs:
                _jobs[job_id]["status"] = "failed"
                _jobs[job_id]["error"] = str(exc)


def start_catalog_job(
    image_bytes: bytes,
    image_filename: str = "product.jpg",
    image_mime_type: str = "image/jpeg",
    audio_bytes: Optional[bytes] = None,
    audio_filename: str = "audio.wav",
    raw_material_cost: float = 0.0,
    labour_cost: float = 0.0,
    packaging_cost: float = 0.0,
    other_cost: float = 0.0,
    quality: Optional[str] = "standard",
    demand: Optional[str] = "medium",
    artisan_notes: Optional[str] = None,
    skip_bg_removal: bool = False,
) -> str:
    """
    Spawns background task for catalog generation and returns immediately with job_id.
    """
    job_id = create_job()

    # Launch in a background thread so FastAPI handler returns immediately (<10ms)
    worker_thread = threading.Thread(
        target=_execute_catalog_worker,
        kwargs={
            "job_id": job_id,
            "image_bytes": image_bytes,
            "image_filename": image_filename,
            "image_mime_type": image_mime_type,
            "audio_bytes": audio_bytes,
            "audio_filename": audio_filename,
            "raw_material_cost": raw_material_cost,
            "labour_cost": labour_cost,
            "packaging_cost": packaging_cost,
            "other_cost": other_cost,
            "quality": quality,
            "demand": demand,
            "artisan_notes": artisan_notes,
            "skip_bg_removal": skip_bg_removal,
        },
        daemon=True,
    )
    worker_thread.start()

    return job_id

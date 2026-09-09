"""
Jobs router — Gate 12: Async AI Processing.

Exposes:
- POST /ai/generate-catalog-async: starts long-running job and returns immediately with job_id.
- GET /ai/status/{job_id}: retrieves current job status ('processing', 'completed', 'failed').
"""

from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.models.jobs import AsyncCatalogSubmissionResponse, JobStatusResponse
from app.services.job_service import get_job, start_catalog_job

router = APIRouter(prefix="/ai", tags=["async-jobs"])


@router.post(
    "/generate-catalog-async",
    response_model=AsyncCatalogSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_catalog_async(
    image: Optional[UploadFile] = File(None, description="Product photograph to be processed in the background."),
    photo: Optional[UploadFile] = File(None, description="Product photograph alias."),
    file: Optional[UploadFile] = File(None, description="Product photograph alias."),
    audio: Optional[UploadFile] = File(None, description="Optional artisan voice audio file."),
    raw_material_cost: Optional[float] = Form(0.0, description="Raw material cost in INR."),
    labour_cost: Optional[float] = Form(0.0, description="Artisan labour cost in INR."),
    packaging_cost: Optional[float] = Form(0.0, description="Packaging cost in INR."),
    other_cost: Optional[float] = Form(0.0, description="Miscellaneous overhead in INR."),
    quality: Optional[str] = Form("standard", description="Artisan craft quality."),
    demand: Optional[str] = Form("medium", description="Market demand level."),
    artisan_notes: Optional[str] = Form(None, description="Optional artisan story or notes."),
    skip_bg_removal: Optional[bool] = Form(False, description="Optional flag to skip background removal."),
) -> AsyncCatalogSubmissionResponse:
    """
    Start an asynchronous catalog generation pipeline.
    Returns HTTP 202 Accepted immediately with a unique job ID to poll.
    """
    img = image or photo or file
    if img is None:
        raise HTTPException(status_code=400, detail="Image file is missing.")
    image_bytes = await img.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Image file is empty.")

    audio_bytes: Optional[bytes] = None
    audio_filename: str = "audio.wav"
    if audio is not None:
        audio_bytes = await audio.read()
        audio_filename = audio.filename or "audio.wav"

    job_id = start_catalog_job(
        image_bytes=image_bytes,
        image_filename=image.filename or "product.jpg",
        image_mime_type=image.content_type or "image/jpeg",
        audio_bytes=audio_bytes,
        audio_filename=audio_filename,
        raw_material_cost=raw_material_cost or 0.0,
        labour_cost=labour_cost or 0.0,
        packaging_cost=packaging_cost or 0.0,
        other_cost=other_cost or 0.0,
        quality=quality,
        demand=demand,
        artisan_notes=artisan_notes,
        skip_bg_removal=bool(skip_bg_removal),
    )

    return AsyncCatalogSubmissionResponse(
        job_id=job_id,
        status="processing",
        message="Catalog generation started in the background. Poll /ai/status/{job_id} for results.",
    )


@router.get("/status/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str) -> JobStatusResponse:
    """
    Poll the status of an asynchronous job.

    Returns:
        - processing: { "job_id": "...", "status": "processing" }
        - completed: { "job_id": "...", "status": "completed", "result": { ... } }
        - failed: { "job_id": "...", "status": "failed", "error": "..." }
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return job

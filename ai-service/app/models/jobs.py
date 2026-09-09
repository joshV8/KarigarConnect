"""
Async job models — Gate 12: Async AI Processing.

Defines schemas for non-blocking asynchronous catalog generation jobs and polling status,
per 12_GATE_ASYNC_JOBS.md.
"""

from typing import Optional
from pydantic import BaseModel, Field

from app.models.catalog import CatalogResult


class AsyncCatalogSubmissionResponse(BaseModel):
    """Immediate response returned to client when an async job is launched."""
    job_id: str = Field(..., description="Unique tracking identifier for the background job.")
    status: str = Field(default="processing", description="Initial status of the job ('processing').")
    message: str = Field(
        default="Catalog generation started in the background. Poll /ai/status/{job_id} for results.",
        description="User-friendly status notice.",
    )


class JobStatusResponse(BaseModel):
    """
    Response schema for polling GET /ai/status/{job_id}.

    Per 12_GATE_ASYNC_JOBS.md:
    - Processing: { "status": "processing", "job_id": "..." }
    - Completed: { "status": "completed", "result": { ... } }
    - Failed: { "status": "failed", "error": "..." }
    """
    job_id: str = Field(..., description="Unique job identifier.")
    status: str = Field(..., description="Current job status: 'processing', 'completed', or 'failed'.")
    result: Optional[CatalogResult] = Field(None, description="Complete catalog result if status is completed.")
    error: Optional[str] = Field(None, description="Error message if status is failed.")

"""
Artisan AI Service — main FastAPI application entrypoint.

Gate 1 — AI Service Foundation.
Gate 2 — Image Upload & Validation.
Gate 3 — Background Removal.
Gate 4 — Image Enhancement.
Gate 5 — Product Vision / Attribute Extraction.
Gate 6 — Speech-to-Text.

This module wires up the FastAPI app, loads environment variables, and
registers feature routers as their gates are completed.
"""

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.routers import background as background_router
from app.routers import catalog as catalog_router
from app.routers import description as description_router
from app.routers import enhancement as enhancement_router
from app.routers import image as image_router
from app.routers import jobs as jobs_router
from app.routers import pricing as pricing_router
from app.routers import seo as seo_router
from app.routers import speech as speech_router
from app.routers import translation as translation_router
from app.routers import vision as vision_router

# Load environment variables from .env for local development.
# In production, real environment variables should be injected by the
# deployment platform instead of relying on a .env file.
load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("artisan_ai_service")


def _cors_origins() -> list[str]:
    """Return explicitly configured browser origins for deployed environments."""
    configured = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
    if configured:
        return [origin.strip() for origin in configured.split(",") if origin.strip()]
    # Local Flutter web and the API dashboard are the only safe defaults.
    return ["http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:8000"]

app = FastAPI(
    title="Artisan AI Service",
    description="AI/ML backend for the KarigarConnect Artisan AI Marketplace.",
    version="1.0.0",
)

# Browser clients must be explicitly configured in production through
# CORS_ALLOW_ORIGINS (a comma-separated list); do not use a wildcard.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Basic global error handler so an unexpected failure in any future
    router/service returns a clean structured JSON error instead of
    leaking a raw stack trace to the client.
    """
    logger.exception("Unhandled exception while processing %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "An unexpected error occurred. Please try again.",
        },
    )


@app.get("/health")
def health():
    """
    Basic liveness check. Used by the deployment platform, Person 3's
    backend, and manual testing to confirm the AI service is running.
    """
    return {"status": "ok"}


app.include_router(image_router.router)
app.include_router(background_router.router)
app.include_router(enhancement_router.router)
app.include_router(vision_router.router)
app.include_router(speech_router.router)
app.include_router(translation_router.router)
app.include_router(description_router.router)
app.include_router(seo_router.router)
app.include_router(pricing_router.router)
app.include_router(catalog_router.router)
app.include_router(jobs_router.router)







@app.get("/")
def root():
    """Simple root route so hitting the base URL doesn't 404 during manual checks."""
    return {
        "service": "Artisan AI Service",
        "status": "ok",
        "docs": "/docs",
        "dashboard": "/dashboard",
    }


@app.get("/dashboard")
def dashboard():
    """Serve the interactive test dashboard directly from the API service."""
    html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_dashboard.html")
    if os.path.exists(html_path):
        return FileResponse(html_path, media_type="text/html")
    return JSONResponse(status_code=404, content={"message": "test_dashboard.html not found"})

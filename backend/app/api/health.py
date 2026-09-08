import logging
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.config import API_TITLE, API_VERSION, ENVIRONMENT
from app.database import get_db

logger = logging.getLogger("artisan.health")
router = APIRouter(tags=["Health & System"])


@router.get("/health")
def health_check():
    """Health check endpoint to verify that the FastAPI service is running."""
    return {
        "status": "ok",
        "service": "artisan-api",
        "version": API_VERSION,
        "environment": ENVIRONMENT,
    }


@router.get("/health/db")
def database_health_check(response: Response, db: Session = Depends(get_db)):
    """Verifies database connectivity without exposing connection strings or credentials."""
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "service": "artisan-api",
            "database": "connected",
        }
    except Exception as exc:
        logger.error(f"Database health check failed: {exc}", exc_info=True)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unhealthy",
            "service": "artisan-api",
            "database": "disconnected",
        }


@router.get("/version")
def version_check():
    """Returns application name and centralized version number."""
    return {
        "name": API_TITLE,
        "version": API_VERSION,
    }

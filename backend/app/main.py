import os
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.config import (
    API_TITLE,
    API_VERSION,
    ENVIRONMENT,
    ALLOWED_ORIGINS,
)
from app.database import engine, Base
import app.models  # Ensures all models are registered with SQLAlchemy Base
from app.api.health import router as health_router
from app.api.products import router as products_router
from app.api.catalogs import router as catalogs_router
from app.api.buyers import router as buyers_router
from app.api.users import router as users_router
from app.api.enquiries import router as enquiries_router
from app.api.notifications import router as notifications_router
from app.api.marketplace import router as marketplace_router

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("artisan.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting Artisan API (Environment: {ENVIRONMENT}, Version: {API_VERSION})...")
    
    # Create all tables safely on startup
    try:
        Base.metadata.create_all(bind=engine)
        with engine.connect() as conn:
            # Columns compatibility
            conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS seo_title VARCHAR(255);"))
            conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS seo_keywords JSON;"))
            conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS voice_transcription TEXT;"))
            conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS translated_voice_text TEXT;"))
            conn.execute(text("ALTER TABLE catalogs ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'draft';"))
            conn.execute(text("ALTER TABLE enquiries ADD COLUMN IF NOT EXISTS artisan_response TEXT;"))
            conn.execute(text("ALTER TABLE enquiries ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();"))
            conn.execute(text("ALTER TABLE enquiries ADD COLUMN IF NOT EXISTS responded_at TIMESTAMP WITH TIME ZONE;"))
            conn.commit()
        logger.info("Database schema initialized and verified.")
    except Exception as exc:
        logger.error(f"Database initialization error: {exc}", exc_info=True)

    yield
    logger.info("Artisan API shutting down.")


app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Request Logging & Timing Middleware
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start_time = time.time()
    method = request.method
    path = request.url.path
    
    response = await call_next(request)
    
    duration_ms = round((time.time() - start_time) * 1000, 2)
    logger.info(f"[{method}] {path} -> Status {response.status_code} ({duration_ms}ms)")
    return response


# Global Standardized Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Format HTTPExceptions consistently with human-readable detail and error code."""
    status_to_code = {
        400: "BAD_REQUEST",
        401: "AUTH_REQUIRED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        502: "AI_SERVICE_UNAVAILABLE",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT",
    }
    code = getattr(exc, "code", status_to_code.get(exc.status_code, "HTTP_ERROR"))
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": code},
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Format Pydantic validation errors cleanly."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error: please check the submitted request fields.",
            "code": "VALIDATION_ERROR",
            "errors": jsonable_encoder(exc.errors()),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Protect against unexpected stack trace exposure in production."""
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    if ENVIRONMENT == "production":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error", "code": "INTERNAL_SERVER_ERROR"},
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error: {str(exc)}", "code": "INTERNAL_SERVER_ERROR"},
    )


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount local uploads directories for development fallback
uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
os.makedirs(uploads_dir, exist_ok=True)
os.makedirs(os.path.join(uploads_dir, "products"), exist_ok=True)
os.makedirs(os.path.join(uploads_dir, "audio"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Include Routers under both /api/v1 prefix and root for full backwards compatibility
API_V1_PREFIX = "/api/v1"

# Health & System
app.include_router(health_router)
app.include_router(health_router, prefix=API_V1_PREFIX)

# Business domains (Products, Catalogs, Buyers, Users, Enquiries, Notifications, Marketplace)
app.include_router(products_router)
app.include_router(products_router, prefix=API_V1_PREFIX)

app.include_router(catalogs_router)
app.include_router(catalogs_router, prefix=API_V1_PREFIX)

app.include_router(buyers_router)
app.include_router(buyers_router, prefix=API_V1_PREFIX)

app.include_router(users_router)
app.include_router(users_router, prefix=API_V1_PREFIX)

app.include_router(enquiries_router)
app.include_router(enquiries_router, prefix=API_V1_PREFIX)

app.include_router(notifications_router)
app.include_router(notifications_router, prefix=API_V1_PREFIX)

app.include_router(marketplace_router)
app.include_router(marketplace_router, prefix=API_V1_PREFIX)


@app.get("/")
def root():
    """Root endpoint providing service discovery and status."""
    return {
        "title": API_TITLE,
        "version": API_VERSION,
        "environment": ENVIRONMENT,
        "status": "running",
        "docs": "/docs",
        "api_v1": "/api/v1",
    }

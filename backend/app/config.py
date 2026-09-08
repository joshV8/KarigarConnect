import os
from typing import List
from dotenv import load_dotenv
import cloudinary

# Load environment variables from .env file
load_dotenv()

# Environment Mode: "development" | "production" | "testing"
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower().strip()

# Database Configuration
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql://username:password@localhost:5432/artisan_db"
)

# API Metadata
API_TITLE: str = "Artisan App API"
API_VERSION: str = "1.0.0"

# CORS Configuration
# In production, pass comma-separated URLs: ALLOWED_ORIGINS="https://myartisanapp.com,https://artisan-web.vercel.app"
ALLOWED_ORIGINS_RAW: str = os.getenv("ALLOWED_ORIGINS", "")
if ALLOWED_ORIGINS_RAW.strip():
    ALLOWED_ORIGINS: List[str] = [origin.strip() for origin in ALLOWED_ORIGINS_RAW.split(",") if origin.strip()]
else:
    # Development default: allow all origins
    ALLOWED_ORIGINS: List[str] = ["*"]

# Cloudinary Storage Configuration
CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "")
CLOUDINARY_FOLDER: str = os.getenv("CLOUDINARY_FOLDER", "artisan/products")

IS_CLOUDINARY_CONFIGURED: bool = bool(
    CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET
)

if IS_CLOUDINARY_CONFIGURED:
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True,
    )

# AI Service Configuration (Person 2 Integration)
# In production, defaults to "remote" if an AI_SERVICE_URL is set, otherwise "mock"
_default_ai_mode = "remote" if (ENVIRONMENT == "production" and os.getenv("AI_SERVICE_URL")) else "mock"
AI_MODE: str = os.getenv("AI_MODE", _default_ai_mode).lower().strip()
AI_SERVICE_URL: str = os.getenv("AI_SERVICE_URL", "http://localhost:9000").rstrip("/")
AI_SERVICE_TIMEOUT: float = float(os.getenv("AI_SERVICE_TIMEOUT", "120.0"))

# Pricing Engine Configuration (Phase 5)
ARTISAN_MARGIN_PERCENT: float = float(os.getenv("ARTISAN_MARGIN_PERCENT", "20.0"))
DEFAULT_MARKET_ADJUSTMENT: float = float(os.getenv("DEFAULT_MARKET_ADJUSTMENT", "0.0"))
DEFAULT_DEMAND_ADJUSTMENT: float = float(os.getenv("DEFAULT_DEMAND_ADJUSTMENT", "0.0"))

# Firebase Authentication Configuration (Phase 7)
# In production, defaults to "firebase" unless mock is explicitly set
_default_auth_mode = "firebase" if (ENVIRONMENT == "production") else "mock"
AUTH_MODE: str = os.getenv("AUTH_MODE", _default_auth_mode).lower().strip()
FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "")
FIREBASE_CLIENT_EMAIL: str = os.getenv("FIREBASE_CLIENT_EMAIL", "")
FIREBASE_PRIVATE_KEY: str = os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n")
FIREBASE_CREDENTIALS_PATH: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "")

IS_FIREBASE_CONFIGURED: bool = bool(
    (FIREBASE_PROJECT_ID and FIREBASE_CLIENT_EMAIL and FIREBASE_PRIVATE_KEY)
    or (FIREBASE_CREDENTIALS_PATH and os.path.exists(FIREBASE_CREDENTIALS_PATH))
)

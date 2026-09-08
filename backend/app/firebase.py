import logging
from typing import Optional, Dict, Any
import firebase_admin
from firebase_admin import auth, credentials

from app.config import (
    AUTH_MODE,
    FIREBASE_PROJECT_ID,
    FIREBASE_CLIENT_EMAIL,
    FIREBASE_PRIVATE_KEY,
    FIREBASE_CREDENTIALS_PATH,
    IS_FIREBASE_CONFIGURED,
)

logger = logging.getLogger("artisan.firebase")

_firebase_app: Optional[firebase_admin.App] = None


def initialize_firebase() -> Optional[firebase_admin.App]:
    """Initialize Firebase Admin SDK singleton once on application startup."""
    global _firebase_app
    if _firebase_app is not None or firebase_admin._apps:
        return _firebase_app or firebase_admin.get_app()

    if not IS_FIREBASE_CONFIGURED:
        logger.info(
            f"[FIREBASE] Real Firebase credentials not provided. Operating in AUTH_MODE='{AUTH_MODE}'."
        )
        return None

    try:
        if FIREBASE_CREDENTIALS_PATH:
            cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        else:
            cred = credentials.Certificate(
                {
                    "type": "service_account",
                    "project_id": FIREBASE_PROJECT_ID,
                    "client_email": FIREBASE_CLIENT_EMAIL,
                    "private_key": FIREBASE_PRIVATE_KEY,
                }
            )

        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info(f"Firebase Admin SDK initialized for project '{FIREBASE_PROJECT_ID}'.")
        return _firebase_app
    except Exception as exc:
        logger.error(f"Failed to initialize Firebase Admin SDK: {exc}", exc_info=True)
        return None


def verify_firebase_id_token(id_token: str) -> Dict[str, Any]:
    """Verify a Firebase ID token and return decoded claims.
    
    Raises ValueError or firebase_admin.exceptions.FirebaseError if verification fails.
    """
    if not firebase_admin._apps and IS_FIREBASE_CONFIGURED:
        initialize_firebase()

    decoded_token = auth.verify_id_token(id_token)
    return decoded_token

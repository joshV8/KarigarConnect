import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import AUTH_MODE
from app.database import get_db
from app.models.user import User
from app.firebase import verify_firebase_id_token

logger = logging.getLogger("artisan.auth")

# FastAPI security scheme allowing Swagger UI Bearer token entry
security_scheme = HTTPBearer(
    auto_error=False,
    description="Enter your Firebase ID Token (or mock token in AUTH_MODE=mock, e.g. 'mock_user_1')",
)


def get_current_user(
    auth_creds: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency to verify bearer token and resolve authenticated PostgreSQL User."""
    if not auth_creds or not auth_creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_creds.credentials.strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token cannot be empty",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ----------------------------------------------------
    # Development Mock Authentication Mode
    # ----------------------------------------------------
    if AUTH_MODE == "mock":
        # Reject deliberately invalid test tokens
        if token.lower() in {"invalid", "bad_token", "expired", "fake"}:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        uid = token if token.startswith("uid_") or token.startswith("mock_") else f"mock_{token}"
        user = db.query(User).filter(User.firebase_uid == uid).first()
        if not user:
            user = User(
                firebase_uid=uid,
                name=f"Artisan {uid[-6:]}",
                phone="+91-98765-43210",
                language="hi",
                location="India",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        return user

    # ----------------------------------------------------
    # Production Firebase Authentication Mode
    # ----------------------------------------------------
    try:
        claims = verify_firebase_id_token(token)
    except Exception as exc:
        logger.warning(f"Firebase token verification failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    uid = claims.get("uid")
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token claims: missing uid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Find or auto-provision user in PostgreSQL
    user = db.query(User).filter(User.firebase_uid == uid).first()
    if not user:
        user = User(
            firebase_uid=uid,
            name=claims.get("name") or "Artisan",
            phone=claims.get("phone_number"),
            language="hi",
            location=None,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user

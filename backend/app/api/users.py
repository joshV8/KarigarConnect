from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.api.dependencies import get_current_user

router = APIRouter(
    prefix="/users",
    tags=["Users & Profile"],
)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current artisan profile",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """Retrieve profile and settings for the authenticated artisan."""
    return current_user


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update artisan profile",
)
def update_current_user_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update preferred language, name, or location for the authenticated artisan."""
    if payload.name is not None:
        cleaned_name = payload.name.strip()
        if not cleaned_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Name cannot be empty",
            )
        current_user.name = cleaned_name

    if payload.language is not None:
        current_user.language = payload.language.strip()

    if payload.location is not None:
        current_user.location = payload.location.strip()

    db.commit()
    db.refresh(current_user)
    return current_user

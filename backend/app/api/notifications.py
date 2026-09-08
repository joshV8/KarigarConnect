from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    UnreadCountResponse,
)
from app.api.dependencies import get_current_user

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="List in-app notifications for authenticated artisan",
)
def list_notifications(
    unread_only: bool = Query(default=False, description="Filter to unread notifications only"),
    limit: int = Query(default=20, ge=1, le=100, description="Pagination limit"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve notifications belonging to the authenticated artisan, ordered newest first."""
    base_query = db.query(Notification).filter(Notification.user_id == current_user.id)

    total_count = base_query.count()
    unread_count = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read == False)
        .count()
    )

    query = base_query
    if unread_only:
        query = query.filter(Notification.is_read == False)

    notifications = (
        query.order_by(Notification.created_at.desc(), Notification.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return NotificationListResponse(
        notifications=notifications,
        total=total_count,
        unread_count=unread_count,
    )


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
    summary="Get unread notification count for badge counters",
)
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the total number of unread notifications for the authenticated artisan."""
    count = (
        db.query(func.count(Notification.id))
        .filter(Notification.user_id == current_user.id, Notification.is_read == False)
        .scalar()
        or 0
    )
    return UnreadCountResponse(count=count)


@router.put(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark a specific notification as read (Owner only)",
)
def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a single notification as read if owned by the current user."""
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current_user.id)
        .first()
    )
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


@router.put(
    "/read-all",
    summary="Mark all notifications as read for current user",
)
def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all unread notifications belonging to the current user as read."""
    updated_rows = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read == False)
        .update({Notification.is_read: True}, synchronize_session=False)
    )
    db.commit()
    return {
        "status": "success",
        "message": f"Marked {updated_rows} notifications as read",
        "updated_count": updated_rows,
    }

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    """Schema representing an in-app notification for an artisan."""
    id: int
    user_id: int
    type: str
    title: str
    message: str
    related_product_id: Optional[int] = None
    related_enquiry_id: Optional[int] = None
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    """Paginated list of notifications with unread counts."""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int


class UnreadCountResponse(BaseModel):
    """Quick unread notifications count for app badge counters."""
    count: int

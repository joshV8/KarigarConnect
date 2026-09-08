import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models.notification import Notification

logger = logging.getLogger("artisan.notification_service")


class NotificationService:
    """Service to create, retrieve, and manage in-app notifications for artisans."""

    @staticmethod
    def create_notification(
        db: Session,
        user_id: int,
        title: str,
        message: str,
        type: str = "new_enquiry",
        related_product_id: Optional[int] = None,
        related_enquiry_id: Optional[int] = None,
    ) -> Notification:
        """Create and persist a notification record for a specific user."""
        try:
            notification = Notification(
                user_id=user_id,
                type=type,
                title=title.strip(),
                message=message.strip(),
                related_product_id=related_product_id,
                related_enquiry_id=related_enquiry_id,
                is_read=False,
            )
            db.add(notification)
            db.commit()
            db.refresh(notification)
            logger.info(f"Created notification ID={notification.id} for User ID={user_id} (Type={type})")
            return notification
        except Exception as exc:
            db.rollback()
            logger.error(f"Failed to create notification: {exc}", exc_info=True)
            raise


notification_service = NotificationService()

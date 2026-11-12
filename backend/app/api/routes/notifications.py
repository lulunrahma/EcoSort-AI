from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.pydantic_models import NotificationResponse
from backend.app.services.notification_service import NotificationService

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.get("", response_model=List[NotificationResponse])
def get_notifications(
    limit: int = Query(default=50, ge=1, le=100),
    unread_only: bool = Query(default=False),
    db: Session = Depends(get_db)
):
    """Retrieves notifications log."""
    notifs = NotificationService.get_notifications(db, limit=limit, unread_only=unread_only)
    return [NotificationResponse.model_validate(n) for n in notifs]

@router.patch("/{notif_id}/read")
def mark_read(notif_id: int, db: Session = Depends(get_db)):
    """Marks a single notification as read."""
    success = NotificationService.mark_as_read(db, notif_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found.")
    return {"success": True, "message": "Notification marked as read."}

@router.post("/read-all")
def mark_all_read(db: Session = Depends(get_db)):
    """Marks all notifications as read."""
    count = NotificationService.mark_all_as_read(db)
    return {"success": True, "marked_count": count}


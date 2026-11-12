import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.models.entities import Notification, DetectionEvent
from backend.app.core.config import settings
from backend.app.core.logging import logger

class NotificationService:
    # Memory tracker for rule cooldowns: {rule_key: last_triggered_timestamp}
    _cooldowns: Dict[str, float] = {}

    @classmethod
    def evaluate_detection(cls, db: Session, event: DetectionEvent):
        """Checks if a new detection event trips an alert rule."""
        cname = event.class_name
        rule_key = f"high_volume_{cname}"
        now_ts = time.time()

        # Check cooldown
        last_time = cls._cooldowns.get(rule_key, 0)
        if (now_ts - last_time) < settings.ALERT_COOLDOWN_SECONDS:
            return

        # Query count of same class in the time window
        window_start = datetime.now(timezone.utc) - timedelta(seconds=settings.ALERT_WINDOW_SECONDS)
        count = (
            db.query(DetectionEvent)
            .filter(
                DetectionEvent.class_name == cname,
                DetectionEvent.detected_at >= window_start
            )
            .count()
        )

        if count >= settings.ALERT_THRESHOLD_COUNT:
            cls._cooldowns[rule_key] = now_ts
            title = f"Peringatan Volume Tinggi: {cname}"
            msg = (
                f"Terdeteksi {count} objek '{cname}' dalam rentang waktu "
                f"{settings.ALERT_WINDOW_SECONDS} detik terakhir pada meja pemilahan."
            )
            cls.create_notification(
                db=db,
                ntype="threshold_exceeded",
                title=title,
                message=msg,
                related_detection_id=event.id,
                rule_key=rule_key
            )
            logger.info(f"Notification triggered: {title}")

    @classmethod
    def create_notification(
        cls,
        db: Session,
        ntype: str,
        title: str,
        message: str,
        related_detection_id: Optional[int] = None,
        rule_key: Optional[str] = None
    ) -> Notification:
        notif = Notification(
            created_at=datetime.now(timezone.utc),
            type=ntype,
            title=title,
            message=message,
            related_detection_id=related_detection_id,
            rule_key=rule_key,
            is_read=False
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif

    @staticmethod
    def get_notifications(db: Session, limit: int = 50, unread_only: bool = False) -> List[Notification]:
        query = db.query(Notification)
        if unread_only:
            query = query.filter(Notification.is_read == False)
        return query.order_by(desc(Notification.created_at)).limit(limit).all()

    @staticmethod
    def mark_as_read(db: Session, notif_id: int) -> bool:
        notif = db.query(Notification).filter(Notification.id == notif_id).first()
        if notif:
            notif.is_read = True
            db.commit()
            return True
        return False

    @staticmethod
    def mark_all_as_read(db: Session) -> int:
        count = db.query(Notification).filter(Notification.is_read == False).update({"is_read": True})
        db.commit()
        return count


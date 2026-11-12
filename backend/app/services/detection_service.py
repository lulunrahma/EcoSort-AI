import json
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.app.models.entities import DetectionEvent, CameraSession
from backend.app.core.config import (
    OFFICIAL_CLASSES,
    CLASS_COLOR_PALETTE,
    MACRO_CATEGORIES,
    MACRO_CATEGORY_META
)
from backend.app.schemas.pydantic_models import ClassCount, ChartPoint, MacroCount
from backend.app.core.logging import logger

class DetectionService:
    @staticmethod
    def record_event(db: Session, event_data: Dict[str, Any]) -> DetectionEvent:
        """Stores a verified counting event into the database."""
        session_id = event_data.get("session_id")
        if session_id is None:
            active_session = db.query(CameraSession).filter(CameraSession.status == "active").first()
            if not active_session:
                active_session = CameraSession(status="active", camera_name="Default Session")
                db.add(active_session)
                db.commit()
                db.refresh(active_session)
            session_id = active_session.id

        event = DetectionEvent(
            camera_session_id=session_id,
            detected_at=datetime.now(timezone.utc),
            class_id=event_data["class_id"],
            class_name=event_data["class_name"],
            confidence=event_data["confidence"],
            track_id=event_data.get("track_id"),
            bbox_json=json.dumps(event_data.get("bbox", [])),
            snapshot_path=event_data.get("snapshot_path"),
            event_type=event_data.get("event_type", "line_crossing")
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def get_events(
        db: Session,
        page: int = 1,
        limit: int = 20,
        class_name: Optional[str] = None,
        macro_category: Optional[str] = None,
        min_confidence: Optional[float] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        session_id: Optional[int] = None
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """Queries detection history with filtering and pagination."""
        query = db.query(DetectionEvent)

        if class_name:
            query = query.filter(DetectionEvent.class_name == class_name)
        if min_confidence is not None:
            query = query.filter(DetectionEvent.confidence >= min_confidence)
        if start_date:
            query = query.filter(DetectionEvent.detected_at >= start_date)
        if end_date:
            query = query.filter(DetectionEvent.detected_at <= end_date)
        if session_id:
            query = query.filter(DetectionEvent.camera_session_id == session_id)

        # Macro Category Filter
        if macro_category:
            valid_classes = [c for c, m in MACRO_CATEGORIES.items() if m.lower() == macro_category.lower()]
            query = query.filter(DetectionEvent.class_name.in_(valid_classes))

        total = query.count()
        offset = (page - 1) * limit
        items = query.order_by(desc(DetectionEvent.detected_at)).offset(offset).limit(limit).all()

        formatted_items = []
        for it in items:
            formatted_items.append({
                "id": it.id,
                "camera_session_id": it.camera_session_id,
                "detected_at": it.detected_at,
                "class_id": it.class_id,
                "class_name": it.class_name,
                "macro_category": MACRO_CATEGORIES.get(it.class_name, "Anorganik"),
                "confidence": it.confidence,
                "track_id": it.track_id,
                "bbox_json": it.bbox_json,
                "snapshot_path": it.snapshot_path,
                "event_type": it.event_type
            })

        return total, formatted_items

    @staticmethod
    def get_summary(db: Session) -> Dict[str, Any]:
        """Calculates KPI summary statistics from the database including Macro Categories."""
        total = db.query(func.count(DetectionEvent.id)).scalar() or 0
        
        # Count per class
        class_rows = (
            db.query(DetectionEvent.class_name, func.count(DetectionEvent.id))
            .group_by(DetectionEvent.class_name)
            .all()
        )
        counts_dict = {row[0]: row[1] for row in class_rows}

        macro_counts = {"Anorganik": 0, "Organik": 0, "Berbahaya": 0}
        class_counts = []
        for idx, cname in enumerate(OFFICIAL_CLASSES):
            cnt = counts_dict.get(cname, 0)
            macro = MACRO_CATEGORIES.get(cname, "Anorganik")
            macro_counts[macro] = macro_counts.get(macro, 0) + cnt
            class_counts.append(ClassCount(
                class_id=idx,
                class_name=cname,
                count=cnt,
                color=CLASS_COLOR_PALETTE.get(cname, "#64748B"),
                macro_category=macro
            ))

        active_session = db.query(CameraSession).filter(CameraSession.status == "active").first()
        active_session_id = active_session.id if active_session else None

        return {
            "total_detections": total,
            "active_session_id": active_session_id,
            "class_counts": class_counts,
            "macro_counts": macro_counts
        }

    @staticmethod
    def get_chart_data(db: Session, hours: int = 24) -> Dict[str, Any]:
        """Calculates timeline and class/macro distribution for dashboard charts."""
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(hours=hours)

        # Timeline grouped by hour
        events = (
            db.query(DetectionEvent.detected_at)
            .filter(DetectionEvent.detected_at >= start_time)
            .all()
        )

        slots = {}
        for i in range(hours):
            t = start_time + timedelta(hours=i)
            slot_key = t.strftime("%H:00")
            slots[slot_key] = 0

        for e in events:
            if e.detected_at:
                key = e.detected_at.strftime("%H:00")
                if key in slots:
                    slots[key] += 1

        timeline = [ChartPoint(label=k, value=v) for k, v in slots.items()]

        summary = DetectionService.get_summary(db)
        distribution = summary["class_counts"]

        macro_dist = []
        for m_name, count in summary["macro_counts"].items():
            meta = MACRO_CATEGORY_META.get(m_name, {})
            macro_dist.append(MacroCount(
                category=m_name,
                count=count,
                color=meta.get("color", "#3B82F6"),
                icon=meta.get("icon", "📦"),
                description=meta.get("description", "")
            ))

        return {
            "timeline": timeline,
            "distribution": distribution,
            "macro_distribution": macro_dist
        }

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.pydantic_models import DashboardSummaryResponse, DashboardChartsResponse
from backend.app.services.detection_service import DetectionService
from backend.app.services.notification_service import NotificationService
from backend.app.cv.camera import camera_manager

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Provides high-level KPI card statistics calculated strictly from the database."""
    summary = DetectionService.get_summary(db)
    unread_notifs = len(NotificationService.get_notifications(db, limit=100, unread_only=True))

    return DashboardSummaryResponse(
        total_detections=summary["total_detections"],
        active_session_id=summary["active_session_id"],
        camera_status=camera_manager.status,
        model_status=camera_manager.detector.status,
        class_counts=summary["class_counts"],
        macro_counts=summary["macro_counts"],
        recent_notifications_count=unread_notifs
    )

@router.get("/charts", response_model=DashboardChartsResponse)
def get_dashboard_charts(hours: int = Query(default=24, ge=1, le=168), db: Session = Depends(get_db)):
    """Provides chart datasets for detection timeline and category distribution."""
    chart_data = DetectionService.get_chart_data(db, hours=hours)
    return DashboardChartsResponse(
        timeline=chart_data["timeline"],
        distribution=chart_data["distribution"],
        macro_distribution=chart_data["macro_distribution"]
    )


from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.pydantic_models import DetectionListResponse, DetectionEventResponse
from backend.app.services.detection_service import DetectionService
from backend.app.models.entities import DetectionEvent

router = APIRouter(prefix="/api/detections", tags=["Detections"])

@router.get("", response_model=DetectionListResponse)
def get_detections(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    class_name: Optional[str] = None,
    macro_category: Optional[str] = None,
    min_confidence: Optional[float] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    session_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Retrieves paginated and filtered detection events history."""
    total, items = DetectionService.get_events(
        db=db,
        page=page,
        limit=limit,
        class_name=class_name,
        macro_category=macro_category,
        min_confidence=min_confidence,
        start_date=start_date,
        end_date=end_date,
        session_id=session_id
    )

    return DetectionListResponse(
        total=total,
        items=[DetectionEventResponse.model_validate(item) for item in items],
        page=page,
        limit=limit
    )

@router.get("/{event_id}", response_model=DetectionEventResponse)
def get_detection_detail(event_id: int, db: Session = Depends(get_db)):
    """Retrieves a single detection event detail by ID."""
    event = db.query(DetectionEvent).filter(DetectionEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Detection event not found.")
    return DetectionEventResponse.model_validate(event)


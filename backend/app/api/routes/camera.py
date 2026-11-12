import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.core.database import get_db, SessionLocal
from backend.app.models.entities import CameraSession
from backend.app.cv.camera import camera_manager
from backend.app.services.detection_service import DetectionService
from backend.app.services.notification_service import NotificationService
from backend.app.core.logging import logger

router = APIRouter(prefix="/api/camera", tags=["Camera"])

# Callback to persist events and evaluate notifications
def on_detection_event(event_data: dict):
    db = SessionLocal()
    try:
        saved_event = DetectionService.record_event(db, event_data)
        NotificationService.evaluate_detection(db, saved_event)
    except Exception as e:
        logger.error(f"Error persisting detection event: {e}")
    finally:
        db.close()

# Register event callback once
if not camera_manager.event_callbacks:
    camera_manager.register_event_callback(on_detection_event)

@router.post("/start")
def start_camera(camera_index: int = Query(default=0), db: Session = Depends(get_db)):
    """Starts the camera capture and inference session."""
    # Create or retrieve active camera session in DB
    active_session = db.query(CameraSession).filter(CameraSession.status == "active").first()
    if not active_session:
        active_session = CameraSession(
            started_at=datetime.now(timezone.utc),
            status="active",
            camera_name=f"Webcam {camera_index}"
        )
        db.add(active_session)
        db.commit()
        db.refresh(active_session)

    success, message = camera_manager.start(session_id=active_session.id, camera_index=camera_index)
    return {
        "success": success,
        "message": message,
        "session_id": active_session.id,
        "camera_status": camera_manager.status
    }

@router.post("/stop")
def stop_camera(db: Session = Depends(get_db)):
    """Stops the camera capture session and releases hardware."""
    success, message = camera_manager.stop()
    
    # Mark DB session as stopped
    active_sessions = db.query(CameraSession).filter(CameraSession.status == "active").all()
    for s in active_sessions:
        s.status = "stopped"
        s.ended_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "success": success,
        "message": message,
        "camera_status": camera_manager.status
    }

@router.get("/status")
def get_camera_status():
    """Returns current live camera and inference status."""
    return {
        "status": camera_manager.status,
        "message": camera_manager.status_message,
        "fps": camera_manager.current_fps,
        "active_session_id": camera_manager.current_session_id,
        "model_status": camera_manager.detector.status,
        "model_message": camera_manager.detector.status_message,
        "is_demo_mode": camera_manager.detector.is_demo_mode,
        "line_ratio": camera_manager.counter.line_ratio,
        "session_counts": camera_manager.counter.class_counts,
        "total_count": camera_manager.counter.total_count
    }

def generate_mjpeg_frames():
    """Generator for MJPEG stream."""
    while True:
        frame_bytes = camera_manager.last_jpeg_bytes
        if frame_bytes is not None:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )
        time.sleep(0.04)  # ~25 FPS max stream output

@router.get("/stream")
def video_stream():
    """MJPEG Video Streaming Endpoint."""
    return StreamingResponse(
        generate_mjpeg_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


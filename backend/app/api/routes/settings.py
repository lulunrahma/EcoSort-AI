import os
from typing import Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.core.config import settings, OFFICIAL_CLASSES, MACRO_CATEGORIES, MACRO_CATEGORY_META
from backend.app.cv.camera import camera_manager

router = APIRouter(prefix="/api/settings", tags=["Settings"])

class UpdateSettingsRequest(BaseModel):
    confidence_threshold: float = None
    virtual_line_y: float = None
    demo_mode: bool = None
    max_fps: int = None

@router.get("")
def get_settings():
    """Gets application configuration and hardware/model state."""
    model_exists = os.path.exists(settings.MODEL_PATH)
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "camera_index": camera_manager.camera_index,
        "camera_status": camera_manager.status,
        "camera_message": camera_manager.status_message,
        "model_path": settings.MODEL_PATH,
        "model_exists": model_exists,
        "model_status": camera_manager.detector.status,
        "model_message": camera_manager.detector.status_message,
        "is_demo_mode": camera_manager.detector.is_demo_mode,
        "confidence_threshold": camera_manager.detector.conf_threshold,
        "max_fps": settings.MAX_INFERENCE_FPS,
        "virtual_line_y": camera_manager.counter.line_ratio,
        "classes": OFFICIAL_CLASSES,
        "macro_categories": MACRO_CATEGORIES,
        "macro_category_meta": MACRO_CATEGORY_META,
        "dataset_dir": "./dataset",
        "snapshot_dir": settings.SNAPSHOT_DIR,
        "report_dir": settings.REPORT_DIR
    }

@router.post("")
def update_settings(req: UpdateSettingsRequest):
    """Updates runtime CV and detection settings."""
    if req.confidence_threshold is not None:
        camera_manager.detector.conf_threshold = max(0.05, min(0.99, req.confidence_threshold))
    if req.virtual_line_y is not None:
        camera_manager.counter.set_line_ratio(req.virtual_line_y)
    if req.demo_mode is not None:
        camera_manager.detector.is_demo_mode = req.demo_mode
        if req.demo_mode:
            camera_manager.detector.status = "demo"
            camera_manager.detector.status_message = "Demo / Simulated detection mode is active."
        else:
            camera_manager.detector.load_model()

    return {
        "success": True,
        "message": "Settings updated successfully.",
        "settings": get_settings()
    }

@router.post("/reload-model")
def reload_model():
    """Triggers a reload of the YOLO model from disk (useful once training finishes)."""
    camera_manager.detector.load_model()
    return {
        "success": True,
        "status": camera_manager.detector.status,
        "message": camera_manager.detector.status_message
    }


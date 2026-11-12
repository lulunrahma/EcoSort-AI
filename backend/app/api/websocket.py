import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.cv.camera import camera_manager
from backend.app.core.logging import logger

router = APIRouter(tags=["WebSocket"])

@router.websocket("/ws/detection")
async def websocket_detection_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket client connected to /ws/detection")
    try:
        while True:
            # Send latest detection frame metadata
            payload = {
                "type": "detection_update",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "camera_status": camera_manager.status,
                "model_status": camera_manager.detector.status,
                "fps": camera_manager.current_fps,
                "objects": camera_manager.last_objects,
                "session_counts": camera_manager.counter.class_counts,
                "session_macro_counts": camera_manager.get_macro_counts(),
                "total_count": camera_manager.counter.total_count,
                "line_ratio": camera_manager.counter.line_ratio
            }
            await websocket.send_json(payload)
            await asyncio.sleep(0.1)  # ~10 Hz stream updates
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected from /ws/detection")
    except Exception as e:
        logger.warning(f"WebSocket connection error: {e}")


import os
import time
import json
import threading
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Callable, Tuple
import cv2
import numpy as np

from backend.app.core.config import settings, OFFICIAL_CLASSES, CLASS_COLOR_PALETTE, MACRO_CATEGORIES
from backend.app.core.logging import logger
from backend.app.cv.detector import WasteDetector
from backend.app.cv.tracker import WasteTracker
from backend.app.cv.counter import EventCounter

def hex_to_bgr(hex_str: str) -> Tuple[int, int, int]:
    hex_str = hex_str.lstrip("#")
    r, g, b = tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
    return (b, g, r)  # OpenCV uses BGR

class CameraManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CameraManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self.camera_index = settings.CAMERA_INDEX
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running: bool = False
        self.thread: Optional[threading.Thread] = None
        
        self.detector = WasteDetector()
        self.tracker = WasteTracker()
        self.counter = EventCounter()
        
        self.current_session_id: Optional[int] = None
        self.last_frame: Optional[np.ndarray] = None
        self.last_annotated_frame: Optional[np.ndarray] = None
        self.last_jpeg_bytes: Optional[bytes] = None
        self.last_objects: List[Dict[str, Any]] = []
        self.current_fps: float = 0.0
        self.status: str = "stopped"  # "stopped", "running", "error"
        self.status_message: str = "Camera is stopped."
        
        # Event callbacks (e.g. for saving to DB and firing alerts)
        self.event_callbacks: List[Callable[[Dict[str, Any]], None]] = []

    def register_event_callback(self, cb: Callable[[Dict[str, Any]], None]):
        self.event_callbacks.append(cb)

    def start(self, session_id: Optional[int] = None, camera_index: Optional[int] = None) -> Tuple[bool, str]:
        with self._lock:
            if self.is_running:
                return True, "Camera is already running."

            if camera_index is not None:
                self.camera_index = camera_index

            self.current_session_id = session_id
            self.counter.reset()
            self.tracker.reset()

            # Attempt to open camera device
            logger.info(f"Opening camera device index {self.camera_index}...")
            # Use CAP_DSHOW on Windows for fast webcam init
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY)
            
            # Check if camera opened
            if not self.cap.isOpened():
                logger.warning(f"Could not open physical camera at index {self.camera_index}. Enabling simulated camera feed.")
                self.cap.release()
                self.cap = None

            self.is_running = True
            self.status = "running"
            self.status_message = "Camera running." if self.cap else "Simulated camera stream running (no physical webcam found)."

            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            return True, self.status_message

    def stop(self) -> Tuple[bool, str]:
        with self._lock:
            if not self.is_running:
                return True, "Camera is already stopped."

            self.is_running = False
            self.status = "stopped"
            self.status_message = "Camera stopped."

            if self.cap is not None:
                self.cap.release()
                self.cap = None

            logger.info("Camera capture stopped and resources released.")
            return True, "Camera stopped successfully."

    def _capture_loop(self):
        fps_limit = max(1, settings.MAX_INFERENCE_FPS)
        frame_interval = 1.0 / fps_limit
        prev_time = time.time()
        frame_counter = 0

        while self.is_running:
            start_loop = time.time()

            if self.cap is not None and self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    logger.warning("Failed to grab frame from physical webcam. Falling back to test frame.")
                    frame = self._generate_test_frame()
            else:
                frame = self._generate_test_frame()

            self.last_frame = frame.copy()

            # Run Object Detection
            detections = self.detector.detect(frame)
            
            # Run Tracking
            tracked_objects = self.tracker.update(detections)
            self.last_objects = tracked_objects

            # Evaluate Counting Events
            new_events = self.counter.evaluate_events(self.tracker, frame.shape[0])

            # Dispatch events to callbacks
            for event in new_events:
                event["session_id"] = self.current_session_id
                # Optionally save snapshot for the counting event
                snapshot_filename = f"event_{int(time.time()*1000)}_{event['class_name']}.jpg"
                snapshot_path = os.path.join(settings.SNAPSHOT_DIR, snapshot_filename)
                try:
                    cv2.imwrite(snapshot_path, frame)
                    event["snapshot_path"] = snapshot_path
                except Exception as e:
                    logger.error(f"Failed to save snapshot: {e}")
                    event["snapshot_path"] = None

                for cb in self.event_callbacks:
                    try:
                        cb(event)
                    except Exception as err:
                        logger.error(f"Error in event callback: {err}")

            # Annotate frame
            annotated = self._annotate_frame(frame, tracked_objects)
            self.last_annotated_frame = annotated

            # Encode JPEG for streaming
            ret, jpeg = cv2.imencode('.jpg', annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if ret:
                self.last_jpeg_bytes = jpeg.tobytes()

            # FPS calculation
            frame_counter += 1
            elapsed = time.time() - prev_time
            if elapsed >= 1.0:
                self.current_fps = round(frame_counter / elapsed, 1)
                frame_counter = 0
                prev_time = time.time()

            # Sleep to match max FPS limit
            loop_duration = time.time() - start_loop
            sleep_time = max(0.005, frame_interval - loop_duration)
            time.sleep(sleep_time)

    def _generate_test_frame(self) -> np.ndarray:
        """Generates a clean synthetic sorting table background."""
        w, h = 640, 480
        # Dark slate conveyor belt background
        frame = np.full((h, w, 3), (35, 42, 49), dtype=np.uint8)

        # Draw grid / conveyor texture
        now = time.time()
        offset = int((now * 60) % 40)
        for y in range(offset, h, 40):
            cv2.line(frame, (0, y), (w, y), (45, 55, 65), 1)

        # Header bar on test canvas
        cv2.rectangle(frame, (0, 0), (w, 36), (20, 26, 32), -1)
        cv2.putText(
            frame,
            "EcoSort AI - Waste Sorting Table (Webcam Simulation)",
            (15, 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (200, 225, 200),
            1,
            cv2.LINE_AA
        )
        return frame

    def get_macro_counts(self) -> Dict[str, int]:
        macros = {"Anorganik": 0, "Organik": 0, "Berbahaya": 0}
        for cname, cnt in self.counter.class_counts.items():
            m = MACRO_CATEGORIES.get(cname, "Anorganik")
            macros[m] = macros.get(m, 0) + cnt
        return macros

    def _annotate_frame(self, frame: np.ndarray, objects: List[Dict[str, Any]]) -> np.ndarray:
        """Annotates bounding boxes, tracks, macro categories, labels, and virtual counting line."""
        annotated = frame.copy()
        h, w = annotated.shape[:2]

        # 1. Draw Virtual Counting Line (Futuristic Purple-Blue Glow line)
        line_y = int(self.counter.line_ratio * h)
        cv2.line(annotated, (0, line_y), (w, line_y), (255, 120, 160), 2)  # Glowing neon violet
        cv2.putText(
            annotated,
            f"VIRTUAL SORTING LINE (y={line_y})",
            (15, max(20, line_y - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 120, 160),
            1,
            cv2.LINE_AA
        )

        # 2. Draw Detections
        for obj in objects:
            cname = obj.get("class_name", "unknown")
            conf = obj.get("confidence", 0.0)
            track_id = obj.get("track_id", None)
            bbox = obj.get("bbox", [0, 0, 0, 0])
            x1, y1, x2, y2 = bbox

            macro_cat = MACRO_CATEGORIES.get(cname, "Anorganik")
            obj["macro_category"] = macro_cat

            hex_col = CLASS_COLOR_PALETTE.get(cname, "#3B82F6")
            color = hex_to_bgr(hex_col)

            # Box with subtle corner marks for futuristic HUD look
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            corner_len = min(15, (x2 - x1) // 4, (y2 - y1) // 4)
            # Top-left corner
            cv2.line(annotated, (x1, y1), (x1 + corner_len, y1), (255, 255, 255), 2)
            cv2.line(annotated, (x1, y1), (x1, y1 + corner_len), (255, 255, 255), 2)
            # Bottom-right corner
            cv2.line(annotated, (x2, y2), (x2 - corner_len, y2), (255, 255, 255), 2)
            cv2.line(annotated, (x2, y2), (x2, y2 - corner_len), (255, 255, 255), 2)

            # Label text: e.g. plastic_bottle [Anorganik] 94% #12
            track_str = f" #{track_id}" if track_id is not None else ""
            label = f"{cname} [{macro_cat}]{track_str} {int(conf * 100)}%"

            # Label badge
            (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
            badge_y1 = max(0, y1 - th - baseline - 4)
            badge_y2 = y1
            cv2.rectangle(annotated, (x1, badge_y1), (x1 + tw + 8, badge_y2), color, -1)
            cv2.putText(
                annotated,
                label,
                (x1 + 4, badge_y2 - baseline - 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.42,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )

        # 3. HUD Overlay (Status & FPS)
        hud_bg = (30, 20, 45)
        cv2.rectangle(annotated, (w - 150, 10), (w - 10, 42), hud_bg, -1)
        cv2.rectangle(annotated, (w - 150, 10), (w - 10, 42), (180, 100, 255), 1)
        cv2.putText(
            annotated,
            f"FPS: {self.current_fps}",
            (w - 138, 32),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 200, 100),
            1,
            cv2.LINE_AA
        )

        return annotated

camera_manager = CameraManager()

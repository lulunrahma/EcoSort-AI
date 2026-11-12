import os
import random
import time
from typing import List, Dict, Any, Tuple
import cv2
import numpy as np

from backend.app.core.config import settings, OFFICIAL_CLASSES
from backend.app.core.logging import logger

RAW_TO_OFFICIAL_MAP = {
    "plastic bottle": "plastic_bottle",
    "plastic_bottle": "plastic_bottle",
    "plastic bag": "plastic_bag",
    "plastic_bag": "plastic_bag",
    "zip plastic bag": "plastic_bag",
    "paper": "paper",
    "paper bag": "paper",
    "paper cups": "paper",
    "cardboard": "cardboard",
    "aluminum can": "metal_can",
    "metal_can": "metal_can",
    "tin": "metal_can",
    "glass bottle": "glass_bottle",
    "glass_bottle": "glass_bottle",
}

class WasteDetector:
    def __init__(self, model_path: str = None, conf_threshold: float = None):
        self.model_path = model_path or settings.MODEL_PATH
        self.conf_threshold = conf_threshold or settings.CONFIDENCE_THRESHOLD
        self.model = None
        self.status = "uninitialized"  # "ready", "training_in_progress", "error", "demo"
        self.status_message = ""
        self.is_demo_mode = False
        
        self.load_model()

    def load_model(self):
        """Attempts to load the YOLO model from model_path.
        If file does not exist, provides an informative status without crashing."""
        if not os.path.exists(self.model_path):
            self.status = "training_in_progress"
            self.status_message = (
                f"Model weights not found at '{self.model_path}'. "
                "Dataset training currently in progress. Simulated demo detection can be enabled in Settings."
            )
            logger.warning(self.status_message)
            self.model = None
            return

        try:
            from ultralytics import YOLO
            logger.info(f"Loading YOLO model from '{self.model_path}'...")
            self.model = YOLO(self.model_path)
            
            # Validate classes if model provides them
            model_names = self.model.names
            logger.info(f"Loaded model classes: {model_names}")
            
            self.status = "ready"
            self.status_message = f"Model loaded successfully ({len(model_names)} classes)."
        except Exception as e:
            self.status = "error"
            self.status_message = f"Failed to load model: {str(e)}"
            logger.error(self.status_message)
            self.model = None

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Run object detection on an OpenCV BGR frame.
        Returns a list of dicts:
        [{'class_id': int, 'class_name': str, 'confidence': float, 'bbox': [x1, y1, x2, y2]}]
        """
        if self.is_demo_mode or self.status != "ready" or self.model is None:
            if self.is_demo_mode:
                return self._generate_demo_detections(frame)
            return []

        h, w = frame.shape[:2]
        results = self.model.predict(
            source=frame,
            conf=self.conf_threshold,
            imgsz=settings.IMAGE_SIZE,
            verbose=False
        )

        detections = []
        if not results:
            return detections

        first_res = results[0]
        boxes = first_res.boxes
        if boxes is None:
            return detections

        for box in boxes:
            cls_idx = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            
            raw_name = first_res.names.get(cls_idx, "")
            raw_norm = str(raw_name).lower().strip()

            # Resolve to one of the 6 official classes
            if raw_norm in RAW_TO_OFFICIAL_MAP:
                class_name = RAW_TO_OFFICIAL_MAP[raw_norm]
                cls_idx = OFFICIAL_CLASSES.index(class_name)
            elif len(first_res.names) == len(OFFICIAL_CLASSES) and cls_idx < len(OFFICIAL_CLASSES):
                class_name = OFFICIAL_CLASSES[cls_idx]
            else:
                # If model detected a non-target class from a broader 42-class model, skip
                continue

            xyxy = box.xyxy[0].tolist()
            x1, y1, x2, y2 = [int(v) for v in xyxy]

            # Clamp coordinates
            x1 = max(0, min(w - 1, x1))
            y1 = max(0, min(h - 1, y1))
            x2 = max(0, min(w - 1, x2))
            y2 = max(0, min(h - 1, y2))

            detections.append({
                "class_id": cls_idx,
                "class_name": class_name,
                "confidence": round(conf, 3),
                "bbox": [x1, y1, x2, y2]
            })

        return detections

    def _generate_demo_detections(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Simulate realistic waste detection movement across the sorting table."""
        h, w = frame.shape[:2]
        now = time.time()
        
        # Animate 1 or 2 moving simulated items moving downwards (conveyor/sorting table simulation)
        t = now * 0.4
        progress = (t % 5.0) / 5.0  # 0 to 1 over 5 seconds
        
        y_pos = int(progress * (h - 100))
        x_pos = int((w / 2) + 80 * np.sin(t))
        
        # Pick class based on cycle
        cycle = int(t / 5.0) % len(OFFICIAL_CLASSES)
        class_name = OFFICIAL_CLASSES[cycle]
        
        box_w, box_h = 100, 140
        x1 = max(10, min(w - box_w - 10, x_pos - box_w // 2))
        y1 = max(10, min(h - box_h - 10, y_pos))
        x2 = x1 + box_w
        y2 = y1 + box_h
        
        return [{
            "class_id": cycle,
            "class_name": class_name,
            "confidence": round(0.85 + 0.1 * np.sin(now), 2),
            "bbox": [x1, y1, x2, y2]
        }]

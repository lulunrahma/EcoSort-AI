import math
from typing import List, Dict, Any, Optional

def calculate_iou(boxA: List[int], boxB: List[int]) -> float:
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)
    if interArea == 0:
        return 0.0

    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou

class TrackedObject:
    def __init__(self, track_id: int, detection: Dict[str, Any]):
        self.track_id = track_id
        self.class_id = detection["class_id"]
        self.class_name = detection["class_name"]
        self.confidence = detection["confidence"]
        self.bbox = detection["bbox"]
        
        # Centroid (cx, cy)
        self.centroid = (
            (self.bbox[0] + self.bbox[2]) // 2,
            (self.bbox[1] + self.bbox[3]) // 2
        )
        self.history = [self.centroid]
        self.lost_count = 0
        self.counted = False  # Flag for line-crossing / event deduplication

    def update(self, detection: Dict[str, Any]):
        self.bbox = detection["bbox"]
        self.confidence = detection["confidence"]
        self.class_id = detection["class_id"]
        self.class_name = detection["class_name"]
        self.centroid = (
            (self.bbox[0] + self.bbox[2]) // 2,
            (self.bbox[1] + self.bbox[3]) // 2
        )
        self.history.append(self.centroid)
        if len(self.history) > 30:
            self.history.pop(0)
        self.lost_count = 0

class WasteTracker:
    def __init__(self, max_lost: int = 15, iou_threshold: float = 0.3, max_dist: float = 200.0):
        self.max_lost = max_lost
        self.iou_threshold = iou_threshold
        self.max_dist = max_dist
        self.next_track_id = 1
        self.tracks: Dict[int, TrackedObject] = {}

    def update(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Associates detections with existing tracks using IoU matching and Centroid distance fallback.
        Returns the detections updated with track_id and track metadata.
        """
        # If no active tracks, register all as new
        if not self.tracks:
            for det in detections:
                t = TrackedObject(self.next_track_id, det)
                self.tracks[self.next_track_id] = t
                det["track_id"] = self.next_track_id
                self.next_track_id += 1
            return detections

        track_ids = list(self.tracks.keys())
        matched_tracks = set()
        matched_detections = set()

        # Step 1: IoU matching
        for det_idx, det in enumerate(detections):
            best_iou = 0.0
            best_track_id = None

            for tid in track_ids:
                if tid in matched_tracks:
                    continue
                iou = calculate_iou(self.tracks[tid].bbox, det["bbox"])
                if iou > best_iou:
                    best_iou = iou
                    best_track_id = tid

            if best_iou >= self.iou_threshold and best_track_id is not None:
                self.tracks[best_track_id].update(det)
                det["track_id"] = best_track_id
                matched_tracks.add(best_track_id)
                matched_detections.add(det_idx)

        # Step 2: Centroid distance matching fallback for remaining unmatched detections
        for det_idx, det in enumerate(detections):
            if det_idx in matched_detections:
                continue

            cx = (det["bbox"][0] + det["bbox"][2]) // 2
            cy = (det["bbox"][1] + det["bbox"][3]) // 2

            min_dist = float("inf")
            best_track_id = None

            for tid in track_ids:
                if tid in matched_tracks:
                    continue
                # Same class preferred
                if self.tracks[tid].class_name != det["class_name"]:
                    continue

                tcx, tcy = self.tracks[tid].centroid
                dist = math.hypot(cx - tcx, cy - tcy)
                if dist < min_dist and dist <= self.max_dist:
                    min_dist = dist
                    best_track_id = tid

            if best_track_id is not None:
                self.tracks[best_track_id].update(det)
                det["track_id"] = best_track_id
                matched_tracks.add(best_track_id)
                matched_detections.add(det_idx)

        # Step 3: Unmatched detections become new tracks
        for det_idx, det in enumerate(detections):
            if det_idx not in matched_detections:
                t = TrackedObject(self.next_track_id, det)
                self.tracks[self.next_track_id] = t
                det["track_id"] = self.next_track_id
                self.next_track_id += 1

        # Increment lost count for unmatched tracks and prune old ones
        for tid in track_ids:
            if tid not in matched_tracks:
                self.tracks[tid].lost_count += 1
                if self.tracks[tid].lost_count > self.max_lost:
                    del self.tracks[tid]

        return detections

    def reset(self):
        self.tracks.clear()
        self.next_track_id = 1


from typing import List, Dict, Any, Optional, Tuple
from backend.app.core.config import settings, OFFICIAL_CLASSES
from backend.app.cv.tracker import WasteTracker, TrackedObject
from backend.app.core.logging import logger

class EventCounter:
    def __init__(self, line_ratio: float = None, mode: str = None):
        self.line_ratio = line_ratio if line_ratio is not None else settings.VIRTUAL_LINE_Y
        self.mode = mode or settings.COUNTING_MODE
        self.class_counts: Dict[str, int] = {c: 0 for c in OFFICIAL_CLASSES}
        self.total_count: int = 0
        self.already_counted_tracks = set()

    def set_line_ratio(self, ratio: float):
        """Set vertical ratio of virtual counting line (0.1 to 0.9)."""
        self.line_ratio = max(0.1, min(0.9, ratio))

    def evaluate_events(self, tracker: WasteTracker, frame_height: int) -> List[Dict[str, Any]]:
        """Evaluates active tracks against the virtual counting line.
        Returns a list of newly generated counting event dictionaries.
        """
        line_y = int(self.line_ratio * frame_height)
        new_events = []

        for tid, track in tracker.tracks.items():
            if tid in self.already_counted_tracks:
                continue

            # Need at least two points in history to determine direction
            if len(track.history) < 2:
                continue

            prev_y = track.history[-2][1]
            curr_y = track.history[-1][1]

            is_crossed = False
            direction = "none"

            # Check top-to-bottom crossing (standard for conveyor/sorting table)
            if prev_y < line_y <= curr_y:
                is_crossed = True
                direction = "top_to_bottom"
            # Or bottom-to-top crossing
            elif prev_y > line_y >= curr_y:
                is_crossed = True
                direction = "bottom_to_top"

            # In track completion mode, if track is stable and has lived at least 5 frames
            if self.mode == "track_completed" and not is_crossed:
                if len(track.history) >= 8 and not track.counted:
                    is_crossed = True
                    direction = "track_verified"

            if is_crossed:
                track.counted = True
                self.already_counted_tracks.add(tid)
                
                # Update counters
                cname = track.class_name
                if cname in self.class_counts:
                    self.class_counts[cname] += 1
                else:
                    self.class_counts[cname] = 1
                self.total_count += 1

                event_data = {
                    "class_id": track.class_id,
                    "class_name": track.class_name,
                    "confidence": track.confidence,
                    "track_id": tid,
                    "bbox": track.bbox,
                    "event_type": f"line_crossing_{direction}",
                    "direction": direction
                }
                new_events.append(event_data)
                logger.info(f"Counting Event Triggered: {cname} (Track #{tid}) crossing line at y={line_y}")

        return new_events

    def reset(self):
        self.class_counts = {c: 0 for c in OFFICIAL_CLASSES}
        self.total_count = 0
        self.already_counted_tracks.clear()


from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, Index
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class CameraSession(Base):
    __tablename__ = "camera_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    started_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="active", nullable=False)  # active, stopped, error
    camera_name = Column(String(100), default="Webcam 0", nullable=False)
    notes = Column(Text, nullable=True)

    events = relationship("DetectionEvent", back_populates="session", cascade="all, delete-orphan")

class DetectionEvent(Base):
    __tablename__ = "detection_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_session_id = Column(Integer, ForeignKey("camera_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    detected_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    class_id = Column(Integer, nullable=False)
    class_name = Column(String(50), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    track_id = Column(Integer, nullable=True, index=True)
    bbox_json = Column(Text, nullable=True)  # JSON formatted [x1, y1, x2, y2]
    snapshot_path = Column(String(255), nullable=True)
    event_type = Column(String(50), default="line_crossing", nullable=False)  # line_crossing, track_completed

    session = relationship("CameraSession", back_populates="events")

    __table_args__ = (
        Index("idx_class_date", "class_name", "detected_at"),
        Index("idx_session_date", "camera_session_id", "detected_at"),
    )

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    type = Column(String(50), nullable=False)  # threshold_exceeded, camera_error, model_error, system
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    related_detection_id = Column(Integer, nullable=True)
    rule_key = Column(String(100), nullable=True)

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    file_path = Column(String(255), nullable=False)
    status = Column(String(50), default="completed", nullable=False)  # completed, generating, failed
    parameters_json = Column(Text, nullable=True)


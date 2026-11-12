from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# Class Mapping Schema
class ClassCount(BaseModel):
    class_id: int
    class_name: str
    count: int
    color: str
    macro_category: str = "Anorganik"

# Macro Category Count Schema
class MacroCount(BaseModel):
    category: str
    count: int
    color: str
    icon: str
    description: str

# Detection Object in Live Frame
class DetectedObject(BaseModel):
    class_id: int
    class_name: str
    macro_category: str = "Anorganik"
    confidence: float
    track_id: Optional[int] = None
    bbox: List[int] = Field(description="[x1, y1, x2, y2] in pixel coordinates")

# Live Update Payload (WebSocket Contract)
class LiveDetectionPayload(BaseModel):
    type: str = "detection_update"
    timestamp: str
    camera_status: str
    model_status: str
    fps: float
    objects: List[DetectedObject]
    session_counts: Dict[str, int]
    session_macro_counts: Dict[str, int] = {}
    recent_event: Optional[Dict[str, Any]] = None

# Camera Session Schemas
class CameraSessionResponse(BaseModel):
    id: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    status: str
    camera_name: str
    notes: Optional[str] = None
    total_events: int = 0

    model_config = ConfigDict(from_attributes=True)

# Detection Event Schemas
class DetectionEventResponse(BaseModel):
    id: int
    camera_session_id: int
    detected_at: datetime
    class_id: int
    class_name: str
    macro_category: str = "Anorganik"
    confidence: float
    track_id: Optional[int] = None
    bbox_json: Optional[str] = None
    snapshot_path: Optional[str] = None
    event_type: str

    model_config = ConfigDict(from_attributes=True)

class DetectionListResponse(BaseModel):
    total: int
    items: List[DetectionEventResponse]
    page: int
    limit: int

# Dashboard Summary Schema
class DashboardSummaryResponse(BaseModel):
    total_detections: int
    active_session_id: Optional[int] = None
    camera_status: str
    model_status: str
    class_counts: List[ClassCount]
    macro_counts: Dict[str, int] = {"Anorganik": 0, "Organik": 0, "Berbahaya": 0}
    recent_notifications_count: int

# Dashboard Charts Schema
class ChartPoint(BaseModel):
    label: str
    value: int

class DashboardChartsResponse(BaseModel):
    timeline: List[ChartPoint]
    distribution: List[ClassCount]
    macro_distribution: List[MacroCount] = []

# Notification Schemas
class NotificationResponse(BaseModel):
    id: int
    created_at: datetime
    type: str
    title: str
    message: str
    is_read: bool
    related_detection_id: Optional[int] = None
    rule_key: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# Report Schemas
class ReportGenerateRequest(BaseModel):
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    title: Optional[str] = "Laporan Monitoring Pemilahan Sampah - EcoSort AI"

class ReportResponse(BaseModel):
    id: int
    created_at: datetime
    period_start: datetime
    period_end: datetime
    file_path: str
    status: str
    filename: str

    model_config = ConfigDict(from_attributes=True)

# Settings Schemas
class AppSettingsSchema(BaseModel):
    camera_index: int
    model_path: str
    confidence_threshold: float
    max_fps: int
    virtual_line_y: float
    demo_mode: bool = False
    model_status: str
    camera_status: str

# Chatbot Schemas
class ChatMessage(BaseModel):
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None

class ChatResponse(BaseModel):
    reply: str
    suggested_actions: Optional[List[str]] = None
    stats_context: Optional[Dict[str, Any]] = None

# Root Cause Analysis (RCA) Schemas
class RCADiagnostic(BaseModel):
    id: str
    title: str
    severity: str  # "high" | "medium" | "low"
    timestamp: str
    category: str  # "Berbahaya" | "Anorganik" | "Organik" | "System"
    problem_statement: str
    five_whys: List[str]
    ishikawa: Dict[str, List[str]]  # {"Man": [...], "Machine": [...], "Method": [...], "Material": [...], "Environment": [...]}
    corrective_actions: List[str]
    preventive_actions: List[str]
    status: str  # "active" | "investigating" | "resolved"

class RCAListResponse(BaseModel):
    diagnostics: List[RCADiagnostic]
    summary: Dict[str, int]

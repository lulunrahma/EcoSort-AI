import os
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.config import OFFICIAL_CLASSES, MACRO_CATEGORIES, settings
from backend.app.core.database import Base, get_db
from backend.app.main import app
from backend.app.cv.tracker import WasteTracker
from backend.app.cv.counter import EventCounter
from backend.app.services.detection_service import DetectionService
from backend.app.services.notification_service import NotificationService
from backend.app.services.report_service import ReportService
from backend.app.services.rca_service import RCAService

# In-memory SQLite for test isolation with StaticPool
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_class_mapping_order():
    """Validates that the 6 official classes match the exact required specification."""
    expected = [
        "plastic_bottle",
        "plastic_bag",
        "paper",
        "cardboard",
        "metal_can",
        "glass_bottle"
    ]
    assert OFFICIAL_CLASSES == expected
    assert len(OFFICIAL_CLASSES) == 6

def test_macro_categories_mapping():
    """Validates macro waste sorting rules:
    - plastic_bottle, plastic_bag, glass_bottle -> Anorganik
    - paper, cardboard -> Organik
    - metal_can -> Berbahaya
    """
    assert MACRO_CATEGORIES["plastic_bottle"] == "Anorganik"
    assert MACRO_CATEGORIES["plastic_bag"] == "Anorganik"
    assert MACRO_CATEGORIES["glass_bottle"] == "Anorganik"
    assert MACRO_CATEGORIES["paper"] == "Organik"
    assert MACRO_CATEGORIES["cardboard"] == "Organik"
    assert MACRO_CATEGORIES["metal_can"] == "Berbahaya"

def test_health_check_endpoint():
    """Validates the /api/health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "EcoSort AI"

def test_requirements_docs_endpoint():
    """Validates that the API loads requirements from folder requirements/."""
    response = client.get("/api/requirements")
    assert response.status_code == 200
    files = response.json()
    assert len(files) >= 4
    filenames = [f["filename"] for f in files]
    assert "01_PRD_EcoSort_AI.md" in filenames
    assert "03_MASTER_PROMPT_ANTIGRAVITY_EcoSort_AI.md" in filenames

def test_tracking_and_event_counting_deduplication():
    """Validates that a tracked object crossing the virtual line is counted only ONCE."""
    tracker = WasteTracker()
    counter = EventCounter(line_ratio=0.5)

    # Frame 1: Object above line (y=100)
    det1 = [{"class_id": 0, "class_name": "plastic_bottle", "confidence": 0.95, "bbox": [100, 80, 160, 120]}]
    updated1 = tracker.update(det1)
    events1 = counter.evaluate_events(tracker, frame_height=400)
    assert len(events1) == 0  # Not crossed yet

    # Frame 2: Object crosses line (y=250 > line_y=200)
    det2 = [{"class_id": 0, "class_name": "plastic_bottle", "confidence": 0.94, "bbox": [100, 230, 160, 270]}]
    updated2 = tracker.update(det2)
    events2 = counter.evaluate_events(tracker, frame_height=400)
    assert len(events2) == 1  # Crosses line!
    assert events2[0]["class_name"] == "plastic_bottle"
    assert counter.total_count == 1

    # Frame 3: Object continues downwards (y=300 > line_y=200)
    det3 = [{"class_id": 0, "class_name": "plastic_bottle", "confidence": 0.93, "bbox": [100, 280, 160, 320]}]
    updated3 = tracker.update(det3)
    events3 = counter.evaluate_events(tracker, frame_height=400)
    # Deduplication test: MUST NOT count again!
    assert len(events3) == 0
    assert counter.total_count == 1

def test_database_detection_service_with_macro_categories():
    """Validates storing detection event and querying summary with macro categories."""
    db = TestingSessionLocal()
    # Add plastic_bottle (Anorganik)
    DetectionService.record_event(db, {
        "class_id": 0,
        "class_name": "plastic_bottle",
        "confidence": 0.92,
        "track_id": 1,
        "bbox": [100, 200, 150, 300],
        "event_type": "line_crossing_top_to_bottom"
    })
    # Add paper (Organik)
    DetectionService.record_event(db, {
        "class_id": 2,
        "class_name": "paper",
        "confidence": 0.89,
        "track_id": 2,
        "bbox": [200, 200, 260, 300],
        "event_type": "line_crossing_top_to_bottom"
    })
    # Add metal_can (Berbahaya)
    DetectionService.record_event(db, {
        "class_id": 4,
        "class_name": "metal_can",
        "confidence": 0.94,
        "track_id": 3,
        "bbox": [300, 200, 350, 300],
        "event_type": "line_crossing_top_to_bottom"
    })

    summary = DetectionService.get_summary(db)
    assert summary["total_detections"] == 3
    assert summary["macro_counts"]["Anorganik"] == 1
    assert summary["macro_counts"]["Organik"] == 1
    assert summary["macro_counts"]["Berbahaya"] == 1

    # Filter detections by macro_category
    total_anorg, items_anorg = DetectionService.get_events(db, macro_category="Anorganik")
    assert total_anorg == 1
    assert items_anorg[0]["class_name"] == "plastic_bottle"

    total_b3, items_b3 = DetectionService.get_events(db, macro_category="Berbahaya")
    assert total_b3 == 1
    assert items_b3[0]["class_name"] == "metal_can"
    db.close()

def test_rca_diagnostics_endpoint():
    """Validates Root Cause Analysis endpoint and status update."""
    res = client.get("/api/rca")
    assert res.status_code == 200
    data = res.json()
    assert "diagnostics" in data
    assert len(data["diagnostics"]) >= 4

    # Check RCA-001 (Metal Can Hazardous Anomaly)
    rca1 = next(d for d in data["diagnostics"] if d["id"] == "RCA-001")
    assert rca1["category"] == "Berbahaya"
    assert len(rca1["five_whys"]) == 5
    assert "Man (Manusia)" in rca1["ishikawa"]
    assert len(rca1["corrective_actions"]) >= 1

    # Update status test
    update_res = client.patch("/api/rca/RCA-001/status", json={"status": "resolved"})
    assert update_res.status_code == 200
    assert update_res.json()["success"] is True

def test_chatbot_endpoint():
    """Validates the AI Chatbot query and contextual response."""
    # Test query about waste sorting
    res1 = client.post("/api/chat", json={"message": "Bagaimana pilahan sampah botol plastik dan kaleng?"})
    assert res1.status_code == 200
    data1 = res1.json()
    assert "Anorganik" in data1["reply"]
    assert "Berbahaya" in data1["reply"]

    # Test query about RCA
    res2 = client.post("/api/chat", json={"message": "Jelaskan analisis RCA untuk kaleng logam"})
    assert res2.status_code == 200
    data2 = res2.json()
    assert "Root Cause Analysis" in data2["reply"] or "RCA" in data2["reply"]

def test_notification_service_and_cooldown():
    """Validates notification threshold triggering and cooldown mechanism."""
    db = TestingSessionLocal()
    for _ in range(settings.ALERT_THRESHOLD_COUNT):
        event = DetectionService.record_event(db, {
            "class_id": 1,
            "class_name": "plastic_bag",
            "confidence": 0.88,
            "track_id": 2,
            "bbox": [50, 100, 120, 200]
        })
        NotificationService.evaluate_detection(db, event)

    notifs = NotificationService.get_notifications(db)
    assert len(notifs) >= 1
    assert "plastic_bag" in notifs[0].title
    db.close()

def test_report_generation():
    """Validates ReportLab PDF creation with macro category breakdown."""
    db = TestingSessionLocal()
    DetectionService.record_event(db, {
        "class_id": 4,
        "class_name": "metal_can",
        "confidence": 0.91,
        "track_id": 5,
        "bbox": [200, 200, 250, 300]
    })

    report = ReportService.generate_pdf(db)
    assert report.id is not None
    assert os.path.exists(report.file_path)
    assert report.status == "completed"

    try:
        os.remove(report.file_path)
    except Exception:
        pass
    db.close()

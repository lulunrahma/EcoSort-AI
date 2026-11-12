import os
from typing import List, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict

# The 6 Official Mandatory Classes — Strictly preserved
OFFICIAL_CLASSES: List[str] = [
    "plastic_bottle",
    "plastic_bag",
    "paper",
    "cardboard",
    "metal_can",
    "glass_bottle"
]

# Waste Sorting Macro Category mapping
# Sesuai instruksi:
# - plastic_bottle, plastic_bag, glass_bottle -> Anorganik
# - paper, cardboard -> Organik
# - metal_can -> Berbahaya
MACRO_CATEGORIES: Dict[str, str] = {
    "plastic_bottle": "Anorganik",
    "plastic_bag": "Anorganik",
    "paper": "Organik",
    "cardboard": "Organik",
    "metal_can": "Berbahaya",
    "glass_bottle": "Anorganik"
}

MACRO_CATEGORY_META: Dict[str, Dict[str, Any]] = {
    "Organik": {
        "color": "#10B981",
        "bg": "rgba(16, 185, 129, 0.12)",
        "border": "#34d399",
        "icon": "🍃",
        "description": "Limbah serat selulosa ramah lingkungan (Kertas, Kardus)",
        "disposal": "Keringkan dan daur ulang sebagai pulp daur ulang atau kompos terkontrol."
    },
    "Anorganik": {
        "color": "#2563EB",
        "bg": "rgba(37, 99, 235, 0.12)",
        "border": "#60a5fa",
        "icon": "🧴",
        "description": "Limbah sintetis plastik & kaca tidak mudah terurai",
        "disposal": "Bilas residu, kompresi, dan teruskan ke pabrik daur ulang polimer/silika."
    },
    "Berbahaya": {
        "color": "#7C3AED",
        "bg": "rgba(124, 58, 237, 0.12)",
        "border": "#a78bfa",
        "icon": "⚠️",
        "description": "Limbah logam / kaleng berpotensi korosif, tajam, dan residu kimia (B3)",
        "disposal": "Isolasi di wadah khusus tahan tusuk berlabel ungu/merah B3, tangani dengan APD."
    }
}

# Elegant Futuristic Palette (White, Electric Blue, Violet/Purple)
CLASS_COLOR_PALETTE: Dict[str, str] = {
    "plastic_bottle": "#3B82F6",  # Electric Blue
    "plastic_bag": "#06B6D4",     # Neon Cyan
    "paper": "#10B981",           # Emerald Green (Organik)
    "cardboard": "#059669",       # Deep Mint (Organik)
    "metal_can": "#8B5CF6",       # Futuristic Violet (Berbahaya)
    "glass_bottle": "#6366F1"     # Indigo Blue
}

class Settings(BaseSettings):
    APP_NAME: str = "EcoSort AI"
    APP_VERSION: str = "1.1.0"
    APP_ENV: str = "development"
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite:///./ecosort.db"

    # Computer Vision & Camera
    CAMERA_INDEX: int = 0
    MODEL_PATH: str = "./models/best.pt"
    CONFIDENCE_THRESHOLD: float = 0.40
    IMAGE_SIZE: int = 640
    MAX_INFERENCE_FPS: int = 15

    # Tracking & Counting
    TRACKER_TYPE: str = "bytetrack"
    COUNTING_MODE: str = "line_crossing"  # 'line_crossing' or 'track_completed'
    VIRTUAL_LINE_Y: float = 0.50          # 0.0 to 1.0 (relative vertical position)

    # Storage paths
    SNAPSHOT_DIR: str = "./storage/snapshots"
    REPORT_DIR: str = "./storage/reports"

    # Notifications
    ALERT_WINDOW_SECONDS: int = 60
    ALERT_THRESHOLD_COUNT: int = 5
    ALERT_COOLDOWN_SECONDS: int = 120

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# Ensure directories exist
os.makedirs(settings.SNAPSHOT_DIR, exist_ok=True)
os.makedirs(settings.REPORT_DIR, exist_ok=True)

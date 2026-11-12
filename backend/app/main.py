import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.core.database import init_db
from backend.app.core.logging import logger
from backend.app.cv.camera import camera_manager

from backend.app.api.routes.camera import router as camera_router
from backend.app.api.routes.dashboard import router as dashboard_router
from backend.app.api.routes.detections import router as detections_router
from backend.app.api.routes.notifications import router as notifications_router
from backend.app.api.routes.reports import router as reports_router
from backend.app.api.routes.settings import router as settings_router
from backend.app.api.routes.requirements_docs import router as requirements_router
from backend.app.api.routes.chat import router as chat_router
from backend.app.api.routes.rca import router as rca_router
from backend.app.api.websocket import router as ws_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting EcoSort AI Backend Application...")
    init_db()
    logger.info("Database initialized successfully.")
    yield
    # Shutdown
    logger.info("Shutting down EcoSort AI Backend...")
    camera_manager.stop()
    logger.info("Camera resources released. Clean shutdown complete.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Web Dashboard Computer Vision Pemantauan & Deteksi Sampah YOLO",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files & Storage mounts
static_dir = os.path.abspath("frontend/static")
storage_snapshots = os.path.abspath(settings.SNAPSHOT_DIR)

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

if os.path.exists(storage_snapshots):
    app.mount("/storage/snapshots", StaticFiles(directory=storage_snapshots), name="snapshots")

# Include Routers
app.include_router(camera_router)
app.include_router(dashboard_router)
app.include_router(detections_router)
app.include_router(notifications_router)
app.include_router(reports_router)
app.include_router(settings_router)
app.include_router(requirements_router)
app.include_router(chat_router)
app.include_router(rca_router)
app.include_router(ws_router)

@app.get("/api/health", tags=["Health"])
def health_check():
    """Health check endpoint for system monitoring."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "camera_status": camera_manager.status,
        "model_status": camera_manager.detector.status,
        "model_path": settings.MODEL_PATH
    }

@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
async def serve_index():
    """Serves the main EcoSort AI Web Dashboard."""
    template_path = os.path.abspath("frontend/templates/index.html")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>EcoSort AI Web Dashboard</h1><p>Template not found.</p>")


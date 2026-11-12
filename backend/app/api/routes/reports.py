import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.core.database import get_db
from backend.app.models.entities import Report
from backend.app.schemas.pydantic_models import ReportGenerateRequest, ReportResponse
from backend.app.services.report_service import ReportService
from backend.app.core.logging import logger

router = APIRouter(prefix="/api/reports", tags=["Reports"])

@router.post("/generate", response_model=ReportResponse)
def generate_report(req: ReportGenerateRequest, db: Session = Depends(get_db)):
    """Generates a PDF analytics report using ReportLab."""
    try:
        report = ReportService.generate_pdf(
            db=db,
            period_start=req.period_start,
            period_end=req.period_end,
            title=req.title or "Laporan Monitoring Pemilahan Sampah - EcoSort AI"
        )
        return ReportResponse(
            id=report.id,
            created_at=report.created_at,
            period_start=report.period_start,
            period_end=report.period_end,
            file_path=report.file_path,
            status=report.status,
            filename=os.path.basename(report.file_path)
        )
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

@router.get("", response_model=List[ReportResponse])
def get_reports(limit: int = Query(default=30, ge=1, le=100), db: Session = Depends(get_db)):
    """Retrieves list of generated reports."""
    reports = db.query(Report).order_by(Report.created_at.desc()).limit(limit).all()
    results = []
    for r in reports:
        results.append(ReportResponse(
            id=r.id,
            created_at=r.created_at,
            period_start=r.period_start,
            period_end=r.period_end,
            file_path=r.file_path,
            status=r.status,
            filename=os.path.basename(r.file_path)
        ))
    return results

@router.get("/{report_id}/download")
def download_report(report_id: int, db: Session = Depends(get_db)):
    """Downloads the generated PDF report safely."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report record not found.")

    if not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report file not found on disk.")

    filename = os.path.basename(report.file_path)
    return FileResponse(
        path=report.file_path,
        media_type="application/pdf",
        filename=filename
    )

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.pydantic_models import RCAListResponse, RCADiagnostic
from backend.app.services.rca_service import RCAService

router = APIRouter(prefix="/api/rca", tags=["Root Cause Analysis"])

@router.get("", response_model=RCAListResponse)
def get_rca_diagnostics(db: Session = Depends(get_db)):
    """Retrieves all Root Cause Analysis diagnostics and active anomaly status."""
    res = RCAService.get_all_diagnostics(db)
    return RCAListResponse(
        diagnostics=[RCADiagnostic(**d) for d in res["diagnostics"]],
        summary=res["summary"]
    )

@router.patch("/{diagnostic_id}/status")
def update_rca_status(diagnostic_id: str, payload: Dict[str, str] = Body(...)):
    """Updates the resolution status of an RCA diagnostic (active, investigating, resolved)."""
    new_status = payload.get("status")
    if new_status not in ["active", "investigating", "resolved"]:
        raise HTTPException(status_code=400, detail="Invalid status. Allowed: active, investigating, resolved.")
    
    RCAService.update_status(diagnostic_id, new_status)
    return {
        "success": True,
        "message": f"Status for {diagnostic_id} successfully updated to '{new_status}'."
    }

@router.post("", response_model=RCADiagnostic)
def create_custom_rca(payload: Dict[str, Any] = Body(...)):
    """Creates a new custom RCA investigation report."""
    new_diag = RCAService.create_custom_rca(payload)
    return RCADiagnostic(**new_diag)


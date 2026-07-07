from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.decision_intelligence import (
    DecisionGenerateRequest,
    DecisionOptimizeRequest,
    DecisionResponse,
    DecisionListResponse
)
from app.services.decision_intelligence.decision_manager import DecisionManager

router = APIRouter(prefix="/decisions-engine", tags=["decision-intelligence-engine"])

@router.post("/generate", response_model=DecisionResponse)
def generate_decision(request: DecisionGenerateRequest, db: Session = Depends(get_db)):
    manager = DecisionManager(db)
    try:
        dec = manager.generate_decision(request)
        return dec
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize", response_model=DecisionResponse)
def optimize_decision(request: DecisionOptimizeRequest, db: Session = Depends(get_db)):
    # Stub for dynamically recalculating scenarios based on new constraints
    manager = DecisionManager(db)
    dec = manager.get_decision(request.decision_id)
    if not dec:
        raise HTTPException(status_code=404, detail="Decision not found")
    return dec

@router.get("/workspace/{workspace_id}", response_model=DecisionListResponse)
def get_decisions_by_workspace(workspace_id: str, db: Session = Depends(get_db)):
    manager = DecisionManager(db)
    decs = manager.list_by_workspace(workspace_id)
    return DecisionListResponse(decisions=decs, total=len(decs))

@router.get("/{decision_id}", response_model=DecisionResponse)
def get_decision(decision_id: str, db: Session = Depends(get_db)):
    manager = DecisionManager(db)
    dec = manager.get_decision(decision_id)
    if not dec:
        raise HTTPException(status_code=404, detail="Decision not found")
    return dec

@router.post("/{decision_id}/approve")
def approve_decision(decision_id: str, db: Session = Depends(get_db)):
    manager = DecisionManager(db)
    dec = manager.get_decision(decision_id)
    if dec:
        dec.approval_status = "APPROVED"
        manager.repository.update_decision(dec)
    return {"status": "SUCCESS"}

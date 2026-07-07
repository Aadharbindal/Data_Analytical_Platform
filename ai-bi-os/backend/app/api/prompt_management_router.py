from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core.database import get_db
from app.schemas.prompt_management import (
    PromptTemplateCreate, PromptTemplateResponse,
    PromptVersionCreate, PromptVersionResponse,
    PromptReviewRequest, PromptApproveRequest,
    PromptPublishRequest, PromptRollbackRequest,
    PromptDiffResponse, PromptHistoryResponse
)
from app.services.prompt_management import PromptManagementService

router = APIRouter(prefix="/prompt-management", tags=["Prompt Management Engine"])

@router.post("/templates", response_model=PromptTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(request: PromptTemplateCreate, db: Session = Depends(get_db)):
    service = PromptManagementService(db)
    return service.create_template(request)

@router.get("/templates", response_model=List[PromptTemplateResponse])
def get_templates(workspace_id: str, db: Session = Depends(get_db)):
    service = PromptManagementService(db)
    return service.get_templates(workspace_id)

@router.post("/version", response_model=PromptVersionResponse, status_code=status.HTTP_201_CREATED)
def create_version(request: PromptVersionCreate, db: Session = Depends(get_db)):
    service = PromptManagementService(db)
    return service.create_version(request)

@router.post("/review")
def submit_review(request: PromptReviewRequest, db: Session = Depends(get_db)):
    service = PromptManagementService(db)
    try:
        service.review_version(request)
        return {"status": "Review submitted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/approve")
def approve_version(request: PromptApproveRequest, db: Session = Depends(get_db)):
    service = PromptManagementService(db)
    try:
        service.approve_version(request)
        return {"status": "Version approved successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/publish", response_model=PromptVersionResponse)
def publish_version(request: PromptPublishRequest, db: Session = Depends(get_db)):
    service = PromptManagementService(db)
    try:
        return service.publish_version(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/rollback", response_model=PromptVersionResponse)
def rollback_version(request: PromptRollbackRequest, db: Session = Depends(get_db)):
    service = PromptManagementService(db)
    try:
        return service.rollback_version(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/diff", response_model=PromptDiffResponse)
def get_diff(version_id: str, db: Session = Depends(get_db)):
    service = PromptManagementService(db)
    try:
        return service.get_diff(version_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/history", response_model=List[PromptHistoryResponse])
def get_history(db: Session = Depends(get_db)):
    service = PromptManagementService(db)
    return service.get_history()

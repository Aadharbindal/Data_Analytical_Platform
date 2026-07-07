from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core.database import get_db
from app.schemas.prompt import (
    PromptBuildRequest, PromptObjectResponse, 
    PromptValidationRequest, PromptOptimizationRequest
)
from app.services.prompt_builder import PromptService

router = APIRouter(prefix="/prompt", tags=["Prompt Builder"])

@router.post("/build", response_model=PromptObjectResponse, status_code=status.HTTP_201_CREATED)
def build_prompt(request: PromptBuildRequest, db: Session = Depends(get_db)):
    """
    Builds an optimized prompt payload from Context and Evidence objects.
    """
    service = PromptService(db)
    try:
        return service.build_prompt(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rebuild", response_model=PromptObjectResponse)
def rebuild_prompt(prompt_id: str, db: Session = Depends(get_db)):
    """
    Forces a rebuild of an existing prompt payload.
    """
    service = PromptService(db)
    obj = service.get_prompt(prompt_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return obj

@router.post("/validate")
def validate_prompt(request: PromptValidationRequest, db: Session = Depends(get_db)):
    service = PromptService(db)
    return service.validate_prompt(request)

@router.post("/optimize", response_model=PromptObjectResponse)
def optimize_prompt(request: PromptOptimizationRequest, db: Session = Depends(get_db)):
    service = PromptService(db)
    try:
        return service.optimize_prompt(request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/history", response_model=List[Dict[str, Any]])
def get_prompt_history(db: Session = Depends(get_db)):
    service = PromptService(db)
    return service.get_history()

@router.get("/{prompt_id}", response_model=PromptObjectResponse)
def get_prompt(prompt_id: str, db: Session = Depends(get_db)):
    service = PromptService(db)
    obj = service.get_prompt(prompt_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return obj

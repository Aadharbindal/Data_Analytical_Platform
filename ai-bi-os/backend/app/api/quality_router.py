from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.quality.quality_registry import QualityRegistryService
from app.schemas.quality import QualityAssessmentResponse, QualityReportResponse, QualityViolationResponse
from app.models.quality import QualityViolation

router = APIRouter(prefix="/api/v1/datasets/{dataset_id}/quality", tags=["quality"])

@router.get("", response_model=QualityAssessmentResponse)
def get_dataset_quality(dataset_id: str, db: Session = Depends(get_db)):
    registry = QualityRegistryService(db)
    assessment = registry.get_assessment(dataset_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Quality assessment not found or still processing")
    return assessment

@router.get("/report", response_model=QualityReportResponse)
def get_quality_report(dataset_id: str, db: Session = Depends(get_db)):
    registry = QualityRegistryService(db)
    assessment = registry.get_assessment(dataset_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Quality assessment not found")
        
    critical = [v for v in assessment.violations if v.severity == "Critical"]
    warnings = [v for v in assessment.violations if v.severity in ["High", "Medium", "Low"]]
    
    return {
        "assessment": assessment,
        "critical_issues": critical,
        "warnings": warnings
    }

@router.get("/issues", response_model=List[QualityViolationResponse])
def get_quality_issues(dataset_id: str, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    registry = QualityRegistryService(db)
    assessment = registry.get_assessment(dataset_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Quality assessment not found")
        
    issues = db.query(QualityViolation).filter(QualityViolation.assessment_id == assessment.id).limit(limit).offset(offset).all()
    return issues

@router.post("/evaluate")
def rebuild_dataset_quality(dataset_id: str, db: Session = Depends(get_db)):
    """Triggers a background rebuild of the quality assessment for the latest version."""
    from app.models.dataset import DatasetVersion
    from app.worker import process_quality_task
    
    latest_version = db.query(DatasetVersion).filter(
        DatasetVersion.dataset_id == dataset_id,
        DatasetVersion.is_active == True
    ).first()
    
    if not latest_version:
        raise HTTPException(status_code=404, detail="No active version found")
        
    storage = latest_version.storage_locations[0]
    
    process_quality_task.delay(latest_version.id, storage.storage_path, latest_version.file_type)
    return {"status": "success", "message": "Quality evaluation queued."}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.services.privacy.privacy_registry import PrivacyRegistryService
from app.schemas.privacy import (
    PrivacyAssessmentResponse, SensitiveColumnResponse, ComplianceAssessmentResponse,
    RiskAssessmentResponse, GovernancePolicyResponse
)
from app.models.privacy import PrivacyAssessment

# ─── Router 1: dataset-scoped (existing) ────────────────────────────────────
router = APIRouter(prefix="/api/v1/datasets/{dataset_id}/privacy", tags=["privacy"])

@router.get("", response_model=PrivacyAssessmentResponse)
def get_privacy_overview(dataset_id: str, db: Session = Depends(get_db)):
    registry = PrivacyRegistryService(db)
    assessment = registry.get_assessment(dataset_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Privacy assessment not found or still processing")
    return assessment

@router.get("/pii", response_model=List[SensitiveColumnResponse])
def get_pii_columns(dataset_id: str, db: Session = Depends(get_db)):
    registry = PrivacyRegistryService(db)
    assessment = registry.get_assessment(dataset_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Privacy assessment not found")
    return assessment.sensitive_columns

@router.get("/compliance", response_model=ComplianceAssessmentResponse)
def get_compliance_status(dataset_id: str, db: Session = Depends(get_db)):
    registry = PrivacyRegistryService(db)
    assessment = registry.get_assessment(dataset_id)
    if not assessment or not assessment.compliance:
        raise HTTPException(status_code=404, detail="Compliance data not found")
    return assessment.compliance

@router.get("/risk", response_model=RiskAssessmentResponse)
def get_risk_scores(dataset_id: str, db: Session = Depends(get_db)):
    registry = PrivacyRegistryService(db)
    assessment = registry.get_assessment(dataset_id)
    if not assessment or not assessment.risk:
        raise HTTPException(status_code=404, detail="Risk data not found")
    return assessment.risk

@router.get("/policies", response_model=GovernancePolicyResponse)
def get_governance_policies(dataset_id: str, db: Session = Depends(get_db)):
    registry = PrivacyRegistryService(db)
    assessment = registry.get_assessment(dataset_id)
    if not assessment or not assessment.policy:
        raise HTTPException(status_code=404, detail="Policy data not found")
    return assessment.policy

@router.post("/scan")
def trigger_privacy_scan(dataset_id: str, db: Session = Depends(get_db)):
    """Manually triggers a background rebuild of the privacy assessment."""
    from app.models.dataset import DatasetVersion
    from app.worker import process_privacy_task

    latest_version = db.query(DatasetVersion).filter(
        DatasetVersion.dataset_id == dataset_id,
        DatasetVersion.is_active == True
    ).first()

    if not latest_version:
        raise HTTPException(status_code=404, detail="No active version found")

    storage = latest_version.storage_locations[0]

    process_privacy_task.delay(latest_version.id, storage.storage_path, latest_version.file_type)
    return {"status": "success", "message": "Privacy scan queued."}


# ─── Router 2: version-scoped (frontend-compatible) ─────────────────────────
# Frontend calls: GET /api/v1/privacy/{dataset_version_id}/report
# This returns a flattened PrivacyReport matching the frontend PrivacyReport type.

class PIIColumnOut(BaseModel):
    column_name: str
    pii_types: List[str]
    confidence: float
    masking_strategy: str

class PrivacyReportOut(BaseModel):
    id: str
    dataset_version_id: str
    pii_columns: List[PIIColumnOut]
    risk_level: str  # "low" | "medium" | "high" | "critical"
    compliance_status: str
    created_at: str


version_router = APIRouter(prefix="/api/v1/privacy", tags=["privacy"])


def _risk_score_to_level(score: Optional[float]) -> str:
    if score is None:
        return "low"
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def _build_compliance_status(assessment: PrivacyAssessment) -> str:
    if not assessment.compliance:
        return "Not Assessed"
    c = assessment.compliance
    if c.gdpr_status == "Violations Found" or c.ccpa_status == "Violations Found":
        return "Violations Found"
    if c.gdpr_status == "Compliant" or c.ccpa_status == "Compliant":
        return "Compliant"
    return "Not Applicable"


@version_router.get("/{dataset_version_id}/report", response_model=PrivacyReportOut)
def get_privacy_report_by_version(dataset_version_id: str, db: Session = Depends(get_db)):
    """
    Returns a flattened privacy report for the given dataset version.
    This endpoint matches what the frontend privacyApi.report() calls.
    """
    assessment = db.query(PrivacyAssessment).filter(
        PrivacyAssessment.dataset_version_id == dataset_version_id
    ).first()

    if not assessment:
        raise HTTPException(
            status_code=404,
            detail=f"No privacy assessment found for version {dataset_version_id}. Run a privacy scan first."
        )

    # Build pii_columns list from sensitive_columns + detections
    pii_cols: List[PIIColumnOut] = []
    for sc in assessment.sensitive_columns:
        pii_types = [d.entity_type for d in sc.detections]
        avg_confidence = (
            sum(d.confidence_score for d in sc.detections) / len(sc.detections)
            if sc.detections else 0.0
        )
        pii_cols.append(PIIColumnOut(
            column_name=sc.column_name,
            pii_types=pii_types if pii_types else [sc.classification_level],
            confidence=round(avg_confidence, 4),
            masking_strategy=sc.masking_recommendation,
        ))

    # Risk level
    overall_score = assessment.risk.overall_governance_score if assessment.risk else None
    risk_level = _risk_score_to_level(overall_score)

    # Compliance summary
    compliance_status = _build_compliance_status(assessment)

    return PrivacyReportOut(
        id=assessment.id,
        dataset_version_id=assessment.dataset_version_id,
        pii_columns=pii_cols,
        risk_level=risk_level,
        compliance_status=compliance_status,
        created_at=assessment.created_at.isoformat(),
    )

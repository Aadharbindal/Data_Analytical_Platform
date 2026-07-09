from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class PIIDetectionResponse(BaseModel):
    id: str
    entity_type: str
    confidence_score: float
    detection_method: str
    false_positive_probability: float
    
    class Config:
        from_attributes = True

class SensitiveColumnResponse(BaseModel):
    id: str
    schema_column_id: str
    column_name: str
    classification_level: str
    masking_recommendation: str
    detections: List[PIIDetectionResponse] = []
    
    class Config:
        from_attributes = True

class DataClassificationResponse(BaseModel):
    overall_classification: str
    contains_pii: bool
    contains_financial: bool
    contains_healthcare: bool
    
    class Config:
        from_attributes = True

class ComplianceAssessmentResponse(BaseModel):
    gdpr_status: str
    ccpa_status: str
    hipaa_status: str
    pci_dss_status: str
    violations: List[str]
    recommendations: List[str]
    
    class Config:
        from_attributes = True

class RiskAssessmentResponse(BaseModel):
    privacy_risk_score: float
    compliance_risk_score: float
    business_risk_score: float
    exposure_risk_score: float
    overall_governance_score: float
    
    class Config:
        from_attributes = True

class GovernancePolicyResponse(BaseModel):
    data_owner: str
    steward: str
    retention_policy: str
    access_policy: List[str]
    sharing_policy: str
    
    class Config:
        from_attributes = True

class PrivacyAssessmentResponse(BaseModel):
    id: str
    dataset_version_id: str
    created_at: datetime
    
    classification: Optional[DataClassificationResponse] = None
    compliance: Optional[ComplianceAssessmentResponse] = None
    risk: Optional[RiskAssessmentResponse] = None
    policy: Optional[GovernancePolicyResponse] = None
    
    class Config:
        from_attributes = True

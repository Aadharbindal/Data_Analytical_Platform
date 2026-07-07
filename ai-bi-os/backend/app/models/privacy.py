from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, Float, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class PrivacyAssessment(Base):
    __tablename__ = "privacy_assessments"
    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_version_id = Column(String, ForeignKey("dataset_versions.id"), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    version = relationship("DatasetVersion")
    sensitive_columns = relationship("SensitiveColumn", back_populates="assessment", cascade="all, delete-orphan")
    classification = relationship("DataClassification", back_populates="assessment", uselist=False, cascade="all, delete-orphan")
    compliance = relationship("ComplianceAssessment", back_populates="assessment", uselist=False, cascade="all, delete-orphan")
    risk = relationship("RiskAssessment", back_populates="assessment", uselist=False, cascade="all, delete-orphan")
    policy = relationship("GovernancePolicy", back_populates="assessment", uselist=False, cascade="all, delete-orphan")

class SensitiveColumn(Base):
    __tablename__ = "sensitive_columns"
    id = Column(String, primary_key=True, default=generate_uuid)
    assessment_id = Column(String, ForeignKey("privacy_assessments.id"))
    schema_column_id = Column(String, ForeignKey("schema_columns.id"))
    
    column_name = Column(String, nullable=False)
    classification_level = Column(String, nullable=False) # e.g. "PII", "Regulated", "Confidential"
    masking_recommendation = Column(String, nullable=False) # e.g. "Hash", "Full Mask", "Partial Mask"
    
    assessment = relationship("PrivacyAssessment", back_populates="sensitive_columns")
    detections = relationship("PIIDetection", back_populates="column", cascade="all, delete-orphan")

class PIIDetection(Base):
    __tablename__ = "pii_detections"
    id = Column(String, primary_key=True, default=generate_uuid)
    sensitive_column_id = Column(String, ForeignKey("sensitive_columns.id"))
    
    entity_type = Column(String, nullable=False) # e.g., "Email Address", "Credit Card", "SSN"
    confidence_score = Column(Float, default=0.0)
    detection_method = Column(String, nullable=False) # e.g., "Regex Match", "Dictionary", "Context"
    false_positive_probability = Column(Float, default=0.0)
    
    column = relationship("SensitiveColumn", back_populates="detections")

class DataClassification(Base):
    __tablename__ = "data_classifications"
    id = Column(String, primary_key=True, default=generate_uuid)
    assessment_id = Column(String, ForeignKey("privacy_assessments.id"), unique=True)
    
    overall_classification = Column(String, nullable=False) # e.g., "Highly Confidential", "Public"
    contains_pii = Column(Boolean, default=False)
    contains_financial = Column(Boolean, default=False)
    contains_healthcare = Column(Boolean, default=False)
    
    assessment = relationship("PrivacyAssessment", back_populates="classification")

class ComplianceAssessment(Base):
    __tablename__ = "compliance_assessments"
    id = Column(String, primary_key=True, default=generate_uuid)
    assessment_id = Column(String, ForeignKey("privacy_assessments.id"), unique=True)
    
    gdpr_status = Column(String, default="Not Applicable") # "Compliant", "Violations Found", "Not Applicable"
    ccpa_status = Column(String, default="Not Applicable")
    hipaa_status = Column(String, default="Not Applicable")
    pci_dss_status = Column(String, default="Not Applicable")
    
    violations = Column(JSON, default=list) # List of identified compliance risks
    recommendations = Column(JSON, default=list)
    
    assessment = relationship("PrivacyAssessment", back_populates="compliance")

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    id = Column(String, primary_key=True, default=generate_uuid)
    assessment_id = Column(String, ForeignKey("privacy_assessments.id"), unique=True)
    
    privacy_risk_score = Column(Float, default=0.0)
    compliance_risk_score = Column(Float, default=0.0)
    business_risk_score = Column(Float, default=0.0)
    exposure_risk_score = Column(Float, default=0.0)
    overall_governance_score = Column(Float, default=0.0)
    
    assessment = relationship("PrivacyAssessment", back_populates="risk")

class GovernancePolicy(Base):
    __tablename__ = "governance_policies"
    id = Column(String, primary_key=True, default=generate_uuid)
    assessment_id = Column(String, ForeignKey("privacy_assessments.id"), unique=True)
    
    data_owner = Column(String, default="Unassigned")
    steward = Column(String, default="Unassigned")
    
    retention_policy = Column(String, default="Keep 30 Days") # e.g., "Delete", "Keep 90 Days", "Archive"
    access_policy = Column(JSON, default=list) # e.g. ["Admin", "Data Scientist"]
    sharing_policy = Column(String, default="Restricted")
    
    assessment = relationship("PrivacyAssessment", back_populates="policy")

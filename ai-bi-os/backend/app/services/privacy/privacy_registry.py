from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.models.privacy import (
    PrivacyAssessment, SensitiveColumn, PIIDetection, DataClassification,
    ComplianceAssessment, RiskAssessment, GovernancePolicy
)
from app.models.dataset import DatasetVersion

class PrivacyRegistryService:
    def __init__(self, db: Session):
        self.db = db

    def save_assessment(self, dataset_version_id: str, results: Dict[str, Any]) -> PrivacyAssessment:
        existing = self.db.query(PrivacyAssessment).filter(PrivacyAssessment.dataset_version_id == dataset_version_id).first()
        if existing:
            self.db.delete(existing)
            self.db.commit()
            
        assessment = PrivacyAssessment(dataset_version_id=dataset_version_id)
        self.db.add(assessment)
        self.db.flush()
        
        # 1. Classification
        cls_data = results.get("classification", {})
        cls = DataClassification(
            assessment_id=assessment.id,
            overall_classification=cls_data.get("overall_classification", "Public"),
            contains_pii=cls_data.get("contains_pii", False),
            contains_financial=cls_data.get("contains_financial", False),
            contains_healthcare=cls_data.get("contains_healthcare", False)
        )
        self.db.add(cls)
        
        # 2. Compliance
        comp_data = results.get("compliance", {})
        comp = ComplianceAssessment(
            assessment_id=assessment.id,
            gdpr_status=comp_data.get("gdpr_status", "Not Applicable"),
            ccpa_status=comp_data.get("ccpa_status", "Not Applicable"),
            hipaa_status=comp_data.get("hipaa_status", "Not Applicable"),
            pci_dss_status=comp_data.get("pci_dss_status", "Not Applicable"),
            violations=comp_data.get("violations", []),
            recommendations=comp_data.get("recommendations", [])
        )
        self.db.add(comp)
        
        # 3. Risk
        risk_data = results.get("risk", {})
        risk = RiskAssessment(
            assessment_id=assessment.id,
            **risk_data
        )
        self.db.add(risk)
        
        # 4. Governance Policy (Auto-generated based on classification)
        retention = "Keep 30 Days" if cls.overall_classification in ["Highly Confidential", "Confidential"] else "Keep 1 Year"
        access = ["Admin", "Data Owner"] if cls.overall_classification == "Highly Confidential" else ["Admin", "Analyst", "Data Scientist"]
        
        policy = GovernancePolicy(
            assessment_id=assessment.id,
            retention_policy=retention,
            access_policy=access,
            sharing_policy="Restricted" if cls.contains_pii else "Internal"
        )
        self.db.add(policy)
        self.db.flush()
        
        # 5. Sensitive Columns & Detections
        # Group detections by column
        col_groups = {}
        for det in results.get("detections", []):
            cid = det["schema_column_id"]
            if cid not in col_groups:
                col_groups[cid] = []
            col_groups[cid].append(det)
            
        for cid, dets in col_groups.items():
            # Determine masking strategy based on worst entity
            mask_strategy = "Hash"
            for d in dets:
                if d["entity_type"] in ["Credit Card", "SSN"]:
                    mask_strategy = "Full Mask"
                elif d["entity_type"] in ["Email Address", "Phone Number"]:
                    mask_strategy = "Partial Mask"
                    
            scol = SensitiveColumn(
                assessment_id=assessment.id,
                schema_column_id=cid,
                column_name=dets[0]["column_name"],
                classification_level="PII", # simplified
                masking_recommendation=mask_strategy
            )
            self.db.add(scol)
            self.db.flush()
            
            for d in dets:
                pdet = PIIDetection(
                    sensitive_column_id=scol.id,
                    entity_type=d["entity_type"],
                    confidence_score=d["confidence_score"],
                    detection_method=d["detection_method"],
                    false_positive_probability=d["false_positive_probability"]
                )
                self.db.add(pdet)
                
        self.db.commit()
        return assessment

    def get_assessment(self, dataset_id: str) -> PrivacyAssessment:
        latest_version = self.db.query(DatasetVersion).filter(
            DatasetVersion.dataset_id == dataset_id,
            DatasetVersion.is_active == True
        ).first()
        
        if not latest_version:
            return None
            
        return self.db.query(PrivacyAssessment).filter(PrivacyAssessment.dataset_version_id == latest_version.id).first()

from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.models.quality import QualityAssessment, QualityDimension, QualityViolation, QualityScore
from app.models.dataset import DatasetVersion

class QualityRegistryService:
    def __init__(self, db: Session):
        self.db = db

    def save_assessment(self, dataset_version_id: str, results: Dict[str, Any]) -> QualityAssessment:
        # Check and delete existing
        existing = self.db.query(QualityAssessment).filter(QualityAssessment.dataset_version_id == dataset_version_id).first()
        if existing:
            self.db.delete(existing)
            self.db.commit()
            
        # Create Assessment
        assessment = QualityAssessment(dataset_version_id=dataset_version_id)
        self.db.add(assessment)
        self.db.flush()
        
        scores = []
        
        # Save Dimensions and Violations
        for dim_name, dim_data in results.items():
            score_val = dim_data["score"]
            scores.append(score_val)
            
            dimension = QualityDimension(
                assessment_id=assessment.id,
                dimension_name=dim_name.capitalize(),
                score=score_val,
                confidence=0.9,
                explanation=dim_data.get("explanation", "")
            )
            self.db.add(dimension)
            
            for v in dim_data.get("violations", []):
                violation = QualityViolation(
                    assessment_id=assessment.id,
                    schema_column_id=v.get("schema_column_id"),
                    issue_category=v["issue_category"],
                    severity=v["severity"],
                    priority=v["priority"],
                    affected_rows_count=v["affected_rows_count"],
                    root_cause=v.get("root_cause"),
                    suggested_fix=v.get("suggested_fix")
                )
                self.db.add(violation)
                
        # Save Score
        overall = sum(scores) / len(scores) if scores else 0.0
        
        # Simple readiness logic
        business_ready = max(0.0, overall - 5.0)
        analytics_ready = max(0.0, overall - 10.0)
        ai_ready = max(0.0, overall - 20.0) # AI requires the highest quality data
        
        q_score = QualityScore(
            assessment_id=assessment.id,
            overall_score=round(overall, 2),
            business_readiness_score=round(business_ready, 2),
            analytics_readiness_score=round(analytics_ready, 2),
            ai_readiness_score=round(ai_ready, 2)
        )
        self.db.add(q_score)
        self.db.commit()
        
        return assessment

    def get_assessment(self, dataset_id: str) -> QualityAssessment:
        latest_version = self.db.query(DatasetVersion).filter(
            DatasetVersion.dataset_id == dataset_id,
            DatasetVersion.is_active == True
        ).first()
        
        if not latest_version:
            return None
            
        return self.db.query(QualityAssessment).filter(QualityAssessment.dataset_version_id == latest_version.id).first()

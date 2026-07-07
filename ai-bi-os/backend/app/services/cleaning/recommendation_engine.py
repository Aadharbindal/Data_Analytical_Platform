from sqlalchemy.orm import Session
from typing import List

from app.models.quality import QualityAssessment, QualityViolation
from app.models.cleaning import CleaningRecommendation
from app.models.schema import SchemaColumn

class RecommendationEngine:
    """Reads quality violations and generates actionable cleaning recommendations."""
    
    def __init__(self, db: Session):
        self.db = db

    def generate_recommendations(self, dataset_version_id: str) -> List[CleaningRecommendation]:
        assessment = self.db.query(QualityAssessment).filter(QualityAssessment.dataset_version_id == dataset_version_id).first()
        if not assessment:
            return []
            
        violations = self.db.query(QualityViolation).filter(QualityViolation.assessment_id == assessment.id).all()
        
        # Clear old recommendations for this version
        self.db.query(CleaningRecommendation).filter(CleaningRecommendation.dataset_version_id == dataset_version_id).delete()
        
        recommendations = []
        for v in violations:
            col = self.db.query(SchemaColumn).filter(SchemaColumn.id == v.schema_column_id).first() if v.schema_column_id else None
            col_name = col.original_header if col else None
            
            if v.issue_category == "Missing Values":
                # Recommend Fill strategy based on classification
                strategy = "median" if col and col.classification == "Measure" else "mode"
                rec = CleaningRecommendation(
                    dataset_version_id=dataset_version_id,
                    quality_violation_id=v.id,
                    recommended_operation="FILL_NULLS",
                    target_column=col_name,
                    recommended_parameters={"strategy": strategy},
                    confidence_score=0.85,
                    reasoning=f"Common practice to impute missing {col.classification if col else 'values'} with {strategy}."
                )
                recommendations.append(rec)
                
            elif v.issue_category == "Whitespace Inconsistency":
                rec = CleaningRecommendation(
                    dataset_version_id=dataset_version_id,
                    quality_violation_id=v.id,
                    recommended_operation="TRIM_WHITESPACE",
                    target_column=col_name,
                    recommended_parameters={},
                    confidence_score=0.99,
                    reasoning="Safe operation to standardize categorical fields."
                )
                recommendations.append(rec)
                
            elif v.issue_category == "Mixed Casing":
                rec = CleaningRecommendation(
                    dataset_version_id=dataset_version_id,
                    quality_violation_id=v.id,
                    recommended_operation="LOWERCASE",
                    target_column=col_name,
                    recommended_parameters={},
                    confidence_score=0.90,
                    reasoning="Normalizing case resolves categorical duplication."
                )
                recommendations.append(rec)
                
            elif v.issue_category == "Duplicate Rows":
                rec = CleaningRecommendation(
                    dataset_version_id=dataset_version_id,
                    quality_violation_id=v.id,
                    recommended_operation="DROP_DUPLICATES",
                    target_column=None,
                    recommended_parameters={},
                    confidence_score=0.95,
                    reasoning="Identical rows across all columns detected."
                )
                recommendations.append(rec)
                
            elif v.issue_category == "Business Rule Violation" and "MUST BE >= 0" in v.root_cause:
                rec = CleaningRecommendation(
                    dataset_version_id=dataset_version_id,
                    quality_violation_id=v.id,
                    recommended_operation="ABSOLUTE_VALUE",
                    target_column=col_name,
                    recommended_parameters={},
                    confidence_score=0.75,
                    reasoning="Converts negative values to positive in financial measures."
                )
                recommendations.append(rec)

        self.db.add_all(recommendations)
        self.db.commit()
        return recommendations

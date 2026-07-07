from sqlalchemy.orm import Session
from app.models.quality import QualityAssessment
from app.models.privacy import PrivacyAssessment, RiskAssessment
from app.models.semantic import SemanticDomain
from app.models.catalog import CatalogScore

class ScoringEngine:
    """Calculates meta-scores for a dataset."""
    
    @staticmethod
    def calculate_scores(db: Session, catalog_id: str, version_id: str):
        # Quality
        quality = db.query(QualityAssessment).filter(QualityAssessment.dataset_version_id == version_id).first()
        quality_score = quality.score.overall_score if quality and quality.score else 0.0
        
        # Privacy & Risk
        privacy = db.query(PrivacyAssessment).filter(PrivacyAssessment.dataset_version_id == version_id).first()
        risk = db.query(RiskAssessment).filter(RiskAssessment.assessment_id == privacy.id).first() if privacy else None
        gov_score = risk.overall_governance_score if risk else 0.0
        
        # Semantic mapping completeness (AI Readiness)
        domain = db.query(SemanticDomain).filter(SemanticDomain.dataset_version_id == version_id).first()
        ai_readiness = 100.0 if domain and domain.confidence_score > 0.8 else 50.0
        if not domain:
            ai_readiness = 0.0
            
        # Trust is average of quality and governance
        trust_score = (quality_score + gov_score) / 2
        
        score = CatalogScore(
            catalog_id=catalog_id,
            quality_score=quality_score,
            trust_score=trust_score,
            ai_readiness_score=ai_readiness,
            popularity_score=0.0, # Usage data comes later
            freshness_score=100.0 # Just ingested
        )
        db.add(score)
        db.commit()

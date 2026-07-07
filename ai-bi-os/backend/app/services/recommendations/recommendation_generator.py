from typing import List
from sqlalchemy.orm import Session
from app.models.rule import Decision
from app.models.recommendation import Recommendation, RecommendationEvidence, RecommendationScore

class RecommendationGenerator:
    """Maps Decisions to deterministic recommendation objects."""
    
    @staticmethod
    def generate(db: Session, decisions: List[Decision]) -> List[Recommendation]:
        recommendations = []
        for d in decisions:
            # Deterministic mapping based on Decision title/domain
            category = "OPERATIONAL_RECOMMENDATION"
            if "Revenue" in d.title or "Growth" in d.title:
                category = "REVENUE_GROWTH"
            elif "Cost" in d.title or "Margin" in d.title:
                category = "COST_OPTIMIZATION"
                
            rec = Recommendation(
                dataset_version_id=d.dataset_version_id,
                decision_id=d.id,
                title=f"Action Plan for: {d.title}",
                description=f"Automated recommendation triggered by decision: {d.title}",
                business_domain=d.business_domain,
                category=category,
                priority=d.priority,
                severity=d.severity,
                affected_kpis=d.affected_entities,
                confidence=d.confidence or 0.8
            )
            
            # Link evidence back to the decision
            evidence = RecommendationEvidence(
                evidence_type="DECISION",
                reference_id=d.id,
                description=d.description
            )
            rec.evidence.append(evidence)
            
            # Initial base score
            score = RecommendationScore(
                final_score=0,
                confidence_score=d.confidence or 0.8,
                urgency_score=0.9 if d.severity == "CRITICAL" else 0.5
            )
            rec.score = score
            
            recommendations.append(rec)
        return recommendations

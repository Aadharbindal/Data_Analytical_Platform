from sqlalchemy.orm import Session
import time
from app.services.recommendations.recommendation_planner import RecommendationPlanner
from app.services.recommendations.recommendation_generator import RecommendationGenerator
from app.services.recommendations.action_planning_engine import ActionPlanningEngine
from app.services.recommendations.impact_estimator import ImpactEstimator
from app.services.recommendations.recommendation_validator import RecommendationValidator
from app.services.recommendations.recommendation_prioritizer import RecommendationPrioritizer

class RecommendationOrchestrator:
    """Coordinates the deterministic generation of recommendations."""
    
    @staticmethod
    def process_recommendations(db: Session, dataset_version_id: str) -> int:
        try:
            # 1. Plan
            decisions = RecommendationPlanner.plan(db, dataset_version_id)
            if not decisions:
                return 0
                
            # 2. Generate
            recommendations = RecommendationGenerator.generate(db, decisions)
            
            # 3. Action Planning
            ActionPlanningEngine.plan_actions(recommendations)
            
            # 4. Impact Estimation
            ImpactEstimator.estimate(recommendations)
            
            # 5. Validate
            validated_recs = RecommendationValidator.validate(recommendations)
            
            # 6. Prioritize
            RecommendationPrioritizer.prioritize(validated_recs)
            
            # 7. Persist
            db.add_all(validated_recs)
            db.commit()
            
            valid_count = len([r for r in validated_recs if r.status != "REJECTED"])
            return valid_count
            
        except Exception as e:
            db.rollback()
            raise e

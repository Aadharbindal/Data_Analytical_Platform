from sqlalchemy.orm import Session
from app.services.insights.insight_planner import InsightPlanner
from app.services.insights.insight_generator import InsightGenerator
from app.services.insights.insight_validator import InsightValidator
from app.services.insights.insight_ranker import InsightRanker

class InsightOrchestrator:
    """Coordinates the deterministic generation of business insights from analytics."""
    
    @staticmethod
    def process_insights(db: Session, run_id: str) -> int:
        try:
            # 1. Plan
            plan = InsightPlanner.plan(db, run_id)
            
            # 2. Generate
            raw_insights = InsightGenerator.generate(plan)
            if not raw_insights:
                return 0
                
            # 3. Validate
            validated_insights = InsightValidator.validate(raw_insights)
            
            # 4. Rank
            ranked_insights = InsightRanker.rank(validated_insights)
            
            # 5. Persist
            db.add_all(ranked_insights)
            db.commit()
            
            # Return count of successfully validated insights
            valid_count = len([i for i in ranked_insights if i.status == "VALIDATED"])
            return valid_count
            
        except Exception as e:
            db.rollback()
            raise e

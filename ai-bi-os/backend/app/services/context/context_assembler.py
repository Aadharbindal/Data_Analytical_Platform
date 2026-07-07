from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.insight import Insight
from app.models.recommendation import Recommendation
from app.models.context import ContextItem
import json

class ContextAssembler:
    """Retrieves raw data (Insights, Recommendations) from the database."""
    
    @staticmethod
    def assemble(db: Session, dataset_version_id: str, plan: Dict[str, Any], package_id: str) -> List[ContextItem]:
        items = []
        
        # Pull Insights
        insights = db.query(Insight).filter(Insight.dataset_version_id == dataset_version_id).all()
        for i in insights:
            content = {
                "title": i.title,
                "description": i.description,
                "metric": i.metric_name,
                "value": i.metric_value,
                "confidence": i.score.confidence if i.score else 1.0
            }
            estimated_tokens = len(json.dumps(content)) // 4
            items.append(ContextItem(
                package_id=package_id,
                source_type="INSIGHT",
                source_id=i.id,
                content=content,
                estimated_tokens=estimated_tokens
            ))
            
        # Pull Recommendations
        recommendations = db.query(Recommendation).filter(Recommendation.dataset_version_id == dataset_version_id).all()
        for r in recommendations:
            content = {
                "title": r.title,
                "category": r.category,
                "roi_estimate": r.roi_estimate
            }
            estimated_tokens = len(json.dumps(content)) // 4
            items.append(ContextItem(
                package_id=package_id,
                source_type="RECOMMENDATION",
                source_id=r.id,
                content=content,
                estimated_tokens=estimated_tokens
            ))
            
        # Note: In a full system, we would also pull Rules, Metadata, Quality Reports here.
        return items

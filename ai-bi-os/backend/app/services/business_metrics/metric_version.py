import logging
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.business_metrics import MetricVersion, MetricFormula, MetricStatus, MetricHistory

logger = logging.getLogger("MetricVersionManager")

class MetricVersionManager:
    """
    Manages version increments, statuses, and audit history.
    """
    
    def create_new_version(self, db: Session, metric_id: str, formula_expression: str, 
                           author: str = "system") -> MetricVersion:
        
        # Find latest version number
        latest = db.query(MetricVersion).filter(MetricVersion.metric_id == metric_id).order_by(MetricVersion.version_number.desc()).first()
        next_ver = (latest.version_number + 1) if latest else 1
        
        new_version = MetricVersion(
            metric_id=metric_id,
            version_number=next_ver,
            status=MetricStatus.ACTIVE,
            activation_date=datetime.utcnow()
        )
        db.add(new_version)
        db.flush() # get ID
        
        # Add formula
        formula = MetricFormula(
            version_id=new_version.id,
            expression=formula_expression,
            is_valid=True
        )
        db.add(formula)
        
        # Log History
        history = MetricHistory(
            metric_id=metric_id,
            action="UPDATED_FORMULA" if latest else "CREATED",
            author=author,
            changes={"version": next_ver, "formula": formula_expression}
        )
        db.add(history)
        
        # Deprecate old active versions
        if latest:
            db.query(MetricVersion).filter(
                MetricVersion.metric_id == metric_id,
                MetricVersion.id != new_version.id,
                MetricVersion.status == MetricStatus.ACTIVE
            ).update({"status": MetricStatus.DEPRECATED})
            
        db.commit()
        db.refresh(new_version)
        return new_version

metric_version_manager = MetricVersionManager()

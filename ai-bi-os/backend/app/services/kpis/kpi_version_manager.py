from sqlalchemy.orm import Session
from app.models.kpi import KPIDefinition, KPIVersion, KPIHistory

class KPIVersionManager:
    """Handles versioning of KPI formulas."""
    
    @staticmethod
    def create_version(db: Session, definition_id: str, formula: str, author: str) -> KPIVersion:
        # Get latest version number
        latest_version = db.query(KPIVersion).filter(
            KPIVersion.definition_id == definition_id
        ).order_by(KPIVersion.version_number.desc()).first()
        
        new_version_num = (latest_version.version_number + 1) if latest_version else 1
        
        # Deprecate old versions
        db.query(KPIVersion).filter(
            KPIVersion.definition_id == definition_id,
            KPIVersion.status == "ACTIVE"
        ).update({"status": "DEPRECATED"})
        
        # Create new active version
        new_version = KPIVersion(
            definition_id=definition_id,
            version_number=new_version_num,
            formula_expression=formula,
            author=author,
            status="ACTIVE"
        )
        db.add(new_version)
        
        # Record history
        history = KPIHistory(
            definition_id=definition_id,
            action="UPDATED" if latest_version else "CREATED",
            author=author,
            changes={"formula": formula, "version": new_version_num}
        )
        db.add(history)
        
        return new_version

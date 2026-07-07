from sqlalchemy.orm import Session
from app.models.forecast_governance import ModelLifecycle, ModelGovernance
from fastapi import HTTPException

class LifecycleManager:
    VALID_STATES = ["Development", "Validation", "Approved", "Production", "Deprecated", "Retired"]

    def transition_state(self, db: Session, model_id: str, new_status: str, updated_by: str = None, notes: str = None) -> ModelLifecycle:
        if new_status not in self.VALID_STATES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {self.VALID_STATES}")
        
        gov = db.query(ModelGovernance).filter(ModelGovernance.model_id == model_id).first()
        if not gov:
            raise HTTPException(status_code=404, detail="Model governance object not found")
        
        # Determine approval and deployment status based on lifecycle
        if new_status == "Approved":
            gov.approval_status = "APPROVED"
        elif new_status == "Production":
            gov.deployment_status = "PRODUCTION"
        elif new_status in ["Deprecated", "Retired"]:
            gov.deployment_status = "INACTIVE"
            
        lifecycle_entry = ModelLifecycle(
            model_id=model_id,
            status=new_status,
            updated_by=updated_by,
            notes=notes
        )
        db.add(lifecycle_entry)
        db.commit()
        db.refresh(lifecycle_entry)
        return lifecycle_entry

lifecycle_manager = LifecycleManager()

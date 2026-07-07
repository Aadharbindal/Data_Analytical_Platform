import logging
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.models.regression import RegressionModel, ModelVersion
from app.services.regression.model_repository import model_repository

logger = logging.getLogger("ModelVersionManager")

class ModelVersionManager:
    """Handles incrementing versions and active model toggling."""
    
    def get_or_create_model(self, db: Session, dataset_id: str, name: str, algorithm: str, target: str) -> RegressionModel:
        model = db.query(RegressionModel).filter_by(dataset_id=dataset_id, name=name).first()
        if not model:
            model = model_repository.create_model(db, dataset_id, name, algorithm, target)
            model_repository.log_history(db, model.id, "CREATED")
        return model
        
    def create_new_version(self, db: Session, model_id: str) -> ModelVersion:
        latest = db.query(ModelVersion).filter_by(model_id=model_id).order_by(ModelVersion.version_number.desc()).first()
        next_ver = (latest.version_number + 1) if latest else 1
        
        # Deactivate old
        if latest:
            latest.is_active = False
            
        new_version = model_repository.create_version(db, model_id, next_ver)
        new_version.is_active = True
        return new_version

model_version_manager = ModelVersionManager()

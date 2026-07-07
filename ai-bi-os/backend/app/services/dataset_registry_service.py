from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.dataset import Dataset, DatasetHistory, workspace_dataset
from typing import List, Optional

class DatasetRegistryService:
    def __init__(self, db: Session):
        self.db = db

    def list_datasets(self, workspace_id: Optional[str] = None, project_id: Optional[str] = None, 
                      owner_id: Optional[str] = None, status: Optional[str] = "active",
                      limit: int = 50, offset: int = 0) -> List[Dataset]:
        query = self.db.query(Dataset)
        
        if workspace_id:
            query = query.join(workspace_dataset).filter(workspace_dataset.c.workspace_id == workspace_id)
        if project_id:
            query = query.filter(Dataset.project_id == project_id)
        if owner_id:
            query = query.filter(Dataset.owner_id == owner_id)
        if status:
            query = query.filter(Dataset.status == status)
            
        return query.order_by(desc(Dataset.created_at)).offset(offset).limit(limit).all()

    def get_dataset(self, dataset_id: str) -> Optional[Dataset]:
        return self.db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.status == "active").first()

    def soft_delete_dataset(self, dataset_id: str, user_id: str) -> bool:
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return False
            
        dataset.status = "deleted"
        
        # Log History
        history = DatasetHistory(
            dataset_id=dataset_id,
            user_id=user_id,
            action="delete",
            details={"reason": "soft delete"}
        )
        self.db.add(history)
        self.db.commit()
        return True

    def log_history(self, dataset_id: str, user_id: str, action: str, details: dict = None):
        history = DatasetHistory(
            dataset_id=dataset_id,
            user_id=user_id,
            action=action,
            details=details or {}
        )
        self.db.add(history)
        self.db.commit()

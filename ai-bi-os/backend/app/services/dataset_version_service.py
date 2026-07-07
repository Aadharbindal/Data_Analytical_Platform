from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.dataset import DatasetVersion, DatasetStorage
from typing import List, Optional

class DatasetVersionService:
    def __init__(self, db: Session):
        self.db = db

    def get_versions(self, dataset_id: str) -> List[DatasetVersion]:
        return self.db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_id).order_by(desc(DatasetVersion.version)).all()

    def get_latest_version(self, dataset_id: str) -> Optional[DatasetVersion]:
        return self.db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_id, DatasetVersion.is_active == True).first()

    def rollback_version(self, dataset_id: str, target_version: int) -> bool:
        """Sets the specified version as active, and deactivates all others."""
        versions = self.db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_id).all()
        target = None
        for v in versions:
            if v.version == target_version:
                target = v
                v.is_active = True
            else:
                v.is_active = False
                
        if target:
            self.db.commit()
            return True
        return False

    def register_version(self, dataset_id: str, original_filename: str, stored_filename: str,
                         file_hash: str, file_size: int, file_type: str, 
                         provider_id: str, storage_path: str) -> DatasetVersion:
        
        # Determine next version number
        existing_count = self.db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_id).count()
        next_version = existing_count + 1
        
        # Deactivate existing active versions
        self.db.query(DatasetVersion).filter(
            DatasetVersion.dataset_id == dataset_id, 
            DatasetVersion.is_active == True
        ).update({"is_active": False})
        
        # Create Version
        new_version = DatasetVersion(
            dataset_id=dataset_id,
            version=next_version,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_hash=file_hash,
            file_size_bytes=file_size,
            file_type=file_type,
            is_active=True
        )
        self.db.add(new_version)
        self.db.flush() # flush to get the new_version.id
        
        # Create Storage mapping
        storage_map = DatasetStorage(
            dataset_version_id=new_version.id,
            provider_id=provider_id,
            storage_path=storage_path
        )
        self.db.add(storage_map)
        self.db.commit()
        
        return new_version

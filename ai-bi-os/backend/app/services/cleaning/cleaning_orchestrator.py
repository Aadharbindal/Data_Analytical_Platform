from sqlalchemy.orm import Session
from typing import List, Dict, Any
import os
import time
import polars as pl

from app.models.dataset import Dataset, DatasetVersion, DatasetStorage
from app.models.cleaning import TransformationPipeline, TransformationStep, CleaningHistory
from app.services.storage.local_provider import LocalStorageProvider
from app.services.cleaning.transformation_engine import TransformationEngine

class CleaningOrchestrator:
    def __init__(self, db: Session):
        self.db = db
        self.storage = LocalStorageProvider()

    def apply_pipeline(self, dataset_id: str, steps: List[Dict[str, Any]], user_id: str = "system") -> str:
        """
        Executes the cleaning pipeline, creates a new dataset version (immutability),
        and tracks history.
        """
        start_time = time.time()
        
        # 1. Get current active version
        current_version = self.db.query(DatasetVersion).filter(
            DatasetVersion.dataset_id == dataset_id,
            DatasetVersion.is_active == True
        ).first()
        
        if not current_version:
            raise ValueError("No active dataset version found.")
            
        location = current_version.storage_locations[0]
        file_path = os.path.join(self.storage.base_dir, location.storage_path)
        
        # 2. Load with Polars
        if current_version.file_type == 'csv':
            df = pl.read_csv(file_path)
        elif current_version.file_type == 'parquet':
            df = pl.read_parquet(file_path)
        else:
            import pandas as pd
            if current_version.file_type == 'json':
                df = pl.from_pandas(pd.read_json(file_path, lines=True))
            else:
                df = pl.from_pandas(pd.read_excel(file_path))
                
        # 3. Apply Transformations
        clean_df = TransformationEngine.execute_pipeline(df, steps)
        
        # 4. Save to new Parquet file (Standardizing to Parquet after cleaning)
        new_version_number = current_version.version_number + 1
        new_file_name = f"{dataset_id}_v{new_version_number}.parquet"
        
        # In a real app we'd use the storage provider to upload the stream, 
        # but for local we just write to the path.
        workspace_dir = os.path.dirname(file_path)
        new_full_path = os.path.join(workspace_dir, new_file_name)
        
        clean_df.write_parquet(new_full_path)
        file_size = os.path.getsize(new_full_path)
        
        # 5. Database Updates
        # Deactivate old
        current_version.is_active = False
        
        # Create new version
        new_version = DatasetVersion(
            dataset_id=dataset_id,
            version_number=new_version_number,
            file_type="parquet",
            file_size_bytes=file_size,
            is_active=True,
            created_by=user_id
        )
        self.db.add(new_version)
        self.db.flush()
        
        # Create storage location
        new_loc = StorageLocation(
            dataset_version_id=new_version.id,
            provider="local",
            storage_path=os.path.join(os.path.basename(workspace_dir), new_file_name)
        )
        self.db.add(new_loc)
        
        # Save Pipeline mapping
        pipeline = TransformationPipeline(
            dataset_id=dataset_id,
            name=f"Cleaning applied at v{new_version_number}"
        )
        self.db.add(pipeline)
        self.db.flush()
        
        for idx, s in enumerate(steps):
            t_step = TransformationStep(
                pipeline_id=pipeline.id,
                step_order=idx,
                operation_type=s["operation_type"],
                target_column=s.get("target_column"),
                parameters=s.get("parameters", {})
            )
            self.db.add(t_step)
            
        # Log History
        exec_time_ms = int((time.time() - start_time) * 1000)
        history = CleaningHistory(
            dataset_id=dataset_id,
            original_version_id=current_version.id,
            new_version_id=new_version.id,
            pipeline_id=pipeline.id,
            execution_time_ms=exec_time_ms,
            affected_rows=len(clean_df),
            snapshot_steps=steps
        )
        self.db.add(history)
        
        self.db.commit()
        return new_version.id
        
    def rollback(self, dataset_id: str) -> str:
        """Rolls back the active pointer to the previous version."""
        versions = self.db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_id).order_by(DatasetVersion.version_number.desc()).all()
        if len(versions) < 2:
            raise ValueError("No previous version to rollback to.")
            
        current = versions[0]
        previous = versions[1]
        
        current.is_active = False
        previous.is_active = True
        self.db.commit()
        
        return previous.id

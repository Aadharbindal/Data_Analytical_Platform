from sqlalchemy.orm import Session
from app.models.dataset import Dataset, DatasetVersion, UploadJob, workspace_dataset
from app.schemas.dataset import DatasetCreateRequest

class DatasetRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_dataset_by_id(self, dataset_id: str):
        return self.db.query(Dataset).filter(Dataset.id == dataset_id).first()

    def get_datasets_for_workspace(self, workspace_id: str):
        return self.db.query(Dataset).join(workspace_dataset).filter(workspace_dataset.c.workspace_id == workspace_id).all()

    def create_upload_job(self, user_id: str, workspace_id: str, dataset_name: str = None, dataset_id: str = None):
        job = UploadJob(
            user_id=user_id,
            workspace_id=workspace_id,
            dataset_name=dataset_name,
            dataset_id=dataset_id,
            status="pending"
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def update_upload_job_status(self, job_id: str, status: str = None, error_message: str = None, file_hash: str = None, current_step: str = None, progress: float = None):
        job = self.db.query(UploadJob).filter(UploadJob.id == job_id).first()
        if job:
            if status is not None:
                job.status = status
            if error_message is not None:
                job.error_message = error_message
            if file_hash is not None:
                job.file_hash = file_hash
            if current_step is not None:
                job.current_step = current_step
            if progress is not None:
                job.progress = progress
            self.db.commit()
            self.db.refresh(job)
        return job

    def get_upload_job(self, job_id: str):
        return self.db.query(UploadJob).filter(UploadJob.id == job_id).first()

    def create_dataset(self, name: str, owner_id: str, workspace_id: str, description: str = None, project_id: str = None):
        dataset = Dataset(
            name=name,
            description=description,
            owner_id=owner_id,
            project_id=project_id
        )
        self.db.add(dataset)
        
        # Link to workspace
        stmt = workspace_dataset.insert().values(workspace_id=workspace_id, dataset_id=dataset.id)
        self.db.execute(stmt)
        
        self.db.commit()
        self.db.refresh(dataset)
        return dataset

    def create_dataset_version(self, dataset_id: str, file_path: str, file_hash: str, file_size: int, file_type: str):
        # Determine next version
        existing_versions = self.db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_id).count()
        next_version = existing_versions + 1
        
        # Deactivate old versions
        self.db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_id).update({"is_active": False})
        
        new_version = DatasetVersion(
            dataset_id=dataset_id,
            version=next_version,
            file_path=file_path,
            file_hash=file_hash,
            file_size_bytes=file_size,
            file_type=file_type,
            is_active=True
        )
        self.db.add(new_version)
        self.db.commit()
        self.db.refresh(new_version)
        return new_version

    def check_hash_exists(self, file_hash: str) -> bool:
        return self.db.query(DatasetVersion).filter(DatasetVersion.file_hash == file_hash).first() is not None

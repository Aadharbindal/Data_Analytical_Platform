from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Float, Table, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

# Join table for Workspace and Dataset
workspace_dataset = Table(
    'workspace_dataset',
    Base.metadata,
    Column('workspace_id', String, ForeignKey('workspaces.id'), primary_key=True),
    Column('dataset_id', String, ForeignKey('datasets.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Workspace(Base):
    __tablename__ = "workspaces"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, index=True)
    owner_id = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User")
    datasets = relationship("Dataset", secondary=workspace_dataset, back_populates="workspaces")

class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, index=True)
    workspace_id = Column(String, ForeignKey("workspaces.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

class StorageProvider(Base):
    __tablename__ = "storage_providers"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, index=True, unique=True) # e.g., 'local', 's3'
    config = Column(JSON, nullable=True) # Connection details, bucket names
    created_at = Column(DateTime, default=datetime.utcnow)

class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True)
    owner_id = Column(String, ForeignKey("users.id"))
    status = Column(String, default="active") # active, deleted
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User")
    workspaces = relationship("Workspace", secondary=workspace_dataset, back_populates="datasets")
    versions = relationship("DatasetVersion", back_populates="dataset", cascade="all, delete-orphan")
    history = relationship("DatasetHistory", back_populates="dataset", cascade="all, delete-orphan")

    @property
    def latest_version(self):
        """Returns the currently active version (is_active=True), or the most recent."""
        active = [v for v in self.versions if v.is_active]
        if active:
            return sorted(active, key=lambda v: v.version, reverse=True)[0]
        if self.versions:
            return sorted(self.versions, key=lambda v: v.version, reverse=True)[0]
        return None

class DatasetVersion(Base):
    __tablename__ = "dataset_versions"
    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_id = Column(String, ForeignKey("datasets.id"))
    version = Column(Integer, default=1)
    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False)
    file_hash = Column(String, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    file_type = Column(String, nullable=False)  # csv, json, parquet, xlsx
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    dataset = relationship("Dataset", back_populates="versions")
    storage_locations = relationship("DatasetStorage", back_populates="version", cascade="all, delete-orphan")

class DatasetStorage(Base):
    __tablename__ = "dataset_storage"
    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_version_id = Column(String, ForeignKey("dataset_versions.id"))
    provider_id = Column(String, ForeignKey("storage_providers.id"))
    storage_path = Column(String, nullable=False) # e.g. workspace-123/project-456/dataset-789/v1/raw.csv
    created_at = Column(DateTime, default=datetime.utcnow)

    version = relationship("DatasetVersion", back_populates="storage_locations")
    provider = relationship("StorageProvider")

class DatasetHistory(Base):
    __tablename__ = "dataset_history"
    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_id = Column(String, ForeignKey("datasets.id"))
    user_id = Column(String, ForeignKey("users.id"))
    action = Column(String, nullable=False) # upload, rename, delete, restore
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    dataset = relationship("Dataset", back_populates="history")
    user = relationship("User")

class UploadJob(Base):
    __tablename__ = "upload_jobs"
    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=True)
    dataset_name = Column(String, nullable=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True)
    user_id = Column(String, ForeignKey("users.id"))
    workspace_id = Column(String, ForeignKey("workspaces.id"))
    status = Column(String, default="pending") # pending, processing, completed, failed
    error_message = Column(String, nullable=True)
    file_hash = Column(String, nullable=True)
    current_step = Column(String, default="Initializing")
    progress = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

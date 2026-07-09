from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class DatasetVersionResponse(BaseModel):
    id: str
    version: int
    original_filename: str
    stored_filename: str
    file_size_bytes: int
    file_type: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class DatasetResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    project_id: Optional[str] = None
    owner_id: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    versions: List[DatasetVersionResponse] = []
    latest_version: Optional[DatasetVersionResponse] = None

    class Config:
        from_attributes = True

class DatasetListResponse(BaseModel):
    items: List[DatasetResponse]
    total: int
    limit: int
    offset: int

class UploadJobResponse(BaseModel):
    id: str
    dataset_id: Optional[str]
    dataset_name: Optional[str]
    status: str
    error_message: Optional[str]
    current_step: Optional[str] = "Initializing"
    progress: Optional[float] = 0.0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DatasetCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    workspace_id: str
    project_id: Optional[str] = None

class DatasetUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    project_id: Optional[str] = None

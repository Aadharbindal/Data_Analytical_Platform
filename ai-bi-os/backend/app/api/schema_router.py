from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.schema.schema_registry import SchemaRegistryService
from app.schemas.schema import DatasetSchemaResponse, SchemaColumnResponse, SchemaQualityResponse, SchemaRelationshipResponse

router = APIRouter(prefix="/api/v1/datasets/{dataset_id}/schema", tags=["schema"])

@router.get("", response_model=DatasetSchemaResponse)
def get_dataset_schema(dataset_id: str, db: Session = Depends(get_db)):
    registry = SchemaRegistryService(db)
    schema = registry.get_schema_for_dataset(dataset_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found or still processing")
    return schema

@router.get("/columns", response_model=List[SchemaColumnResponse])
def get_schema_columns(dataset_id: str, db: Session = Depends(get_db)):
    registry = SchemaRegistryService(db)
    schema = registry.get_schema_for_dataset(dataset_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    return schema.columns

@router.get("/quality", response_model=SchemaQualityResponse)
def get_schema_quality(dataset_id: str, db: Session = Depends(get_db)):
    registry = SchemaRegistryService(db)
    schema = registry.get_schema_for_dataset(dataset_id)
    if not schema or not schema.quality:
        raise HTTPException(status_code=404, detail="Schema Quality not found")
    return schema.quality

@router.get("/relationships", response_model=List[SchemaRelationshipResponse])
def get_schema_relationships(dataset_id: str, db: Session = Depends(get_db)):
    registry = SchemaRegistryService(db)
    schema = registry.get_schema_for_dataset(dataset_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    return schema.relationships

@router.post("/rebuild")
def rebuild_dataset_schema(dataset_id: str, db: Session = Depends(get_db)):
    """Triggers a background rebuild of the schema for the latest version."""
    from app.models.dataset import DatasetVersion
    from app.worker import process_schema_task
    
    latest_version = db.query(DatasetVersion).filter(
        DatasetVersion.dataset_id == dataset_id,
        DatasetVersion.is_active == True
    ).first()
    
    if not latest_version:
        raise HTTPException(status_code=404, detail="No active version found")
        
    # Queue rebuild task
    # Note: In a real system, we'd need to extract the physical file path based on provider.
    # For LocalStorage Provider, storage_locations holds the relative path.
    storage = latest_version.storage_locations[0]
    
    process_schema_task.delay(latest_version.id, storage.storage_path, latest_version.file_type)
    return {"status": "success", "message": "Schema rebuild queued."}

# Diffs can be complex, skipping for MVP endpoint unless specifically requested to compare two given version IDs.
# GET /datasets/{id}/schema/diff

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core.database import get_db
from app.schemas.analytics_registry import (
    AnalyticsObjectCreate, AnalyticsObjectResponse, 
    ObjectSearchRequest, LineageResponse, ObjectVersionResponse
)
from app.services.analytics_registry_service import AnalyticsRegistryService
from app.models.analytics_registry import AnalyticsObject, ObjectVersion

router = APIRouter(prefix="/analytics-registry", tags=["Analytics Registry"])

@router.post("/register", response_model=AnalyticsObjectResponse, status_code=status.HTTP_201_CREATED)
def register_object(obj_in: AnalyticsObjectCreate, db: Session = Depends(get_db)):
    service = AnalyticsRegistryService(db)
    return service.register_object(obj_in)

@router.post("/bulk-register", response_model=List[AnalyticsObjectResponse], status_code=status.HTTP_201_CREATED)
def bulk_register_objects(objects_in: List[AnalyticsObjectCreate], db: Session = Depends(get_db)):
    service = AnalyticsRegistryService(db)
    return service.bulk_register(objects_in)

@router.get("/{object_id}", response_model=AnalyticsObjectResponse)
def get_object(object_id: str, db: Session = Depends(get_db)):
    service = AnalyticsRegistryService(db)
    obj = service.get_object(object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Analytics object not found")
    return obj

@router.get("/dataset/{dataset_id}", response_model=List[AnalyticsObjectResponse])
def get_objects_by_dataset(dataset_id: str, db: Session = Depends(get_db)):
    service = AnalyticsRegistryService(db)
    search_req = ObjectSearchRequest(dataset_id=dataset_id, limit=100)
    objects, _ = service.search_objects(search_req)
    return objects

@router.get("/workspace/{workspace_id}", response_model=List[AnalyticsObjectResponse])
def get_objects_by_workspace(workspace_id: str, db: Session = Depends(get_db)):
    service = AnalyticsRegistryService(db)
    search_req = ObjectSearchRequest(workspace_id=workspace_id, limit=100)
    objects, _ = service.search_objects(search_req)
    return objects

@router.post("/search", response_model=Dict[str, Any])
def search_objects(search_req: ObjectSearchRequest, db: Session = Depends(get_db)):
    service = AnalyticsRegistryService(db)
    objects, total = service.search_objects(search_req)
    return {
        "items": objects,
        "total": total,
        "limit": search_req.limit,
        "offset": search_req.offset
    }

@router.get("/lineage/{object_id}", response_model=LineageResponse)
def get_object_lineage(object_id: str, db: Session = Depends(get_db)):
    service = AnalyticsRegistryService(db)
    lineage = service.get_lineage(object_id)
    if not lineage:
        raise HTTPException(status_code=404, detail="Analytics object not found")
    return lineage

@router.get("/version/{object_id}", response_model=List[ObjectVersionResponse])
def get_object_versions(object_id: str, db: Session = Depends(get_db)):
    obj = db.query(AnalyticsObject).filter(AnalyticsObject.id == object_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Analytics object not found")
    versions = db.query(ObjectVersion).filter(ObjectVersion.object_id == object_id).all()
    return versions

@router.post("/archive", response_model=Dict[str, str])
def archive_object(object_id: str, actor_id: str = "system", db: Session = Depends(get_db)):
    service = AnalyticsRegistryService(db)
    success = service.archive_object(object_id, actor_id=actor_id)
    if not success:
        raise HTTPException(status_code=404, detail="Analytics object not found")
    return {"status": "success", "message": "Object archived"}

@router.post("/restore", response_model=Dict[str, str])
def restore_object(object_id: str, actor_id: str = "system", db: Session = Depends(get_db)):
    service = AnalyticsRegistryService(db)
    success = service.restore_object(object_id, actor_id=actor_id)
    if not success:
        raise HTTPException(status_code=404, detail="Analytics object not found")
    return {"status": "success", "message": "Object restored"}

@router.delete("/{object_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_object(object_id: str, db: Session = Depends(get_db)):
    obj = db.query(AnalyticsObject).filter(AnalyticsObject.id == object_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Analytics object not found")
    db.delete(obj)
    db.commit()
    # Cache invalidation
    from app.services.analytics_registry_cache import analytics_cache
    analytics_cache.invalidate_object(object_id)
    return None

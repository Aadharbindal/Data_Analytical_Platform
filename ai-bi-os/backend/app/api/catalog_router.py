from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.catalog import MetadataCatalog, CatalogRecommendation
from app.services.catalog.search_engine import SearchEngine
from app.schemas.catalog import (
    SearchResultResponse, CatalogOverviewResponse, 
    DatasetDocumentationResponse, CatalogRecommendationResponse, CatalogListResponse
)

router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])

@router.get("", response_model=List[CatalogListResponse])
def get_catalog_list(workspace_id: str = "workspace-123", db: Session = Depends(get_db)):
    """Get all catalog entries for a workspace."""
    from app.models.dataset import Dataset
    
    from app.models.dataset import Workspace
    catalogs = db.query(MetadataCatalog).join(Dataset).join(Dataset.workspaces).filter(Workspace.id == workspace_id).all()
    
    results = []
    for cat in catalogs:
        # Extract column count from entries if available
        col_count = 0
        for entry in cat.entries:
            if entry.key == "column_count":
                col_count = int(entry.value)
                break
                
        # Extract business domain from entries or dataset
        business_domain = None
        description = cat.documentation.business_summary if cat.documentation else None
        
        results.append({
            "id": cat.dataset_id,
            "name": cat.dataset.name,
            "business_domain": business_domain,
            "description": description,
            "column_count": col_count,
            "last_updated": cat.last_indexed_at,
            "owner": cat.dataset.owner_id,
            "tags": [t.tag_name for t in cat.tags]
        })
        
    return results


@router.get("/search", response_model=List[SearchResultResponse])
def search_catalog(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """Full-text ranked search across the metadata catalog."""
    results = SearchEngine.search(db, query_string=q)
    return results

@router.get("/{dataset_id}", response_model=CatalogOverviewResponse)
def get_catalog_entry(dataset_id: str, db: Session = Depends(get_db)):
    """Get the full catalog overview for a specific dataset."""
    catalog = db.query(MetadataCatalog).filter(MetadataCatalog.dataset_id == dataset_id).first()
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog entry not found. Still indexing?")
    return catalog

@router.get("/{dataset_id}/documentation", response_model=DatasetDocumentationResponse)
def get_dataset_documentation(dataset_id: str, db: Session = Depends(get_db)):
    catalog = db.query(MetadataCatalog).filter(MetadataCatalog.dataset_id == dataset_id).first()
    if not catalog or not catalog.documentation:
        raise HTTPException(status_code=404, detail="Documentation not found")
    return catalog.documentation

@router.get("/{dataset_id}/recommendations", response_model=List[CatalogRecommendationResponse])
def get_dataset_recommendations(dataset_id: str, db: Session = Depends(get_db)):
    catalog = db.query(MetadataCatalog).filter(MetadataCatalog.dataset_id == dataset_id).first()
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog entry not found")
    
    recs = db.query(CatalogRecommendation).filter(CatalogRecommendation.catalog_id == catalog.id).all()
    return recs

@router.post("/rebuild/{dataset_id}")
def rebuild_catalog_for_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Manually force a re-index of a specific dataset."""
    from app.models.dataset import DatasetVersion
    from app.worker import process_catalog_task
    
    version = db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_id, DatasetVersion.is_active == True).first()
    if not version:
        raise HTTPException(status_code=404, detail="Active dataset version not found.")
        
    process_catalog_task.delay(dataset_id)
    return {"status": "success", "message": "Catalog indexing queued."}

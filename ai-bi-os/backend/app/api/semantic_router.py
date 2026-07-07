from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.semantic.semantic_registry import SemanticRegistryService
from app.schemas.semantic import (
    SemanticDomainResponse, BusinessEntityResponse, BusinessMetricResponse,
    SemanticColumnResponse, BusinessGlossaryResponse, OntologyNodeResponse,
    OntologyEdgeResponse, SemanticRecommendationResponse
)

router = APIRouter(prefix="/api/v1/datasets/{dataset_id}/semantic", tags=["semantic"])

@router.get("", summary="Get Semantic Overview")
def get_semantic_overview(dataset_id: str, db: Session = Depends(get_db)):
    registry = SemanticRegistryService(db)
    data = registry.get_semantic_data(dataset_id)
    if not data:
        raise HTTPException(status_code=404, detail="Semantic data not found or processing")
    
    return {
        "domain": data.get("domain"),
        "entities_count": len(data.get("entities", [])),
        "metrics_count": len(data.get("metrics", []))
    }

@router.get("/domain", response_model=SemanticDomainResponse)
def get_semantic_domain(dataset_id: str, db: Session = Depends(get_db)):
    registry = SemanticRegistryService(db)
    data = registry.get_semantic_data(dataset_id)
    if not data or not data.get("domain"):
        raise HTTPException(status_code=404, detail="Domain data not found")
    return data["domain"]

@router.get("/entities", response_model=List[BusinessEntityResponse])
def get_business_entities(dataset_id: str, db: Session = Depends(get_db)):
    registry = SemanticRegistryService(db)
    data = registry.get_semantic_data(dataset_id)
    return data.get("entities", [])

@router.get("/metrics", response_model=List[BusinessMetricResponse])
def get_business_metrics(dataset_id: str, db: Session = Depends(get_db)):
    registry = SemanticRegistryService(db)
    data = registry.get_semantic_data(dataset_id)
    return data.get("metrics", [])

@router.get("/glossary", response_model=List[BusinessGlossaryResponse])
def get_business_glossary(dataset_id: str, db: Session = Depends(get_db)):
    registry = SemanticRegistryService(db)
    data = registry.get_semantic_data(dataset_id)
    return data.get("glossary", [])

@router.get("/ontology")
def get_ontology(dataset_id: str, db: Session = Depends(get_db)):
    registry = SemanticRegistryService(db)
    data = registry.get_semantic_data(dataset_id)
    nodes = [{"id": n.id, "label": n.node_label, "type": n.node_type} for n in data.get("nodes", [])]
    edges = [{"source": e.source_node_id, "target": e.target_node_id, "relation": e.relation_name} for e in data.get("edges", [])]
    return {"nodes": nodes, "edges": edges}

@router.get("/recommendations", response_model=List[SemanticRecommendationResponse])
def get_semantic_recommendations(dataset_id: str, db: Session = Depends(get_db)):
    registry = SemanticRegistryService(db)
    data = registry.get_semantic_data(dataset_id)
    return data.get("recommendations", [])

@router.post("/rebuild")
def rebuild_semantic_layer(dataset_id: str, db: Session = Depends(get_db)):
    from app.models.dataset import DatasetVersion
    from app.worker import process_semantic_task
    
    version = db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_id, DatasetVersion.is_active == True).first()
    if not version:
        raise HTTPException(status_code=404, detail="Active dataset version not found.")
        
    process_semantic_task.delay(version.id)
    return {"status": "success", "message": "Semantic inference queued."}

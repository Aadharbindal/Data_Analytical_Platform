from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.kpi import KPIDefinition, KPIHistory
from app.schemas.kpi import KPIDefinitionSchema, KPICreateRequest, KPICalculateRequest
from app.services.kpis.kpi_validator import KPIValidator
from app.services.kpis.kpi_version_manager import KPIVersionManager

router = APIRouter(prefix="/api/v1/kpis", tags=["kpis"])

@router.post("/", response_model=KPIDefinitionSchema)
def create_kpi(request: KPICreateRequest, db: Session = Depends(get_db)):
    """Creates a new KPI definition and initial version."""
    
    # 1. Validate formula
    try:
        KPIValidator.validate_formula(request.formula)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    # 2. Create definition
    definition = KPIDefinition(
        workspace_id=request.workspace_id,
        name=request.name,
        category=request.category,
        description=request.description,
        is_custom=True
    )
    db.add(definition)
    db.flush()
    
    # 3. Create initial version
    KPIVersionManager.create_version(db, definition.id, request.formula, request.author)
    
    db.commit()
    db.refresh(definition)
    return definition

@router.get("/", response_model=List[KPIDefinitionSchema])
def list_kpis(workspace_id: str, db: Session = Depends(get_db)):
    """Retrieves available KPIs."""
    return db.query(KPIDefinition).filter(KPIDefinition.workspace_id == workspace_id).all()

@router.post("/calculate")
def trigger_kpi_calculation(request: KPICalculateRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Triggers calculation for a single KPI."""
    from app.worker import process_kpi_calculation_task
    
    task = process_kpi_calculation_task.delay(
        workspace_id=request.workspace_id,
        dataset_version_id=request.dataset_version_id,
        definition_id=request.definition_id,
        dimension=request.dimension
    )
    return {"status": "accepted", "message": "KPI calculation queued", "task_id": task.id}

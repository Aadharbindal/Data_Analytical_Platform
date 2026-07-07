from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.business_metrics import (
    CalculateMetricRequest, CalculateMetricResponse, 
    CreateMetricRequest, MetricResponse, MetricHistoryResponse
)
from app.services.business_metrics.metrics_service import business_metrics_service
from app.services.business_metrics.metric_registry import metric_registry
from app.models.business_metrics import BusinessMetric, MetricDefinition, MetricHistory

router = APIRouter(prefix="/api/v1/metrics", tags=["business_metrics"])

@router.post("/calculate", response_model=CalculateMetricResponse)
async def calculate_metric(req: CalculateMetricRequest, db: Session = Depends(get_db)):
    """Calculate a metric with intelligent caching."""
    try:
        result = business_metrics_service.calculate_metric(
            db=db,
            metric_id=req.metric_id,
            dataset_version_id=req.dataset_version_id,
            dimension=req.dimension,
            dimension_value=req.dimension_value,
            time_window=req.time_window,
            force_refresh=req.force_refresh
        )
        return CalculateMetricResponse(
            metric_id=req.metric_id,
            value=result["value"],
            cached=result["cached"]
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[MetricResponse])
async def get_metrics(domain: str = None):
    """List all registered business metrics."""
    if domain:
        metrics = metric_registry.get_metrics_by_domain(domain)
    else:
        metrics = metric_registry.get_all_metrics()
        
    return [
        MetricResponse(
            id=m["id"],
            name=m["name"],
            domain=m["domain"],
            description=m.get("description"),
            is_custom=False,
            supported_dimensions=m.get("supported_dimensions", []),
            supported_time_windows=m.get("supported_time_windows", []),
            formula=m["formula"]
        ) for m in metrics
    ]

@router.get("/{metric_id}", response_model=MetricResponse)
async def get_metric(metric_id: str):
    """Get a specific metric definition."""
    m = metric_registry.get_metric(metric_id)
    if not m:
        raise HTTPException(status_code=404, detail="Metric not found")
        
    return MetricResponse(
        id=m["id"],
        name=m["name"],
        domain=m["domain"],
        description=m.get("description"),
        is_custom=False,
        supported_dimensions=m.get("supported_dimensions", []),
        supported_time_windows=m.get("supported_time_windows", []),
        formula=m["formula"]
    )

@router.post("", response_model=MetricResponse)
async def create_custom_metric(req: CreateMetricRequest, db: Session = Depends(get_db)):
    """Create a new custom metric."""
    # MVP: Mock returning what was requested.
    # Production: Write to BusinessMetric, MetricDefinition, and MetricVersion via metric_version_manager
    return MetricResponse(
        id="custom_123",
        name=req.name,
        domain=req.domain,
        description=req.description,
        is_custom=True,
        supported_dimensions=req.supported_dimensions,
        supported_time_windows=req.supported_time_windows,
        formula=req.formula
    )

@router.get("/system/history", response_model=List[MetricHistoryResponse])
async def get_history(metric_id: str = None, db: Session = Depends(get_db)):
    """Get audit trail of metric changes."""
    query = db.query(MetricHistory)
    if metric_id:
        query = query.filter(MetricHistory.metric_id == metric_id)
        
    history = query.order_by(MetricHistory.timestamp.desc()).limit(100).all()
    
    return [
        MetricHistoryResponse(
            id=h.id,
            metric_id=h.metric_id,
            action=h.action,
            author=h.author or "system",
            timestamp=h.timestamp,
            changes=h.changes
        ) for h in history
    ]

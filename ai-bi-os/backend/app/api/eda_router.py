from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.eda import (
    RunEDARequest, EDARunResponse, EDAProfileResponse, 
    DatasetSummaryResponse, ColumnProfileResponse, 
    DistributionResponse, OutlierResponse
)
from app.services.eda.eda_service import eda_service
from app.models.eda import EDARun, EDAProfile, DatasetSummary, EDAColumnProfile

router = APIRouter(prefix="/api/v1/eda", tags=["eda"])

@router.post("/run", response_model=EDARunResponse)
async def run_eda(req: RunEDARequest, db: Session = Depends(get_db)):
    """Trigger an EDA run for a dataset."""
    try:
        result = eda_service.run_eda(
            db=db,
            dataset_id=req.dataset_id,
            dataset_version_id=req.dataset_version_id,
            schema_info=req.schema_info
        )
        return EDARunResponse(
            run_id=result["run_id"],
            status=result["status"],
            execution_time_ms=result["execution_time_ms"]
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dataset_version_id}", response_model=EDAProfileResponse)
async def get_eda_profile(dataset_version_id: str, db: Session = Depends(get_db)):
    """Get the full EDA profile for a dataset version."""
    run = db.query(EDARun).filter(
        EDARun.dataset_version_id == dataset_version_id,
        EDARun.status == "COMPLETED"
    ).order_by(EDARun.generated_at.desc()).first()
    
    if not run or not run.profile:
        raise HTTPException(status_code=404, detail="EDA Profile not found")
        
    p = run.profile
    s = p.summary
    
    col_responses = []
    for c in p.columns:
        spec_stats = None
        if c.data_type == "NUMERIC":
            spec_stats = c.numeric_stats
        elif c.data_type == "VARCHAR":
            spec_stats = c.text_stats
        elif c.data_type == "DATE":
            spec_stats = c.date_stats
            
        dist = None
        if c.distribution:
            dist = DistributionResponse(type=c.distribution.distribution_type, confidence=c.distribution.confidence_score)
            
        outs = None
        if c.outliers:
            outs = [OutlierResponse(method=o.method_used, value=o.value_flagged, score=o.score) for o in c.outliers]
            
        col_responses.append(ColumnProfileResponse(
            column_name=c.column_name,
            data_type=c.data_type,
            null_count=c.null_count,
            null_percentage=c.null_percentage,
            distinct_count=c.distinct_count,
            memory_usage_bytes=c.memory_usage_bytes,
            specific_stats=spec_stats,
            distribution=dist,
            outliers=outs
        ))
        
    return EDAProfileResponse(
        run_id=run.id,
        completeness_score=p.completeness_score,
        consistency_score=p.consistency_score,
        usability_score=p.usability_score,
        eda_quality_score=p.eda_quality_score,
        warnings=p.warnings or [],
        summary=DatasetSummaryResponse(
            total_rows=s.total_rows,
            total_columns=s.total_columns,
            dataset_size_bytes=s.dataset_size_bytes,
            memory_usage_bytes=s.memory_usage_bytes,
            numeric_columns=s.numeric_columns,
            categorical_columns=s.categorical_columns,
            date_columns=s.date_columns,
            boolean_columns=s.boolean_columns,
            text_columns=s.text_columns
        ),
        columns=col_responses
    )

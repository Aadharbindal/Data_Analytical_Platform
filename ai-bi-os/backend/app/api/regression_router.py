from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.regression import (
    TrainRegressionRequest, TrainRegressionResponse, PredictRequest, PredictionResponse,
    FeatureImportanceResponse, ResidualAnalysisResponse
)
from app.services.regression.regression_service import regression_service
from app.models.regression import RegressionModel, RegressionRun

router = APIRouter(prefix="/api/v1/regression", tags=["regression"])

@router.post("/train", response_model=TrainRegressionResponse)
async def train_regression(req: TrainRegressionRequest, db: Session = Depends(get_db)):
    """Trigger a regression model training run."""
    try:
        result = regression_service.train_model(
            db=db,
            dataset_id=req.dataset_id,
            dataset_version_id=req.dataset_version_id,
            model_name=req.model_name,
            algorithm=req.algorithm,
            target_variable=req.target_variable,
            dataset_stats=req.dataset_stats,
            all_features=req.all_features
        )
        return TrainRegressionResponse(**result)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict", response_model=List[PredictionResponse])
async def predict(req: PredictRequest, db: Session = Depends(get_db)):
    """Make predictions using the active version of a trained model."""
    try:
        results = regression_service.predict(db, req.model_id, req.inputs)
        return [PredictionResponse(**r) for r in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{id}/importance", response_model=List[FeatureImportanceResponse])
async def get_feature_importance(id: str, db: Session = Depends(get_db)):
    run = db.query(RegressionRun).join(RegressionRun.model).filter(
        RegressionModel.id == id,
        RegressionRun.status == "COMPLETED"
    ).order_by(RegressionRun.created_at.desc()).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Active model run not found")
        
    return [
        FeatureImportanceResponse(
            feature_name=fi.feature_name,
            importance_rank=fi.importance_rank,
            standardized_coefficient=fi.standardized_coefficient,
            p_value=fi.p_value,
            vif=fi.vif
        ) for fi in run.feature_importance
    ]

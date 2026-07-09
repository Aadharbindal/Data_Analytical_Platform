from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class TrainRegressionRequest(BaseModel):
    dataset_id: str
    dataset_version_id: str
    model_name: str
    algorithm: str
    target_variable: str
    dataset_stats: Dict[str, Any]
    all_features: List[str]

class PredictRequest(BaseModel):
    model_id: str
    inputs: List[Dict[str, float]]

class PredictionResponse(BaseModel):
    input_features: Dict[str, float]
    predicted_value: float
    confidence_lower: Optional[float]
    confidence_upper: Optional[float]

class TrainRegressionResponse(BaseModel):
    model_id: str
    version: int
    run_id: str
    status: str
    metrics: Dict[str, float]

class FeatureImportanceResponse(BaseModel):
    feature_name: str
    importance_rank: int
    standardized_coefficient: float
    p_value: Optional[float]
    vif: Optional[float]

class ResidualAnalysisResponse(BaseModel):
    residual_mean: float
    residual_variance: float
    normality_test_stat: Optional[float]
    normality_p_value: Optional[float]
    homoscedasticity_test_stat: Optional[float]
    homoscedasticity_p_value: Optional[float]

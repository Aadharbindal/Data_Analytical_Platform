from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class DistributionColumnRequest(BaseModel):
    name: str
    type: str
    valid_count: int

class RunDistributionRequest(BaseModel):
    dataset_id: str
    dataset_version_id: str
    columns: List[DistributionColumnRequest]

class DistributionRunResponse(BaseModel):
    run_id: str
    status: str
    columns_processed: int
    execution_time_ms: float

class GoodnessOfFitSchema(BaseModel):
    test_name: str
    test_statistic: float
    p_value: float
    rejected: bool

class DistributionFitSchema(BaseModel):
    distribution_type: str
    is_best_fit: bool
    log_likelihood: Optional[float]
    aic: Optional[float]
    bic: Optional[float]
    parameters: List[Dict[str, float]]
    gof_results: List[GoodnessOfFitSchema]

class DensityProfileSchema(BaseModel):
    kde_x: Optional[List[float]]
    kde_y: Optional[List[float]]
    histogram_bins: Optional[List[float]]
    histogram_counts: Optional[List[int]]

class DistributionProfileResponse(BaseModel):
    column_name: str
    column_type: str
    mean: Optional[float]
    median: Optional[float]
    variance: Optional[float]
    skewness: Optional[float]
    kurtosis: Optional[float]
    entropy: Optional[float]
    is_heavy_tail: Optional[bool]
    modality: Optional[str]
    best_fit: Optional[str]
